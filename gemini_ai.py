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

    def parse_video_details(self, video_title, video_description):
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,  # Lower temperature for more deterministic results
            max_output_tokens=100,
            candidate_count=1
        )
        
        prompt = f"""
        Extract the song title and artist from this YouTube music video.
        Video Title: {video_title}
        Video Description: {video_description}
        
        Format: 
        Artist: [main artist name]
        Title: [song title]
        """
        
        response = self.gemini_ai.generate_content(prompt, generation_config)
        
        parsed = response.text.strip().split('\n')
        artist = parsed[0].replace('Artist: ', '').strip()
        title = parsed[1].replace('Title: ', '').strip()
        
        return {
            'artist': artist,
            'title': title
        }

# # Initialize GeminiAI
# gemini_ai = GeminiAI(api_key=GEMINI_API_KEY, model_name="gemini-1.5-flash")

# # Initialize VideoDetailsParser
# parser = VideoDetailsParser(gemini_ai)

# # Example usage
# # details = parser.parse_video_details("Roddy Ricch", "The Box by BBC Radio 1Xtra")
# # print(details)
