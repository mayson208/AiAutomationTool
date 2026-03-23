# Changelog

All notable changes to STUDIO are documented here.

## [Unreleased]
- Roblox niche support (research complete)
- Multi-channel YouTube support (planned)

## [1.3.0] — Voice Library
- Full ElevenLabs voice library sync and browser
- Voice cards with gender, accent, age, use-case tags
- In-browser waveform preview with niche-matched sample text
- Favorites system with persistent storage
- Per-voice settings (stability/similarity/style) per niche
- Voice cloning workflow with consent gate
- Usage tracking per voice
- Global voice indicator bar on every page
- Active voice persisted to .env automatically

## [1.2.0] — Content Tools
- SEO & Metadata module: 5 scored title options, full description, 20+ tags
- Content Calendar: 30-day AI schedule with evergreen/trending/seasonal mix
- Topic Bank: generate 25-100 video title ideas per niche
- Compliance checker: 0-100 risk score, demonetization keyword detection
- AI disclosure text generator for YouTube descriptions
- Music license source checker

## [1.1.0] — Niche Optimization & Real-Time Progress
- Real-time pipeline progress via Server-Sent Events (SSE)
- API key status dashboard on Settings page
- 11 niches with per-niche CPM rates, voice settings, thumbnail prompts, script styles
- Hook Generator: 3 hook options per topic (Shock, Question, Story formulas)
- Humanizer pass on all scripts via second Claude API call
- DALL-E 3 thumbnail A/B testing (1-3 variations)
- Parallel processing: thumbnail + footage run simultaneously during voiceover
- 3-step retry logic with exponential backoff on all API calls
- Quality tiers: Fast / Balanced / Premium
- Script, audio, thumbnail, video outputs organized into subdirectories
- run.bat launcher for Windows

## [1.0.0] — Initial Release
- One-Click Pipeline: end-to-end video production from topic to YouTube
- Script Writer with Claude AI (claude-sonnet-4-6)
- Voiceover generation with ElevenLabs (eleven_multilingual_v2)
- Thumbnail generation with DALL-E 3
- Stock footage search and download via Pexels API
- Video assembly with MoviePy + FFmpeg
- YouTube upload via Data API v3
- Analytics dashboard with channel stats
- Video history browser
- Settings page with API key management (saved to .env)
- Dark YouTube-style UI (red/black theme)
