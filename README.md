# STUDIO — AI YouTube Automation Dashboard

STUDIO is a one-click YouTube video production dashboard built with Python Flask. Enter a topic, click Generate, and STUDIO automatically writes the script, produces a voiceover, generates a thumbnail, downloads stock footage, assembles the final video, and optionally uploads it to YouTube.

---

## Features

- **One-Click Pipeline** — Full end-to-end video production from a single topic input
- **Script Writer** — Claude AI generates structured YouTube scripts with titles, descriptions, tags, and timestamped sections
- **Voiceover Generator** — ElevenLabs converts scripts to natural-sounding MP3 audio
- **Thumbnail Generator** — DALL-E 3 creates eye-catching 16:9 YouTube thumbnails
- **Stock Footage** — Search and download royalty-free clips from Pexels
- **Video Assembler** — MoviePy stitches footage and voiceover into a finished MP4
- **YouTube Uploader** — Uploads directly to your channel via YouTube Data API v3
- **Analytics Dashboard** — View subscriber count, total views, and recent video stats
- **History** — Browse all previously generated videos
- **Settings** — Manage all API keys from the UI (saved to .env)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Flask 3.x |
| AI Script | Anthropic Claude (claude-sonnet-4-6) |
| AI Image | OpenAI DALL-E 3 |
| Text-to-Speech | ElevenLabs |
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
├── app.py                  # Flask application and all routes
├── config.py               # Centralised settings and API key loading
├── pipeline.py             # Full automation orchestrator
├── script_writer.py        # Claude AI script generation
├── voiceover.py            # ElevenLabs text-to-speech
├── thumbnail.py            # DALL-E 3 thumbnail generation
├── footage.py              # Pexels stock footage search and download
├── video_assembler.py      # MoviePy video assembly
├── youtube_uploader.py     # YouTube Data API v3 uploader
├── analytics.py            # YouTube channel analytics
├── requirements.txt        # Python dependencies
├── .env                    # API keys (gitignored)
├── .env.example            # Template for .env
├── templates/
│   ├── base.html           # Sidebar layout and navigation
│   ├── index.html          # One-click pipeline page
│   ├── script.html         # Script writer page
│   ├── voiceover.html      # Voiceover generator page
│   ├── thumbnail.html      # Thumbnail generator page
│   ├── footage.html        # Stock footage search page
│   ├── analytics.html      # Channel analytics page
│   ├── history.html        # Video history page
│   └── settings.html       # API key settings page
├── static/
│   ├── css/style.css       # Dark YouTube-style stylesheet
│   └── js/main.js          # Pipeline progress animation
└── outputs/                # Generated files (gitignored)
```

---

## Usage

### One-Click Pipeline

1. Go to the home page (One-Click Pipeline)
2. Enter a video topic
3. Choose duration and privacy setting
4. Optionally check "Auto-upload to YouTube"
5. Click **Generate Video**
6. Wait while the pipeline completes all 6 steps automatically

### Individual Tools

Each tool is also available independently:
- `/script` — Generate a script only
- `/voiceover` — Generate audio from any text
- `/thumbnail` — Generate a thumbnail for any topic
- `/footage` — Search and download Pexels clips
- `/analytics` — View channel stats
- `/history` — Review past generations

---

## Important Notes

- The `outputs/` directory is gitignored — all generated files stay local
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
