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
        "tone": "straight-talking, sharp, like a friend who actually knows money",
        "style": "Hit them with a shocking number or counterintuitive money fact in the first sentence — no setup. Short punchy sentences. Use contractions. Say 'most people' not 'numerous individuals'. Say 'back then' not 'during that period'. Sound like a smart friend explaining why they're doing something most people get wrong. Every 90 seconds, drop a curiosity gap — tease the next piece of info before fully landing it.",
        "hook_style": "a shocking money stat or the thing most people get completely backwards",
        "optimal_minutes": 12,
        "cpm": "$15-50",
    },
    "motivation": {
        "label": "Motivational & Quotes",
        "tone": "urgent, real, emotionally direct — not a self-help book",
        "style": "Open with a single powerful line — a gut-punch truth or a shocking story moment. No warm-up. Short sentences. Use 'you' constantly. Say 'you're' not 'one is'. Speak like someone who's been through it and is telling you what they wish they'd known. Build momentum sentence by sentence. End with a direct challenge to the viewer, not a summary.",
        "hook_style": "a raw emotional truth or a story dropped in mid-action",
        "optimal_minutes": 6,
        "cpm": "$5-10",
    },
    "facts": {
        "label": "Did You Know / Facts",
        "tone": "enthusiastic, curious, like a friend texting you something wild they just found out",
        "style": "Lead with the most mind-blowing fact — no intro, no context, just drop it. Keep each fact to 30-60 seconds of tight narration. Use '...' for dramatic pauses. Say 'nobody knows why' not 'the cause remains undetermined'. Say 'they figured it out' not 'scientists determined'. Use second person: 'You're looking at something that shouldn't exist.' Between facts, tease the next one with a curiosity gap.",
        "hook_style": "the single most shocking fact in the whole video, delivered raw with no setup",
        "optimal_minutes": 8,
        "cpm": "$4-10",
    },
    "top10": {
        "label": "Top 10 Lists",
        "tone": "confident, entertaining, slightly conspiratorial",
        "style": "Start at #10, build to #1. Open by teasing the #1 pick with a one-liner — don't explain it yet. Keep each entry tight: one shocking sentence to introduce it, then the payoff. Use second person throughout. Tease upcoming entries: 'Wait till you get to #3.' Short sentences. No academic tone. Sound like you're running through a list with a friend.",
        "hook_style": "a one-line tease about the #1 pick that makes them have to keep watching",
        "optimal_minutes": 10,
        "cpm": "$4-8",
    },
    "truecrime": {
        "label": "True Crime",
        "tone": "serious, tense, like a true crime podcast but tighter",
        "style": "Open at the most dramatic moment — drop in mid-scene, no intro. 'It was 2 AM. Nobody heard anything.' Short declarative sentences build dread. Then pull back and build the timeline. Use cliffhangers before section breaks. Say 'nobody could explain it' not 'the circumstances remained unclear'. Use contractions. Build tension with short incomplete sentences. Handle real victims with respect.",
        "hook_style": "the single most chilling moment of the story, dropped in cold with no setup",
        "optimal_minutes": 20,
        "cpm": "$4-9",
    },
    "history": {
        "label": "History",
        "tone": "like a genuinely excited person who actually knows the history and can't believe how wild it is — not a textbook, not a dramatic movie trailer, just a real person being honest about how insane the past was",
        "style": """Open cold with the most jaw-dropping fact or scene — no intro whatsoever.

The goal is to be THREE things at once: informative (real facts, real context, real history), casual (sounds like a real person talking, never an essay), and exciting (makes the viewer feel genuine wonder or disbelief).

Structure each section like this: drop a wild fact → explain the context behind it in plain language → connect it to something the viewer can visualize or feel → reveal the next wild thing.

Say 'nobody knows how they did it' not 'the methodology remains undetermined'.
Say 'back then' not 'during that era'.
Say 'they figured out' not 'scholars determined'.
Use scale and comparison: 'That's taller than a 20-story building. And they built it without cranes.'
Use wonder: 'Think about what that actually means...'
Make the past feel immediate — use present tense descriptions when describing historical scenes.
Sound like you personally can't believe this is real, because it genuinely is that wild.

Every 90-120 seconds add a pattern interrupt — shift the angle, ask a sharp question, or drop a surprise before continuing.
End sections with a teaser for what comes next — never let a section land flat.
Use curiosity gaps: start a revelation, pause with '...', then land the payoff after a beat.""",
        "hook_style": "drop cold into the single most shocking moment — no intro. Use one of these formulas: drop mid-scene ('It's [year]. [Something unexpected happening].'), counterintuitive reversal ('[Common belief]. That's completely backwards.'), scale shock ('[ancient thing] was [modern comparison] — built without [modern tool]'), or personal stakes ('This man had 48 hours to [action] before [consequence].')",
        "optimal_minutes": 15,
        "cpm": "$5-10",
    },
    "history_short": {
        "label": "History Shorts (60-Second Format)",
        "tone": "urgent, punchy, genuinely amazed — like you're about to tell a friend the wildest thing you just found out and you only have 60 seconds before they have to leave",
        "style": """This is a YouTube Short / TikTok. Vertical format. 45-60 seconds. Every single word earns its place.

6-PART PRODUCTION STRUCTURE (follow this exactly):
1. VISUAL HOOK (0-2s): The most dramatic or visually striking moment — described in [B-ROLL] marker. This is what stops the scroll.
2. SPOKEN HOOK (0-3s): One raw sentence. Drop the most shocking or counterintuitive fact cold — no setup, no 'Did you know', no intro. Just the statement. Viewer thinks: 'wait, that can't be right.'
3. DEEPENING (3-15s): One or two sentences that make it MORE mysterious, not less. Deepen the disbelief before explaining anything.
4. THE REVEAL (15-45s): The single most interesting fact, story beat, or insight — explained simply and fast. One thing only. No branching.
5. GUT-PUNCH CLOSE (45-55s): One line that recontextualizes everything above — a twist, a callback, or a statistic that makes the jaw drop.
6. LOOP POINT (55-60s): The final frame or line should naturally lead back to the opening — engineer the ending so viewers want to replay. Ideally the last word/image echoes the first.

LOOP ENGINEERING — THIS IS CRITICAL:
- Write the ending FIRST, then write the opening to mirror it.
- The last line should create a question or tension that the first line answers.
- Do NOT use a CTA — it breaks the loop and kills replays.
- No 'Like and subscribe.' No 'Follow for more.' The loop IS the call to action.

RULES:
- 110-135 words total. Count every word.
- Single topic. One fact or story arc. No branching.
- Sentences: 5-10 words max. One thought per sentence.
- Contractions everywhere: didn't, couldn't, they're, it's.
- No filler: cut 'basically', 'actually', 'essentially', 'remember'.
- Present tense for historical scenes: 'It's 1347. A ship pulls into port...'
- '...' for micro-pauses before reveals.
- Every paragraph gets a [B-ROLL: specific searchable footage query] marker ABOVE it — footage must match what's being said.

PROVEN VIRAL HOOK FORMULAS (pick the strongest for this topic):
- Drop cold into a scene: 'It's [year]. [Something unexpected is happening].'
- Counterintuitive reversal: '[Common belief]. That's completely backwards.'
- Scale shock: '[Ancient thing] was [modern comparison] — built without [modern tool].'
- Forgotten history: 'Nobody talks about what happened [before/after the famous event].'
- Personal stakes: 'This man had 48 hours to [action] before [consequence].'
- Modern mirror: '[Ancient civilization] figured out [modern concept] [X] years before we did.'

TOPICS THAT PERFORM BEST:
- Single shocking facts (ancient tech, forgotten inventions, bizarre laws)
- 'They got it wrong for 100 years' corrections
- Wild historical coincidences
- Forgotten people who changed history
- 'Textbooks skip this part' moments
- Events that feel eerily modern""",
        "hook_style": "one raw sentence — the single most shocking or counterintuitive thing about this topic, no setup. Viewer thinks 'wait, that can't be right' in the first 2 seconds.",
        "optimal_minutes": 1,
        "cpm": "$3-6 (Shorts CPM lower but volume/reach compensates — optimize for replays and shares)",
    },
    "science": {
        "label": "Science & Space",
        "tone": "wonder-struck, accessible, like someone who just learned something that broke their brain",
        "style": "Open with a mind-bending concept stated simply — no jargon, no setup. 'There's a place in the universe where time moves slower. You could live there for a year and come back to find 10 years have passed on Earth.' Short sentences. Use analogies to everyday things. Say 'we still don't know why' not 'the underlying mechanism remains elusive'. Second person: 'You're not going to believe what they found.' Use '...' for pauses that let the weird stuff land.",
        "hook_style": "a single mind-breaking concept stated in plain language with no setup",
        "optimal_minutes": 10,
        "cpm": "$6-12",
    },
    "selfimprovement": {
        "label": "Self Improvement",
        "tone": "warm but direct — like a friend who stopped making excuses and is telling you what actually worked",
        "style": "Open with a relatable struggle stated bluntly — not 'Many individuals find it challenging' but 'Most people quit in the first week. Here's why.' Short sentences. Use 'you' constantly. Use contractions. Give specific actionable advice in plain language. Say 'the trick is' not 'the optimal approach involves'. Back up claims conversationally: 'There's actually research on this and it's pretty wild.' End with a direct challenge, not a summary.",
        "hook_style": "a blunt relatable truth about a struggle, stated in one punchy sentence",
        "optimal_minutes": 10,
        "cpm": "$5-10",
    },
    "horror": {
        "label": "Horror & Scary Stories",
        "tone": "atmospheric, deeply unsettling, like someone whispering something they shouldn't know",
        "style": "Open with the single most unsettling detail — no buildup, just drop it cold. 'The door was locked from the inside. Nobody was home.' Short sentences that punch. Use sensory details: sounds, smells, textures. Build dread through what's NOT explained. Use '...' for pauses that let the horror land. Say 'nobody ever figured out what it was' not 'the identity of the entity remained unverified'. Handle real events with care.",
        "hook_style": "the single most chilling unexplained detail, stated cold in one sentence",
        "optimal_minutes": 15,
        "cpm": "$3-7",
    },
    "meditation": {
        "label": "Meditation & Sleep",
        "tone": "calm, slow, like a gentle voice in a quiet room",
        "style": "Open with a soft invitation — no shock, just ease them in. Long gentle sentences. Use breathing cues naturally: 'Take a slow breath...' Guide visualization step by step. Repeat calming phrases. Avoid sudden changes in pace or tone. Use '...' for natural breathing pauses. This is the one niche where slow and soft beats punchy.",
        "hook_style": "a gentle peaceful invitation to let go and relax",
        "optimal_minutes": 30,
        "cpm": "$3-6",
    },
    "news": {
        "label": "News Summary",
        "tone": "clear, direct, no-spin — like a trusted friend who read everything so you don't have to",
        "style": "Lead with the single most important development in one plain sentence. No 'In today's news...' or 'We're going to cover...' Just: what happened. Then give context in short punchy sentences. Say 'what this means for you' not 'the implications for the general public'. Use contractions. Keep it factual but conversational. End with what to watch next, stated simply.",
        "hook_style": "the most significant thing that happened, stated in one plain direct sentence",
        "optimal_minutes": 7,
        "cpm": "$4-8",
    },
    "roblox": {
        "label": "Roblox Gaming",
        "tone": "energetic, slightly dramatic, fast — teen and young adult audience",
        "style": "State the challenge in the first 5 seconds flat. No intro. 'I tried to survive 24 hours in the hardest Roblox game ever made. Here's what happened.' First person. Short fast sentences. React to what's happening in real time. Build tension, then a payoff. Use humor. Keep it moving — no dead air. IMPORTANT: Frame as teen/adult content — avoid child-directed language to prevent 'Made for Kids' classification which eliminates monetization.",
        "hook_style": "the bold challenge or crazy premise stated immediately in 5 seconds — no warmup",
        "optimal_minutes": 12,
        "cpm": "$2-4 (WARNING: 'Made for Kids' label drops CPM to ~$0.30 — frame as teen/adult content)",
    },
}

HOOK_FORMULAS = [
    "SHOCK: Drop the single most shocking or counterintuitive fact about this topic — no intro, no context, just the raw statement. Make them think 'wait, what?' in the first two seconds.",
    "QUESTION: Ask one sharp, personal question the viewer immediately wants answered — something that makes them feel like they've been missing something. No setup before the question.",
    "STORY: Drop into a dramatic scene mid-action — no introduction, no context. Put the viewer inside the moment. One or two short sentences maximum before the payoff.",
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

Each hook is the opening 20-30 seconds of narration (spoken aloud, ~60-80 words each).

CRITICAL RULES FOR ALL THREE HOOKS:
- The very first sentence must be the hook — a shocking statement or sharp question. Zero setup.
- Short punchy sentences. 1-2 sentences per thought max.
- Use contractions: didn't, couldn't, wasn't, they're, you're.
- Use second person where natural: "You're looking at...", "Think about that."
- Use "..." for dramatic pauses that let the wild stuff land.
- NEVER start with: "In this video", "Today we're going to", "Let's explore", "Throughout history", "It's worth noting"
- NO academic language. Say "a lot of people" not "numerous individuals". Say "figured out" not "determined". Say "back then" not "during that period".
- Sound like a smart friend who just learned something wild and can't wait to tell you.

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
Target length: {duration_minutes} minutes (~{duration_minutes * 150} words of spoken narration)
{hook_instruction}

VOICE AND STYLE — NON-NEGOTIABLE:
- Write exactly how a person talks, not how a person writes.
- Short punchy sentences. 1-2 sentences per thought. Max.
- Use contractions everywhere: didn't, couldn't, wasn't, they're, you're, it's, that's.
- Use "..." for dramatic pauses where the information should land before moving on.
- Use second person naturally: "You're looking at...", "Think about that for a second.", "You probably didn't know this."
- Sound like a smart friend telling you something wild they just learned — not a textbook, not a documentary voiceover, not an essay.

BANNED PHRASES — NEVER USE ANY OF THESE:
- "In this video" / "In today's video"
- "Today we're going to" / "We're going to explore"
- "Let's explore" / "Let's dive into" / "Let's take a look"
- "It's worth noting" / "It is important to note"
- "Throughout history" / "Historians believe" / "Scholars have long"
- "In conclusion" / "To summarize" / "As we've seen"
- "Numerous individuals" → say "a lot of people"
- "During that period" → say "back then"
- "Determined" / "ascertained" → say "figured out"
- "Constructed" → say "built"
- "Demonstrated" → say "showed"
- "Utilized" → say "used"
- "In order to" → say "to"

RETENTION RULES (apply throughout):
- Hook must be a shocking statement or sharp question in the very first sentence — zero setup before it.
- Pattern interrupt every 90-120 seconds: shift angle, ask a sharp question, reveal a surprise.
- Curiosity gap: start explaining something, pause with "...", then reveal after a B-roll beat.
- Every section transition must tease what's next — never end a section flat.

VISUAL ALIGNMENT — CRITICAL:
Every paragraph of narration must have a [B-ROLL: ...] marker BEFORE it describing exactly what footage should be on screen while that narration plays. The B-roll description must match what is being said — if you're talking about ancient stone tools, the B-roll should be stone tools or hands carving stone. If you're describing a river valley, show a river valley. The viewer should always be SEEING what you're SAYING.

Write the B-roll description as a specific, searchable footage query (e.g., "aerial drone shot over ancient ruins at sunset", "close-up of carved stone hieroglyphs", "wide shot of desert landscape with pyramids in background").

FORMAT (use exactly these labels):
TITLE: [YouTube title with number or power word, 60 chars max]
DESCRIPTION: [150-word SEO description with keywords]
TAGS: [15 comma-separated tags]

SCRIPT:
[HOOK - 0:00]
[B-ROLL: specific footage description matching the opening visual]
[hook narration]

[SECTION 1 - timestamp]
[B-ROLL: specific footage matching what is being described]
[narration paragraph — 3-5 sentences]
[B-ROLL: next specific footage as the topic shifts]
[narration paragraph — 3-5 sentences]

[continue — every paragraph gets its own B-ROLL marker above it...]

[CTA - timestamp]
[B-ROLL: wide cinematic shot or relevant ending visual]
[like, comment, subscribe — brief and natural, one or two sentences]

[OUTRO - timestamp]
[B-ROLL: final cinematic shot]
[closing — one punchy line that makes them think, not a summary]"""

        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        script_text = message.content[0].text

        # Run humanizer pass
        humanizer_prompt = f"""You are editing a YouTube narration script. Your job is to strip out every remaining trace of AI writing and make it sound like a real person talking — specifically, like a smart, enthusiastic friend who just learned something wild and wants to tell you about it.

GO THROUGH THE ENTIRE SCRIPT AND FIX EVERY INSTANCE OF:
- Sentences longer than 2 thoughts — split them up
- Any formal or academic phrasing — replace with casual speech
- Missing contractions — "do not" → "don't", "they are" → "they're", "it is" → "it's"
- Generic transitions like "Furthermore", "Additionally", "Moreover", "In addition" — cut or replace with "And", "But", "So", "Here's the thing"
- Any phrase that sounds like it was written to be read, not spoken — rewrite it as speech
- Spots where a "..." pause would help the information land — add them
- Any place that still sounds like a YouTube intro ("Today we're going to...", "In this video...", "Let's explore...") — cut it, start with the hook directly

BANNED WORDS AND PHRASES — replace every single one:
- "numerous" → "a lot of" / "tons of"
- "individuals" → "people"
- "constructed" → "built"
- "demonstrated" → "showed"
- "utilized" → "used"
- "determined" / "ascertained" → "figured out"
- "during that period" → "back then"
- "it is worth noting" → cut it or say "here's the thing"
- "in order to" → "to"
- "the construction of" → "building"
- "throughout history" → cut it

KEEP INTACT — do not change:
- All [B-ROLL: ...] markers
- All section headers and timestamps
- All TITLE, DESCRIPTION, TAGS sections

Only rewrite the spoken narration. Return the complete script with all formatting preserved.

Script to humanize:
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
