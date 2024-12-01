from secret import GOOGLE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import json
from googleapiclient.discovery import build
from flask import Flask, request, redirect, g, render_template, make_response, jsonify, session
import requests
from urllib.parse import quote
from youtube import get_channel_playlists, get_playlist_video_details

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Client Keys and Config
CLIENT_ID = SPOTIFY_CLIENT_ID
CLIENT_SECRET = SPOTIFY_CLIENT_SECRET
COOKIE_DURATION = 3600
SECURE_COOKIES = False

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private"

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "client_id": CLIENT_ID
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/auth")
def auth():
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/callback/")
def callback():
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    
    session['access_token'] = access_token
    session['refresh_token'] = refresh_token
    
    return redirect('/dashboard')

@app.route("/dashboard")
def dashboard():
    if 'access_token' not in session:
        return redirect('/auth')
    return render_template("dashboard.html")

@app.route("/api/fetch-playlists", methods=['POST'])
def fetch_playlists():
    channel_id = request.json.get('channelId')
    youtube_service = build("youtube", "v3", developerKey=GOOGLE_API_KEY)
    playlists = get_channel_playlists(youtube_service, channel_id)
    return jsonify(playlists)

from flask import Response, stream_with_context

@app.route("/api/import-playlists")
def import_playlists():
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    def generate():
        playlists = json.loads(request.args.get('playlists'))
        sp = spotipy.Spotify(auth=session['access_token'])
        youtube_service = build("youtube", "v3", developerKey=GOOGLE_API_KEY)
        
        for playlist in playlists:
            message = f"Starting import of playlist: {playlist['playlistName']}"
            print(message)
            yield f"data: {message}\n\n"
            
            try:
                user_profile = sp.current_user()
                print(sp.current_user)
                # Unfollow existing playlists with same name
                message = f"Checking for existing playlists named: {playlist['playlistName']}"
                print(message)
                yield f"data: {message}\n\n"
                
                existing_playlists = sp.current_user_playlists()
                print(existing_playlists)
                for existing_playlist in existing_playlists['items']:
                    if existing_playlist['name'] == playlist['playlistName']:
                        message = f"Unfollowing existing playlist: {playlist['playlistName']}"
                        print(message)
                        yield f"data: {message}\n\n"
                        sp.current_user_unfollow_playlist(existing_playlist['id'])
                
                new_playlist = sp.user_playlist_create(user_profile['id'], playlist['playlistName'])
                videos = get_playlist_video_details(youtube_service, playlist['playlistId'])
                
                for video in videos:
                    try:
                        search_results = sp.search(q=f"track:{video['title']} artist:{video['artist']}", type='track', limit=1)
                        if search_results['tracks']['items']:
                            track = search_results['tracks']['items'][0]
                            sp.playlist_add_items(new_playlist['id'], [track['id']])
                            message = f"success: Added {video['title']} by {video['artist']}"
                            # print(message)
                            yield f"data: {message}\n\n"
                        else:
                            message = f"warning: Not found: {video['title']} by {video['artist']}"
                            print(message)
                            yield f"data: {message}\n\n"
                    except Exception as e:
                        message = f"error: Failed to process {video['title']}: {str(e)}"
                        print(message)
                        yield f"data: {message}\n\n"
                
                message = f"success: Created playlist '{playlist['playlistName']}' - {new_playlist['external_urls']['spotify']}"
                print(message)
                yield f"data: {message}\n\n"
            except Exception as e:
                message = f"error: Failed to import playlist {playlist['playlistName']}: {str(e)}"
                print(message)
                yield f"data: {message}\n\n"
        
        message = "All imports completed"
        # print(message)
        yield f"data: {message}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(debug=False, port=PORT)

