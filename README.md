# Youtube to Spotify Porter

Convert YouTube playlists to Spotify playlists with intelligent song matching powered by Gemini AI.  



## Setup  

1. Clone the repository:  
    ```bash
    git clone https://github.com/Underemployed/yt-to-spotify-playlist.git
    cd yt-to-spotify-playlist
    ```

2. Create `secret.py` from template:  
    ```python
    # YouTube API Key  
    # Get from: https://console.cloud.google.com/apis/dashboard  
    GOOGLE_API_KEY = "your_youtube_api_key"  

    # Spotify API Keys  
    # Get from: https://developer.spotify.com/dashboard  
    SPOTIFY_CLIENT_ID = "your_spotify_client_id"  
    SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret"  

    # Gemini API Keys  
    # Get from: https://ai.google.dev/gemini-api/docs/text-generation?lang=python  
    GEMINI_API_KEYS = [
        "gemini_api_key_1",
        "gemini_api_key_2",
        "gemini_api_key_3",
        "gemini_api_key_4"
    ]
    ```  

3. Install dependencies:  
    ```bash
    pip install -r requirements.txt
    ```  

4. Run the app:  
    ```bash
    python main.py
    ```  

5. Access at: [http://localhost:8080](http://localhost:8080)  

## Usage  

1. Log in with your Spotify account  
2. Enter a YouTube channel ID  
3. Select playlists to import  
4. Watch real-time progress as songs are matched and imported  

## Features  

- Import YouTube playlists to Spotify with smart song matching  
- Real-time progress tracking with server-sent events  
- Batch processing for efficient imports  
- Multiple API key support with automatic rotation  
- Intelligent title/artist parsing using Gemini AI  
- Handles remixes, covers, and various video title formats
  
## License  

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

