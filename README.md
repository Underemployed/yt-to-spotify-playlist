# Playlist Import API

## API Endpoints


### POST /login
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

### GET /logout
Logs out the user.

**Response:**
```json
{
    "status": "success"
}
```

---

### GET /api/auth-status
Gets the authentication status.

**Response:**
```json
{
    "authenticated": boolean,
    "has_credentials": boolean
}
```

---

### GET /api/user-profile
Gets the User Profile (image URL can be null).

**Response:**
```json
{
    "display_name": "John Doe",
    "image_url": "https://profile-image.spotify.com/user/..." | null
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
## Workflow

### 1. Initial Setup
1. User visits React frontend.
2. Frontend displays credential input form.
3. User enters Spotify Client ID and Secret.
4. Frontend calls POST /login with credentials.

### 2. Spotify Authentication
1. After successful credential save, frontend shows "Connect to Spotify" button.
2. Button click redirects to Spotify auth page.
3. User authorizes the application.
4. Callback redirects to frontend dashboard.

### 3. Dashboard Operations
1. Frontend checks auth status via GET /api/auth-status.
2. Loads user profile via GET /api/user-profile.
3. User enters YouTube channel ID.
4. Frontend fetches playlists via POST /api/fetch-playlists.
5. User selects playlists to import.

### 4. Import Process
1. Frontend initiates EventSource connection to /api/import-playlists.
2. Backend processes each playlist:
    - Fetches video details.
    - Matches songs using Gemini AI.
    - Creates Spotify playlist.
    - Adds tracks in batches.
3. Frontend displays real-time progress.
4. Process completes with playlist links.

### 5. Session Management
1. User can logout via GET /logout.
2. Frontend handles auth state changes.
3. Token refresh happens automatically.
