from google.generativeai import GenerativeModel
import google.generativeai as genai
from secret import GEMINI_API_KEY

class GeminiAI:
    def __init__(self, api_key, model_name):
        self.api_key = api_key
        self.model_name = model_name
        self.model = self._initialize_model()

    def _initialize_model(self):
        genai.configure(api_key=self.api_key)
        return genai.GenerativeModel(self.model_name)

    def generate_content(self, prompt, generation_config):
        return self.model.generate_content(prompt, generation_config=generation_config)

class VideoDetailsParser:
    def __init__(self, gemini_ai):
        self.gemini_ai = gemini_ai

    def parse_video_details(self, video_title, channel_name):
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=100,
            candidate_count=1
        )
        
        prompt = f"""
        Extract the song title and artist from this YouTube music video.
        Video Title: {video_title}
        Channel Name: {channel_name}

        Consider:
        1. Channel might be the artist name
        2. Title might contain "Artist - Song"
        3. Remixes and covers should note original artist
        4. If the title is a remix or cover, it should be noted
        5. Basically we are trying to get the artist and song name from yt video title and channel name
        6. If not obvious, use the channel name as artist same with the song title
        7. Answer must be in the format:
        Artist: [main artist name]
        Title: [song title]
        
        Format:
        Artist: [main artist name]
        Title: [song title]
        """
        
        response = self.gemini_ai.generate_content(prompt, generation_config)
        parsed = response.text.strip().split('\n')
        
        print(f"\nInput Song: {video_title}")
        print(f"Input Channel: {channel_name}")
        
        artist = parsed[0].replace('Artist: ', '').strip()
        title = parsed[1].replace('Title: ', '').strip()
        
        print(f"Extracted Artist: {artist}  Song: {title}\n")
        
        return {
            'artist': artist,
            'title': title
        }
    


if __name__ == "__main__":
    gemini_ai = GeminiAI(api_key=GEMINI_API_KEY, model_name="gemini-1.5-flash")
    parser = VideoDetailsParser(gemini_ai)
    details = parser.parse_video_details("Roddy Ricch - The Box", "The Box by BBC Radio 1Xtra")
    print(details)
