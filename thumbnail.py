"""thumbnail.py — Generate YouTube thumbnails using DALL-E 3 with niche-specific styles."""
import requests
import os
from datetime import datetime
from pathlib import Path
import config

NICHE_THUMBNAIL_STYLES = {
    "ranking": "Bold giant number (40–60% of frame height) in red or gold on the left. 2–3 relevant visuals (flags, athlete photos, movie posters) on the right stacked vertically. 3-word title in Impact or Anton font with thick black stroke, white fill. High contrast. Red/gold for military/power topics. Blue/white for geography/data. Black/yellow for sports. The number IS the hook — make it dominate. Looks like it belongs next to MrBeast or WatchMojo but sharper and cleaner.",
    "finance": "Dark navy or black background. A single dominant visual — stacks of cash, a graph spiking, or a luxurious item. Bold yellow or gold text overlay in the left or right third, 3-5 words max, creating a curiosity gap (e.g. 'They Lied To You' or 'The $1M Mistake'). High contrast. Looks like it belongs next to Graham Stephan or Andrei Jikh.",
    "motivation": "Split composition: dramatic dark background on one side, bright warm light breaking through on the other. A silhouette of a person or a powerful lone figure. Bold white or orange text, 2-4 words, placed in high-contrast area. Should feel like a gut punch just from the image alone.",
    "facts": "Extremely high contrast. One central impossible-looking or mind-bending image that makes no sense at first glance. Bright background (electric blue, hot orange, or lime green). Bold white text with black shadow — a short question or shocking claim (3-5 words). Arrow pointing at the impossible thing. Viewer should think 'wait, what?' before reading a single word.",
    "top10": "Dark background. A dramatic montage or single shocking central image. Bold numbered text in red or gold. Short teaser text about the #1 entry in white. High energy, organized, looks like it belongs on WatchMojo or MrBeast adjacent channels.",
    "truecrime": "Almost entirely black. One harsh light source illuminating a face in shadow, a crime scene detail, or a mysterious object. Red accent — one red element only (text, line, or stain). 3-4 white words in uppercase. Deeply unsettling. Viewer feels something is wrong before they read anything.",
    "history": """Ultra-dramatic ancient scene — ruins, artifacts, or landscapes that look impossibly epic or mysterious.
    High contrast: rich dark shadows with bright warm highlights (golden hour, torchlight, dramatic sky).
    Bold white or golden text overlay, max 5 words, creating a burning question or shocking claim — examples: 'HOW DID THEY DO THIS?', 'THIS SHOULDN\\'T EXIST', 'NOBODY CAN EXPLAIN THIS', 'THE TRUTH ABOUT ANCIENT EGYPT'.
    Text should be large, readable at thumbnail size, placed in a clean area of sky or dark background.
    The image alone should make someone stop scrolling. Think: National Geographic meets MrBeast clickbait energy.
    No generic stock photo feel — it must look cinematic, dramatic, and real.""",
    "science": "Deep space or extreme close-up of something microscopic — the contrast of impossibly large or impossibly small. Dark background (near-black with deep purple or blue glow). One stunning central visual that looks almost fake. White text overlay, 4-5 words, a question or impossible claim. Should feel like the universe just broke.",
    "selfimprovement": "Split before/after composition, or a single person in a moment of transformation. Clean, warm background (amber, cream). Bold readable text in dark color, 3-5 words, direct address ('You're Doing This Wrong', 'Stop Doing This Now'). Feels personal and urgent without being loud.",
    "horror": "90% black. One terrifying focal point — a shadowy face, a hand reaching from darkness, an open door with nothing beyond it. A single red accent element. 2-4 uppercase white words. Viewer should feel their stomach drop just looking at it.",
    "meditation": "Soft, serene. Peaceful nature scene — still water, mountain mist, a single candle in darkness. Soft gradient blues and purples. Gentle white text, lowercase, 4-6 words. No hard edges anywhere. Should feel like exhaling.",
    "news": "Clean split layout. Map, flag, or key figure on one side. Bold white headline text on dark background on the other side. Professional but urgent. Red breaking news bar optional. Looks credible and important.",
    "roblox": "Neon explosion — electric blue, hot pink, bright yellow. Central shocked/excited face (avatar or real player). Huge bold text, 2-3 words, all caps. Red arrows or circles highlighting something. High energy chaos that stops a teen mid-scroll.",
}

NICHE_PROMPTS = {
    "finance": "A viral YouTube thumbnail for a finance video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio. This thumbnail must make someone stop scrolling.",
    "motivation": "A powerful viral YouTube thumbnail for a motivational video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio. It must create an emotional reaction before they read the title.",
    "facts": "A viral YouTube thumbnail for a facts video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio. The thumbnail alone should make someone think 'wait, what?'",
    "truecrime": "A viral YouTube thumbnail for a true crime video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio. Must create immediate unease and curiosity.",
    "history": "A viral YouTube thumbnail for a history video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio. This must be so visually striking and mysterious that someone scrolling past it CANNOT ignore it.",
    "science": "A viral YouTube thumbnail for a science video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio. Must make the viewer feel like reality just broke.",
    "horror": "A viral YouTube thumbnail for a horror video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio. Must feel genuinely terrifying at thumbnail size.",
    "meditation": "A calming YouTube thumbnail for a meditation video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio.",
    "news": "A professional urgent YouTube thumbnail for a news video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio.",
    "roblox": "A viral Roblox YouTube thumbnail for a video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio. Must stop a teen mid-scroll.",
    "top10": "A viral YouTube thumbnail for a top 10 video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio.",
    "selfimprovement": "A viral YouTube thumbnail for a self improvement video about: \"{title}\". {style} No borders, no watermarks. 16:9 ratio.",
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
