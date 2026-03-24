"""pipeline.py — Orchestrate the full one-click video automation pipeline."""
import os
import json
import threading
from datetime import datetime
from pathlib import Path
import config
from studio_logger import get_logger
import script_writer
import voiceover
import thumbnail
import footage
import video_assembler
import youtube_uploader

logger = get_logger(__name__)

HISTORY_FILE = config.BASE_DIR / "outputs" / "history.json"

QUALITY_TIERS = {
    "fast":     {"thumbnail_variations": 1, "thumbnail_quality": "standard", "max_broll_queries": 5,  "clips_per_query": 2, "script_humanize": False},
    "balanced": {"thumbnail_variations": 2, "thumbnail_quality": "standard", "max_broll_queries": 10, "clips_per_query": 3, "script_humanize": True},
    "premium":  {"thumbnail_variations": 3, "thumbnail_quality": "hd",       "max_broll_queries": 15, "clips_per_query": 3, "script_humanize": True},
}

def _load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def _save_history(entry: dict):
    history = _load_history()
    history.insert(0, entry)
    history = history[:50]
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def _retry(func, *args, retries=3, **kwargs):
    """Call func with retries on failure."""
    last_error = None
    for attempt in range(retries):
        result = func(*args, **kwargs)
        if result.get("success"):
            return result
        last_error = result.get("error", "Unknown error")
        if attempt < retries - 1:
            import time
            wait = 2 ** attempt
            logger.warning("Attempt %d failed: %s — retrying in %ds", attempt + 1, last_error, wait)
            time.sleep(wait)
    logger.error("All %d attempts failed: %s", retries, last_error)
    return {"success": False, "error": f"Failed after {retries} attempts: {last_error}"}

def run_pipeline(topic: str, duration_minutes: int = None,
                 upload: bool = False, privacy: str = "private",
                 niche: str = "facts", quality_tier: str = "balanced",
                 format: str = "shorts",
                 progress_callback=None) -> dict:
    """Run the full automation pipeline with niche optimization and quality tiers."""
    tier = QUALITY_TIERS.get(quality_tier, QUALITY_TIERS["balanced"])

    def progress(step, msg):
        if progress_callback:
            progress_callback(step, 6, msg)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {"topic": topic, "niche": niche, "quality_tier": quality_tier, "timestamp": ts, "steps": {}}
    logger.info("Pipeline started — topic=%r niche=%s quality=%s", topic, niche, quality_tier)

    # Step 1 — Script
    progress(1, f"Generating {niche} script with Claude...")
    logger.info("Step 1: generating script")
    script_result = _retry(script_writer.generate_script, topic,
                           duration_minutes=duration_minutes, niche=niche)
    result["steps"]["script"] = script_result
    if not script_result["success"]:
        return {"success": False, "error": f"Script failed: {script_result['error']}", **result}

    # Step 2 — Voiceover + Parallel: Thumbnail + Footage search
    progress(2, "Generating voiceover and searching footage in parallel...")

    thumb_result = {"success": False, "error": "Not started"}
    footage_result = {"success": False, "error": "Not started"}

    def gen_thumbnail():
        nonlocal thumb_result
        thumb_result = _retry(thumbnail.generate_thumbnail, topic,
                               title=script_result.get("title"),
                               niche=niche,
                               variations=tier["thumbnail_variations"])

    def search_footage_parallel():
        nonlocal footage_result
        # Parse B-ROLL markers from script for targeted searches
        broll_queries = footage.parse_broll_markers(script_result.get("script", ""))
        # Fallback to topic if no markers found
        if not broll_queries:
            broll_queries = [topic]
        broll_queries = broll_queries[:tier["max_broll_queries"]]
        footage_result = footage.search_footage_multi(
            broll_queries,
            clips_per_query=tier["clips_per_query"]
        )

    # Start parallel tasks
    t1 = threading.Thread(target=gen_thumbnail)
    t2 = threading.Thread(target=search_footage_parallel)
    t1.start(); t2.start()

    # Generate voiceover while parallel tasks run
    vo_result = _retry(voiceover.generate_voiceover,
                        script_result["script"],
                        niche=niche,
                        output_filename=f"voiceover_{niche}_{ts}.mp3")
    result["steps"]["voiceover"] = vo_result

    # Wait for parallel tasks
    t1.join(); t2.join()
    result["steps"]["thumbnail"] = thumb_result
    result["steps"]["footage"] = footage_result

    if not vo_result["success"]:
        return {"success": False, "error": f"Voiceover failed: {vo_result['error']}", **result}

    # Step 3 — Download clips
    progress(3, "Downloading stock footage clips...")
    clip_paths = []
    max_clips = tier["max_broll_queries"] * tier["clips_per_query"]
    if footage_result["success"] and footage_result.get("videos"):
        for i, vid in enumerate(footage_result["videos"][:max_clips]):
            progress(3, f"Downloading clip {i+1} of {min(len(footage_result['videos']), max_clips)}...")
            dl = footage.download_clip(vid["url"], output_filename=f"clip_{niche}_{ts}_{i}.mp4")
            if dl["success"]:
                clip_paths.append(dl["path"])

    # Extract section labels from script for text overlays
    import re as _re
    section_labels = _re.findall(
        r'\[(?:SECTION \d+|HOOK|INTRO)[^\]]*\]\s*\n.*?\n(.{10,60})',
        script_result.get("script", ""),
        _re.DOTALL
    )
    # Fallback: grab first sentence of each B-ROLL section
    if not section_labels:
        section_labels = []

    # Step 4 — Assemble video
    progress(4, "Assembling video (this takes a few minutes)...")
    if clip_paths:
        def assembly_progress(msg):
            progress(4, f"Assembling: {msg}")
        video_result = _retry(video_assembler.assemble_video,
                               vo_result["path"], clip_paths,
                               output_filename=f"video_{niche}_{ts}.mp4",
                               progress_callback=assembly_progress,
                               section_labels=section_labels,
                               format=format)
    else:
        video_result = {"success": False, "error": "No clips downloaded — skipping assembly"}
    result["steps"]["video"] = video_result

    # Step 5 — Upload (optional)
    progress(5, "Uploading to YouTube..." if upload else "Skipping upload...")
    upload_result = {"success": False, "error": "Upload skipped"}
    if upload and video_result.get("success"):
        tags = [t.strip() for t in script_result.get("tags", "").split(",") if t.strip()]
        upload_result = _retry(youtube_uploader.upload_video,
                                video_path=video_result["path"],
                                title=script_result.get("title", topic),
                                description=script_result.get("description", ""),
                                tags=tags, privacy=privacy)
    result["steps"]["upload"] = upload_result

    progress(6, "Pipeline complete!")

    entry = {
        "topic": topic, "niche": niche, "quality_tier": quality_tier,
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
        "topic": topic, "niche": niche,
        "title": script_result.get("title", topic),
        "script": script_result.get("script", ""),
        "voiceover_path": vo_result.get("path"),
        "thumbnail_path": thumb_result.get("path") if thumb_result.get("success") else None,
        "video_path": video_result.get("path") if video_result.get("success") else None,
        "youtube_url": upload_result.get("url"),
        "steps": result["steps"],
    }
