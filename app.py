"""app.py — STUDIO Flask application entry point."""
import os
import json
import uuid
import queue
import threading
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_from_directory, jsonify, session, Response, stream_with_context
)
from dotenv import load_dotenv, set_key

load_dotenv()
import config

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

# Ensure outputs dir exists
config.OUTPUTS_DIR.mkdir(exist_ok=True)

# ── Job store for SSE progress ─────────────────────────────────────────────────
_jobs: dict = {}  # job_id -> {"queue": Queue, "result": dict|None, "done": bool}
_jobs_lock = threading.Lock()


def _get_job(job_id):
    with _jobs_lock:
        return _jobs.get(job_id)


def _create_job(job_id):
    with _jobs_lock:
        _jobs[job_id] = {"queue": queue.Queue(), "result": None, "done": False}
    return _jobs[job_id]


# ── Serve output files ────────────────────────────────────────────────────────
@app.route("/outputs/<path:filename>")
def serve_output(filename):
    # Try subdirectories first
    for subdir in ["audio", "scripts", "thumbnails", "videos"]:
        subpath = config.OUTPUTS_DIR / subdir / filename
        if subpath.exists():
            return send_from_directory(config.OUTPUTS_DIR / subdir, filename)
    return send_from_directory(config.OUTPUTS_DIR, filename)


# ── Index / Pipeline ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    missing = config.missing_keys()
    job_id = request.args.get("job")
    return render_template(
        "index.html",
        active="pipeline",
        result=session.pop("pipeline_result", None),
        missing=missing,
        job_id=job_id,
    )


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

    job_id = str(uuid.uuid4())
    job = _create_job(job_id)
    q = job["queue"]

    def run():
        def progress(step, total, msg):
            q.put({"step": step, "total": total, "msg": msg})

        result = pipe.run_pipeline(
            topic,
            duration_minutes=duration,
            upload=upload,
            privacy=privacy,
            progress_callback=progress,
        )
        with _jobs_lock:
            _jobs[job_id]["result"] = result
            _jobs[job_id]["done"] = True
        q.put(None)  # sentinel — signals completion

    threading.Thread(target=run, daemon=True).start()
    return redirect(url_for("index", job=job_id))


@app.route("/pipeline/progress/<job_id>")
def pipeline_progress(job_id):
    job = _get_job(job_id)

    def generate():
        if not job:
            yield 'data: {"error": "Job not found"}\n\n'
            return
        q = job["queue"]
        while True:
            try:
                item = q.get(timeout=60)
            except queue.Empty:
                yield 'data: {"ping": true}\n\n'
                continue
            if item is None:
                result = job.get("result", {})
                yield f"data: {json.dumps({'done': True, 'success': result.get('success', False), 'title': result.get('title', ''), 'error': result.get('error', '')})}\n\n"
                break
            yield f"data: {json.dumps(item)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Script Writer ─────────────────────────────────────────────────────────────
@app.route("/script")
def script_page():
    return render_template("script.html", active="script",
                           result=session.pop("script_result", None),
                           hooks=session.pop("hooks_result", None))


@app.route("/script/hooks", methods=["POST"])
def generate_hooks_route():
    import script_writer
    topic = request.form.get("topic", "").strip()
    niche = request.form.get("niche", "facts")
    duration = request.form.get("duration", "8")
    if not topic:
        flash("Enter a topic.", "error")
        return redirect(url_for("script_page"))
    result = script_writer.generate_hooks(topic, niche)
    if result["success"]:
        session["hooks_result"] = {
            "topic": topic,
            "niche": niche,
            "duration": duration,
            "options": result["hooks"],
        }
    else:
        flash(f"Error: {result['error']}", "error")
    return redirect(url_for("script_page"))


@app.route("/script/generate", methods=["POST"])
def generate_script():
    import script_writer
    topic = request.form.get("topic", "").strip()
    duration = int(request.form.get("duration", 8))
    niche = request.form.get("niche", "facts")
    selected_hook = request.form.get("selected_hook", "").strip() or None
    if not topic:
        flash("Enter a topic.", "error")
        return redirect(url_for("script_page"))
    result = script_writer.generate_script(topic, duration, niche, selected_hook)
    if result["success"]:
        session["script_result"] = result
        session["last_script"] = result["script"]
        session["last_niche"] = niche
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
    prefill_script = session.get("last_script", "")
    return render_template("voiceover.html", active="voiceover",
                           result=session.pop("voiceover_result", None),
                           prefill_script=prefill_script)


@app.route("/voiceover/generate", methods=["POST"])
def generate_voiceover():
    import voiceover as vo
    script_text = request.form.get("script", "").strip()
    niche = request.form.get("niche", "facts")
    if not script_text:
        flash("Paste a script to generate voiceover.", "error")
        return redirect(url_for("voiceover_page"))
    result = vo.generate_voiceover(script_text, niche=niche)
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
    niche = request.form.get("niche", "facts")
    variations = int(request.form.get("variations", 1))
    if not topic:
        flash("Enter a topic.", "error")
        return redirect(url_for("thumbnail_page"))
    result = thumb.generate_thumbnail(topic, title=title, niche=niche, variations=variations)
    if result["success"]:
        session["thumbnail_result"] = result
        flash(f"Generated {result['variation_count']} thumbnail(s)!", "success")
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


# ── Content Calendar ──────────────────────────────────────────────────────────
@app.route("/calendar")
def calendar_page():
    return render_template("calendar.html", active="calendar",
                           calendar=session.pop("calendar_result", None),
                           topic_bank=session.pop("topic_bank_result", None))

@app.route("/calendar/generate", methods=["POST"])
def generate_calendar():
    import content_calendar as cal
    niche = request.form.get("niche", "facts")
    posting_freq = int(request.form.get("posting_freq", 3))
    result = cal.generate_calendar(niche, posting_freq)
    if result["success"]:
        session["calendar_result"] = result
        flash(f"Generated {result['total_videos']}-video calendar!", "success")
    else:
        flash(f"Error: {result['error']}", "error")
    return redirect(url_for("calendar_page"))

@app.route("/calendar/topics", methods=["POST"])
def generate_topics():
    import content_calendar as cal
    niche = request.form.get("niche", "facts")
    count = int(request.form.get("count", 50))
    result = cal.generate_topic_bank(niche, count)
    if result["success"]:
        session["topic_bank_result"] = result
        flash(f"Generated {result['count']} topic ideas!", "success")
    else:
        flash(f"Error: {result['error']}", "error")
    return redirect(url_for("calendar_page"))


# ── SEO ──────────────────────────────────────────────────────────────────────
@app.route("/seo")
def seo_page():
    import seo
    return render_template("seo.html", active="seo",
                           result=session.pop("seo_result", None),
                           cpm_table=seo.get_cpm_table())

@app.route("/seo/generate", methods=["POST"])
def generate_seo():
    import seo
    topic = request.form.get("topic", "").strip()
    title = request.form.get("title", "").strip()
    niche = request.form.get("niche", "facts")
    if not topic:
        flash("Enter a topic.", "error")
        return redirect(url_for("seo_page"))
    script_text = session.get("last_script", "")
    result = seo.generate_seo_package(topic, title or topic, niche, script_text)
    if result["success"]:
        session["seo_result"] = result
    else:
        flash(f"Error: {result['error']}", "error")
    return redirect(url_for("seo_page"))


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
        "ANTHROPIC_API_KEY":   config.ANTHROPIC_API_KEY,
        "ELEVENLABS_API_KEY":  config.ELEVENLABS_API_KEY,
        "ELEVENLABS_VOICE_ID": config.ELEVENLABS_VOICE_ID,
        "OPENAI_API_KEY":      config.OPENAI_API_KEY,
        "PEXELS_API_KEY":      config.PEXELS_API_KEY,
        "YOUTUBE_CLIENT_ID":   config.YOUTUBE_CLIENT_ID,
        "YOUTUBE_CLIENT_SECRET": config.YOUTUBE_CLIENT_SECRET,
    }
    return render_template("settings.html", active="settings", current=current)


@app.route("/settings/save", methods=["POST"])
def save_settings():
    env_path = config.BASE_DIR / ".env"
    keys = [
        "ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID",
        "OPENAI_API_KEY", "PEXELS_API_KEY", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET",
    ]
    for key in keys:
        val = request.form.get(key, "").strip()
        if val:
            set_key(str(env_path), key, val)
    load_dotenv(override=True)
    flash("Settings saved. Restart the app for changes to take effect.", "success")
    return redirect(url_for("settings_page"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
