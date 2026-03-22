"""script_writer.py — Generate YouTube scripts using Claude API."""
import anthropic
import config

def generate_script(topic: str, duration_minutes: int = 8) -> dict:
    """Generate a full YouTube script for the given topic."""
    if not config.ANTHROPIC_API_KEY:
        return {"success": False, "error": "ANTHROPIC_API_KEY not set"}
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        prompt = f"""Write a complete YouTube video script for the topic: "{topic}"

The video should be approximately {duration_minutes} minutes long.

Format the script as follows:
- TITLE: An engaging YouTube title (include numbers or power words)
- DESCRIPTION: A 150-word YouTube description with relevant keywords
- TAGS: 10-15 relevant YouTube tags separated by commas
- HOOK (0:00-0:30): Attention-grabbing opening that hooks viewers immediately
- INTRO (0:30-1:00): Brief intro of what the video covers
- MAIN CONTENT: Numbered sections with timestamps, dialogue, and b-roll suggestions
- CALL TO ACTION: Like, comment, subscribe prompt
- OUTRO: Closing remarks

Write naturally as if spoken aloud. Include [B-ROLL: description] markers for footage suggestions."""

        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        script_text = message.content[0].text
        # Parse sections
        lines = script_text.split('\n')
        title = next((l.replace('TITLE:', '').strip() for l in lines if l.startswith('TITLE:')), topic)
        description = ""
        tags = ""
        for i, line in enumerate(lines):
            if line.startswith('DESCRIPTION:'):
                desc_lines = []
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].startswith(('TAGS:', 'HOOK:', 'INTRO:')):
                        break
                    desc_lines.append(lines[j])
                description = ' '.join(desc_lines).strip()
            if line.startswith('TAGS:'):
                tags = line.replace('TAGS:', '').strip()
        return {
            "success": True,
            "topic": topic,
            "title": title,
            "description": description,
            "tags": tags,
            "script": script_text,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
