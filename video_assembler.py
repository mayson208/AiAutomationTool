"""video_assembler.py — Assemble vertical Shorts-style video with Whisper word captions."""
import os
import random
from datetime import datetime
from pathlib import Path
import config

TARGET_W = 1080
TARGET_H = 1920
CLIP_MIN_DURATION = 4
CLIP_MAX_DURATION = 8
CROSSFADE_DURATION = 0.4
KEN_BURNS_ZOOM = 0.05

# Caption settings
CAPTION_FONTSIZE = 72
CAPTION_WORDS_PER_GROUP = 3
CAPTION_Y_RATIO = 0.72   # vertical position (fraction of height)
CAPTION_COLOR = (255, 255, 255)
CAPTION_SHADOW_COLOR = (0, 0, 0)
CAPTION_HIGHLIGHT_COLOR = (255, 220, 50)   # yellow for active word


def _apply_ken_burns(clip, zoom_in=True):
    try:
        if zoom_in:
            zoomed = clip.resize(lambda t: 1.0 + KEN_BURNS_ZOOM * t / max(clip.duration, 0.1))
        else:
            zoomed = clip.resize(lambda t: (1.0 + KEN_BURNS_ZOOM) - KEN_BURNS_ZOOM * t / max(clip.duration, 0.1))
        return zoomed.crop(
            x_center=zoomed.w / 2,
            y_center=zoomed.h / 2,
            width=TARGET_W,
            height=TARGET_H,
        )
    except Exception:
        return clip


def _generate_captions(voiceover_path: str, progress_callback=None) -> list:
    """
    Use Whisper to transcribe voiceover and return word-level timestamps.
    Returns list of dicts: {word, start, end}
    """
    def _prog(msg):
        if progress_callback:
            progress_callback(msg)

    try:
        import whisper
        _prog("Loading Whisper model (this may take a moment)...")
        model = whisper.load_model("base")
        _prog("Transcribing voiceover for captions...")
        result = model.transcribe(
            voiceover_path,
            word_timestamps=True,
            language="en",
            fp16=False,
        )
        words = []
        for segment in result.get("segments", []):
            for w in segment.get("words", []):
                word = w.get("word", "").strip()
                if word:
                    words.append({
                        "word": word,
                        "start": w["start"],
                        "end": w["end"],
                    })
        _prog(f"Captions ready — {len(words)} words transcribed")
        return words
    except Exception as e:
        _prog(f"Whisper transcription failed: {e} — captions skipped")
        return []


def _group_words(words: list, group_size: int = CAPTION_WORDS_PER_GROUP) -> list:
    """
    Group word-level timestamps into caption chunks.
    Returns list of dicts: {text, start, end, words}
    """
    groups = []
    for i in range(0, len(words), group_size):
        chunk = words[i:i + group_size]
        groups.append({
            "text": " ".join(w["word"] for w in chunk),
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
            "words": chunk,
        })
    return groups


def _render_caption_frame(text: str, size: tuple, active_word: str = None) -> "np.ndarray | None":
    """Render a single caption frame with bold white text + thick black outline."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np

        w, h = size
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        fontsize = CAPTION_FONTSIZE
        font = None
        bold_fonts = ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf",
                      "LiberationSans-Bold.ttf", "arial.ttf"]
        for fname in bold_fonts:
            try:
                font = ImageFont.truetype(fname, fontsize)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()

        # Wrap text to fit width
        words = text.split()
        lines, line = [], []
        for word in words:
            test = " ".join(line + [word])
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > w - 80:
                if line:
                    lines.append(" ".join(line))
                line = [word]
            else:
                line.append(word)
        if line:
            lines.append(" ".join(line))

        line_h = fontsize + 12
        total_h = len(lines) * line_h
        y_center = int(h * CAPTION_Y_RATIO)
        y_start = y_center - total_h // 2

        for i, line_text in enumerate(lines):
            bbox = draw.textbbox((0, 0), line_text, font=font)
            tw = bbox[2] - bbox[0]
            x = (w - tw) // 2
            y = y_start + i * line_h

            # Thick black outline (draw 8 directions)
            outline = 4
            for dx in range(-outline, outline + 1):
                for dy in range(-outline, outline + 1):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, y + dy), line_text, font=font, fill=(0, 0, 0, 255))

            # White text (highlight active word in yellow if applicable)
            if active_word and active_word.strip().lower() in line_text.lower():
                # Draw each word, highlight the active one
                cur_x = x
                for word in line_text.split():
                    wb = draw.textbbox((0, 0), word, font=font)
                    ww = wb[2] - wb[0]
                    color = CAPTION_HIGHLIGHT_COLOR if word.strip().strip(".,!?").lower() == active_word.strip(".,!?").lower() else CAPTION_COLOR
                    draw.text((cur_x, y), word, font=font, fill=color + (255,))
                    cur_x += ww + int(fontsize * 0.25)
            else:
                draw.text((x, y), line_text, font=font, fill=CAPTION_COLOR + (255,))

        return np.array(img)
    except Exception:
        return None


def _make_caption_clips(word_groups: list, video_size: tuple, total_duration: float):
    """Build a list of ImageClips for each caption group."""
    try:
        from moviepy.editor import ImageClip
        clips = []
        for group in word_groups:
            start = group["start"]
            end = min(group["end"], total_duration - 0.1)
            if end <= start or start >= total_duration:
                continue
            duration = end - start

            # Use last word as active (highlight word)
            active = group["words"][-1]["word"] if group["words"] else None
            frame = _render_caption_frame(group["text"], video_size, active_word=active)
            if frame is None:
                continue

            clip = (ImageClip(frame, ismask=False)
                    .set_duration(duration)
                    .set_start(start)
                    .fadein(0.05)
                    .fadeout(0.05))
            clips.append(clip)
        return clips
    except Exception:
        return []


def assemble_video(voiceover_path: str, clip_paths: list, output_filename: str = None,
                   progress_callback=None, section_labels: list = None,
                   format: str = "shorts") -> dict:
    """
    Assemble a vertical Shorts-style video with:
    - Ken Burns zoom on each clip
    - Crossfade transitions
    - Whisper word-synced bold captions
    """
    try:
        from moviepy.editor import (
            VideoFileClip, AudioFileClip,
            concatenate_videoclips, CompositeVideoClip,
        )

        if not clip_paths:
            return {"success": False, "error": "No video clips provided"}
        if not os.path.exists(voiceover_path):
            return {"success": False, "error": f"Voiceover not found: {voiceover_path}"}

        def _progress(msg):
            if progress_callback:
                progress_callback(msg)

        # ── Generate captions via Whisper ─────────────────────────────────────
        _progress("Generating word captions with Whisper...")
        word_timestamps = _generate_captions(voiceover_path, progress_callback=_progress)
        word_groups = _group_words(word_timestamps, CAPTION_WORDS_PER_GROUP) if word_timestamps else []

        # ── Load audio ────────────────────────────────────────────────────────
        _progress("Loading audio track...")
        audio = AudioFileClip(voiceover_path)
        total_duration = audio.duration

        # ── Load and prepare clips ────────────────────────────────────────────
        _progress("Preparing footage clips...")
        raw_clips = []
        for path in clip_paths:
            try:
                c = VideoFileClip(str(path)).without_audio()
                if c.duration > 0.5:
                    raw_clips.append(c)
            except Exception:
                pass

        if not raw_clips:
            return {"success": False, "error": "No usable clips loaded"}

        # Build clip sequence to fill audio duration
        processed = []
        zoom_in = True
        clip_idx = 0
        time_filled = 0.0

        while time_filled < total_duration:
            src = raw_clips[clip_idx % len(raw_clips)]
            clip_idx += 1

            remaining = total_duration - time_filled
            target_len = min(
                random.uniform(CLIP_MIN_DURATION, CLIP_MAX_DURATION),
                remaining
            )

            # Trim
            if src.duration > target_len:
                start = random.uniform(0, max(0, src.duration - target_len - 0.1))
                clipped = src.subclip(start, start + target_len)
            else:
                clipped = src

            # Resize to vertical — crop to fill (letterbox-free)
            _progress(f"Processing clip {clip_idx} ({round(time_filled)}s / {round(total_duration)}s)...")
            try:
                src_ratio = clipped.w / clipped.h
                target_ratio = TARGET_W / TARGET_H
                if src_ratio > target_ratio:
                    # Wider than target — scale by height, crop width
                    new_h = TARGET_H
                    new_w = int(src_ratio * new_h)
                    clipped = clipped.resize((new_w, new_h))
                    clipped = clipped.crop(
                        x_center=new_w / 2,
                        y_center=new_h / 2,
                        width=TARGET_W,
                        height=TARGET_H,
                    )
                else:
                    # Taller or equal — scale by width, crop height
                    new_w = TARGET_W
                    new_h = int(new_w / src_ratio)
                    clipped = clipped.resize((new_w, new_h))
                    clipped = clipped.crop(
                        x_center=new_w / 2,
                        y_center=new_h / 2,
                        width=TARGET_W,
                        height=TARGET_H,
                    )
            except Exception:
                pass

            # Ken Burns
            try:
                clipped = _apply_ken_burns(clipped, zoom_in=zoom_in)
                zoom_in = not zoom_in
            except Exception:
                pass

            # Crossfade in
            if processed:
                try:
                    clipped = clipped.crossfadein(CROSSFADE_DURATION)
                except Exception:
                    pass

            processed.append(clipped)
            time_filled += clipped.duration

        # ── Concatenate ───────────────────────────────────────────────────────
        _progress("Concatenating clips with transitions...")
        try:
            final_video = concatenate_videoclips(
                processed,
                padding=-CROSSFADE_DURATION,
                method="compose"
            )
        except Exception:
            final_video = concatenate_videoclips(processed, method="compose")

        if final_video.duration > total_duration:
            final_video = final_video.subclip(0, total_duration)

        # ── Word-synced captions ──────────────────────────────────────────────
        if word_groups:
            _progress("Rendering word captions...")
            try:
                caption_clips = _make_caption_clips(
                    word_groups,
                    (TARGET_W, TARGET_H),
                    total_duration,
                )
                if caption_clips:
                    final_video = CompositeVideoClip([final_video] + caption_clips)
                    _progress(f"Added {len(caption_clips)} caption clips")
            except Exception as e:
                _progress(f"Caption overlay failed: {e} — continuing without captions")

        # ── Set audio and export ──────────────────────────────────────────────
        final_video = final_video.set_audio(audio)

        if not output_filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"video_{ts}.mp4"
        out_path = config.VIDEOS_DIR / output_filename

        _progress("Encoding final video (this takes a few minutes)...")
        final_video.write_videofile(
            str(out_path),
            codec="libx264",
            audio_codec="aac",
            fps=30,
            logger=None,
            preset="fast",
            ffmpeg_params=["-crf", "23"],
        )

        audio.close()
        final_video.close()
        for c in raw_clips:
            try:
                c.close()
            except Exception:
                pass

        return {"success": True, "path": str(out_path), "filename": output_filename}

    except Exception as e:
        return {"success": False, "error": str(e)}
