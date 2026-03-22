"""pipeline.py — Orchestrate the full one-click video automation pipeline."""
import os
import json
from datetime import datetime
from pathlib import Path
import config
import script_writer
import voiceover
import thumbnail
import footage
import video_assembler
import youtube_uploader

HISTORY_FILE = config.BASE_DIR / "outputs" / "history.json"

def _load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def _save_history(entry: dict):
    history = _load_history()
    history.insert(0, entry)
    history = history[:50]  # Keep last 50
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def run_pipeline(topic: str, duration_minutes: int = 8,
                 upload: bool = False, privacy: str = "private",
                 progress_callback=None) -> dict:
    """
    Run the full automation pipeline for a given topic.
    progress_callback(step: int, total: int, message: str) — optional UI callback.
    """
    def progress(step, msg):
        if progress_callback:
            progress_callback(step, 6, msg)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {"topic": topic, "timestamp": ts, "steps": {}}

    # Step 1 — Script
    progress(1, "Generating script with Claude...")
    script_result = script_writer.generate_script(topic, duration_minutes)
    result["steps"]["script"] = script_result
    if not script_result["success"]:
        return {"success": False, "error": f"Script failed: {script_result['error']}", **result}

    # Step 2 — Voiceover
    progress(2, "Generating voiceover with ElevenLabs...")
    vo_result = voiceover.generate_voiceover(
        script_result["script"], output_filename=f"voiceover_{ts}.mp3"
    )
    result["steps"]["voiceover"] = vo_result
    if not vo_result["success"]:
        return {"success": False, "error": f"Voiceover failed: {vo_result['error']}", **result}

    # Step 3 — Thumbnail
    progress(3, "Generating thumbnail with DALL-E...")
    thumb_result = thumbnail.generate_thumbnail(
        topic, title=script_result.get("title"), output_filename=f"thumbnail_{ts}.png"
    )
    result["steps"]["thumbnail"] = thumb_result
    # Non-fatal if thumbnail fails

    # Step 4 — Stock footage
    progress(4, "Searching Pexels for stock footage...")
    footage_result = footage.search_footage(topic, per_page=5)
    result["steps"]["footage"] = footage_result
    clip_paths = []
    if footage_result["success"] and footage_result["videos"]:
        for i, vid in enumerate(footage_result["videos"][:3]):
            dl = footage.download_clip(vid["url"], output_filename=f"clip_{ts}_{i}.mp4")
            if dl["success"]:
                clip_paths.append(dl["path"])

    # Step 5 — Assemble video
    progress(5, "Assembling video with MoviePy...")
    if clip_paths:
        video_result = video_assembler.assemble_video(
            vo_result["path"], clip_paths, output_filename=f"video_{ts}.mp4"
        )
    else:
        video_result = {"success": False, "error": "No clips downloaded — skipping assembly"}
    result["steps"]["video"] = video_result

    # Step 6 — Upload (optional)
    upload_result = {"success": False, "error": "Upload skipped"}
    if upload and video_result.get("success"):
        progress(6, "Uploading to YouTube...")
        tags = [t.strip() for t in script_result.get("tags", "").split(",") if t.strip()]
        upload_result = youtube_uploader.upload_video(
            video_path=video_result["path"],
            title=script_result.get("title", topic),
            description=script_result.get("description", ""),
            tags=tags,
            privacy=privacy,
        )
    result["steps"]["upload"] = upload_result

    entry = {
        "topic": topic,
        "timestamp": ts,
        "title": script_result.get("title", topic),
        "thumbnail": thumb_result.get("filename") if thumb_result.get("success") else None,
        "video": video_result.get("filename") if video_result.get("success") else None,
        "youtube_url": upload_result.get("url"),
        "success": video_result.get("success", False),
    }
    _save_history(entry)

    return {
        "success": True,
        "topic": topic,
        "title": script_result.get("title", topic),
        "script": script_result.get("script", ""),
        "voiceover_path": vo_result.get("path"),
        "thumbnail_path": thumb_result.get("path") if thumb_result.get("success") else None,
        "video_path": video_result.get("path") if video_result.get("success") else None,
        "youtube_url": upload_result.get("url"),
        "steps": result["steps"],
    }
