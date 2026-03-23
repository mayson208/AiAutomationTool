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

# Warn if using the default insecure secret key
if config.FLASK_SECRET_KEY == "dev-secret-key":
    import warnings
    warnings.warn(
        "FLASK_SECRET_KEY is set to the default value. Set a strong random key in .env before deploying.",
        stacklevel=2,
    )

# Ensure outputs dir exists
config.OUTPUTS_DIR.mkdir(exist_ok=True)


# ── Security headers ───────────────────────────────────────────────────────────
@app.after_request
def add_security_headers(response):
    """Add HTTP security headers to every response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ── Health check ───────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    """Return JSON status of all API keys — useful for debugging setup."""
    return jsonify({
        "status": "ok",
        "keys": {
            "ANTHROPIC_API_KEY":   bool(config.ANTHROPIC_API_KEY),
            "ELEVENLABS_API_KEY":  bool(config.ELEVENLABS_API_KEY),
            "ELEVENLABS_VOICE_ID": bool(config.ELEVENLABS_VOICE_ID),
            "OPENAI_API_KEY":      bool(config.OPENAI_API_KEY),
            "PEXELS_API_KEY":      bool(config.PEXELS_API_KEY),
            "YOUTUBE_CLIENT_ID":   bool(config.YOUTUBE_CLIENT_ID),
        },
        "missing": config.missing_keys(),
        "flask_secret_safe": config.FLASK_SECRET_KEY != "dev-secret-key",
    })

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

    niche = request.form.get("niche", "facts")
    quality_tier = request.form.get("quality_tier", "balanced")

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
            niche=niche,
            quality_tier=quality_tier,
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


# ── Compliance ────────────────────────────────────────────────────────────────
@app.route("/compliance")
def compliance_page():
    import compliance
    return render_template("compliance.html", active="compliance",
                           check_result=session.pop("compliance_result", None),
                           music_result=session.pop("music_result", None),
                           disclosure=compliance.get_ai_disclosure("description"),
                           prefill_script=session.get("last_script", ""))

@app.route("/compliance/check", methods=["POST"])
def check_compliance():
    import compliance
    script = request.form.get("script", "").strip()
    if not script:
        flash("Paste a script to check.", "error")
        return redirect(url_for("compliance_page"))
    result = compliance.check_script_policy(script)
    session["compliance_result"] = result
    return redirect(url_for("compliance_page"))

@app.route("/compliance/music", methods=["POST"])
def check_music():
    import compliance
    source = request.form.get("music_source", "").strip()
    if source:
        session["music_result"] = compliance.check_music_license(source)
    return redirect(url_for("compliance_page"))


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


@app.route("/calendar/export")
def export_calendar():
    """Export the last generated calendar as a CSV file."""
    import csv, io
    cal_data = session.get("calendar_result")
    if not cal_data or not cal_data.get("calendar"):
        flash("Generate a calendar first.", "error")
        return redirect(url_for("calendar_page"))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Day", "Topic", "Type", "Niche"])
    for entry in cal_data["calendar"]:
        writer.writerow([
            entry.get("date", ""), entry.get("day", ""),
            entry.get("topic", ""), entry.get("type", ""),
            cal_data.get("niche", ""),
        ])
    csv_content = output.getvalue()
    return Response(
        csv_content, mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=content-calendar.csv"},
    )


@app.route("/calendar/export-topics")
def export_topics():
    """Export the last generated topic bank as a plain text file."""
    bank = session.get("topic_bank_result")
    if not bank or not bank.get("topics"):
        flash("Generate a topic bank first.", "error")
        return redirect(url_for("calendar_page"))
    content = "\n".join(bank["topics"])
    return Response(
        content, mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=topic-bank.txt"},
    )


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


# ── Voice Library ─────────────────────────────────────────────────────────────
@app.route("/voices")
def voices_page():
    import voice_manager as vm
    voices = vm.get_voices()
    db = vm.get_db()
    return render_template("voices.html", active="voices",
                           voices=voices,
                           active_voice=vm.get_active_voice(),
                           favorites=vm.get_favorites(),
                           usage_stats=vm.get_usage_stats(),
                           last_synced=db.get("last_synced"))

@app.route("/voices/sync", methods=["POST"])
def sync_voices():
    import voice_manager as vm
    result = vm.fetch_voices_from_elevenlabs()
    if result["success"]:
        flash(f"Synced {result['count']} voices from ElevenLabs.", "success")
    else:
        flash(f"Sync failed: {result['error']}", "error")
    return redirect(url_for("voices_page"))

@app.route("/voices/set-active", methods=["POST"])
def set_active_voice():
    import voice_manager as vm
    voice_id = request.form.get("voice_id", "")
    voice_name = request.form.get("voice_name", "")
    if voice_id:
        vm.set_active_voice(voice_id, voice_name)
        # Update runtime config
        config.ELEVENLABS_VOICE_ID = voice_id
        flash(f"Active voice set to: {voice_name}", "success")
    return redirect(url_for("voices_page"))

@app.route("/voices/favorite", methods=["POST"])
def toggle_favorite():
    import voice_manager as vm
    data = request.get_json()
    voice_id = data.get("voice_id", "")
    is_fav = vm.toggle_favorite(voice_id)
    return jsonify({"is_favorite": is_fav})

@app.route("/voices/preview", methods=["POST"])
def preview_voice():
    import voice_manager as vm
    data = request.get_json()
    voice_id = data.get("voice_id", "")
    niche = data.get("niche", "general")
    custom_text = data.get("custom_text", None)
    result = vm.generate_preview(voice_id, niche, custom_text)
    return jsonify(result)

@app.route("/outputs/previews/<filename>")
def serve_preview(filename):
    previews_dir = config.OUTPUTS_DIR / "previews"
    return send_from_directory(previews_dir, filename)

@app.route("/voices/clone", methods=["POST"])
def clone_voice():
    import voice_manager as vm
    voice_name = request.form.get("voice_name", "").strip()
    description = request.form.get("description", "").strip()
    files = request.files.getlist("audio_files")
    if not voice_name or not files:
        flash("Voice name and at least one audio file are required.", "error")
        return redirect(url_for("voices_page"))

    # Save uploaded files temporarily
    import tempfile
    tmp_paths = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for f in files:
            tmp_path = Path(tmpdir) / f.filename
            f.save(tmp_path)
            tmp_paths.append(str(tmp_path))
        result = vm.clone_voice(voice_name, tmp_paths, description)

    if result["success"]:
        flash(f"Voice '{voice_name}' cloned successfully! Voice ID: {result['voice_id']}", "success")
    else:
        flash(f"Clone failed: {result['error']}", "error")
    return redirect(url_for("voices_page"))

@app.route("/voices/delete", methods=["POST"])
def delete_voice():
    import voice_manager as vm
    voice_id = request.form.get("voice_id", "")
    result = vm.delete_voice(voice_id)
    if result["success"]:
        flash("Voice deleted.", "success")
    else:
        flash(f"Delete failed: {result['error']}", "error")
    return redirect(url_for("voices_page"))

@app.route("/voices/api/active")
def get_active_voice_api():
    import voice_manager as vm
    return jsonify(vm.get_active_voice())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
