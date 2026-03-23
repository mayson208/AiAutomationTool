"""thumbnail.py — Generate YouTube thumbnails using DALL-E 3 with niche-specific styles."""
import requests
import os
from datetime import datetime
from pathlib import Path
import config

NICHE_THUMBNAIL_STYLES = {
    "finance": "Professional finance aesthetic. Clean background, bold typography, gold and dark blue color palette. Include visual elements suggesting wealth, charts, or currency. Sharp, trustworthy look.",
    "motivation": "Bold and energetic. Bright warm colors (orange, yellow, red). Inspirational imagery — mountains, sunrise, person achieving something. High contrast. Empowering feeling.",
    "facts": "Vibrant and eye-catching. Bright background with a surprising or mind-blowing central image. Bold text space. Use contrast colors. Make it feel like a revelation.",
    "top10": "List-style aesthetic. Bold numbered styling. Clean, organized. Use bright accent colors. Central compelling image. YouTube red and white color scheme works well.",
    "truecrime": "Dark, dramatic, high-contrast. Black background with red accents. Crime scene or investigative aesthetic. Shadowy, mysterious. Yellow police tape or crime imagery.",
    "history": "Cinematic and aged. Sepia tones or dramatic historical colors. Epic scale imagery. Battle scenes, ancient architecture, or dramatic portraits. Documentary feel.",
    "science": "Space and science aesthetic. Deep blues, purples, cosmic imagery. Stars, galaxies, molecular structures, or futuristic visuals. Sense of wonder and discovery.",
    "selfimprovement": "Clean and inspiring. Warm tones — amber, cream, sage green. Person succeeding or transforming. Uplifting. Minimalist with clear focal point.",
    "horror": "Dark and terrifying. Nearly black background. Red accents. Unsettling imagery, shadows, or horror symbols. High contrast. Designed to make viewer feel uneasy.",
    "meditation": "Serene and peaceful. Soft blues, purples, and whites. Nature elements — water, mountains, clouds. Calming. Soft gradients. No sharp contrasts.",
    "news": "Professional news aesthetic. Clean, serious. Dark background with bright accent. Map or globe imagery. Professional typography space. Credible and authoritative.",
    "roblox": "High-energy Roblox gaming thumbnail. Neon and vibrant colors — electric blue, hot pink, bright yellow. Exaggerated shocked or excited expression on an avatar or player. Bold 2-3 word text overlay. Blurred or stylized Roblox game background. Young, energetic, high-CTR style.",
}

NICHE_PROMPTS = {
    "finance": "A professional YouTube thumbnail for a finance video titled: \"{title}\". {style} Make it look like a top-performing finance channel thumbnail. 16:9 ratio, no borders, no watermarks.",
    "motivation": "A powerful YouTube thumbnail for a motivational video titled: \"{title}\". {style} Make it feel inspiring and urgent. 16:9 ratio, no borders, no watermarks.",
    "facts": "An eye-catching YouTube thumbnail for a facts video titled: \"{title}\". {style} It should make people want to click immediately. 16:9 ratio, no borders, no watermarks.",
    "truecrime": "A dramatic YouTube thumbnail for a true crime video titled: \"{title}\". {style} Make it feel like a true crime documentary thumbnail. 16:9 ratio, no borders, no watermarks.",
    "history": "A cinematic YouTube thumbnail for a history video titled: \"{title}\". {style} Make it feel epic and documentary-quality. 16:9 ratio, no borders, no watermarks.",
    "science": "A stunning YouTube thumbnail for a science video titled: \"{title}\". {style} Make it feel like a premium science documentary. 16:9 ratio, no borders, no watermarks.",
    "horror": "A terrifying YouTube thumbnail for a horror video titled: \"{title}\". {style} Make it feel genuinely unsettling. 16:9 ratio, no borders, no watermarks.",
    "meditation": "A peaceful YouTube thumbnail for a meditation video titled: \"{title}\". {style} Make it feel deeply calming. 16:9 ratio, no borders, no watermarks.",
    "roblox": "A high-energy Roblox YouTube thumbnail for a video titled: \"{title}\". {style} Make it look like a viral Roblox channel thumbnail that gets clicked by teens. 16:9 ratio, no borders, no watermarks.",
}

def _get_prompt(topic: str, title: str, niche: str) -> str:
    prompt_text = title or topic
    style = NICHE_THUMBNAIL_STYLES.get(niche, NICHE_THUMBNAIL_STYLES["facts"])
    template = NICHE_PROMPTS.get(niche, "A professional YouTube thumbnail for: \"{title}\". {style} 16:9 ratio, no borders, no watermarks.")
    return template.format(title=prompt_text, style=style)

def generate_thumbnail(topic: str, title: str = None, output_filename: str = None,
                        niche: str = "facts", variations: int = 1) -> dict:
    """Generate YouTube thumbnail(s) using DALL-E 3."""
    if not config.OPENAI_API_KEY:
        return {"success": False, "error": "OPENAI_API_KEY not set"}

    thumbnails_dir = config.OUTPUTS_DIR / "thumbnails"
    thumbnails_dir.mkdir(parents=True, exist_ok=True)

    try:
        headers = {
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        prompt = _get_prompt(topic, title, niche)
        generated = []
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i in range(variations):
            # Vary the prompt slightly for each variation
            varied_prompt = prompt if i == 0 else prompt + f" Variation {i+1}: use a different composition and color emphasis."
            payload = {
                "model": config.OPENAI_IMAGE_MODEL,
                "prompt": varied_prompt,
                "n": 1,
                "size": "1792x1024",
                "quality": "hd" if variations == 1 else "standard",
            }
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                json=payload, headers=headers, timeout=60,
            )
            response.raise_for_status()
            image_url = response.json()["data"][0]["url"]
            img_response = requests.get(image_url, timeout=60)
            img_response.raise_for_status()

            fname = output_filename if (output_filename and i == 0) else f"thumbnail_{niche}_{ts}_v{i+1}.png"
            out_path = thumbnails_dir / fname
            with open(out_path, "wb") as f:
                f.write(img_response.content)
            generated.append({"filename": fname, "path": str(out_path), "url": image_url})

        primary = generated[0]
        return {
            "success": True,
            "path": primary["path"],
            "filename": primary["filename"],
            "url": primary["url"],
            "niche": niche,
            "variations": generated,
            "variation_count": len(generated),
        }
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"OpenAI API error {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def score_thumbnail_ctr(niche: str, has_bold_colors: bool = True) -> dict:
    """Rule-based CTR score for a thumbnail concept."""
    scores = {
        "finance": {"base": 72, "tips": ["Add gold/money imagery", "Keep text under 5 words", "Use dark blue background"]},
        "facts": {"base": 68, "tips": ["Lead with most shocking fact", "Use bright colors", "Add question mark or exclamation"]},
        "motivation": {"base": 65, "tips": ["Use warm colors (orange/yellow)", "Show aspiration/achievement", "Keep text 3 words max"]},
        "truecrime": {"base": 74, "tips": ["Dark background essential", "Red accent colors boost CTR", "Mysterious/dramatic imagery"]},
        "history": {"base": 70, "tips": ["Cinematic/epic scale", "Historical imagery", "Documentary-style text"]},
        "science": {"base": 69, "tips": ["Space/cosmic imagery", "Mind-bending visual", "Use blues and purples"]},
        "horror": {"base": 73, "tips": ["Nearly black background", "One terrifying focal point", "Red accent only"]},
        "meditation": {"base": 62, "tips": ["Keep it simple and calming", "No text needed", "Nature imagery works best"]},
    }
    data = scores.get(niche, {"base": 65, "tips": ["Use high contrast", "Bold central image", "Minimal text"]})
    score = data["base"] + (5 if has_bold_colors else 0)
    return {"score": min(score, 95), "tips": data["tips"]}
