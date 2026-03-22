"""script_writer.py — Generate YouTube scripts using Claude API with niche optimization."""
import anthropic
import re
import os
import json
from datetime import datetime
from pathlib import Path
import config

NICHES = {
    "finance": {
        "label": "Finance & Investing",
        "tone": "authoritative, data-driven, professional",
        "style": "Lead with a surprising statistic or counterintuitive insight. Use numbered frameworks. Cite sources. Address common mistakes. Include actionable takeaways.",
        "hook_style": "shocking financial statistic or common misconception",
        "optimal_minutes": 12,
        "cpm": "$15-50",
    },
    "motivation": {
        "label": "Motivational & Quotes",
        "tone": "passionate, inspiring, urgent",
        "style": "Open with a powerful story or quote. Build emotional momentum. Use short punchy sentences. Include a call to transformation. End with a challenge to the viewer.",
        "hook_style": "powerful story or emotional question",
        "optimal_minutes": 6,
        "cpm": "$5-10",
    },
    "facts": {
        "label": "Did You Know / Facts",
        "tone": "curious, enthusiastic, educational",
        "style": "Start with the most shocking fact. Keep each fact concise (30-60 seconds). Include surprising context. Use curiosity gaps between facts. End with a mind-blowing conclusion.",
        "hook_style": "the most shocking fact in the video",
        "optimal_minutes": 8,
        "cpm": "$4-10",
    },
    "top10": {
        "label": "Top 10 Lists",
        "tone": "entertaining, confident, engaging",
        "style": "Start at #10, build toward #1. Give each item equal weight. Include surprising entries. Use teases ('wait until you see #3'). Keep rankings defensible.",
        "hook_style": "tease about the surprising #1 pick",
        "optimal_minutes": 10,
        "cpm": "$4-8",
    },
    "truecrime": {
        "label": "True Crime",
        "tone": "serious, suspenseful, investigative",
        "style": "Open at the most dramatic moment. Build timeline chronologically. Use cliffhangers between sections. Include investigative details. Handle sensitivity appropriately.",
        "hook_style": "the most dramatic moment of the story",
        "optimal_minutes": 20,
        "cpm": "$4-9",
    },
    "history": {
        "label": "History",
        "tone": "authoritative, storytelling, cinematic",
        "style": "Open with a dramatic scene. Provide rich historical context. Use storytelling arcs. Connect past events to modern relevance. Include lesser-known details.",
        "hook_style": "a dramatic scene or surprising historical fact",
        "optimal_minutes": 15,
        "cpm": "$5-10",
    },
    "science": {
        "label": "Science & Space",
        "tone": "wonder-inducing, informative, accessible",
        "style": "Start with a mind-bending concept. Explain complex ideas simply. Use analogies. Build from basic to advanced. Include recent discoveries. End with implications.",
        "hook_style": "a mind-bending question or recent discovery",
        "optimal_minutes": 10,
        "cpm": "$6-12",
    },
    "selfimprovement": {
        "label": "Self Improvement",
        "tone": "warm, encouraging, actionable",
        "style": "Open with a relatable struggle. Present a clear system or framework. Use numbered steps. Include scientific backing. Give specific actionable advice. End with encouragement.",
        "hook_style": "a relatable pain point or surprising productivity insight",
        "optimal_minutes": 10,
        "cpm": "$5-10",
    },
    "horror": {
        "label": "Horror & Scary Stories",
        "tone": "atmospheric, tense, suspenseful",
        "style": "Build atmosphere slowly. Use sensory details. Pace tension carefully. Include surprising twists. Use cliffhangers. Handle horror elements responsibly.",
        "hook_style": "the most unsettling element of the story",
        "optimal_minutes": 15,
        "cpm": "$3-7",
    },
    "meditation": {
        "label": "Meditation & Sleep",
        "tone": "calm, soothing, gentle",
        "style": "Open softly. Use slow, measured pacing. Include breathing cues. Guide visualization. Use repetitive calming patterns. Avoid sudden changes in tone.",
        "hook_style": "a peaceful invitation to relax",
        "optimal_minutes": 30,
        "cpm": "$3-6",
    },
    "news": {
        "label": "News Summary",
        "tone": "professional, balanced, clear",
        "style": "Lead with the most important development. Provide context and background. Include multiple perspectives. Keep it factual. Summarize clearly. Update viewers on what to watch.",
        "hook_style": "the most significant news development",
        "optimal_minutes": 7,
        "cpm": "$4-8",
    },
}

HOOK_FORMULAS = [
    "SHOCK: Start with the most shocking, counterintuitive, or surprising element related to this topic. Make the viewer think 'I never knew that.'",
    "QUESTION: Open with a powerful question that the viewer desperately wants answered. Make it personal and relatable.",
    "STORY: Begin in the middle of a dramatic story or scene. Drop the viewer into action immediately.",
]

def _save_script(topic: str, niche: str, result: dict) -> str:
    """Save script to outputs/scripts/ organized by date and niche."""
    scripts_dir = config.OUTPUTS_DIR / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{niche}_{re.sub(r'[^a-zA-Z0-9]', '_', topic[:40])}.json"
    out_path = scripts_dir / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"topic": topic, "niche": niche, "timestamp": ts, **result}, f, indent=2, ensure_ascii=False)
    return str(out_path)

def generate_hooks(topic: str, niche: str) -> dict:
    """Generate 3 hook options for the user to choose from."""
    if not config.ANTHROPIC_API_KEY:
        return {"success": False, "error": "ANTHROPIC_API_KEY not set"}
    niche_info = NICHES.get(niche, NICHES["facts"])
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        prompt = f"""Generate exactly 3 different hook options for a YouTube video about: "{topic}"
Niche: {niche_info['label']}
Tone: {niche_info['tone']}

Each hook is the opening 20-30 seconds of the video (spoken aloud, ~75-100 words each).

Hook 1 — SHOCK FORMULA: {HOOK_FORMULAS[0]}
Hook 2 — QUESTION FORMULA: {HOOK_FORMULAS[1]}
Hook 3 — STORY FORMULA: {HOOK_FORMULAS[2]}

Format your response exactly as:
HOOK_1:
[hook text]

HOOK_2:
[hook text]

HOOK_3:
[hook text]"""

        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text
        hooks = []
        for i in range(1, 4):
            pattern = rf"HOOK_{i}:\s*(.*?)(?=HOOK_{i+1}:|$)"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                hooks.append(match.group(1).strip())
            else:
                hooks.append(f"Hook {i} not generated")
        return {"success": True, "hooks": hooks}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_script(topic: str, duration_minutes: int = None, niche: str = "facts",
                    selected_hook: str = None) -> dict:
    """Generate a full YouTube script optimized for the selected niche."""
    if not config.ANTHROPIC_API_KEY:
        return {"success": False, "error": "ANTHROPIC_API_KEY not set"}
    niche_info = NICHES.get(niche, NICHES["facts"])
    if duration_minutes is None:
        duration_minutes = niche_info["optimal_minutes"]
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        hook_instruction = ""
        if selected_hook:
            hook_instruction = f"\n\nIMPORTANT: Start the script with this exact hook:\n{selected_hook}\n"

        prompt = f"""Write a complete YouTube video script for: "{topic}"

Niche: {niche_info['label']}
Tone: {niche_info['tone']}
Style guidelines: {niche_info['style']}
Target length: {duration_minutes} minutes
{hook_instruction}

RETENTION RULES (apply throughout):
- Pattern interrupt every 90-120 seconds (change topic angle, ask question, reveal surprise)
- Open loop: hint at upcoming information to keep viewers watching
- Curiosity gap: start explaining something, pause, continue after B-roll note
- Never start a new section without a transition hook

FORMAT (use exactly these labels):
TITLE: [YouTube title with number or power word, 60 chars max]
DESCRIPTION: [150-word SEO description with keywords]
TAGS: [15 comma-separated tags]

SCRIPT:
[HOOK - 0:00]
[hook content]

[INTRO - 0:30]
[intro content]

[SECTION 1 - timestamp]
[content with [B-ROLL: description] markers]

[continue sections...]

[CTA - timestamp]
[like, comment, subscribe]

[OUTRO - timestamp]
[closing]

Write naturally as spoken dialogue. Include [B-ROLL: description] markers every 45-90 seconds."""

        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        script_text = message.content[0].text

        # Run humanizer pass
        humanizer_prompt = f"""Review this YouTube script and make it sound more natural and human.
Remove any AI writing patterns: overly formal phrasing, repetitive sentence structures, generic transitions.
Make it conversational, punchy, and authentic to the {niche_info['label']} niche.
Keep all [B-ROLL:] markers, timestamps, and section headers exactly as they are.
Only improve the spoken dialogue portions.

Script:
{script_text}"""

        human_message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=6000,
            messages=[{"role": "user", "content": humanizer_prompt}]
        )
        final_script = human_message.content[0].text

        # Parse metadata
        lines = final_script.split('\n')
        title = next((l.replace('TITLE:', '').strip() for l in lines if l.strip().startswith('TITLE:')), topic)
        description, tags = "", ""
        for i, line in enumerate(lines):
            if line.strip().startswith('DESCRIPTION:'):
                desc_lines = []
                for j in range(i + 1, min(i + 15, len(lines))):
                    if lines[j].strip().startswith(('TAGS:', 'SCRIPT:', 'HOOK')):
                        break
                    desc_lines.append(lines[j])
                description = ' '.join(desc_lines).strip()
            if line.strip().startswith('TAGS:'):
                tags = line.replace('TAGS:', '').strip()

        # Estimate readability
        words = len(final_script.split())
        estimated_minutes = round(words / 150)  # ~150 words/minute speaking pace

        result = {
            "success": True,
            "topic": topic,
            "niche": niche,
            "niche_label": niche_info["label"],
            "title": title,
            "description": description,
            "tags": tags,
            "script": final_script,
            "word_count": words,
            "estimated_minutes": estimated_minutes,
            "cpm_range": niche_info["cpm"],
        }
        result["saved_path"] = _save_script(topic, niche, result)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
