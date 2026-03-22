"""app.py — STUDIO Flask application entry point."""
import os
import json
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_from_directory, jsonify, session
)
from dotenv import load_dotenv, set_key

load_dotenv()
import config

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

# Ensure outputs dir exists
config.OUTPUTS_DIR.mkdir(exist_ok=True)

# ── Serve output files ────────────────────────────────────────────────────────
@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(config.OUTPUTS_DIR, filename)

# ── Index / Pipeline ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", active="pipeline", result=session.pop("pipeline_result", None))

@app.route("/pipeline/run", methods=["POST"])
def run_pipeline():
    import pipeline as pipe
    topic = request.form.get("topic", "").strip()
    duration = int(request.form.get("duration", 8))
    upload = bool(request.form.get("upload"))
    privacy = request.form.get("privacy", "private")

    if not topic:
        flash("Please enter a video topic.", "error")
        return redirect(url_for("index"))

    missing = config.missing_keys()
    if missing:
        flash(f"Missing API keys: {', '.join(missing)}. Go to Settings.", "error")
        return redirect(url_for("index"))

    result = pipe.run_pipeline(topic, duration_minutes=duration, upload=upload, privacy=privacy)
    session["pipeline_result"] = result
    if result.get("success"):
        flash(f"Pipeline complete! Video ready: {result.get('title', topic)}", "success")
    else:
        flash(f"Pipeline error: {result.get('error', 'Unknown error')}", "error")
    return redirect(url_for("index"))

# ── Script Writer ─────────────────────────────────────────────────────────────
@app.route("/script")
def script_page():
    return render_template("script.html", active="script", result=session.pop("script_result", None))

@app.route("/script/generate", methods=["POST"])
def generate_script():
    import script_writer
    topic = request.form.get("topic", "").strip()
    duration = int(request.form.get("duration", 8))
    if not topic:
        flash("Enter a topic.", "error")
        return redirect(url_for("script_page"))
    result = script_writer.generate_script(topic, duration)
    if result["success"]:
        session["script_result"] = result
        session["last_script"] = result["script"]
    else:
        flash(f"Error: {result['error']}", "error")
    return redirect(url_for("script_page"))

@app.route("/script/download")
def download_script():
    from flask import Response
    script = session.get("last_script", "No script generated yet.")
    return Response(script, mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=script.txt"})

# ── Voiceover ─────────────────────────────────────────────────────────────────
@app.route("/voiceover")
def voiceover_page():
    return render_template("voiceover.html", active="voiceover", result=session.pop("voiceover_result", None))

@app.route("/voiceover/generate", methods=["POST"])
def generate_voiceover():
    import voiceover as vo
    script_text = request.form.get("script", "").strip()
    if not script_text:
        flash("Paste a script to generate voiceover.", "error")
        return redirect(url_for("voiceover_page"))
    result = vo.generate_voiceover(script_text)
    if result["success"]:
        session["voiceover_result"] = result
        flash("Voiceover generated!", "success")
    else:
        flash(f"Error: {result['error']}", "error")
    return redirect(url_for("voiceover_page"))

# ── Thumbnail ─────────────────────────────────────────────────────────────────
@app.route("/thumbnail")
def thumbnail_page():
    return render_template("thumbnail.html", active="thumbnail", result=session.pop("thumbnail_result", None))

@app.route("/thumbnail/generate", methods=["POST"])
def generate_thumbnail():
    import thumbnail as thumb
    topic = request.form.get("topic", "").strip()
    title = request.form.get("title", "").strip() or None
    if not topic:
        flash("Enter a topic.", "error")
        return redirect(url_for("thumbnail_page"))
    result = thumb.generate_thumbnail(topic, title=title)
    if result["success"]:
        session["thumbnail_result"] = result
        flash("Thumbnail generated!", "success")
    else:
        flash(f"Error: {result['error']}", "error")
    return redirect(url_for("thumbnail_page"))

# ── Stock Footage ─────────────────────────────────────────────────────────────
@app.route("/footage")
def footage_page():
    return render_template("footage.html", active="footage",
                           videos=session.pop("footage_results", None))

@app.route("/footage/search", methods=["POST"])
def search_footage():
    import footage as ft
    query = request.form.get("query", "").strip()
    if not query:
        flash("Enter a search query.", "error")
        return redirect(url_for("footage_page"))
    result = ft.search_footage(query)
    if result["success"]:
        session["footage_results"] = result["videos"]
        flash(f"Found {result['total']} results.", "info")
    else:
        flash(f"Error: {result['error']}", "error")
    return redirect(url_for("footage_page"))

@app.route("/footage/download")
def download_footage():
    import footage as ft
    url = request.args.get("url")
    if not url:
        flash("No URL provided.", "error")
        return redirect(url_for("footage_page"))
    result = ft.download_clip(url)
    if result["success"]:
        flash(f"Clip downloaded: {result['filename']}", "success")
    else:
        flash(f"Error: {result['error']}", "error")
    return redirect(url_for("footage_page"))

# ── Analytics ─────────────────────────────────────────────────────────────────
@app.route("/analytics")
def analytics_page():
    import analytics
    stats = analytics.get_channel_stats()
    videos = analytics.get_recent_videos() if stats.get("success") else None
    return render_template("analytics.html", active="analytics", stats=stats, videos=videos)

# ── History ───────────────────────────────────────────────────────────────────
@app.route("/history")
def history_page():
    import pipeline as pipe
    history = pipe._load_history()
    return render_template("history.html", active="history", history=history)

# ── Settings ──────────────────────────────────────────────────────────────────
@app.route("/settings")
def settings_page():
    current = {
        "ANTHROPIC_API_KEY": config.ANTHROPIC_API_KEY,
        "ELEVENLABS_API_KEY": config.ELEVENLABS_API_KEY,
        "ELEVENLABS_VOICE_ID": config.ELEVENLABS_VOICE_ID,
        "OPENAI_API_KEY": config.OPENAI_API_KEY,
        "PEXELS_API_KEY": config.PEXELS_API_KEY,
        "YOUTUBE_CLIENT_ID": config.YOUTUBE_CLIENT_ID,
        "YOUTUBE_CLIENT_SECRET": config.YOUTUBE_CLIENT_SECRET,
    }
    return render_template("settings.html", active="settings", current=current)

@app.route("/settings/save", methods=["POST"])
def save_settings():
    env_path = config.BASE_DIR / ".env"
    keys = ["ANTHROPIC_API_KEY","ELEVENLABS_API_KEY","ELEVENLABS_VOICE_ID",
            "OPENAI_API_KEY","PEXELS_API_KEY","YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET"]
    for key in keys:
        val = request.form.get(key, "").strip()
        if val:
            set_key(str(env_path), key, val)
    load_dotenv(override=True)
    flash("Settings saved. Restart the app for changes to take effect.", "success")
    return redirect(url_for("settings_page"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
