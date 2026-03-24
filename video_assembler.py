"""video_assembler.py — Assemble video from clips and voiceover using MoviePy."""
import os
import random
from datetime import datetime
from pathlib import Path
import config

TARGET_W = 1920
TARGET_H = 1080
CLIP_MIN_DURATION = 6    # seconds per clip minimum
CLIP_MAX_DURATION = 12   # seconds per clip maximum
CROSSFADE_DURATION = 0.5  # seconds
KEN_BURNS_ZOOM = 0.06    # 6% zoom over clip duration


def _apply_ken_burns(clip, zoom_in=True):
    """Apply a slow Ken Burns zoom effect to a clip."""
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


def _make_text_overlay(text: str, size: tuple, duration: float, position: str = "bottom"):
    """Create a text overlay clip using PIL. No ImageMagick required."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        from moviepy.editor import ImageClip

        w, h = size
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        fontsize = max(40, w // 36)
        font = None
        for font_name in ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"]:
            try:
                font = ImageFont.truetype(font_name, fontsize)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()

        # Wrap long text
        words = text.split()
        lines, line = [], []
        for word in words:
            test = " ".join(line + [word])
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > w - 120:
                if line:
                    lines.append(" ".join(line))
                line = [word]
            else:
                line.append(word)
        if line:
            lines.append(" ".join(line))

        line_h = fontsize + 8
        total_h = len(lines) * line_h
        if position == "bottom":
            y_start = h - total_h - 60
        else:
            y_start = 40

        for i, line_text in enumerate(lines):
            bbox = draw.textbbox((0, 0), line_text, font=font)
            tw = bbox[2] - bbox[0]
            x = (w - tw) // 2
            y = y_start + i * line_h
            # Shadow
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (-3, 0), (3, 0), (0, -3), (0, 3)]:
                draw.text((x + dx, y + dy), line_text, font=font, fill=(0, 0, 0, 220))
            # Main text
            draw.text((x, y), line_text, font=font, fill=(255, 255, 255, 255))

        overlay = np.array(img)
        clip = ImageClip(overlay, ismask=False).set_duration(duration)
        clip = clip.fadein(0.4).fadeout(0.4)
        return clip
    except Exception:
        return None


def assemble_video(voiceover_path: str, clip_paths: list, output_filename: str = None,
                   progress_callback=None, section_labels: list = None) -> dict:
    """Assemble a cinematic video with Ken Burns, crossfades, and text overlays."""
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

        _progress("Loading audio track...")
        audio = AudioFileClip(voiceover_path)
        total_duration = audio.duration

        # ── Build clip sequence ───────────────────────────────────────────────
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

        # Slice each clip to CLIP_MIN–CLIP_MAX seconds, apply Ken Burns
        processed = []
        zoom_in = True
        clip_idx = 0
        time_filled = 0.0

        while time_filled < total_duration:
            src = raw_clips[clip_idx % len(raw_clips)]
            clip_idx += 1

            # How long should this clip be?
            remaining = total_duration - time_filled
            target_len = min(
                random.uniform(CLIP_MIN_DURATION, CLIP_MAX_DURATION),
                remaining
            )

            # Trim source clip
            if src.duration > target_len:
                start = random.uniform(0, max(0, src.duration - target_len - 0.1))
                clipped = src.subclip(start, start + target_len)
            else:
                clipped = src

            # Resize to target
            _progress(f"Processing clip {clip_idx} ({round(time_filled)}s / {round(total_duration)}s)...")
            try:
                clipped = clipped.resize((TARGET_W, TARGET_H))
            except Exception:
                pass

            # Ken Burns
            try:
                clipped = _apply_ken_burns(clipped, zoom_in=zoom_in)
                zoom_in = not zoom_in  # alternate direction
            except Exception:
                pass

            # Crossfade in (skip first clip)
            if processed:
                try:
                    clipped = clipped.crossfadein(CROSSFADE_DURATION)
                except Exception:
                    pass

            processed.append(clipped)
            time_filled += clipped.duration

        # ── Concatenate with crossfades ────────────────────────────────────────
        _progress("Concatenating clips with transitions...")
        try:
            final_video = concatenate_videoclips(
                processed,
                padding=-CROSSFADE_DURATION,
                method="compose"
            )
        except Exception:
            final_video = concatenate_videoclips(processed, method="compose")

        # Trim to exact audio length
        if final_video.duration > total_duration:
            final_video = final_video.subclip(0, total_duration)

        # ── Text overlays ────────────────────────────────────────────────────
        if section_labels:
            _progress("Adding text overlays...")
            try:
                overlays = []
                interval = total_duration / max(len(section_labels), 1)
                for i, label in enumerate(section_labels[:8]):  # max 8 overlays
                    if not label or len(label.strip()) < 3:
                        continue
                    start_t = i * interval + 1.0
                    if start_t >= total_duration - 3:
                        break
                    ov = _make_text_overlay(label.strip(), (TARGET_W, TARGET_H), duration=3.5)
                    if ov is not None:
                        ov = ov.set_start(start_t)
                        overlays.append(ov)

                if overlays:
                    final_video = CompositeVideoClip([final_video] + overlays)
            except Exception:
                pass  # text overlay failure is non-fatal

        # ── Set audio and export ─────────────────────────────────────────────
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
            fps=24,
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
