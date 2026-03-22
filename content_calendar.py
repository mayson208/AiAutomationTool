"""content_calendar.py — Generate 30-day content calendars using Claude API."""
import anthropic
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import config

NICHE_POSTING_FREQ = {
    "finance": 3, "motivation": 7, "facts": 4, "top10": 4,
    "truecrime": 2, "history": 3, "science": 3, "selfimprovement": 4,
    "horror": 2, "meditation": 3, "news": 7,
}

def generate_calendar(niche: str, posting_freq: int = None, start_date: str = None) -> dict:
    """Generate a 30-day content calendar for the given niche."""
    if not config.ANTHROPIC_API_KEY:
        return {"success": False, "error": "ANTHROPIC_API_KEY not set"}

    if posting_freq is None:
        posting_freq = NICHE_POSTING_FREQ.get(niche, 3)

    if start_date is None:
        start_date = datetime.now().strftime("%Y-%m-%d")

    start = datetime.strptime(start_date, "%Y-%m-%d")
    total_videos = min(posting_freq * 4, 30)  # 30-day worth

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        niche_label = niche.replace("_", " ").title()

        prompt = f"""Generate {total_videos} YouTube video topic ideas for a {niche_label} channel over 30 days.

Requirements:
- Mix of evergreen content (70%) and trending/timely topics (30%)
- Vary the format: some lists, some stories, some how-tos, some analyses
- Each topic should be SEO-friendly and clickable
- Spread across {posting_freq} videos per week
- Include reasoning for why each topic will perform well

Format exactly as JSON array:
[
  {{
    "day": 1,
    "date": "YYYY-MM-DD",
    "title": "compelling video title",
    "topic": "brief topic description",
    "type": "evergreen|trending|seasonal",
    "hook": "one-sentence hook for this video",
    "why": "brief reason this will perform"
  }},
  ...
]

Start date: {start_date}
Only output the JSON array, nothing else."""

        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text

        # Extract JSON
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if not json_match:
            return {"success": False, "error": "Could not parse calendar JSON"}

        calendar_data = json.loads(json_match.group(0))

        # Save to data directory
        data_dir = config.BASE_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        cal_path = data_dir / f"calendar_{niche}_{ts}.json"
        with open(cal_path, "w") as f:
            json.dump({"niche": niche, "generated": ts, "calendar": calendar_data}, f, indent=2)

        return {
            "success": True,
            "niche": niche,
            "posting_freq": posting_freq,
            "total_videos": len(calendar_data),
            "calendar": calendar_data,
            "start_date": start_date,
        }
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parse error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_topic_bank(niche: str, count: int = 50) -> dict:
    """Generate a bank of video topic ideas."""
    if not config.ANTHROPIC_API_KEY:
        return {"success": False, "error": "ANTHROPIC_API_KEY not set"}
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        niche_label = niche.replace("_", " ").title()
        prompt = f"""Generate {count} unique YouTube video topic ideas for a {niche_label} channel.

Each should be a compelling, clickable title ready to use.
Mix formats: lists, stories, how-tos, analyses, questions.
Focus on high-search-volume topics that are proven to work.

Output as a JSON array of strings:
["title 1", "title 2", ...]

Only output the JSON array."""

        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if not json_match:
            return {"success": False, "error": "Could not parse topics JSON"}
        topics = json.loads(json_match.group(0))
        return {"success": True, "niche": niche, "topics": topics, "count": len(topics)}
    except Exception as e:
        return {"success": False, "error": str(e)}
