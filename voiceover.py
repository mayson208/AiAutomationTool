"""voiceover.py — Generate MP3 voiceover using ElevenLabs API."""
import requests
import os
from datetime import datetime
from pathlib import Path
import config

def generate_voiceover(script_text: str, output_filename: str = None) -> dict:
    """Convert script text to MP3 using ElevenLabs."""
    if not config.ELEVENLABS_API_KEY or not config.ELEVENLABS_VOICE_ID:
        return {"success": False, "error": "ElevenLabs API key or Voice ID not set"}
    try:
        # Strip stage directions for cleaner audio
        import re
        clean_text = re.sub(r'\[B-ROLL:.*?\]', '', script_text)
        clean_text = re.sub(r'\(.*?\)', '', clean_text)
        clean_text = re.sub(r'TITLE:.*?\n', '', clean_text)
        clean_text = re.sub(r'DESCRIPTION:.*?\n', '', clean_text)
        clean_text = re.sub(r'TAGS:.*?\n', '', clean_text)
        clean_text = ' '.join(clean_text.split())
        # Truncate to ElevenLabs limit
        if len(clean_text) > 5000:
            clean_text = clean_text[:5000]
        url = f"{config.ELEVENLABS_API_URL}/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": config.ELEVENLABS_API_KEY,
        }
        payload = {
            "text": clean_text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        if not output_filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"voiceover_{ts}.mp3"
        out_path = config.OUTPUTS_DIR / output_filename
        with open(out_path, "wb") as f:
            f.write(response.content)
        return {"success": True, "path": str(out_path), "filename": output_filename}
    except Exception as e:
        return {"success": False, "error": str(e)}
