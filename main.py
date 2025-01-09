
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import json
from flask import Flask, request, redirect, render_template, jsonify, session, Response, stream_with_context
import requests
from urllib.parse import quote
from cryptography.fernet import Fernet
import json

import os
app = Flask(__name__)
app.secret_key = os.urandom(12).hex()


# Client Keys and Config
APPSCRIPT_URL = """
https://script.google.com/macros/s/AKfycbyyK5PAIKy6EypJGQ87ELIA2x0Zeu_jq8vNHWWvb3YOww4GRLFk7UUN4fcLu10NtMcD/exec
""".strip()
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



def get_or_create_key():
    key_file = 'secret.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    key = Fernet.generate_key()
    with open(key_file, 'wb') as f:
        f.write(key)
    return key


class SpotifyAuthManager:
    def __init__(self, cipher_suite):
        self.cipher_suite = cipher_suite
        
    def get_spotify_client(self):
        creds = self.load_credentials()
        if not creds or 'access_token' not in session:
            return None
            
        global CLIENT_ID, CLIENT_SECRET
        CLIENT_ID = creds['client_id']
        CLIENT_SECRET = creds['client_secret']
        
        sp = spotipy.Spotify(auth=session['access_token'], requests_timeout=30)
        try:
            sp.current_user()
            return sp
        except spotipy.exceptions.SpotifyException:
            return sp if self.refresh_token() else None

    def check_auth(self):
        return 'access_token' in session and self.get_spotify_client() is not None

    def load_credentials(self):
        try:
            with open('spotify_creds.enc', 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except:
            return None

    def save_credentials(self, client_id, client_secret):
        creds = {'client_id': client_id, 'client_secret': client_secret}
        encrypted_data = self.cipher_suite.encrypt(json.dumps(creds).encode())
        with open('spotify_creds.enc', 'wb') as f:
            f.write(encrypted_data)

    def get_credentials(self):
        creds = self.load_credentials()
        return (creds['client_id'], creds['client_secret']) if creds else (None, None)

    def get_auth_params(self):
        client_id, _ = self.get_credentials()
        return {
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPE,
            "client_id": client_id
        }

    def refresh_token(self):
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

# Initialize auth manager
auth_manager = SpotifyAuthManager(Fernet(get_or_create_key()))

# Route handlers
@app.route("/")
def index():
    return redirect('/profile' if not auth_manager.load_credentials() else '/auth')

@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
        if client_id and client_secret:
            auth_manager.save_credentials(client_id, client_secret)
            return redirect('/auth')
    
    return render_template("profile.html", creds=auth_manager.load_credentials())

@app.route("/auth")
def auth():
    client_id, _ = auth_manager.get_credentials()
    if not client_id:
        return redirect('/profile')
    
    auth_params = auth_manager.get_auth_params()
    url_args = "&".join([f"{key}={quote(val)}" for key, val in auth_params.items()])
    return redirect(f"{SPOTIFY_AUTH_URL}/?{url_args}")

@app.route("/callback/")
def callback():
    client_id, client_secret = auth_manager.get_credentials()
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(request.args['code']),
        "redirect_uri": REDIRECT_URI,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    
    response_data = requests.post(SPOTIFY_TOKEN_URL, data=code_payload).json()
    session['access_token'] = response_data["access_token"]
    session['refresh_token'] = response_data["refresh_token"]
    return redirect('/dashboard')

@app.route("/dashboard")
def dashboard():
    return redirect('/auth') if not auth_manager.check_auth() else render_template("dashboard.html")



@app.route("/api/fetch-playlists", methods=['POST'])
def fetch_playlists():
    if not auth_manager.check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
        
    channel_id = request.json.get('channelId')
    
    # Call AppScript API
    response = requests.post(APPSCRIPT_URL, json={
        "action": "getPlaylists",
        "channelId": channel_id
    },timeout=60)
    
    return jsonify(response.json())

@app.route("/api/import-playlists")
def import_playlists():
    def generate():
        sp = auth_manager.get_spotify_client()
        if not sp:
            yield f"data: error: Not authenticated\n\n"
            return

        playlists = json.loads(request.args.get('playlists'))
        user_profile = sp.current_user()

        for playlist in playlists:
            message = f"Starting import of playlist: {playlist['playlistName']}"
            yield f"data: {message}\n\n"

            try:
                # Get video details from AppScript
                video_response = requests.post(APPSCRIPT_URL, json={
                    "action": "getVideoDetails",
                    "playlistId": playlist['playlistId']
                } ,timeout=60)
                videos = video_response.json()

                # Handle Spotify playlist creation and track addition
                current_playlists = sp.current_user_playlists()
                for existing_playlist in current_playlists['items']:
                    if existing_playlist['name'] == playlist['playlistName']:
                        sp.current_user_unfollow_playlist(existing_playlist['id'])
                        yield f"data: Removed existing playlist: {playlist['playlistName']}\n\n"

                new_playlist = sp.user_playlist_create(user_profile['id'], playlist['playlistName'])
                batch_size = 50
                track_ids = []

                for video in videos:
                    try:
                        if video['title'] == "Deleted video":
                            continue

                        # Use AppScript's Gemini search
                        parsed_response = requests.post(APPSCRIPT_URL, json={
                            "action": "searchWithGemini",
                            "videoTitle": video['title'],
                            "channelName": video['artist']
                        } ,timeout=60)
                        parsed_details = parsed_response.json()

                        search_query = (f"track:{parsed_details['title']} artist:{parsed_details['artist']}"
                                      if parsed_details['artist'].strip() != "" and parsed_details['artist'].strip().lower() != "blank"
                                      else f"track:{parsed_details['title']}")
                        
                        search_results = sp.search(q=search_query, type='track', limit=3)
                        tracks = [track for track in search_results['tracks']['items']
                                if 'podcast' not in track['name'].lower()]

                        if tracks:
                            track = tracks[0]
                            track_ids.append(track['id'])
                            message = f"success: Found {track['name']} by {track['artists'][0]['name']}"
                            yield f"data: {message}\n\n"

                            if len(track_ids) >= batch_size:
                                sp.playlist_add_items(new_playlist['id'], track_ids)
                                yield f"data: success: Added batch of {len(track_ids)} tracks\n\n"
                                track_ids = []
                        else:
                            yield f"data: warning: Not found: {video['title']}\n\n"

                    except Exception as e:
                        yield f"data: error: Failed to process {video['title']} - {str(e)}\n\n"

                if track_ids:
                    sp.playlist_add_items(new_playlist['id'], track_ids)
                    yield f"data: success: Added final batch of {len(track_ids)} tracks\n\n"

                yield f"data: success: Created playlist '{playlist['playlistName']}' - {new_playlist['external_urls']['spotify']}\n\n"

            except Exception as e:
                yield f"data: error: Failed to import playlist {playlist['playlistName']} - {str(e)}\n\n"

        yield "data: All imports completed\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(debug=False, port=PORT)