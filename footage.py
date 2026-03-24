"""footage.py — Search and download stock footage from Pexels."""
import requests
import re
import os
from datetime import datetime
from pathlib import Path
import config


def parse_broll_markers(script_text: str) -> list:
    """Extract all [B-ROLL: description] queries from a script."""
    markers = re.findall(r'\[B-ROLL:\s*(.+?)\]', script_text, re.IGNORECASE)
    # Deduplicate while preserving order
    seen, unique = set(), []
    for m in markers:
        clean = m.strip()
        if clean.lower() not in seen:
            seen.add(clean.lower())
            unique.append(clean)
    return unique


def search_footage(query: str, per_page: int = 5) -> dict:
    """Search Pexels for stock footage clips matching the query."""
    if not config.PEXELS_API_KEY:
        return {"success": False, "error": "PEXELS_API_KEY not set"}
    try:
        headers = {"Authorization": config.PEXELS_API_KEY}
        params = {"query": query, "per_page": per_page, "size": "medium"}
        response = requests.get(f"{config.PEXELS_API_URL}/search",
                                headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        videos = []
        for video in data.get("videos", []):
            best_file = None
            for vf in video.get("video_files", []):
                if vf.get("quality") in ("hd", "sd") and vf.get("file_type") == "video/mp4":
                    if best_file is None or vf.get("width", 0) > best_file.get("width", 0):
                        best_file = vf
            if best_file:
                videos.append({
                    "id": video["id"],
                    "duration": video.get("duration", 0),
                    "url": best_file["link"],
                    "width": best_file.get("width"),
                    "height": best_file.get("height"),
                    "thumbnail": video.get("image", ""),
                    "photographer": video.get("user", {}).get("name", ""),
                    "query": query,
                })
        return {"success": True, "videos": videos, "total": data.get("total_results", 0)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_footage_multi(queries: list, clips_per_query: int = 3) -> dict:
    """Search multiple queries and return a diverse pool of clips."""
    if not queries:
        return {"success": False, "error": "No queries provided"}

    all_videos = []
    seen_ids = set()

    for query in queries:
        result = search_footage(query, per_page=clips_per_query + 1)
        if result.get("success"):
            for v in result["videos"]:
                if v["id"] not in seen_ids:
                    seen_ids.add(v["id"])
                    all_videos.append(v)

    # Fallback: if a query returned nothing, try a simplified version
    if len(all_videos) < len(queries):
        fallback_queries = list({q.split()[0] for q in queries if q.split()})
        for q in fallback_queries:
            result = search_footage(q, per_page=2)
            if result.get("success"):
                for v in result["videos"]:
                    if v["id"] not in seen_ids:
                        seen_ids.add(v["id"])
                        all_videos.append(v)

    if not all_videos:
        return {"success": False, "error": "No footage found for any query"}

    return {"success": True, "videos": all_videos, "total": len(all_videos)}


def download_clip(video_url: str, output_filename: str = None) -> dict:
    """Download a Pexels video clip."""
    try:
        if not output_filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"clip_{ts}.mp4"
        out_path = config.OUTPUTS_DIR / output_filename
        response = requests.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return {"success": True, "path": str(out_path), "filename": output_filename}
    except Exception as e:
        return {"success": False, "error": str(e)}
