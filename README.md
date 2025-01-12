# Playlist Import API

## API Endpoints

### POST /api/credentials
Sets the Spotify credentials.

**Request Body:**
```json
{
    "client_id": "your_spotify_client_id",
    "client_secret": "your_spotify_client_secret"
}
```

**Response:**
```json
{
    "status": "success"
}
```

---

### GET /api/auth-status
Checks the authentication status.

**Response:**
```json
{
    "authenticated": boolean,
    "has_credentials": boolean
}
```

---

### POST /api/fetch-playlists
Fetches playlists from a specified YouTube channel.

**Request Body:**
```json
{
    "channelId": "YOUTUBE_CHANNEL_ID"
}
```

**Response:**
```json
[
    {
        "playlistId": "string",
        "playlistName": "string"
    },
    {
        "playlistId": "string",
        "playlistName": "string"
    }
]
```

---

### GET /api/import-playlists
Imports playlists from YouTube to Spotify.

**Request Query Parameters:**
```json
playlists=[
    {"playlistId":"PLH0cqYRIH9", "playlistName":"Rock Classics"},
    {"playlistId":"PLJ8cMiYb3", "playlistName":"Summer Hits"}
]
```

**Example Import Log:**
```
data: Starting import of playlist: Rock Classics

data: success: Found Stairway to Heaven by Led Zeppelin
data: success: Found Sweet Child O' Mine by Guns N' Roses
data: success: Added batch of 50 tracks
data: warning: Not found: Rare Live Performance
data: success: Created playlist 'Rock Classics' - https://open.spotify.com/playlist/...

data: Starting import of playlist: Summer Hits

data: success: Found Blinding Lights by The Weeknd
data: success: Found Dance Monkey by Tones and I
data: success: Added batch of 50 tracks
data: success: Created playlist 'Summer Hits' - https://open.spotify.com/playlist/...

data: All imports completed
```

---

## JavaScript Function for Playlist Import
The following JavaScript function handles importing playlists on the dashboard:

```javascript
async function importSelectedPlaylists() {
    const selected = Array.from(document.querySelectorAll('.playlist-checkbox:checked'))
        .map(checkbox => ({
            playlistId: checkbox.id,
            playlistName: checkbox.nextElementSibling.textContent.trim()
        }));

    if (selected.length === 0) {
        alert('Please select at least one playlist');
        return;
    }

    const progressLog = document.getElementById('progressLog');
    progressLog.innerHTML = '';
    document.getElementById('progressContainer').classList.remove('hidden');

    const eventSource = new EventSource(`/api/import-playlists?playlists=${encodeURIComponent(JSON.stringify(selected))}`);

    eventSource.onmessage = function (event) {
        const p = document.createElement('p');
        const data = event.data;

        if (data.includes('success:')) {
            p.className = 'text-green-600';
            const message = data.replace('success:', '').trim();
            p.innerHTML = message.includes('spotify') ?
                `${message.split(' - ')[0]} - <a href="${message.split(' - ')[1]}" target="_blank" class="text-blue-500 hover:underline">${message.split(' - ')[1]}</a>` :
                message;
        } else if (data.includes('warning:')) {
            p.className = 'text-yellow-600';
            p.textContent = data.replace('warning:', '').trim();
        } else if (data.includes('error:')) {
            p.className = 'text-red-600';
            p.textContent = data.replace('error:', '').trim();
        } else {
            p.textContent = data;
        }

        progressLog.appendChild(p);
        progressLog.scrollTop = progressLog.scrollHeight;
        document.addEventListener('keydown', function (event) {
            if (event.key === 'ArrowDown') {
                progressLog.scrollTop = progressLog.scrollHeight;
            }
        });

        if (data === 'All imports completed') {
            importInProgress = false;
            document.getElementById('importButton').style.display = 'block';
            eventSource.close();
        }
    };
}
```

---

