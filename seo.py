"""seo.py — YouTube SEO and metadata generation using Claude API."""
import anthropic
import json
import re
from datetime import datetime
from pathlib import Path
import config

NICHE_CPM_TABLE = {
    "Finance & Investing":    {"cpm": "$15-50", "rpm": "$8-27", "competition": "High"},
    "Tech & Business":        {"cpm": "$12-25", "rpm": "$7-14", "competition": "High"},
    "Health & Wellness":      {"cpm": "$8-20",  "rpm": "$4-11", "competition": "Medium"},
    "Science & Space":        {"cpm": "$6-12",  "rpm": "$3-7",  "competition": "Medium"},
    "History":                {"cpm": "$5-10",  "rpm": "$3-6",  "competition": "Medium"},
    "Self Improvement":       {"cpm": "$5-10",  "rpm": "$3-6",  "competition": "Medium-High"},
    "True Crime":             {"cpm": "$4-9",   "rpm": "$2-5",  "competition": "High"},
    "Facts / Did You Know":   {"cpm": "$4-10",  "rpm": "$2-6",  "competition": "High"},
    "Motivational & Quotes":  {"cpm": "$5-10",  "rpm": "$3-6",  "competition": "Very High"},
    "Horror & Scary Stories": {"cpm": "$3-7",   "rpm": "$2-4",  "competition": "Medium"},
    "Top 10 Lists":           {"cpm": "$4-8",   "rpm": "$2-5",  "competition": "Very High"},
    "News Summary":           {"cpm": "$4-8",   "rpm": "$2-5",  "competition": "High"},
    "Meditation & Sleep":     {"cpm": "$3-6",   "rpm": "$2-3",  "competition": "Medium"},
}

def generate_seo_package(topic: str, title: str, niche: str, script_text: str = "") -> dict:
    """Generate complete SEO package: 5 titles, description, tags, chapters."""
    if not config.ANTHROPIC_API_KEY:
        return {"success": False, "error": "ANTHROPIC_API_KEY not set"}
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        niche_label = niche.replace("_", " ").title()

        prompt = f"""Generate a complete YouTube SEO package for a {niche_label} video.

Topic: {topic}
Working Title: {title}
Script excerpt: {script_text[:1000] if script_text else "Not provided"}

Generate exactly the following in this format:

TITLES:
1. [title option 1 — 60 chars max]
2. [title option 2 — 60 chars max]
3. [title option 3 — 60 chars max]
4. [title option 4 — 60 chars max]
5. [title option 5 — 60 chars max]

DESCRIPTION:
[Full YouTube description — 250-350 words. Include: hook paragraph, video summary, timestamps placeholder, relevant links section placeholder, 3-5 hashtags, naturally incorporate 5-8 SEO keywords]

TAGS:
[20-25 comma-separated tags: primary keywords, related topics, broad categories, long-tail phrases]

SEO_SCORE:
[Overall SEO score 0-100 with one-line explanation]

TITLE_SCORES:
1: [score/100]
2: [score/100]
3: [score/100]
4: [score/100]
5: [score/100]"""

        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text

        # Parse titles
        titles = []
        titles_match = re.search(r'TITLES:\n(.*?)(?=\nDESCRIPTION:)', text, re.DOTALL)
        if titles_match:
            for line in titles_match.group(1).strip().split('\n'):
                m = re.match(r'\d+\.\s*(.*)', line.strip())
                if m:
                    titles.append(m.group(1).strip())

        # Parse description
        desc_match = re.search(r'DESCRIPTION:\n(.*?)(?=\nTAGS:)', text, re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else ""

        # Parse tags
        tags_match = re.search(r'TAGS:\n(.*?)(?=\nSEO_SCORE:|$)', text, re.DOTALL)
        tags_str = tags_match.group(1).strip() if tags_match else ""
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]

        # Parse SEO score
        score_match = re.search(r'SEO_SCORE:\n(.*?)(?=\nTITLE_SCORES:|$)', text, re.DOTALL)
        seo_score_text = score_match.group(1).strip() if score_match else "N/A"

        # Parse title scores
        title_scores = []
        ts_match = re.search(r'TITLE_SCORES:\n(.*?)$', text, re.DOTALL)
        if ts_match:
            for line in ts_match.group(1).strip().split('\n'):
                m = re.match(r'\d+:\s*(\d+)', line.strip())
                if m:
                    title_scores.append(int(m.group(1)))

        return {
            "success": True,
            "topic": topic,
            "niche": niche,
            "titles": titles,
            "title_scores": title_scores,
            "description": description,
            "tags": tags,
            "tag_count": len(tags),
            "seo_score": seo_score_text,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_cpm_table() -> dict:
    return NICHE_CPM_TABLE
