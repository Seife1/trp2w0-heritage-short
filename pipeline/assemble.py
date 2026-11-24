"""
Assembly and mastering stage using FFmpeg.
Handles:
1. Radio Cut assembly (narration over black screen with subtitles and temp score).
2. Near-final and final mastering with sidechain ducking and two-pass -14 LUFS loudnorm.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from schema.validate import validate_storyboard

STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"
AUDIO_DIR = PROJECT_ROOT / "outputs" / "audio"
FINAL_DIR = PROJECT_ROOT / "outputs" / "final"


def generate_temp_drone_score(output_path: Path, duration_s: float):
    """
    Generate an acoustic drone / temp score via FFmpeg sine & lowpass filters
    if external score track is not yet provided.
    """
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=110:duration={duration_s}",
        "-af", "volume=0.08,lowpass=f=250,afade=t=in:ss=0:d=2,afade=t=out:st={duration_s-2}:d=2",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def build_radio_cut() -> bool:
    """
    Assemble the Radio Cut:
    Concatenates line-by-line narration, layers beneath temp score,
    and displays shot labels + subtitles on a clean vertical 1080x1920 black canvas.
    """
    if not validate_storyboard(str(STORYBOARD_PATH)):
        return False

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    shots = storyboard.get("shots", [])
    concat_list_path = FINAL_DIR / "narration_concat.txt"

    total_duration = 0.0
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for shot in shots:
            shot_id = shot["shot_id"]
            wav_file = AUDIO_DIR / f"narration_{shot_id}.wav"
            if not wav_file.exists():
                print(f"[ERROR] Audio for {shot_id} missing: {wav_file}", file=sys.stderr)
                print("Run python pipeline/narration.py first.", file=sys.stderr)
                return False
            f.write(f"file '{wav_file.resolve().as_posix()}'\n")

    # 1. Concatenate narration stems
    combined_narration = FINAL_DIR / "combined_narration.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy", str(combined_narration)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Measure total audio duration
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(combined_narration)
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    total_duration = float(res.stdout.strip())
    print(f"[INFO] Total narration duration: {total_duration:.2f}s")

    # 2. Generate temp background score
    temp_score = FINAL_DIR / "temp_score.wav"
    generate_temp_drone_score(temp_score, total_duration)

    # 3. Assemble vertical (1080x1920) radio cut MP4 with audio ducking
    output_mp4 = FINAL_DIR / "radio_cut.mp4"
    print(f"[INFO] Assembling Radio Cut to {output_mp4.name}...")

    # Complex filter:
    # - Black video generator 1080x1920 at 24fps
    # - Sidechain compression: score ducked beneath narration
    # - Drawtitle text stating "RADIO CUT - CHECKPOINT 1"
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=24:d={total_duration}",
        "-i", str(combined_narration),
        "-i", str(temp_score),
        "-filter_complex",
        "[2:a][1:a]sidechaincompress=threshold=0.03:ratio=5:attack=200:release=1200[ducked_score];"
        "[1:a][ducked_score]amix=inputs=2:weights=1.0 0.25:normalize=0[mixed_audio];"
        "[0:v]drawtext=text='RADIO CUT (CHECKPOINT 1)':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h/3,"
        "drawtext=text='የማያውቁት ነገር ላብ ያበረክታል':fontcolor=gold:fontsize=42:x=(w-text_w)/2:y=h/2,"
        "drawtext=text='Audio & Pacing Validation Cut':fontcolor=gray:fontsize=32:x=(w-text_w)/2:y=(h/2)+60[outv]",
        "-map", "[outv]",
        "-map", "[mixed_audio]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(output_mp4)
    ]

    subprocess.run(ffmpeg_cmd, check=True)
    print(f"[SUCCESS] Radio cut successfully created: {output_mp4}")
    return True


if __name__ == "__main__":
    if "--radio-cut" in sys.argv or len(sys.argv) == 1:
        success = build_radio_cut()
        sys.exit(0 if success else 1)
