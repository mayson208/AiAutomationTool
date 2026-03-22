"""footage.py — Search and download stock footage from Pexels."""
import requests
import os
from datetime import datetime
from pathlib import Path
import config

def search_footage(query: str, per_page: int = 5) -> dict:
    """Search Pexels for stock footage clips matching the query."""
    if not config.PEXELS_API_KEY:
        return {"success": False, "error": "PEXELS_API_KEY not set"}
    try:
        headers = {"Authorization": config.PEXELS_API_KEY}
        params = {"query": query, "per_page": per_page, "size": "medium"}
        response = requests.get(f"{config.PEXELS_API_URL}/search", headers=headers, params=params)
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
                })
        return {"success": True, "videos": videos, "total": data.get("total_results", 0)}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
