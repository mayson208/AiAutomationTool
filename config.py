"""config.py — centralised settings and API key loader."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

SCRIPTS_DIR    = OUTPUTS_DIR / "scripts"
AUDIO_DIR      = OUTPUTS_DIR / "audio"
THUMBNAILS_DIR = OUTPUTS_DIR / "thumbnails"
VIDEOS_DIR     = OUTPUTS_DIR / "videos"
DATA_DIR       = BASE_DIR / "data"

for _d in [SCRIPTS_DIR, AUDIO_DIR, THUMBNAILS_DIR, VIDEOS_DIR, DATA_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# API Keys
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
PEXELS_API_KEY      = os.getenv("PEXELS_API_KEY", "")
YOUTUBE_CLIENT_ID     = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
FLASK_SECRET_KEY    = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-6"

# ElevenLabs
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"

# OpenAI
OPENAI_IMAGE_MODEL = "dall-e-3"
OPENAI_IMAGE_SIZE  = "1792x1024"  # YouTube thumbnail ratio

# Pexels
PEXELS_API_URL = "https://api.pexels.com/videos"

# YouTube
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
                  "https://www.googleapis.com/auth/youtube.readonly"]

def missing_keys():
    """Return list of unset API key names."""
    checks = {
        "ANTHROPIC_API_KEY":   ANTHROPIC_API_KEY,
        "ELEVENLABS_API_KEY":  ELEVENLABS_API_KEY,
        "ELEVENLABS_VOICE_ID": ELEVENLABS_VOICE_ID,
        "OPENAI_API_KEY":      OPENAI_API_KEY,
        "PEXELS_API_KEY":      PEXELS_API_KEY,
    }
    return [k for k, v in checks.items() if not v]
