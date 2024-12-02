from google.generativeai import GenerativeModel
import google.generativeai as genai
from secret import GEMINI_API_KEYS
import time

class GeminiAI:
    def __init__(self, api_key, model_name):
        self.api_keys = GEMINI_API_KEYS
        self.current_key_index = 0
        self.model_name = model_name
        self.model = self._initialize_model()

    def _initialize_model(self):
        genai.configure(api_key=self.api_keys[self.current_key_index])
        return genai.GenerativeModel(self.model_name)

    def _rotate_api_key(self):
        print(f"\nRotating API key due to quota limit...")
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.model = self._initialize_model()
        print(f"Switched to API key {self.current_key_index + 1}")

    def generate_content(self, prompt, generation_config):
        for _ in range(len(self.api_keys)):
            try:
                return self.model.generate_content(prompt, generation_config=generation_config)
            except Exception as e:
                if "429" in str(e):
                    print(f"Quota exceeded on API key {self.current_key_index + 1}")
                    time.sleep(5)
                    self._rotate_api_key()
                    continue
                print(f"Gemini Error: {e}")
        print("All API keys exhausted")
        return None


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
        Extract the song title and artist from this YouTube song video.
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
        8. If channel name is empty and unknown and artist not specified in title leave it as "blank"
        Artist: [main artist name]
        Title: [song title]
        
        Format:
        Artist: [main artist name]
        Title: [song title]
        """
        
        try:
            response = self.gemini_ai.generate_content(prompt, generation_config)
            if response is None:
                return None

            parsed = response.text.strip().split('\n')
            print("\n--- Input Details ---")
            print(f"Song Title: {video_title}")
            print(f"Channel Name: {channel_name}")
            print("---------------------\n")
            
            artist = parsed[0].replace('Artist: ', '').strip()
            title = parsed[1].replace('Title: ', '').strip()
            
            print("--- Extracted Details ---")
            print(f"Artist: {artist}")
            print(f"Song Title: {title}")
            print("-------------------------\n")
            
            return {
                'artist': artist,
                'title': title
            }
        except Exception as e:
            print("\n--- Gemini Error ---")
            print(f"Error: {e}")
            print("---------------------\n")
            return None

if __name__ == "__main__":
    gemini_ai = GeminiAI(api_key=GEMINI_API_KEYS[0], model_name="gemini-1.5-flash")
    parser = VideoDetailsParser(gemini_ai)
    details = parser.parse_video_details("Roddy Ricch - The Box", "The Box by BBC Radio 1Xtra")
    print(details)
