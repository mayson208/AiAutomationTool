"""video_assembler.py — Assemble video from clips and voiceover using MoviePy."""
import os
from datetime import datetime
from pathlib import Path
import config

def assemble_video(voiceover_path: str, clip_paths: list, output_filename: str = None,
                   progress_callback=None) -> dict:
    """Combine stock footage clips with a voiceover to create a final video."""
    try:
        from moviepy.editor import (
            VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
        )
        if not clip_paths:
            return {"success": False, "error": "No video clips provided"}
        if not os.path.exists(voiceover_path):
            return {"success": False, "error": f"Voiceover file not found: {voiceover_path}"}
        def _progress(msg):
            if progress_callback:
                progress_callback(msg)

        _progress("Loading audio track...")
        audio = AudioFileClip(voiceover_path)
        total_duration = audio.duration
        # Load and resize clips, loop/trim to fill duration
        target_size = (1920, 1080)
        clips = []
        time_filled = 0.0
        clip_index = 0
        while time_filled < total_duration:
            clip_path = clip_paths[clip_index % len(clip_paths)]
            _progress(f"Processing footage clip {clip_index + 1}...")
            clip = VideoFileClip(str(clip_path)).without_audio()
            clip = clip.resize(target_size)
            remaining = total_duration - time_filled
            if clip.duration > remaining:
                clip = clip.subclip(0, remaining)
            clips.append(clip)
            time_filled += clip.duration
            clip_index += 1
        _progress("Concatenating clips...")
        final_video = concatenate_videoclips(clips, method="compose")
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
        )
        audio.close()
        final_video.close()
        for c in clips:
            c.close()
        return {"success": True, "path": str(out_path), "filename": output_filename}
    except Exception as e:
        return {"success": False, "error": str(e)}
