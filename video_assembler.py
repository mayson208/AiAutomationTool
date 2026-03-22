"""video_assembler.py — Assemble video from clips and voiceover using MoviePy."""
import os
from datetime import datetime
from pathlib import Path
import config

def assemble_video(voiceover_path: str, clip_paths: list, output_filename: str = None) -> dict:
    """Combine stock footage clips with a voiceover to create a final video."""
    try:
        from moviepy.editor import (
            VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
        )
        if not clip_paths:
            return {"success": False, "error": "No video clips provided"}
        if not os.path.exists(voiceover_path):
            return {"success": False, "error": f"Voiceover file not found: {voiceover_path}"}
        # Load audio to get total duration
        audio = AudioFileClip(voiceover_path)
        total_duration = audio.duration
        # Load and resize clips, loop/trim to fill duration
        target_size = (1920, 1080)
        clips = []
        time_filled = 0.0
        clip_index = 0
        while time_filled < total_duration:
            clip_path = clip_paths[clip_index % len(clip_paths)]
            clip = VideoFileClip(str(clip_path)).without_audio()
            clip = clip.resize(target_size)
            remaining = total_duration - time_filled
            if clip.duration > remaining:
                clip = clip.subclip(0, remaining)
            clips.append(clip)
            time_filled += clip.duration
            clip_index += 1
        # Concatenate clips
        final_video = concatenate_videoclips(clips, method="compose")
        # Set audio
        final_video = final_video.set_audio(audio)
        if not output_filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"video_{ts}.mp4"
        out_path = config.OUTPUTS_DIR / output_filename
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
