
from secret import GOOGLE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, GEMINI_API_KEY
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import json
from googleapiclient.discovery import build
from flask import Flask, request, redirect, render_template, jsonify, session, Response, stream_with_context
import requests
from urllib.parse import quote
from youtube import get_channel_playlists, get_playlist_video_details
import google.generativeai as genai
from gemini_ai import GeminiAI, VideoDetailsParser
import time
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize services
youtube_service = build("youtube", "v3", developerKey=GOOGLE_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
gemini_ai = GeminiAI(api_key=GEMINI_API_KEY, model_name="gemini-1.5-flash")
parser = VideoDetailsParser(gemini_ai)

# Client Keys and Config
CLIENT_ID = SPOTIFY_CLIENT_ID
CLIENT_SECRET = SPOTIFY_CLIENT_SECRET
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = f"{SPOTIFY_API_BASE_URL}/{API_VERSION}"

# Server Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = f"{CLIENT_SIDE_URL}:{PORT}/callback/"
SCOPE = "playlist-modify-public playlist-modify-private playlist-read-private"

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "client_id": CLIENT_ID
}

def refresh_spotify_token():
    if 'refresh_token' not in session:
        return False
    
    refresh_payload = {
        'grant_type': 'refresh_token',
        'refresh_token': session['refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    response = requests.post(SPOTIFY_TOKEN_URL, data=refresh_payload)
    if response.status_code == 200:
        token_data = response.json()
        session['access_token'] = token_data['access_token']
        if 'refresh_token' in token_data:
            session['refresh_token'] = token_data['refresh_token']
        return True
    return False

def get_spotify_client():
    if 'access_token' not in session:
        return None
    sp = spotipy.Spotify(auth=session['access_token'], requests_timeout=20)
    try:
        sp.current_user()
        return sp
    except spotipy.exceptions.SpotifyException:
        if refresh_spotify_token():
            sp = spotipy.Spotify(auth=session['access_token'], requests_timeout=20)
            return sp
        return None

def check_auth():
    if 'access_token' not in session:
        return False
    sp = get_spotify_client()
    return sp is not None

@app.route("/")
def index():
    return redirect('/') if not check_auth() else render_template('dashboard.html')

@app.route("/auth")
def auth():
    url_args = "&".join([f"{key}={quote(val)}" for key, val in auth_query_parameters.items()])
    return redirect(f"{SPOTIFY_AUTH_URL}/?{url_args}")

@app.route("/callback/")
def callback():
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(request.args['code']),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    
    response_data = requests.post(SPOTIFY_TOKEN_URL, data=code_payload).json()
    session['access_token'] = response_data["access_token"]
    session['refresh_token'] = response_data["refresh_token"]
    return redirect('/dashboard')

@app.route("/dashboard")
def dashboard():
    return redirect('/auth') if not check_auth() else render_template("dashboard.html")

@app.route("/api/fetch-playlists", methods=['POST'])
def fetch_playlists():
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    channel_id = request.json.get('channelId')
    playlists = get_channel_playlists(youtube_service, channel_id)
    return jsonify(playlists)

@app.route("/api/import-playlists")
def import_playlists():
    def generate():
        sp = get_spotify_client()
        if not sp:
            yield f"data: error: Not authenticated\n\n"
            return

        playlists = json.loads(request.args.get('playlists'))
        user_profile = sp.current_user()

        for playlist in playlists:
            message = f"Starting import of playlist: {playlist['playlistName']}"
            yield f"data: {message}\n\n"
            
            try:
                sp = get_spotify_client()
                # Unfollow existing playlists with same name
                current_playlists = sp.current_user_playlists()
                for existing_playlist in current_playlists['items']:
                    if existing_playlist['name'] == playlist['playlistName']:
                        sp.current_user_unfollow_playlist(existing_playlist['id'])
                        yield f"data: Removed existing playlist: {playlist['playlistName']}\n\n"

                new_playlist = sp.user_playlist_create(user_profile['id'], playlist['playlistName'])
                videos = get_playlist_video_details(youtube_service, playlist['playlistId'])
                
                for video in videos:
                    try:
                        sp = get_spotify_client()
                        if video['title']=="Deleted video":
                            continue
                        if 'release' == video['title'].lower():
                            video["title"] = ""
                            search_results = sp.search(q=f"track:{video['title']}", type='track', limit=3)
                        else:
                            search_results = sp.search(q=f"track:{video['title']} artist:{video['artist']}", type='track', limit=3)
                        tracks = [track for track in search_results['tracks']['items'] if 'podcast' not in track['name'].lower()]
                        
                        if not tracks:
                            parsed_details = parser.parse_video_details(video['title'], video['artist'])
                            sp = get_spotify_client()
                            search_results = sp.search(
                                q=f"track:{parsed_details['title']} artist:{parsed_details['artist']}", 
                                type='track', 
                                limit=3
                            )
                            tracks = [track for track in search_results['tracks']['items'] if 'podcast' not in track['name'].lower()]
                            print(f"Gemini")
                        if tracks:
                            track = tracks[0]
                            sp = get_spotify_client()
                            sp.playlist_add_items(new_playlist['id'], [track['id']])
                            message = f"success: Added {track['name']} by {track['artists'][0]['name']}"
                            yield f"data: {message}\n\n"
                            print(message.split(':',1)[1])
                        else:
                            message = f"warning: Not found: {video['title']}"
                            yield f"data: {message}\n\n"
                            print(message.split(':',1)[1])
                            
                    except Exception as e:
                        message = f"error: Failed to process {video['title']} - {str(e)}"
                        yield f"data: {message}\n\n"
                        print(message.split(':',1)[1])
                    
                    # Ensure only two requests per second
                    time.sleep(0.5)
                
                message = f"success: Created playlist '{playlist['playlistName']}' - {new_playlist['external_urls']['spotify']}"
                yield f"data: {message}\n\n"
                print(message.split(':',1)[1])
                
            except Exception as e:
                message = f"error: Failed to import playlist {playlist['playlistName']} - {str(e)}"
                yield f"data: {message}\n\n"
                print(message.split(':',1)[1])
        
        yield "data: All imports completed\n\n"
        print("All imports completed")

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(debug=True, port=PORT)
