// By Underemployed 5/1/25
// Appscript gemini 
// appscript youtube data api v3
const PROPERTIES = PropertiesService.getScriptProperties();
const GOOGLE_API_KEY = PROPERTIES.getProperty('GOOGLE_API_KEY');
const SPOTIFY_CLIENT_ID = PROPERTIES.getProperty('SPOTIFY_CLIENT_ID');
const SPOTIFY_CLIENT_SECRET = PROPERTIES.getProperty('SPOTIFY_CLIENT_SECRET');
const GEMINI_API_KEYS = JSON.parse(PROPERTIES.getProperty('GEMINI_API_KEYS'));





function testDoPost() {
    const testRequests = [
        { action: 'getPlaylists', channelId: 'UCW15L5aHUcW6sS_NPUYkd0A' },
        { action: 'getVideoDetails', playlistId: 'PLJHtzsPP5ijNPtDWQtrg_QS7GmWPZAfvD' },
        { action: 'searchWithGemini', videoTitle: 'Roddy Ricch - The Box', channelName: 'The Box by BBC Radio 1Xtra' }
    ];

    testRequests.forEach(req => {
        const e = { postData: { contents: JSON.stringify(req) } };
        const response = doPost(e);
        Logger.log(`Testing ${req.action}:`);
        Logger.log(response.getContent());
    });
}







// 
// 
function getChannelPlaylists(channelId = "UCW15L5aHUcW6sS_NPUYkd0A") {
    const response = YouTube.Playlists.list('snippet,contentDetails', {
        channelId: channelId,
        maxResults: 50
    });

    return response.items.reduce((acc, item) => {
        acc[item.snippet.title] = item.id;
        return acc;
    }, {});
}

function cleanSongTitleAndArtist(title, artist) {
    const titlePattern = /(\s*\(.*?\)|\s*\[.*?\]|\s*-\s*Topic\s*$|feat.*|ft.*| - Topic)/gi;
    const artistPattern = /(\s*VEVO|\s*Official.*|\s*Music.*|\s*-\s*Topic\s*$)/gi;

    let cleanedTitle = title.replace(titlePattern, '').replace(/\s+/g, ' ').trim();
    let cleanedArtist = artist.replace(artistPattern, '').replace(/\s+/g, ' ').trim();

    return [cleanedTitle, cleanedArtist];
}

function getPlaylistVideoDetails(playlistId) {
    const videoDetails = [];
    let pageToken = '';

    do {
        const response = YouTube.PlaylistItems.list('snippet', {
            playlistId: playlistId,
            maxResults: 50,
            pageToken: pageToken
        });

        response.items.forEach(item => {
            const [title, artist] = cleanSongTitleAndArtist(
                item.snippet.title,
                item.snippet.videoOwnerChannelTitle || ''
            );
            videoDetails.push({ title, artist });
        });

        pageToken = response.nextPageToken;
    } while (pageToken);

    return videoDetails;
}


function getAllSongs(channelId = "UCW15L5aHUcW6sS_NPUYkd0A") {
    const playlists = getChannelPlaylists(channelId);
    const allSongs = {};

    Object.entries(playlists).forEach(([playlistName, playlistId]) => {
        allSongs[playlistName] = getPlaylistVideoDetails(playlistId);
    });

    return allSongs;
}



class GeminiAI {
    constructor() {
        this.currentKeyIndex = 0;
// 
// 
    }

    rotateApiKey() {
        this.currentKeyIndex = (this.currentKeyIndex + 1) % this.apiKeys.length;
        console.log(`Switched to API key ${this.currentKeyIndex + 1}`);
    }

    generateContent(prompt) {
        let attempts = 0;
// 
// 

        while (attempts < maxAttempts) {
            try {
                const response = UrlFetchApp.fetch(
                    'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent',
                    {
                        method: 'post',
                        headers: {
                            'Content-Type': 'application/json',
                            'x-goog-api-key': this.apiKeys[this.currentKeyIndex],
                        },
                        payload: JSON.stringify({
                            contents: [{ parts: [{ text: prompt }] }],
                            generationConfig: {
                                temperature: 0.1,
                                maxOutputTokens: 100,
                                candidateCount: 1,
                            },
                        }),
                    }
                );

// 
// 
                return JSON.parse(response.getContentText());
            } catch (e) {
                if (e.toString().includes('429')) {
                    console.log(`Quota exceeded on API key ${this.currentKeyIndex + 1}`);
                    Utilities.sleep(5000);
                    this.rotateApiKey();
                    attempts++;
                    continue;
                }
                console.log(`Gemini Error: ${e}`);
                return null;
            }
        }

        console.log("All API keys exhausted after multiple attempts");
        return null;
    }
}



class VideoDetailsParser {
    constructor(geminiAi) {
        this.geminiAi = geminiAi;
    }

    parseVideoDetails(videoTitle, channelName) {
        const prompt = `
      Extract the song title and artist from this YouTube song video.
      Video Title: ${videoTitle}
      Channel Name: ${channelName}

      Consider:
      1. Channel might be the artist name
      2. Title might contain "Artist - Song"
      3. Remixes and covers should note original artist
      4. If the title is a remix or cover, it should be noted
      5. Basically we are trying to get the artist and song name from yt video title and channel name
      6. If not obvious, use the channel name as artist same with the song title
      7. Answer must be in the format:
      8. If channel name is empty and unknown and artist not specified in title leave it as "blank"
      Artist: [main artist name]
      Title: [song title]
    `;

        try {
            const response = this.geminiAi.generateContent(prompt);
            if (!response) return null;

            const parsed = response.candidates[0].content.parts[0].text.trim().split('\n');
            const artist = parsed[0].replace('Artist:', '').trim();
            const title = parsed[1].replace('Title:', '').trim();

            return { artist, title };
        } catch (e) {
            console.log(`Error parsing video details: ${e}`);
            return { videoTitle, channelName };
        }
    }
}

// 
// 
function doPost(e) {
    const request = JSON.parse(e.postData.contents);

    switch (request.action) {
        case 'getPlaylists':
            return ContentService.createTextOutput(
                JSON.stringify(getChannelPlaylists(request.channelId))
            ).setMimeType(ContentService.MimeType.JSON);

        case 'getVideoDetails':
            return ContentService.createTextOutput(
                JSON.stringify(getPlaylistVideoDetails(request.playlistId))
            ).setMimeType(ContentService.MimeType.JSON);

        case 'getAllSongs':
            return ContentService.createTextOutput(
                JSON.stringify(getAllSongs(request.channelId))
            ).setMimeType(ContentService.MimeType.JSON);
        case 'searchWithGemini':
            const geminiAi = new GeminiAI();
            const parser = new VideoDetailsParser(geminiAi);
            const parsedDetails = parser.parseVideoDetails(
                request.videoTitle,
                request.channelName
            );
            return ContentService.createTextOutput(
                JSON.stringify(parsedDetails)
            ).setMimeType(ContentService.MimeType.JSON);
    }
}
