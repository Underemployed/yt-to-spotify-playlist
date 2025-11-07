// By Underemployed 5/1/25
// Appscript gemini
// appscript youtube data api v3


// Set these in Script Properties
function setScriptProperties() {
    const properties = PropertiesService.getScriptProperties();

    properties.setProperties({
        'GOOGLE_API_KEY': '',
        'SPOTIFY_CLIENT_ID': '',
        'SPOTIFY_CLIENT_SECRET': '',
        'GEMINI_API_KEYS': JSON.stringify([
            '',
            '',
            '',
            '',
            ''
        ])
    });
}
// fill wats needed

// Access them in your code using
const PROPERTIES = PropertiesService.getScriptProperties();
const GOOGLE_API_KEY = PROPERTIES.getProperty('GOOGLE_API_KEY');
const SPOTIFY_CLIENT_ID = PROPERTIES.getProperty('SPOTIFY_CLIENT_ID');
const SPOTIFY_CLIENT_SECRET = PROPERTIES.getProperty('SPOTIFY_CLIENT_SECRET');
const GEMINI_API_KEYS = JSON.parse(PROPERTIES.getProperty('GEMINI_API_KEYS'));

const API_KEY = GEMINI_API_KEYS[0]; // put one Gemini API key here




function testDoPost() {
    const testRequests = [
        // {action: 'getPlaylists', channelId: 'UCW15L5aHUcW6sS_NPUYkd0A'},
        // {action: 'getVideoDetails', playlistId: 'PLJHtzsPP5ijNPtDWQtrg_QS7GmWPZAfvD'},
        { action: 'searchWithGemini', videoTitle: 'Roddy Ricch - The Box', channelName: 'The Box by BBC Radio 1Xtra' }
    ];

    testRequests.forEach(req => {
        const e = { postData: { contents: JSON.stringify(req) } };
        const response = doPost(e);
        Logger.log(`Testing ${req.action}:`);
        Logger.log(response.getContent());
    });
}





function testGeminiBasic() {
    const MODEL = 'gemini-2.0-flash';    // safest publicly available model
    const VERSION = 'v1beta';            // correct version for this model

    const url = `https://generativelanguage.googleapis.com/${VERSION}/models/${MODEL}:generateContent?key=${API_KEY}`;

    const prompt = "Write a short poem about coding and coffee.";

    const payload = {
        contents: [
            {
                parts: [
                    { text: prompt }
                ]
            }
        ]
    };

    try {
        const response = UrlFetchApp.fetch(url, {
            method: 'post',
            contentType: 'application/json',
            payload: JSON.stringify(payload)
        });

        const data = JSON.parse(response.getContentText());
        const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || '(no output)';
        Logger.log("Gemini Response:");
        Logger.log(text);
        return text;

    } catch (err) {
        Logger.log("Gemini Test Error:");
        Logger.log(err);
        return null;
    }
}


// YouTube API Functions
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
        this.apiKeys = GEMINI_API_KEYS; // Array of API keys
    }

    rotateApiKey() {
        this.currentKeyIndex = (this.currentKeyIndex + 1) % this.apiKeys.length;
        console.log(`Switched to API key ${this.currentKeyIndex + 1}`);
    }

    generateContent(prompt) {
        let attempts = 0;
        const maxAttempts = this.apiKeys.length * 3; // Allow up to 3 cycles through all keys

        while (attempts < maxAttempts) {
            try {
                const MODEL = 'gemini-2.0-flash';    // safest publicly available model
                const VERSION = 'v1beta';         // stable version


                const response = UrlFetchApp.fetch(
                    `https://generativelanguage.googleapis.com/${VERSION}/models/${MODEL}:generateContent`,
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

                // success
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
            console.log("response")
            console.log(response.candidates[0].content.parts[0].text)
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

// API Endpoints
function doPost(e) {
    const request = JSON.parse(e.postData.contents);

    appendJsonToSheet("inputs", {
        timestamp: new Date(),
        action: request.action,
        requestData: JSON.stringify(request)
    });

    let responseContent;

    switch (request.action) {
        case 'getPlaylists':
            responseContent = JSON.stringify(getChannelPlaylists(request.channelId));
            break;

        case 'getVideoDetails':
            responseContent = JSON.stringify(getPlaylistVideoDetails(request.playlistId));
            break;

        case 'getAllSongs':
            responseContent = JSON.stringify(getAllSongs(request.channelId));
            break;

        case 'searchWithGemini':
            const geminiAi = new GeminiAI();
            const parser = new VideoDetailsParser(geminiAi);
            const parsedDetails = parser.parseVideoDetails(request.videoTitle, request.channelName);
            responseContent = JSON.stringify(parsedDetails);
            break;

        default:
            responseContent = JSON.stringify({ error: "Invalid action" });
    }

    appendJsonToSheet("outputs", {
        timestamp: new Date(),
        action: request.action,
        responseData: responseContent
    });

    return ContentService.createTextOutput(responseContent)
        .setMimeType(ContentService.MimeType.JSON);
}


// logging helpers
function appendJsonToSheet(sheetName, jsonData) {
    let sheet = selectOrCreateSheet(sheetName);
    const headers = Object.keys(jsonData);

    if (sheet.getLastRow() < 1) {
        sheet.appendRow(headers);
    }

    sheet.appendRow(Object.values(jsonData));
}

function selectOrCreateSheet(sheetName) {
    let app = SpreadsheetApp.openByUrl("https://docs.google.com/spreadsheets/d/1WVApqejuPKEzJtvqdQXmRUJ8d8WIyL9EvsDZdaOPmgw/edit?usp=sharing");
    let sheet = app.getSheetByName(sheetName);

    if (!sheet) {
        sheet = app.insertSheet(sheetName);
    }

    return sheet;
}



