"""compliance.py — YouTube compliance checking and AI disclosure management."""
import re
import anthropic
import config

DEMONETIZATION_KEYWORDS = [
    "kill", "murder", "suicide", "terrorist", "bomb", "drugs", "racist",
    "hate", "abuse", "graphic", "explicit", "nsfw", "shooting", "violence",
]

REQUIRED_DISCLOSURE = (
    "This video was created with the assistance of artificial intelligence (AI) tools "
    "for script writing, voiceover, and/or visual content generation."
)

def get_ai_disclosure(format: str = "description") -> str:
    """Return the standard AI disclosure text."""
    if format == "description":
        return f"\n\n⚠️ AI Disclosure: {REQUIRED_DISCLOSURE}"
    elif format == "short":
        return "⚠️ AI-assisted content. See description."
    return REQUIRED_DISCLOSURE

def check_script_policy(script_text: str) -> dict:
    """Flag potential policy violations in a script."""
    issues = []
    warnings = []
    risk_score = 0

    script_lower = script_text.lower()
    for kw in DEMONETIZATION_KEYWORDS:
        count = script_lower.count(kw)
        if count > 0:
            if count >= 3:
                issues.append(f"High-risk keyword '{kw}' appears {count} times")
                risk_score += 15
            else:
                warnings.append(f"Keyword '{kw}' appears {count} time(s) — review context")
                risk_score += 5

    # Check for potential copyright issues
    if re.search(r'(?i)(lyrics|chorus|verse|song by|written by)', script_text):
        warnings.append("Possible copyrighted lyrics detected — remove or paraphrase")
        risk_score += 10

    # Check script length (too short = low value content)
    word_count = len(script_text.split())
    if word_count < 500:
        warnings.append(f"Script only {word_count} words — YouTube may flag as low-value content (aim for 1,000+)")
        risk_score += 8

    # Check for clickbait extremes
    if re.search(r'(?i)\b(100%|guaranteed|secret|they don\'t want you|banned|censored)\b', script_text):
        warnings.append("Potentially misleading claims detected — ensure content backs up the title")
        risk_score += 7

    risk_level = "Low" if risk_score < 15 else "Medium" if risk_score < 35 else "High"
    risk_color = "success" if risk_score < 15 else "warning" if risk_score < 35 else "error"

    return {
        "success": True,
        "risk_score": min(risk_score, 100),
        "risk_level": risk_level,
        "risk_color": risk_color,
        "issues": issues,
        "warnings": warnings,
        "word_count": word_count,
        "disclosure_needed": True,
        "disclosure_text": get_ai_disclosure("description"),
    }

def build_compliant_description(description: str, niche: str) -> str:
    """Add AI disclosure and compliance elements to a description."""
    compliant = description
    if "ai disclosure" not in description.lower() and "artificial intelligence" not in description.lower():
        compliant += get_ai_disclosure("description")
    return compliant

def check_music_license(music_source: str) -> dict:
    """Check if a music source is safe for YouTube monetization."""
    safe_sources = {
        "youtube audio library": "Safe — royalty-free, no attribution needed",
        "epidemic sound": "Safe — subscription covers commercial use",
        "artlist": "Safe — subscription covers commercial use",
        "pixabay": "Safe — CC0 license, no attribution needed",
        "incompetech": "Safe — CC BY license, attribution required",
        "bensound": "Safe with attribution for non-commercial; paid license for monetized",
        "uppbeat": "Safe — free tier requires attribution",
    }
    source_lower = music_source.lower()
    for key, value in safe_sources.items():
        if key in source_lower:
            return {"success": True, "source": music_source, "status": "safe", "notes": value}
    return {
        "success": True,
        "source": music_source,
        "status": "unknown",
        "notes": "Source not in verified list — verify license before using in monetized content",
    }
