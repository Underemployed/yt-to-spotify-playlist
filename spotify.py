# UNDEREMPLOYED
# 9/6/2024
from secret import GOOGLE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

from spotipy.oauth2 import SpotifyOAuth
import spotipy
import json
from flask import Flask, request, redirect, g, render_template
import requests
from urllib.parse import quote

app = Flask(__name__)

#  Client Keys
CLIENT_ID = SPOTIFY_CLIENT_ID
CLIENT_SECRET = SPOTIFY_CLIENT_SECRET

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
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}


@app.route("/")
def index():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/")
def callback():
    # Auth Step 2: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, timeout=10)
    # Auth Step 3: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]
    sp = spotipy.Spotify(auth=access_token)

    # Auth Step 4: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    # Create a dictionary to store existing playlists
    existing_playlists = {playlist['name']: playlist for playlist in playlist_data['items']}

    with open('songs.json', 'r', encoding='utf8') as f:
        all_songs = json.load(f)

    for playlist_name, songs in all_songs.items():
        # If the playlist already exists, unfollow all of them
        if playlist_name in existing_playlists:
            playlists_same_name = [playlist for playlist in playlist_data['items'] if playlist['name'] == playlist_name]
            for playlist in playlists_same_name:
                sp.current_user_unfollow_playlist(playlist['id'])
            del existing_playlists[playlist_name]

        # Create a new playlist
        playlist = sp.user_playlist_create(profile_data['id'], playlist_name)

        # Get the playlist ID
        playlist_id = playlist['id']

        # For each song in the playlist
        for song in songs:
            # Search for the song by title and artist
            results = sp.search(q='artist:' + song['artist'] + ' track:' + song['title'], type='track')

            # If the song was found
            if results['tracks']['items']:
                # Get the first song from the search results
                track = results['tracks']['items'][0]

                # Get the song ID
                track_id = track['id']

                # Add the song to the playlist
                sp.playlist_add_items(playlist_id, [track_id])


    # Combine profile and playlist data to display
    display_arr = [profile_data] + playlist_data["items"]
    return render_template("index.html", sorted_array=display_arr)

if __name__ == "__main__":
    app.run(debug=True, port=PORT)