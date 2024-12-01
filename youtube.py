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

def clean_song_title_and_artist(title, artist):
    # Regular expression pattern to remove unwanted parts from title
    title_pattern = r"(\s*\(.*?\)|\s*\[.*?\]|\s*-\s*Topic\s*$|feat.*|ft.*| - Topic)"
    artist_pattern = r"(\s*VEVO|\s*Official.*|\s*Music.*|\s*-\s*Topic\s*$)"

    # Remove unwanted parts using regex
    cleaned_title = re.sub(title_pattern, '', title, flags=re.IGNORECASE)
    cleaned_artist = re.sub(artist_pattern, '', artist, flags=re.IGNORECASE)

    # Remove extra whitespace and trim
    cleaned_title = ' '.join(cleaned_title.split())
    cleaned_artist = ' '.join(cleaned_artist.split())
    # print(cleaned_title, " by ",cleaned_artist)
    return cleaned_title.strip(), cleaned_artist.strip()

def get_playlist_video_details(youtube_service, playlist_id="PLJHtzsPP5ijNPtDWQtrg_QS7GmWPZAfvD"):
    page_token = None
    video_details = []
    while True:
        request = youtube_service.playlistItems().list(
            part='snippet', playlistId=playlist_id, maxResults=50, pageToken=page_token
        )
        response = request.execute()
        for item in response['items']:
            title, artist = clean_song_title_and_artist(item['snippet']['title'], item['snippet'].get('videoOwnerChannelTitle', ''))
            video_details.append({'title': title, 'artist': artist})
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
if __name__ == "__main__":
    youtube_service = build("youtube", "v3", developerKey=GOOGLE_API_KEY)

    all_songs = get_all_songs(youtube_service)
    all_songs_json = json.dumps(all_songs, indent=4)
    with open('songs.json', 'w', encoding='utf8') as f:
        json.dump(all_songs, f, ensure_ascii=False, indent=4)