import json
import re
from googleapiclient.discovery import build
from secret import GOOGLE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

channelid = "UCW15L5aHUcW6sS_NPUYkd0A"

def get_channel_playlists(youtube_service, channelid="UCW15L5aHUcW6sS_NPUYkd0A"):
    request = youtube_service.playlists().list(
        part='contentDetails,snippet', channelId=channelid, maxResults=50
    )
    response = request.execute()
    playlist_dict = {item['snippet']['title'] :item['id'] for item in response['items']}
    print(playlist_dict ,"\n============================\n")
    return playlist_dict

def clean_song_title(title):
    # Manual replacements dictionary
    manual_replacements = {
        " (Official Music Video)": "",
        " (Official Video)": "",
        " (Official Audio)": "",
        " (Audio)": "",
        " (Official Lyric Video)": "",
        " (Lyrics)": "",
        " [Official Video]": "",
        " [Official Audio]": "",
        " [Lyrics]": "",
        " | Malayalam Rap": "",
        " - Topic": "",
        " HD": "",
        " HQ": "",
        " 4K": "",
        " (HD)": "",
        " (HQ)": "",
        " (4K)": "",
        "VEVO": "",
        "Lyrics": "",
        "Video": "",
        "Official": ""

    }
    
    cleaned_title = title
    for old_text, new_text in manual_replacements.items():
        cleaned_title = cleaned_title.replace(old_text, new_text)
    
    # Remove extra whitespace and trim
    cleaned_title = ' '.join(cleaned_title.split())
    
    return cleaned_title.strip()



def get_playlist_video_details(youtube_service, playlist_id = "PLJHtzsPP5ijNPtDWQtrg_QS7GmWPZAfvD"):
    page_token = None
    video_details = []
    while True:
        request = youtube_service.playlistItems().list(
            part='snippet', playlistId=playlist_id, maxResults=50, pageToken=page_token
        )
        response = request.execute()
        video_details.extend([{
            'title': clean_song_title(item['snippet']['title']), 
            'artist': item['snippet'].get('videoOwnerChannelTitle', '').replace("- Topic", "").strip()
        } for item in response['items']])
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    return video_details



def get_all_songs(youtube_service ,channel_id="UCW15L5aHUcW6sS_NPUYkd0A"):
    playlists = get_channel_playlists(youtube_service, channel_id)
    all_songs = {}
    for playlist_name, playlist_id in playlists.items():
        all_songs[playlist_name] = get_playlist_video_details(youtube_service, playlist_id)
    print(all_songs, "\n======================\n")
    return all_songs

youtube_service = build("youtube", "v3", developerKey=GOOGLE_API_KEY)

all_songs = get_all_songs(youtube_service)
all_songs_json = json.dumps(all_songs, indent=4)
with open('songs.json', 'w', encoding='utf8') as f:
    json.dump(all_songs, f, ensure_ascii=False, indent=4)