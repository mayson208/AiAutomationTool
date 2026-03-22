# STUDIO — AI YouTube Automation Dashboard

STUDIO is a one-click YouTube video production dashboard built with Python Flask. Enter a topic, choose your niche, click Generate — and STUDIO automatically writes a niche-optimized script, produces a voiceover with matching voice settings, generates multiple thumbnail variations, downloads stock footage, assembles the final video, and optionally uploads it to YouTube.

---

## Features

### Core Pipeline
- **One-Click Pipeline** — Full end-to-end video production with niche + quality tier selection
- **Parallel Processing** — Thumbnail generation and footage search run simultaneously during voiceover production
- **Retry Logic** — Each pipeline step retries up to 3 times with exponential backoff
- **Quality Tiers** — Fast (speed priority), Balanced (default), Premium (max quality)

### Script Writer
- **Niche Optimization** — 11 niches with tailored tone, style, and pacing guidelines
- **Hook Generator** — Generates 3 hook options (Shock, Question, Story formulas) to choose from
- **Humanizer Pass** — Second Claude pass removes AI writing patterns for more natural dialogue
- **Retention Triggers** — Pattern interrupts, open loops, and curiosity gaps built into every script
- **Auto-Save** — Scripts saved as JSON to `outputs/scripts/` organized by niche and date
- **CPM Display** — Shows niche CPM range on every generated script

### Voiceover Generator
- **Niche Voice Settings** — 11 presets with research-backed stability/similarity/style values
- **Model Upgrade** — Uses `eleven_multilingual_v2` (higher quality than v1)
- **Settings Preview** — Live preview of voice settings when selecting niche
- **Script Prefill** — Auto-fills from last generated script

### Thumbnail Generator
- **Niche Visual Styles** — DALL-E 3 prompts tailored to each niche's aesthetic
- **A/B Testing** — Generate 1-3 variations in one click for split testing
- **Organized Storage** — Thumbnails saved to `outputs/thumbnails/`

### SEO & Metadata (NEW)
- **5 Title Options** — Each scored and ranked by SEO strength
- **Full Description** — 250-350 word SEO-optimized description with hashtags
- **Tag Generator** — 20-25 tags including long-tail phrases
- **Click-to-Copy** — All titles, descriptions, and tags copyable with one click
- **CPM Reference Table** — Full niche CPM/RPM/competition table

### Content Calendar (NEW)
- **30-Day Calendar** — AI-generated posting schedule with topic ideas per niche
- **Content Types** — Mix of evergreen (70%), trending (30%), and seasonal content
- **Topic Bank** — Generate 25-100 ready-to-use video titles per niche
- **Niche Frequencies** — Pre-set optimal posting frequencies by niche

### Compliance & Safety (NEW)
- **Policy Checker** — Flags demonetization keywords, copyright triggers, and low-value signals
- **Risk Scoring** — 0-100 risk score with color-coded severity
- **AI Disclosure** — Standard YouTube AI disclosure text ready to copy
- **Music License Checker** — Verify if a music source is safe for monetized content
- **Content Guidelines** — Visual reference for always-safe, review-needed, and avoid content

### Other Tools
- **Stock Footage** — Search and download royalty-free clips from Pexels
- **Video Assembler** — MoviePy stitches footage and voiceover into a finished MP4
- **YouTube Uploader** — Uploads directly to your channel via YouTube Data API v3
- **Analytics Dashboard** — View subscriber count, total views, recent video stats, and CPM reference table
- **History** — Browse all previously generated videos
- **Settings** — Manage all API keys from the UI (saved to .env)

---

## Niche Support

| Niche | CPM Range | Optimal Length | Posts/Week |
|-------|-----------|----------------|------------|
| Finance & Investing | $15-50 | 10-20 min | 2-3x |
| Tech & Business | $12-25 | 10-15 min | 2-3x |
| Science & Space | $6-12 | 8-15 min | 2-3x |
| Self Improvement | $5-10 | 8-15 min | 3-4x |
| History | $5-10 | 10-25 min | 2-3x |
| Motivational & Quotes | $5-10 | 3-8 min | Daily |
| Facts / Did You Know | $4-10 | 5-15 min | 3-5x |
| True Crime | $4-9 | 15-30 min | 2-3x |
| News Summary | $4-8 | 5-10 min | Daily |
| Top 10 Lists | $4-8 | 8-15 min | 3-5x |
| Horror & Scary Stories | $3-7 | 10-20 min | 1-2x |
| Meditation & Sleep | $3-6 | 20-60 min | 2-3x |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Flask 3.x |
| AI Script | Anthropic Claude (claude-sonnet-4-6) |
| AI Image | OpenAI DALL-E 3 |
| Text-to-Speech | ElevenLabs (eleven_multilingual_v2) |
| Stock Footage | Pexels API |
| Video Editing | MoviePy |
| YouTube | Google YouTube Data API v3 |
| Styling | Custom dark CSS (YouTube red/white theme) |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/mayson208/AiAutomationTool.git
cd AiAutomationTool
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Copy the template and fill in your keys:

```bash
copy .env.example .env
```

Edit `.env` with your actual API keys:

```
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=your-key-here
ELEVENLABS_VOICE_ID=your-voice-id-here
OPENAI_API_KEY=sk-...
PEXELS_API_KEY=your-pexels-key
YOUTUBE_CLIENT_ID=your-google-client-id
YOUTUBE_CLIENT_SECRET=your-google-client-secret
FLASK_SECRET_KEY=your-random-secret-string
```

You can also set keys from the Settings page inside the app.

### 5. YouTube OAuth Setup (for upload and analytics)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the **YouTube Data API v3**
3. Create OAuth 2.0 credentials (Desktop application type)
4. Download `client_secrets.json` and place it in the project root
5. On first use, a browser window will open for authorization

### 6. Run the app

```bash
python app.py
```

Open your browser to: **http://localhost:5000**

---

## API Keys — Where to Get Them

| Key | Source |
|-----|--------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| `ELEVENLABS_API_KEY` | [elevenlabs.io](https://elevenlabs.io/) — Profile > API Keys |
| `ELEVENLABS_VOICE_ID` | ElevenLabs — Voice Library > click a voice > ID in URL |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| `PEXELS_API_KEY` | [pexels.com/api](https://www.pexels.com/api/) |
| `YOUTUBE_CLIENT_ID/SECRET` | [Google Cloud Console](https://console.cloud.google.com/) — APIs & Services > Credentials |

---

## Project Structure

```
AiAutomationTool/
├── app.py                    # Flask application and all routes
├── config.py                 # Centralised settings and API key loading
├── pipeline.py               # Full automation orchestrator (parallel, retry logic)
├── script_writer.py          # Claude AI script generation with niche optimization
├── voiceover.py              # ElevenLabs TTS with niche voice settings
├── thumbnail.py              # DALL-E 3 thumbnail generation with niche styles
├── footage.py                # Pexels stock footage search and download
├── video_assembler.py        # MoviePy video assembly
├── youtube_uploader.py       # YouTube Data API v3 uploader
├── analytics.py              # YouTube channel analytics
├── seo.py                    # SEO package generator (NEW)
├── content_calendar.py       # 30-day content calendar generator (NEW)
├── compliance.py             # Policy checker and AI disclosure manager (NEW)
├── requirements.txt          # Python dependencies
├── .env                      # API keys (gitignored)
├── .env.example              # Template for .env
├── templates/
│   ├── base.html             # Sidebar layout and navigation
│   ├── index.html            # One-click pipeline page
│   ├── script.html           # Script writer page (with hook generator)
│   ├── voiceover.html        # Voiceover generator page (niche settings)
│   ├── thumbnail.html        # Thumbnail generator page (variations)
│   ├── footage.html          # Stock footage search page
│   ├── seo.html              # SEO & metadata page (NEW)
│   ├── calendar.html         # Content calendar page (NEW)
│   ├── compliance.html       # Compliance & safety page (NEW)
│   ├── analytics.html        # Channel analytics + CPM table
│   ├── history.html          # Video history page
│   └── settings.html         # API key settings page
├── static/
│   ├── css/style.css         # Dark YouTube-style stylesheet
│   └── js/main.js            # Pipeline progress animation
├── outputs/                  # Generated files (gitignored)
│   ├── scripts/              # Saved script JSON files
│   ├── audio/                # Generated MP3 voiceovers
│   ├── thumbnails/           # Generated PNG thumbnails
│   └── videos/               # Assembled MP4 videos
└── data/                     # Content calendars and topic banks
```

---

## Quick Start Guide

### One-Click Pipeline

1. Go to the home page (One-Click Pipeline)
2. Enter a video topic
3. Select your **Niche** (optimizes script, voice, and thumbnail)
4. Choose **Quality Tier** — Balanced is recommended
5. Set duration and privacy
6. Optionally check "Auto-upload to YouTube"
7. Click **Generate Video** and watch real-time progress

### Script Writer (with Hook Generator)

1. Go to Script Writer
2. Enter topic and select niche
3. Click **Generate 3 Hook Options**
4. Pick the hook formula that fits best (Shock, Question, or Story)
5. Select duration and click **Generate Full Script**
6. Script is humanized automatically and saved to `outputs/scripts/`

### SEO Package

1. Go to SEO & Metadata
2. Enter topic and niche
3. Get 5 scored title options, full description, and 20+ tags
4. Click any title to copy instantly

### Content Calendar

1. Go to Content Calendar
2. Select niche and posting frequency
3. Generate a 30-day schedule with topic ideas
4. Or generate a topic bank of 25-100 video titles

### Compliance Check

1. Go to Compliance & Safety
2. Paste your script for policy review
3. Get risk score and specific issues to fix
4. Copy the AI disclosure for your description

---

## Important Notes

- The `outputs/` and `data/` directories are gitignored — all generated files stay local
- `token.pickle` and `client_secrets.json` are gitignored for security
- API keys in `.env` are never committed to git
- YouTube upload requires `client_secrets.json` from Google Cloud Console
- MoviePy requires FFmpeg — install it from [ffmpeg.org](https://ffmpeg.org/) and add to PATH

### Installing FFmpeg on Windows

```bash
winget install ffmpeg
```

Or download from [ffmpeg.org/download.html](https://ffmpeg.org/download.html) and add the `bin` folder to your system PATH.

---

## License

MIT License — use freely for personal and commercial projects.
