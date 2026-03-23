# Contributing to STUDIO — AI YouTube Automation

Thank you for your interest in contributing to STUDIO! This guide covers everything you need to get set up, the code style we follow, and how to submit changes.

---

## Table of Contents

1. [Fork and Clone](#fork-and-clone)
2. [Dev Environment Setup](#dev-environment-setup)
3. [Code Style Guidelines](#code-style-guidelines)
4. [How to Add a New Niche](#how-to-add-a-new-niche)
5. [How to Submit a Pull Request](#how-to-submit-a-pull-request)
6. [How to Report Bugs](#how-to-report-bugs)

---

## Fork and Clone

1. Click **Fork** on the GitHub repo page to create your own copy.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/AiAutomationTool.git
   cd AiAutomationTool
   ```
3. Add the upstream remote so you can pull updates:
   ```bash
   git remote add upstream https://github.com/mayson208/AiAutomationTool.git
   ```
4. To keep your fork up to date:
   ```bash
   git fetch upstream
   git checkout master
   git merge upstream/master
   ```

---

## Dev Environment Setup

### Requirements

- Python 3.10 or higher
- FFmpeg installed and on your system PATH
- API keys for the services you intend to test (see `.env.example`)

### Steps

```bash
# 1. Create and activate a virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the environment template and fill in your keys
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux

# 4. Run the app
python app.py
# Open http://localhost:5000
```

### Running Without All API Keys

Most modules degrade gracefully when a key is missing — they return `{"success": False, "error": "...KEY not set"}`. You can develop and test individual modules with just the key(s) that module needs.

---

## Code Style Guidelines

We follow standard Python conventions with a few project-specific rules:

### General

- **Python 3.10+** — use modern syntax (`match/case`, `X | Y` union types, etc.)
- **Type hints** on all new function signatures
- **Google-style docstrings** on all public functions:
  ```python
  def my_function(topic: str, count: int = 5) -> dict:
      """Generate something useful.

      Args:
          topic: The subject to generate content for.
          count: How many items to generate.

      Returns:
          A dict with keys: success (bool), data (list), error (str).
      """
  ```
- **No hardcoded API keys** — always read from `config.py` which reads from `.env`
- **Use `config.py`** for all path and settings references — don't construct paths manually in other modules

### Naming

- Functions: `snake_case`
- Constants / module-level dicts: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`
- Private helpers: prefix with `_` (e.g., `_clean_script()`)

### Error Handling

All public functions that call external APIs must return a consistent dict:
```python
# On success:
{"success": True, "data": ..., "other_keys": ...}

# On failure:
{"success": False, "error": "human-readable error message"}
```

Never let an exception bubble up unhandled from a module function. Catch and wrap it.

### Imports

Order: stdlib → third-party → local (`config`, other project modules). Separate groups with a blank line.

### Formatting

We don't enforce a formatter, but keep lines under 100 characters and use 4-space indentation.

---

## How to Add a New Niche

Adding a niche means updating several files so it appears consistently across all modules. Here is the complete checklist:

### 1. `script_writer.py` — Add to `NICHES` dict

```python
"yourniche": {
    "label": "Your Niche Label",
    "tone": "describe the voice tone",
    "style": "describe the script style and structure",
    "hook_style": "what makes a great hook for this niche",
    "optimal_minutes": 10,        # typical video length
    "cpm": "$X-Y",                # estimated CPM range
},
```

### 2. `voiceover.py` — Add to `NICHE_VOICE_SETTINGS`

```python
"yourniche": {"stability": 0.60, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": True},
```

Adjust values based on the energy level of the niche:
- High energy (gaming, motivation): lower stability (~0.40), higher style (~0.55)
- Calm (meditation, finance): higher stability (~0.75–0.85), lower style (~0.05–0.20)

### 3. `thumbnail.py` — Add to `NICHE_THUMBNAIL_STYLES` and `NICHE_PROMPTS`

```python
# In NICHE_THUMBNAIL_STYLES:
"yourniche": "Visual description of the thumbnail aesthetic...",

# In NICHE_PROMPTS:
"yourniche": "A [adjective] YouTube thumbnail for a [niche] video titled: \"{title}\". {style} Make it feel [goal]. 16:9 ratio, no borders, no watermarks.",
```

### 4. `voice_manager.py` — Add to `NICHE_SAMPLES`, `NICHE_PRESETS`, `NICHE_VOICE_TRAITS`

```python
# NICHE_SAMPLES — a realistic sample sentence for voice preview
"yourniche": "A sample sentence that sounds natural for this niche.",

# NICHE_PRESETS — same values as voiceover.py settings
"yourniche": {"stability": 0.60, "similarity_boost": 0.75, "style": 0.35},

# NICHE_VOICE_TRAITS — words that describe the ideal voice for this niche
"yourniche": ["engaging", "clear", "energetic", "friendly"],
```

### 5. `seo.py` — Add to `NICHE_CPM_TABLE`

```python
"Your Niche Label": {"cpm": "$X-Y", "rpm": "$A-B", "competition": "Medium"},
```

### 6. `content_calendar.py` — Add to `NICHE_POSTING_FREQ`

```python
"yourniche": 4,  # recommended posts per week
```

### 7. All HTML Templates — Add to every `<select>` niche dropdown

In each of these templates: `index.html`, `script.html`, `voiceover.html`, `thumbnail.html`, `seo.html`, `calendar.html`, `compliance.html`, `footage.html`

```html
<option value="yourniche">Your Niche Label</option>
```

### 8. Research Notes

Before adding a niche, document your research:
- Typical CPM and RPM ranges
- Audience demographics
- Optimal video length
- Top content formats
- Thumbnail formula (colors, face/no face, text style)
- Voice style (energy, pace, tone)
- Any platform policy considerations (e.g., Made for Kids label risk)

---

## How to Submit a Pull Request

1. **Create a branch** from `master` with a descriptive name:
   ```bash
   git checkout master
   git pull origin master
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** — keep commits focused. One logical change per commit.

3. **Commit with a clear message**:
   ```bash
   git commit -m "feature: add [niche] niche across all modules

   Brief description of what changed and why.

   Co-Authored-By: Your Name <your@email.com>"
   ```

4. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** on GitHub:
   - Target branch: `master`
   - Title: concise description (under 70 characters)
   - Body: what changed, why, and how to test it

6. **Respond to review feedback** — we aim to review PRs within a few days.

---

## How to Report Bugs

Open a GitHub Issue with the following information:

**Title**: Short description of the bug (e.g., "Thumbnail generation fails for horror niche")

**Body**:
```
## What happened
Describe what you expected vs. what actually happened.

## Steps to reproduce
1. Go to...
2. Click...
3. See error...

## Error output
Paste the full error message or traceback here.

## Environment
- OS: Windows 11 / macOS / Linux
- Python version: 3.x.x
- Which API keys are set (don't paste actual keys)

## Additional context
Any other relevant information.
```

---

## Questions?

Open a GitHub Discussion or file an Issue with the `question` label.
