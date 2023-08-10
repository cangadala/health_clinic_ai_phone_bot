import os
from dotenv import load_dotenv
# Load .env stored keys
load_dotenv()

### Env Info

# Api Keys

# OpenAI for LLM
openai_api_key = os.getenv('OPENAI_API_KEY')

# Deepgram for 
deepgram_api_key = os.getenv('DEEPGRAM_API_KEY')

# 
azure_speech_key = os.getenv('AZURE_SPEECH_KEY')
azure_speech_region = os.getenv('AZURE_SPEECH_REGION')

# Twilio for phone calling
twilio_secret_id = os.getenv('TWILIO_SECRET_ID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')

# Eleven Labs
eleven_labs_api_key=os.getenv("ELEVENLABS_API_KEY")
eleven_labs_voice_id=os.getenv("ELEVENLABS_VOICE_ID")

# Other
base_url = os.getenv('BASE_URL')

# Api Keys unused
speechmatics_api_key = os.getenv('SPEECHMATICS_API_KEY')
#
vocode_api_key = os.getenv('VOCODE_API_KEY')


# Chunk Size
CHUNK_SIZE = 1024

# Path
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
# os.makedirs(OUTPUT_DIR, exist_ok=True)
# OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'generated_audio.mp3')

