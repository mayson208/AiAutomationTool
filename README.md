<div align="center">

# 🎬 STUDIO
### AI-Powered YouTube Automation Dashboard

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Claude](https://img.shields.io/badge/Claude-Sonnet_4.6-CC785C?style=for-the-badge)](https://anthropic.com)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-TTS-FF6B35?style=for-the-badge)](https://elevenlabs.io)
[![DALL·E](https://img.shields.io/badge/DALL·E_3-Thumbnails-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**Enter a topic → Get a finished YouTube video. Fully automated.**

[Features](#-features) · [Quick Start](#-quick-start) · [Niches](#-niche-support--cpm-rates) · [API Keys](#-api-keys) · [Architecture](#-architecture)

</div>

---

## ✨ What STUDIO Does

STUDIO is a one-click YouTube production pipeline. You type a topic — STUDIO writes the script, records the voiceover, generates thumbnails, sources stock footage, assembles the video, and uploads it to YouTube. Every step is niche-optimized using research-backed settings for 11 content categories.

```
Topic Input  →  Script (Claude AI)  →  Voiceover (ElevenLabs)
     →  Thumbnail (DALL-E 3)  →  Footage (Pexels)  →  Video (MoviePy)  →  YouTube ✓
```

---

## 🚀 Features

### ⚡ One-Click Pipeline
- Full end-to-end automation in a single click
- **Real-time SSE progress** — watch each step complete live in the browser
- **Parallel processing** — thumbnail generation and footage search run simultaneously
- **3-step retry logic** with exponential backoff on every API call
- **3 Quality Tiers** — Fast · Balanced · Premium

### 📝 Script Writer
| Feature | Detail |
|---------|--------|
| Hook Generator | 3 hooks per topic — Shock, Question, and Story formulas |
| Niche Optimization | 11 niches with tailored tone, pacing, and retention triggers |
| Humanizer Pass | Second Claude pass removes AI patterns for natural dialogue |
| Auto-Save | Scripts saved as JSON to `outputs/scripts/` |
| CPM Preview | Shows expected CPM range for the selected niche |

### 🎙️ Voice Library
- **Full ElevenLabs library sync** — browse every voice you have access to
- **Voice cards** with gender, accent, age, use-case tags
- **In-browser preview** — waveform animation with niche-matched sample text
- **Favorites** — star voices for quick access
- **Per-voice settings** — custom stability/similarity/style per niche
- **Voice cloning** — upload audio samples, consent-gated clone workflow
- **Usage tracking** — see which voices you use most
- **Global voice bar** — active voice shown on every page

### 🖼️ Thumbnail Generator
- DALL-E 3 with **niche-specific visual style prompts**
- **A/B test** up to 3 variations per video
- CTR scoring with improvement tips
- Saved to `outputs/thumbnails/`

### 📊 SEO & Metadata
- **5 title options** — each scored and ranked by SEO strength
- **Full 300-word description** with hashtags and timestamps
- **20-25 tags** including long-tail phrases
- Click-to-copy on every field
- Full niche CPM/RPM reference table

### 📅 Content Calendar
- **30-day AI content schedule** with evergreen/trending/seasonal mix
- **Topic bank** — generate 25-100 ready-to-use video titles
- Niche-optimized posting frequencies built in

### ✅ Compliance & Safety
- **Policy checker** — risk score 0-100 with specific issue flagging
- Demonetization keyword detection
- Standard **AI disclosure text** for YouTube descriptions
- Music license source checker
- Content guideline reference card

### 📈 Analytics Dashboard
- Live channel stats (subscribers, views, watch time)
- Recent video performance table
- CPM reference by niche

---

## ⚡ Quick Start

### 1. Clone & install

```bash
git clone https://github.com/mayson208/AiAutomationTool.git
cd AiAutomationTool
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 2. Add API keys

```bash
copy .env.example .env
```

Open `.env` and fill in:

```env
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=your-key
ELEVENLABS_VOICE_ID=your-voice-id
OPENAI_API_KEY=sk-...
PEXELS_API_KEY=your-key
FLASK_SECRET_KEY=any-random-string
```

> You can also set keys from the **Settings** page inside the app — no file editing needed.

### 3. Run

```bash
python app.py
# or double-click run.bat on Windows
```

Open **http://localhost:5000** in your browser.

### 4. Select a voice

Go to **Voice Library → Sync** to load your ElevenLabs voices, preview them, and set one as active. All voiceover generation will use the active voice automatically.

---

## 🎯 Niche Support & CPM Rates

| Niche | CPM Range | Optimal Length | Posts/Week | Voice Style |
|-------|-----------|:--------------:|:----------:|-------------|
| 💰 Finance & Investing | **$15–50** | 10–20 min | 2–3× | Authoritative & measured |
| 🧠 Science & Space | $6–12 | 8–15 min | 2–3× | Informative & wonder-inducing |
| 💪 Self Improvement | $5–10 | 8–15 min | 3–4× | Warm & encouraging |
| 📜 History | $5–10 | 10–25 min | 2–3× | Documentary storytelling |
| 🔥 Motivational | $5–10 | 3–8 min | Daily | Energetic & passionate |
| 💡 Facts / Did You Know | $4–10 | 5–15 min | 3–5× | Engaging & curious |
| 🔍 True Crime | $4–9 | 15–30 min | 2–3× | Serious & dramatic |
| 📰 News Summary | $4–8 | 5–10 min | Daily | Professional & clear |
| 🏆 Top 10 Lists | $4–8 | 8–15 min | 3–5× | Entertaining & confident |
| 👻 Horror & Scary | $3–7 | 10–20 min | 1–2× | Tense & atmospheric |
| 🧘 Meditation & Sleep | $3–6 | 20–60 min | 2–3× | Calm & soothing |

---

## 🔑 API Keys

| Key | Where to Get It | Cost |
|-----|----------------|------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) | Pay-per-use |
| `ELEVENLABS_API_KEY` | [elevenlabs.io](https://elevenlabs.io/) → Profile → API Keys | Free tier available |
| `ELEVENLABS_VOICE_ID` | ElevenLabs → Voice Library → click voice → copy ID | — |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | Pay-per-use |
| `PEXELS_API_KEY` | [pexels.com/api](https://www.pexels.com/api/) | **Free** |
| `YOUTUBE_CLIENT_ID/SECRET` | Google Cloud Console → YouTube Data API v3 | **Free** |

> **Minimum to get started:** `ANTHROPIC_API_KEY` + `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` + `OPENAI_API_KEY` + `PEXELS_API_KEY`
>
> YouTube upload keys are optional — skip them to use everything else.

---

## 🏗️ Architecture

```
AiAutomationTool/
├── app.py                    # Flask routes (all endpoints)
├── config.py                 # API keys, paths, constants
│
├── pipeline.py               # ⚡ Orchestrator — parallel + retry
├── script_writer.py          # 📝 Claude AI script + hook generator
├── voiceover.py              # 🎙️ ElevenLabs TTS (niche-optimized)
├── voice_manager.py          # 🎛️ Voice library, favorites, cloning
├── thumbnail.py              # 🖼️ DALL-E 3 thumbnails (A/B variations)
├── footage.py                # 🎬 Pexels stock footage
├── video_assembler.py        # ✂️ MoviePy final assembly
├── youtube_uploader.py       # 📤 YouTube Data API v3
├── analytics.py              # 📊 Channel stats
├── seo.py                    # 🔍 SEO titles, descriptions, tags
├── content_calendar.py       # 📅 30-day content planner
├── compliance.py             # ✅ Policy checker + AI disclosure
│
├── templates/                # Jinja2 HTML pages (11 pages)
├── static/css/style.css      # Dark YouTube-style theme
├── static/js/main.js         # SSE progress + voice bar JS
│
├── outputs/                  # Generated files (gitignored)
│   ├── audio/                # MP3 voiceovers
│   ├── thumbnails/           # PNG thumbnails
│   ├── videos/               # MP4 assembled videos
│   ├── scripts/              # JSON script files
│   └── previews/             # Voice preview cache
└── data/                     # App data (voices.json gitignored)
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Flask 3.x |
| AI Script Generation | Anthropic Claude (claude-sonnet-4-6) |
| AI Thumbnail | OpenAI DALL-E 3 |
| Text-to-Speech | ElevenLabs (eleven_multilingual_v2) |
| Stock Footage | Pexels API |
| Video Assembly | MoviePy + FFmpeg |
| YouTube | Google YouTube Data API v3 |
| Progress Streaming | Server-Sent Events (SSE) |
| Styling | Custom dark CSS — YouTube red/black theme |

---

## 📋 Requirements

- Python 3.10+
- FFmpeg (for video assembly) — `winget install ffmpeg` on Windows
- ElevenLabs Starter plan or above for voice cloning
- ~$0.50–2.00 per video in API costs (script + thumbnail + voiceover)

---

## 🛡️ Security Notes

- API keys live in `.env` — never committed to git
- `data/voices.json` is gitignored (contains your voice preferences)
- `token.pickle` and `client_secrets.json` are gitignored
- Voice cloning requires explicit consent confirmation in the UI

---

## 📄 License

MIT — use freely for personal and commercial projects.

---

<div align="center">

Built with ❤️ using Claude AI · ElevenLabs · DALL-E 3 · Pexels

</div>
