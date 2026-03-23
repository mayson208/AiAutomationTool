"""voiceover.py — Generate voiceover using ElevenLabs with niche-optimized settings."""
import requests
import re
import os
import json
from datetime import datetime
from pathlib import Path
import config

NICHE_VOICE_SETTINGS = {
    "finance":       {"stability": 0.70, "similarity_boost": 0.80, "style": 0.20, "use_speaker_boost": True},
    "motivation":    {"stability": 0.40, "similarity_boost": 0.70, "style": 0.60, "use_speaker_boost": True},
    "facts":         {"stability": 0.60, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": True},
    "top10":         {"stability": 0.60, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": True},
    "truecrime":     {"stability": 0.65, "similarity_boost": 0.80, "style": 0.40, "use_speaker_boost": True},
    "history":       {"stability": 0.70, "similarity_boost": 0.80, "style": 0.30, "use_speaker_boost": True},
    "science":       {"stability": 0.65, "similarity_boost": 0.80, "style": 0.25, "use_speaker_boost": True},
    "selfimprovement": {"stability": 0.55, "similarity_boost": 0.75, "style": 0.40, "use_speaker_boost": True},
    "horror":        {"stability": 0.60, "similarity_boost": 0.75, "style": 0.45, "use_speaker_boost": True},
    "meditation":    {"stability": 0.85, "similarity_boost": 0.90, "style": 0.05, "use_speaker_boost": False},
    "news":          {"stability": 0.75, "similarity_boost": 0.85, "style": 0.15, "use_speaker_boost": True},
    "roblox":        {"stability": 0.45, "similarity_boost": 0.70, "style": 0.55, "use_speaker_boost": True},
}

def _clean_script(script_text: str) -> str:
    """Strip script markers and stage directions for TTS."""
    text = re.sub(r'\[B-ROLL:.*?\]', '', script_text)
    text = re.sub(r'\[B-ROLL:[^\]]*\]', '', text)
    text = re.sub(r'^(TITLE:|DESCRIPTION:|TAGS:|SECTION \d+|HOOK -|INTRO -|CTA -|OUTRO -).*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\d+:\d+\s*[-–]\s*\d+:\d+', '', text)
    text = re.sub(r'^\s*[-–*]\s*', '', text, flags=re.MULTILINE)
    text = ' '.join(text.split())
    return text

def generate_voiceover(script_text: str, output_filename: str = None,
                        niche: str = "facts") -> dict:
    """Convert script text to MP3 using ElevenLabs with niche-optimal settings."""
    if not config.ELEVENLABS_API_KEY or not config.ELEVENLABS_VOICE_ID:
        return {"success": False, "error": "ElevenLabs API key or Voice ID not set"}
    try:
        clean_text = _clean_script(script_text)
        if not clean_text.strip():
            return {"success": False, "error": "No text to convert after cleaning"}

        # Save to organized subdirectory
        audio_dir = config.OUTPUTS_DIR / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        if not output_filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"voiceover_{niche}_{ts}.mp3"

        # Use niche-optimized voice settings
        voice_settings = NICHE_VOICE_SETTINGS.get(niche, NICHE_VOICE_SETTINGS["facts"])

        try:
            import voice_manager as vm
            active = vm.get_active_voice()
            active_voice_id = active.get("voice_id") or config.ELEVENLABS_VOICE_ID
        except Exception:
            active_voice_id = config.ELEVENLABS_VOICE_ID
        url = f"{config.ELEVENLABS_API_URL}/text-to-speech/{active_voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": config.ELEVENLABS_API_KEY,
        }
        payload = {
            "text": clean_text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": voice_settings,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        out_path = audio_dir / output_filename
        with open(out_path, "wb") as f:
            f.write(response.content)

        file_size = os.path.getsize(out_path)

        try:
            import voice_manager as vm
            vm.track_usage(active_voice_id, len(clean_text))
        except Exception:
            pass

        return {
            "success": True,
            "path": str(out_path),
            "filename": output_filename,
            "niche": niche,
            "voice_settings": voice_settings,
            "file_size_kb": round(file_size / 1024),
        }
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"ElevenLabs API error: {e.response.status_code} — {e.response.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_preview(preview_text: str, niche: str = "facts") -> dict:
    """Generate a short 30-second preview sample."""
    preview_clean = preview_text[:500] if len(preview_text) > 500 else preview_text
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return generate_voiceover(preview_clean, f"preview_{niche}_{ts}.mp3", niche)
