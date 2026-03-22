"""voice_manager.py — Voice management system for STUDIO."""
import json
import os
import requests
import re
from datetime import datetime, timedelta
from pathlib import Path
import config

DATA_DIR = config.BASE_DIR / "data"
VOICES_DB = DATA_DIR / "voices.json"
PREVIEWS_DIR = config.OUTPUTS_DIR / "previews"

# Niche sample sentences for voice previews
NICHE_SAMPLES = {
    "finance":       "In the next 10 minutes, I'm going to show you exactly how compound interest can turn $500 a month into over a million dollars.",
    "motivation":    "Every single day is a chance to become the person you were always meant to be. The question is — will you take it?",
    "facts":         "Did you know that the human brain generates enough electricity to power a small light bulb? Here are 10 more facts that will blow your mind.",
    "truecrime":     "On the night of March 14th, Brian Shaffer walked into a bar and was captured on security cameras entering — but was never seen leaving.",
    "history":       "In the summer of 1945, a single decision made in a war room thousands of miles away would change the course of human history forever.",
    "science":       "The universe is so vast that if you drove at highway speed, it would take you 37 million years just to reach the nearest star.",
    "selfimprovement": "The one habit that transformed my productivity wasn't waking up at 5am or cold showers — it was something far simpler.",
    "horror":        "The babysitter thought the calls were a prank. By the time she realized they were coming from inside the house, it was already too late.",
    "meditation":    "Take a deep breath in... and slowly release. Let your thoughts drift away like clouds across a calm summer sky.",
    "news":          "Here are the five most important stories you need to know about today, explained clearly and concisely in under ten minutes.",
    "top10":         "From number ten down to the most shocking entry at number one — here are the top ten mysteries that science still cannot explain.",
    "general":       "Welcome to STUDIO — your AI-powered YouTube automation platform. Let's create something amazing together.",
}

# Voice personality tags and niche recommendations (for curated/built-in voices)
VOICE_METADATA = {
    # These get merged with data fetched from ElevenLabs API
    # keyed by voice_id
}

def _load_db() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if VOICES_DB.exists():
        with open(VOICES_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "active_voice_id": "",
        "active_voice_name": "",
        "favorites": [],
        "custom_settings": {},   # voice_id -> {stability, similarity_boost, style}
        "niche_presets": {},     # voice_id -> {niche -> settings}
        "usage_stats": {},       # voice_id -> {count, total_chars, last_used}
        "last_synced": None,
        "voices_cache": [],      # cached ElevenLabs voice list
        "channels": {},          # channel_id -> {name, voice_id, voice_name}
    }

def _save_db(db: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(VOICES_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def get_db() -> dict:
    return _load_db()

# ── ElevenLabs API helpers ───────────────────────────────────────────────────

def fetch_voices_from_elevenlabs() -> dict:
    """Fetch all available voices from ElevenLabs API."""
    if not config.ELEVENLABS_API_KEY:
        return {"success": False, "error": "ELEVENLABS_API_KEY not set"}
    try:
        headers = {"xi-api-key": config.ELEVENLABS_API_KEY}
        resp = requests.get(f"{config.ELEVENLABS_API_URL}/voices", headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        voices = data.get("voices", [])

        db = _load_db()
        now = datetime.now().isoformat()

        # Tag voices added in last 30 days
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()

        enriched = []
        for v in voices:
            labels = v.get("labels", {})
            settings = v.get("settings") or {}
            enriched.append({
                "voice_id":    v.get("voice_id", ""),
                "name":        v.get("name", ""),
                "category":    v.get("category", "premade"),  # premade | cloned | professional
                "gender":      labels.get("gender", "").capitalize() or "Unknown",
                "accent":      labels.get("accent", "").capitalize() or "Unknown",
                "age":         labels.get("age", "").capitalize() or "",
                "use_case":    labels.get("use case", labels.get("use_case", "")),
                "description": v.get("description", ""),
                "preview_url": v.get("preview_url", ""),
                "fine_tuning_state": v.get("fine_tuning", {}).get("state", ""),
                "is_new": v.get("created_at_unix", 0) > 0,  # mark as potentially new
                "languages": [lang.get("language", "") for lang in v.get("verified_languages", [])],
                "default_settings": {
                    "stability":       settings.get("stability", 0.5),
                    "similarity_boost": settings.get("similarity_boost", 0.75),
                    "style":           settings.get("style", 0.0),
                },
            })

        db["voices_cache"] = enriched
        db["last_synced"] = now
        _save_db(db)
        return {"success": True, "voices": enriched, "count": len(enriched)}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"ElevenLabs API error {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_voices(force_refresh: bool = False) -> list:
    """Get voices from cache or fetch fresh."""
    db = _load_db()
    # Refresh if cache is empty or older than 24 hours or forced
    if force_refresh or not db.get("voices_cache"):
        result = fetch_voices_from_elevenlabs()
        if result["success"]:
            return result["voices"]
    return db.get("voices_cache", [])

def get_voice_by_id(voice_id: str) -> dict | None:
    voices = get_voices()
    return next((v for v in voices if v["voice_id"] == voice_id), None)

# ── Active voice management ──────────────────────────────────────────────────

def set_active_voice(voice_id: str, voice_name: str = ""):
    db = _load_db()
    db["active_voice_id"] = voice_id
    db["active_voice_name"] = voice_name or voice_id
    _save_db(db)
    # Also update config env so voiceover.py picks it up
    from dotenv import set_key
    env_path = config.BASE_DIR / ".env"
    set_key(str(env_path), "ELEVENLABS_VOICE_ID", voice_id)

def get_active_voice() -> dict:
    db = _load_db()
    voice_id = db.get("active_voice_id") or config.ELEVENLABS_VOICE_ID
    voice_name = db.get("active_voice_name", "")
    if not voice_name and voice_id:
        v = get_voice_by_id(voice_id)
        if v:
            voice_name = v["name"]
    return {"voice_id": voice_id, "voice_name": voice_name or "Not set"}

# ── Favorites ────────────────────────────────────────────────────────────────

def toggle_favorite(voice_id: str) -> bool:
    """Toggle favorite status. Returns True if now favorited."""
    db = _load_db()
    favs = db.get("favorites", [])
    if voice_id in favs:
        favs.remove(voice_id)
        is_fav = False
    else:
        favs.append(voice_id)
        is_fav = True
    db["favorites"] = favs
    _save_db(db)
    return is_fav

def get_favorites() -> list:
    db = _load_db()
    return db.get("favorites", [])

# ── Per-voice settings ────────────────────────────────────────────────────────

NICHE_PRESETS = {
    "finance":       {"stability": 0.70, "similarity_boost": 0.80, "style": 0.20},
    "motivation":    {"stability": 0.40, "similarity_boost": 0.70, "style": 0.60},
    "facts":         {"stability": 0.60, "similarity_boost": 0.75, "style": 0.35},
    "top10":         {"stability": 0.60, "similarity_boost": 0.75, "style": 0.35},
    "truecrime":     {"stability": 0.65, "similarity_boost": 0.80, "style": 0.40},
    "history":       {"stability": 0.70, "similarity_boost": 0.80, "style": 0.30},
    "science":       {"stability": 0.65, "similarity_boost": 0.80, "style": 0.25},
    "selfimprovement": {"stability": 0.55, "similarity_boost": 0.75, "style": 0.40},
    "horror":        {"stability": 0.60, "similarity_boost": 0.75, "style": 0.45},
    "meditation":    {"stability": 0.85, "similarity_boost": 0.90, "style": 0.05},
    "news":          {"stability": 0.75, "similarity_boost": 0.85, "style": 0.15},
    "general":       {"stability": 0.60, "similarity_boost": 0.75, "style": 0.30},
}

def get_voice_settings(voice_id: str, niche: str = "general") -> dict:
    """Get settings for a voice+niche combination."""
    db = _load_db()
    custom = db.get("custom_settings", {}).get(voice_id)
    if custom:
        return custom
    # Check niche presets saved for this voice
    niche_preset = db.get("niche_presets", {}).get(voice_id, {}).get(niche)
    if niche_preset:
        return niche_preset
    # Fall back to global niche presets
    return NICHE_PRESETS.get(niche, NICHE_PRESETS["general"])

def save_voice_settings(voice_id: str, settings: dict, niche: str = None):
    db = _load_db()
    if niche:
        if "niche_presets" not in db:
            db["niche_presets"] = {}
        if voice_id not in db["niche_presets"]:
            db["niche_presets"][voice_id] = {}
        db["niche_presets"][voice_id][niche] = settings
    else:
        if "custom_settings" not in db:
            db["custom_settings"] = {}
        db["custom_settings"][voice_id] = settings
    _save_db(db)

# ── Voice preview ─────────────────────────────────────────────────────────────

def generate_preview(voice_id: str, niche: str = "general", custom_text: str = None) -> dict:
    """Generate a preview audio file for a voice. Cached by voice+niche."""
    if not config.ELEVENLABS_API_KEY:
        return {"success": False, "error": "ELEVENLABS_API_KEY not set"}

    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = re.sub(r'[^a-zA-Z0-9]', '_', f"{voice_id}_{niche}")
    cache_file = PREVIEWS_DIR / f"{cache_key}.mp3"

    # Return cached preview if exists and no custom text
    if cache_file.exists() and not custom_text:
        return {"success": True, "filename": cache_file.name, "cached": True}

    text = custom_text or NICHE_SAMPLES.get(niche, NICHE_SAMPLES["general"])
    # Limit preview to ~200 chars
    text = text[:200]

    settings = get_voice_settings(voice_id, niche)
    try:
        url = f"{config.ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": config.ELEVENLABS_API_KEY,
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": settings,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()

        fname = f"preview_{cache_key}.mp3" if custom_text else f"{cache_key}.mp3"
        out_path = PREVIEWS_DIR / fname
        with open(out_path, "wb") as f:
            f.write(resp.content)

        return {"success": True, "filename": fname, "cached": False}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── Usage tracking ────────────────────────────────────────────────────────────

def track_usage(voice_id: str, char_count: int = 0):
    db = _load_db()
    if "usage_stats" not in db:
        db["usage_stats"] = {}
    stats = db["usage_stats"].get(voice_id, {"count": 0, "total_chars": 0, "last_used": None})
    stats["count"] += 1
    stats["total_chars"] += char_count
    stats["last_used"] = datetime.now().isoformat()
    db["usage_stats"][voice_id] = stats
    _save_db(db)

def get_usage_stats() -> dict:
    db = _load_db()
    return db.get("usage_stats", {})

# ── Voice cloning ─────────────────────────────────────────────────────────────

def clone_voice(name: str, audio_files: list, description: str = "") -> dict:
    """Clone a voice using ElevenLabs IVC API."""
    if not config.ELEVENLABS_API_KEY:
        return {"success": False, "error": "ELEVENLABS_API_KEY not set"}
    try:
        url = f"{config.ELEVENLABS_API_URL}/voices/add"
        headers = {"xi-api-key": config.ELEVENLABS_API_KEY}
        files = [("files", (Path(f).name, open(f, "rb"), "audio/mpeg")) for f in audio_files]
        data = {"name": name, "description": description or f"Custom voice: {name}"}
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=120)
        resp.raise_for_status()
        voice_id = resp.json().get("voice_id", "")
        # Force refresh voice cache
        fetch_voices_from_elevenlabs()
        return {"success": True, "voice_id": voice_id, "name": name}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"Clone failed: {e.response.status_code} — {e.response.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_voice(voice_id: str) -> dict:
    """Delete a cloned voice from ElevenLabs."""
    if not config.ELEVENLABS_API_KEY:
        return {"success": False, "error": "ELEVENLABS_API_KEY not set"}
    try:
        headers = {"xi-api-key": config.ELEVENLABS_API_KEY}
        resp = requests.delete(f"{config.ELEVENLABS_API_URL}/voices/{voice_id}", headers=headers, timeout=15)
        resp.raise_for_status()
        fetch_voices_from_elevenlabs()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── Niche recommendations ─────────────────────────────────────────────────────

NICHE_VOICE_TRAITS = {
    "finance":       ["professional", "authoritative", "trustworthy", "news", "business"],
    "motivation":    ["energetic", "warm", "inspiring", "conversational", "young"],
    "facts":         ["clear", "engaging", "friendly", "educational", "neutral"],
    "truecrime":     ["dramatic", "mysterious", "storytelling", "serious", "narrative"],
    "history":       ["authoritative", "dramatic", "storytelling", "documentary", "deep"],
    "science":       ["clear", "intelligent", "engaging", "educational", "neutral"],
    "selfimprovement": ["warm", "friendly", "conversational", "inspiring", "calm"],
    "horror":        ["mysterious", "dramatic", "dark", "storytelling", "tense"],
    "meditation":    ["calm", "soothing", "gentle", "slow", "peaceful"],
    "news":          ["professional", "neutral", "authoritative", "clear", "news"],
    "top10":         ["engaging", "energetic", "entertaining", "clear", "friendly"],
    "general":       ["clear", "neutral", "professional"],
}

def get_recommended_voices(niche: str, all_voices: list) -> list:
    """Return voices sorted by niche fit."""
    traits = NICHE_VOICE_TRAITS.get(niche, NICHE_VOICE_TRAITS["general"])
    def score(v):
        text = f"{v.get('use_case','')} {v.get('description','')} {v.get('accent','')}".lower()
        return sum(1 for t in traits if t in text)
    return sorted(all_voices, key=score, reverse=True)
