import json
import time
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import praw
from googleapiclient.discovery import build

# ---------------------------------
# CONFIGURATION & CREDENTIALS
# ---------------------------------

# Spotify credentials (replace with your actual credentials)
SPOTIFY_CLIENT_ID = 'YOUR_SPOTIFY_CLIENT_ID'
SPOTIFY_CLIENT_SECRET = 'YOUR_SPOTIFY_CLIENT_SECRET'

# Reddit credentials (replace with your actual credentials)
REDDIT_CLIENT_ID = 'YOUR_REDDIT_CLIENT_ID'
REDDIT_CLIENT_SECRET = 'YOUR_REDDIT_CLIENT_SECRET'
REDDIT_USER_AGENT = 'hiphop_data_project/0.1'

# YouTube API key (replace with your actual API key)
YOUTUBE_API_KEY = 'YOUR_YOUTUBE_API_KEY'

# ---------------------------------
# SETUP API CLIENTS
# ---------------------------------

# Spotify client using Spotipy
spotify_auth_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID, 
    client_secret=SPOTIFY_CLIENT_SECRET
)
sp = spotipy.Spotify(auth_manager=spotify_auth_manager)

# Reddit client using PRAW
reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                     client_secret=REDDIT_CLIENT_SECRET,
                     user_agent=REDDIT_USER_AGENT)

# YouTube client using google-api-python-client
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# ---------------------------------
# FUNCTIONS TO FETCH DATA
# ---------------------------------

def fetch_spotify_data_for_artist(artist_name):
    """
    Fetch artist details (including followers and popularity),
    top tracks, and audio features for each track from Spotify.
    """
    results = sp.search(q=artist_name, type='artist', limit=1)
    if not results['artists']['items']:
        return {}
    
    artist = results['artists']['items'][0]
    artist_id = artist['id']
    artist_data = {
        'artist_name': artist['name'],
        'artist_id': artist_id,
        'followers': artist['followers']['total'],
        'popularity': artist['popularity']
    }
    
    # Fetch top tracks
    top_tracks_data = sp.artist_top_tracks(artist['uri'])
    tracks = []
    for track in top_tracks_data['tracks']:
        track_info = {
            'track_name': track['name'],
            'track_id': track['id'],
            'track_popularity': track['popularity'],
            'preview_url': track.get('preview_url')
        }
        # Fetch audio features for the track
        features = sp.audio_features([track['id']])[0]
        if features:
            track_info['audio_features'] = {
                'danceability': features.get('danceability'),
                'energy': features.get('energy'),
                'speechiness': features.get('speechiness'),
                'acousticness': features.get('acousticness'),
                'instrumentalness': features.get('instrumentalness'),
                'liveness': features.get('liveness'),
                'loudness': features.get('loudness'),
                'tempo': features.get('tempo'),
                'valence': features.get('valence')
            }
        tracks.append(track_info)
    
    artist_data['top_tracks'] = tracks
    return artist_data

def fetch_reddit_data_for_artist(artist_name, subreddits=['hiphopheads']):
    """
    Fetch up to 10 posts from each specified subreddit that mention the artist.
    For each post, capture key metrics such as title, score, comment count, upvote ratio, URL, and creation time.
    """
    posts = []
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        # Use search to get posts relevant to the artist
        for submission in subreddit.search(artist_name, sort='hot', limit=10):
            posts.append({
                'subreddit': subreddit_name,
                'title': submission.title,
                'score': submission.score,
                'num_comments': submission.num_comments,
                'upvote_ratio': getattr(submission, 'upvote_ratio', None),
                'url': submission.url,
                'created_utc': submission.created_utc
            })
    return posts

def fetch_youtube_data_for_artist(artist_name):
    """
    Fetch top 10 YouTube videos for the query "artist_name official music video"
    and then retrieve additional statistics (views, likes, dislikes, comment count).
    """
    query = f"{artist_name} official music video"
    search_request = youtube.search().list(
        part='snippet',
        q=query,
        type='video',
        maxResults=10
    )
    search_response = search_request.execute()
    
    videos = []
    video_ids = []
    for item in search_response.get('items', []):
        video_id = item['id']['videoId']
        video_ids.append(video_id)
        videos.append({
            'videoId': video_id,
            'title': item['snippet']['title'],
            'description': item['snippet']['description'],
            'publishedAt': item['snippet']['publishedAt']
        })
    
    # Fetch detailed statistics for each video
    if video_ids:
        stats_request = youtube.videos().list(
            part='statistics',
            id=','.join(video_ids)
        )
        stats_response = stats_request.execute()
        stats_dict = {}
        for video in stats_response.get('items', []):
            stats_dict[video['id']] = video.get('statistics', {})
        for video in videos:
            video['statistics'] = stats_dict.get(video['videoId'], {})
    
    return videos

# ---------------------------------
# MAIN FUNCTION: AGGREGATE DATA
# ---------------------------------

def main():
    # Define a list of hip-hop artists. This focused list will allow for more consistent insights.
    artists = [
        "Eminem", "Drake", "Kendrick Lamar", "J. Cole",
        "Nicki Minaj", "Cardi B", "Travis Scott", "Migos",
        "Post Malone", "Lil Wayne", "Future", "Meek Mill"
    ]
    
    aggregated_data = []
    
    for artist in artists:
        print(f"Fetching data for {artist}...")
        spotify_data = fetch_spotify_data_for_artist(artist)
        reddit_data = fetch_reddit_data_for_artist(artist)  # Using hiphopheads as the primary subreddit
        youtube_data = fetch_youtube_data_for_artist(artist)
        
        artist_data = {
            'artist': artist,
            'spotify': spotify_data,
            'reddit': reddit_data,
            'youtube': youtube_data,
            'timestamp': time.time()
        }
        aggregated_data.append(artist_data)
        
        # Sleep to avoid API rate limits
        time.sleep(random.uniform(1, 2))
    
    # Save the aggregated data to a JSON file.
    output_filename = "aggregated_hiphop_data.json"
    with open(output_filename, "w") as outfile:
        json.dump(aggregated_data, outfile, indent=2)
    
    print(f"Data collection complete. Aggregated data saved to {output_filename}")

if __name__ == '__main__':
    main()
