"""thumbnail.py — Generate YouTube thumbnails using DALL-E 3."""
import requests
import os
from datetime import datetime
from pathlib import Path
import config

def generate_thumbnail(topic: str, title: str = None, output_filename: str = None) -> dict:
    """Generate a YouTube thumbnail image using DALL-E 3."""
    if not config.OPENAI_API_KEY:
        return {"success": False, "error": "OPENAI_API_KEY not set"}
    try:
        prompt_text = title or topic
        prompt = f"""Create a professional YouTube thumbnail for a video titled: "{prompt_text}"

Requirements:
- Bold, eye-catching design with high contrast
- Large readable text overlay (3-5 words max)
- Professional and clean look
- YouTube thumbnail style (16:9 ratio)
- Vibrant colors that pop on dark backgrounds
- Photorealistic or high-quality illustration style
- NO watermarks, NO borders"""

        headers = {
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config.OPENAI_IMAGE_MODEL,
            "prompt": prompt,
            "n": 1,
            "size": config.OPENAI_IMAGE_SIZE,
            "quality": "standard",
        }
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            json=payload, headers=headers
        )
        response.raise_for_status()
        image_url = response.json()["data"][0]["url"]
        # Download the image
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        if not output_filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"thumbnail_{ts}.png"
        out_path = config.OUTPUTS_DIR / output_filename
        with open(out_path, "wb") as f:
            f.write(img_response.content)
        return {
            "success": True,
            "path": str(out_path),
            "filename": output_filename,
            "url": image_url,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
