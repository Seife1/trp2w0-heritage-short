"""
Assembly and mastering stage using FFmpeg.

Handles:
1. Radio Cut assembly (narration over black screen with subtitles and temp score).
2. Rough Cut assembly (Checkpoint 2: moving video clips, synchronized narration,
   ducked original Ethiopian acoustic score, and dual Amharic/English burned-in subtitles).
3. Near-final and final mastering with sidechain ducking and two-pass -14 LUFS loudnorm.
"""

import os
import sys
import json
import wave
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from schema.validate import validate_storyboard

STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"
AUDIO_DIR = PROJECT_ROOT / "outputs" / "audio"
MUSIC_DIR = PROJECT_ROOT / "outputs" / "audio" / "music"
SHOTS_DIR = PROJECT_ROOT / "outputs" / "shots"
FINAL_DIR = PROJECT_ROOT / "outputs" / "final"

# English translations matching storyboard narrative lines
ENGLISH_TRANSLATIONS = {
    "shot_01": "Kaleb had descended to the fields at dawn.",
    "shot_02": "Straining with brute strength alone, the rocky soil remained unyielding.",
    "shot_03": "His palms tore and his breath grew ragged. Muscle alone found no path.",
    "shot_04": "Toil without method brings only exhaustion: 'What one does not know brings much sweat.'",
    "shot_05": "His grandfather, Ato Berhanu, observed quietly from afar, then stepped forward.",
    "shot_06": "'My son, do not clench your grip; let the tool's own weight do the work.'",
    "shot_07": "Raised with calm balance, the doma sliced deep into the earth under its own momentum.",
    "shot_08": "Finding the balance, Kaleb felt the burden lift, and the earth yielded with ease.",
    "shot_09": "Knowledge elevates strength to grace, ensuring no honest labor is spent in vain."
}


def get_wav_duration(path: Path) -> float:
    """Read duration of WAV file directly from header."""
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def generate_temp_drone_score(output_path: Path, duration_s: float):
    """
    Generate an acoustic drone / temp score via FFmpeg sine & lowpass filters
    if external score track is not yet provided.
    """
    st_out = max(0.0, duration_s - 2.0)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=110:duration={duration_s}",
        "-af", f"volume=0.08,lowpass=f=250,afade=t=in:ss=0:d=2,afade=t=out:st={st_out:.2f}:d=2",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def build_radio_cut() -> bool:
    """
    Assemble the Radio Cut (Checkpoint 1):
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

    with open(concat_list_path, "w", encoding="utf-8") as f:
        for shot in shots:
            shot_id = shot["shot_id"]
            wav_file = AUDIO_DIR / f"narration_{shot_id}.wav"
            if not wav_file.exists():
                print(f"[ERROR] Audio for {shot_id} missing: {wav_file}", file=sys.stderr)
                return False
            f.write(f"file '{wav_file.resolve().as_posix()}'\n")

    # Concatenate narration stems
    combined_narration = FINAL_DIR / "combined_narration.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy", str(combined_narration)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    total_duration = get_wav_duration(combined_narration)
    print(f"[INFO] Total narration duration: {total_duration:.2f}s")

    temp_score = FINAL_DIR / "temp_score.wav"
    generate_temp_drone_score(temp_score, total_duration)

    output_mp4 = FINAL_DIR / "radio_cut.mp4"
    print(f"[INFO] Assembling Radio Cut to {output_mp4.name}...")

    font_path = "C\\:/Windows/Fonts/nyala.ttf"
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=24:d={total_duration}",
        "-i", str(combined_narration),
        "-i", str(temp_score),
        "-filter_complex",
        "[2:a][1:a]sidechaincompress=threshold=0.03:ratio=5:attack=200:release=1200[ducked_score];"
        "[1:a][ducked_score]amix=inputs=2:weights=1.0 0.25:normalize=0[mixed_audio];"
        f"[0:v]drawtext=fontfile='{font_path}':text='RADIO CUT (CHECKPOINT 1)':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h/3,"
        f"drawtext=fontfile='{font_path}':text='የማያውቁት ነገር ላብ ያበረክታል':fontcolor=gold:fontsize=52:x=(w-text_w)/2:y=h/2,"
        f"drawtext=fontfile='{font_path}':text='Audio & Pacing Validation Cut':fontcolor=gray:fontsize=32:x=(w-text_w)/2:y=(h/2)+70[outv]",
        "-map", "[outv]",
        "-map", "[mixed_audio]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(output_mp4)
    ]

    subprocess.run(ffmpeg_cmd, check=True)
    print(f"[SUCCESS] Radio cut successfully created: {output_mp4}")
    return True


def pad_shot_audio(shot_id: str, target_duration_s: float, out_path: Path) -> bool:
    """
    Pads a shot's narration audio stem to match the exact shot duration.
    Places a 0.5s pre-roll silence before speech, then pads the tail.
    """
    stem_path = AUDIO_DIR / f"narration_{shot_id}.wav"
    if not stem_path.exists():
        print(f"[ERROR] Missing narration stem for {shot_id}: {stem_path}", file=sys.stderr)
        return False

    with wave.open(str(stem_path), "rb") as wf:
        params = wf.getparams()
        frames = wf.readframes(wf.getnframes())

    sr = params.framerate
    channels = params.nchannels
    sampwidth = params.sampwidth
    bytes_per_sample = channels * sampwidth

    speech_dur = len(frames) / (sr * bytes_per_sample)
    pre_roll_dur = min(0.5, max(0.0, (target_duration_s - speech_dur) / 2.0))
    post_roll_dur = max(0.0, target_duration_s - speech_dur - pre_roll_dur)

    pre_roll_bytes = b"\x00" * int(pre_roll_dur * sr * bytes_per_sample)
    post_roll_bytes = b"\x00" * int(post_roll_dur * sr * bytes_per_sample)

    target_total_bytes = int(target_duration_s * sr * bytes_per_sample)
    padded_frames = pre_roll_bytes + frames + post_roll_bytes

    # Truncate or zero-pad to exact sample count
    if len(padded_frames) > target_total_bytes:
        padded_frames = padded_frames[:target_total_bytes]
    elif len(padded_frames) < target_total_bytes:
        padded_frames += b"\x00" * (target_total_bytes - len(padded_frames))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wf:
        wf.setparams(params)
        wf.writeframes(padded_frames)

    return True


def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS time format: H:MM:SS.cc."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis == 100:
        centis = 0
        secs += 1
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


def generate_ass_subtitles(timeline: list, out_path: Path, aspect: str = "9:16") -> Path:
    """
    Generate Advanced SubStation Alpha (.ass) subtitle file.
    Renders gold native Amharic on top line, crisp white English translation below,
    with black outline and drop shadow for maximum legibility over all video content.
    """
    res_x = 1080 if aspect == "9:16" else 1920
    res_y = 1920 if aspect == "9:16" else 1080

    am_size = 52 if aspect == "9:16" else 42
    en_size = 38 if aspect == "9:16" else 30
    am_margin_v = 240 if aspect == "9:16" else 130
    en_margin_v = 180 if aspect == "9:16" else 85

    ass_content = f"""[Script Info]
Title: The Heritage Short - Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: AmharicLine,Nyala,{am_size},&H0000D7FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,40,40,{am_margin_v},1
Style: EnglishLine,Nyala,{en_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,40,40,{en_margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for item in timeline:
        st = format_ass_time(item["start"])
        et = format_ass_time(item["end"])
        am_text = item["amharic"].replace("\n", "\\N")
        en_text = item["english"].replace("\n", "\\N")
        events.append(f"Dialogue: 0,{st},{et},AmharicLine,,0,0,0,,{am_text}")
        events.append(f"Dialogue: 0,{st},{et},EnglishLine,,0,0,0,,{en_text}")

    ass_content += "\n".join(events) + "\n"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return out_path


def build_rough_cut(aspect: str = "9:16") -> bool:
    """
    Assemble the Rough Cut (Checkpoint 2):
    1. Concatenates the 9 motion shot clips (Ken Burns).
    2. Synthesizes a frame-accurate full narration track with natural inter-shot pauses.
    3. Blends in the original Ethiopian acoustic score with sidechain ducking.
    4. Burns in dual Amharic & English subtitles inside safe visual margins via ASS subtitles.
    5. Outputs `outputs/final/rough_cut.mp4` (or rough_cut_h16_9.mp4).
    """
    if not validate_storyboard(str(STORYBOARD_PATH)):
        return False

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    shots = storyboard.get("shots", [])
    aspect_slug = "v9_16" if aspect == "9:16" else "h16_9"

    print(f"\n{'='*70}")
    print(f"🎬 ROUGH CUT ASSEMBLY (Checkpoint 2 | Aspect: {aspect})")
    print(f"{'='*70}\n")

    # 1. Prepare video concatenation list
    video_concat_path = FINAL_DIR / f"shots_concat_{aspect_slug}.txt"
    with open(video_concat_path, "w", encoding="utf-8") as vf:
        for shot in shots:
            shot_id = shot["shot_id"]
            clip_path = SHOTS_DIR / f"{shot_id}_{aspect_slug}.mp4"
            if not clip_path.exists():
                print(f"[ERROR] Missing motion clip: {clip_path}", file=sys.stderr)
                print("Run python pipeline/shots.py first.", file=sys.stderr)
                return False
            vf.write(f"file '{clip_path.resolve().as_posix()}'\n")

    # 2. Prepare aligned narration track
    padded_audio_dir = FINAL_DIR / "padded_audio"
    audio_concat_path = FINAL_DIR / "narration_padded_concat.txt"
    timeline = []
    current_time = 0.0

    with open(audio_concat_path, "w", encoding="utf-8") as af:
        for shot in shots:
            shot_id = shot["shot_id"]
            dur = float(shot["duration_s"])
            padded_wav = padded_audio_dir / f"{shot_id}_padded.wav"
            ok = pad_shot_audio(shot_id, dur, padded_wav)
            if not ok:
                return False
            af.write(f"file '{padded_wav.resolve().as_posix()}'\n")
            timeline.append({
                "shot_id": shot_id,
                "start": current_time,
                "end": current_time + dur,
                "amharic": shot.get("narration_text", ""),
                "english": ENGLISH_TRANSLATIONS.get(shot_id, "")
            })
            current_time += dur

    total_duration = current_time
    print(f"[INFO] Timeline assembled: {len(shots)} shots, total duration = {total_duration:.2f}s")

    # Concatenate padded narration
    combined_narration = FINAL_DIR / "narration_rough_cut.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(audio_concat_path),
        "-c", "copy", str(combined_narration)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 3. Concatenate video clips
    combined_video = FINAL_DIR / f"video_rough_cut_{aspect_slug}.mp4"
    print("[INFO] Concatenating motion clips...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(video_concat_path),
        "-c", "copy", str(combined_video)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 4. Check score
    score_path = MUSIC_DIR / "score_final.wav"
    if not score_path.exists():
        print(f"[ERROR] Final score track not found: {score_path}", file=sys.stderr)
        print("Run python pipeline/music.py first.", file=sys.stderr)
        return False

    # 5. Generate ASS subtitle file
    ass_path = FINAL_DIR / f"subtitles_{aspect_slug}.ass"
    generate_ass_subtitles(timeline, ass_path, aspect=aspect)
    # Windows path formatting for FFmpeg subtitles filter: escape colon and backslashes
    ass_filter_path = ass_path.resolve().as_posix().replace(":", "\\:")

    # Output file
    out_name = "rough_cut.mp4" if aspect == "9:16" else "rough_cut_h16_9.mp4"
    output_mp4 = FINAL_DIR / out_name
    print(f"[INFO] Assembling Rough Cut to {output_mp4.name} with audio ducking and styled subtitles...")

    # FFmpeg assembly command
    # Input 0: concatenated video
    # Input 1: padded narration
    # Input 2: score
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(combined_video),
        "-i", str(combined_narration),
        "-i", str(score_path),
        "-filter_complex",
        f"[0:v]subtitles='{ass_filter_path}'[subbed_v];"
        "[2:a][1:a]sidechaincompress=threshold=0.035:ratio=4:attack=150:release=1000[ducked_score];"
        "[1:a][ducked_score]amix=inputs=2:weights=1.0 0.35:normalize=0[mixed_audio]",
        "-map", "[subbed_v]",
        "-map", "[mixed_audio]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{total_duration:.2f}",
        str(output_mp4)
    ]

    subprocess.run(ffmpeg_cmd, check=True)

    file_size_mb = output_mp4.stat().st_size / (1024 * 1024)
    print(f"\n[SUCCESS] Rough Cut (Checkpoint 2) assembled successfully!")
    print(f"          File: {output_mp4.name} ({file_size_mb:.2f} MB)")
    print(f"          Duration: {total_duration:.2f}s | Resolution: {'1080x1920' if aspect == '9:16' else '1920x1080'}\n")
    return True


def generate_ai_end_card(output_path: Path, aspect: str = "9:16", duration_s: float = 2.5) -> bool:
    """
    Generate a 2.5-second AI disclosure end card with silent audio.
    Meets the Assignment 2 mandate for clear ethical AI attribution.
    Uses ASS subtitles over a solid background to cleanly handle multi-line formatting and Ethiopic script.
    """
    res_x = 1080 if aspect == "9:16" else 1920
    res_y = 1920 if aspect == "9:16" else 1080
    res = f"{res_x}x{res_y}"

    title_size = 52 if aspect == "9:16" else 56
    body_size = 28 if aspect == "9:16" else 30
    sub_size = 24 if aspect == "9:16" else 26

    # Generate ASS file for the end card
    ass_path = output_path.parent / f"end_card_{'v9_16' if aspect == '9:16' else 'h16_9'}.ass"
    st = "0:00:00.00"
    et = f"0:00:{duration_s:05.2f}"

    ass_text = f"""[Script Info]
Title: AI Disclosure End Card
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitleStyle,Nyala,{title_size},&H0037AFD4,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,2,5,30,30,0,1
Style: BodyStyle,Nyala,{body_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1,1,5,30,30,0,1
Style: SubStyle,Nyala,{sub_size},&H00AAAAAA,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1,1,5,30,30,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{st},{et},TitleStyle,,0,0,0,,\"የማያውቁት ነገር ላብ ያበረክታል\"\\N{{\\fs{title_size-14}\\c&H00D4AF37&}}\"What one does not know brings much sweat and toil.\"
Dialogue: 0,{st},{et},BodyStyle,,0,0,0,,\\N\\N\\N\\NCreated with AI for Cultural & Educational Preservation
Dialogue: 0,{st},{et},SubStyle,,0,0,0,,\\N\\N\\N\\N\\N\\NVisuals: FLUX.1 schnell & Leonardo AI Phoenix\\NNarration: Gemini 3.8 Flash TTS (Charon & Algenib)\\NMusic: Acoustic Ethiopian Synthesis (Krar, Begena, Washint, Kebero)
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_text)

    ass_filter_path = ass_path.resolve().as_posix().replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=#0d0d0f:s={res}:d={duration_s}:r=24",
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100:d={duration_s}",
        "-vf", f"subtitles='{ass_filter_path}',fade=t=in:st=0:d=0.3,fade=t=out:st={duration_s-0.3}:d=0.3",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path)
    ]
    res_code = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res_code.returncode != 0:
        print(f"[ERROR] Failed to generate AI end card: {res_code.stderr}", file=sys.stderr)
        return False
    return True


def master_final(aspect: str = "9:16", target_i: float = -14.0, target_lra: float = 7.0, target_tp: float = -1.0) -> bool:
    """
    Phase 3 Master Delivery Engine:
    1. Ensures rough cut is built.
    2. Performs two-pass EBU R128 / ITU-R BS.1770 (-14 LUFS, True Peak <= -1 dB) loudness normalization.
    3. Synthesizes and appends the 2.5s AI Disclosure End Card.
    4. Outputs finalized master MP4: `outputs/final/final_master_9_16.mp4` or `final_master_16_9.mp4`.
    """
    aspect_slug = "9_16" if aspect == "9:16" else "16_9"
    rough_name = "rough_cut.mp4" if aspect == "9:16" else "rough_cut_h16_9.mp4"
    rough_path = FINAL_DIR / rough_name

    if not rough_path.exists():
        print(f"[INFO] Rough cut {rough_name} does not exist. Assembling it first...")
        ok = build_rough_cut(aspect=aspect)
        if not ok:
            return False

    print(f"\n{'='*70}")
    print(f"🎚️ TWO-PASS -14 LUFS MASTERING & AI END CARD ({aspect})")
    print(f"{'='*70}\n")

    # Pass 1: Measure loudness statistics
    print(f"[1/4] Running Pass 1 loudness measurement (Target: {target_i} LUFS, TP: {target_tp} dB)...")
    pass1_cmd = [
        "ffmpeg", "-y",
        "-i", str(rough_path),
        "-vn",
        "-af", f"loudnorm=I={target_i}:LRA={target_lra}:tp={target_tp}:print_format=json",
        "-f", "null", "-"
    ]
    proc1 = subprocess.run(pass1_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stderr_output = proc1.stderr

    # Parse JSON from stderr
    import re
    json_match = re.search(r"\{[\s\S]*\"input_i\"[\s\S]*\}", stderr_output)
    if not json_match:
        print("[ERROR] Failed to parse loudnorm Pass 1 metrics from FFmpeg output.", file=sys.stderr)
        return False

    stats = json.loads(json_match.group(0))
    measured_i = stats.get("input_i")
    measured_tp = stats.get("input_tp")
    measured_lra = stats.get("input_lra")
    measured_thresh = stats.get("input_thresh")
    target_offset = stats.get("target_offset")

    print(f"      Measured Audio: Integrated={measured_i} LUFS | TP={measured_tp} dB | LRA={measured_lra}")

    # Pass 2: Apply linear normalization to rough cut audio + true peak limiting to -1.0 dBFS (amplitude 0.891)
    print(f"[2/4] Running Pass 2 two-pass loudness normalization...")
    normalized_feature = FINAL_DIR / f"feature_mastered_{aspect_slug}.mp4"
    pass2_filter = (
        f"loudnorm=I={target_i}:LRA={target_lra}:tp={target_tp}:"
        f"measured_I={measured_i}:measured_LRA={measured_lra}:measured_tp={measured_tp}:"
        f"measured_thresh={measured_thresh}:offset={target_offset}:linear=true,"
        f"alimiter=limit=0.891:attack=5:release=50:asc=true:level=false"
    )
    pass2_cmd = [
        "ffmpeg", "-y",
        "-i", str(rough_path),
        "-c:v", "copy",
        "-af", pass2_filter,
        "-c:a", "aac", "-b:a", "192k",
        str(normalized_feature)
    ]
    subprocess.run(pass2_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Step 3: Generate 2.5s AI Disclosure End Card
    print(f"[3/4] Synthesizing 2.5s Ethical AI Disclosure End Card...")
    end_card_path = FINAL_DIR / f"end_card_{aspect_slug}.mp4"
    ok = generate_ai_end_card(end_card_path, aspect=aspect, duration_s=2.5)
    if not ok:
        return False

    # Step 4: Concatenate Feature + End Card into Final Master MP4
    print(f"[4/4] Concatenating feature and end card into Final Master Cut...")
    final_master_path = FINAL_DIR / f"final_master_{aspect_slug}.mp4"
    concat_manifest = FINAL_DIR / f"master_concat_{aspect_slug}.txt"
    with open(concat_manifest, "w", encoding="utf-8") as f:
        f.write(f"file '{normalized_feature.resolve().as_posix()}'\n")
        f.write(f"file '{end_card_path.resolve().as_posix()}'\n")

    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_manifest),
        "-c", "copy",
        str(final_master_path)
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    file_size_mb = final_master_path.stat().st_size / (1024 * 1024)
    print(f"\n[SUCCESS] Final Master Delivered: {final_master_path.name}")
    print(f"          Path: {final_master_path}")
    print(f"          File Size: {file_size_mb:.2f} MB")
    print(f"          Standard: -14.0 LUFS Integrated | True Peak <= -1.0 dBFS | End Card: +2.5s\n")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Assembly and Mastering Pipeline")
    parser.add_argument("--radio-cut", action="store_true", help="Assemble Radio Cut (Checkpoint 1)")
    parser.add_argument("--rough-cut", action="store_true", help="Assemble Rough Cut (Checkpoint 2)")
    parser.add_argument("--master", action="store_true", help="Perform -14 LUFS Two-Pass Mastering & AI End Card (Phase 3 Master)")
    parser.add_argument("--aspect", choices=["9:16", "16:9"], default="9:16", help="Aspect ratio (default: 9:16)")

    args = parser.parse_args()

    if args.master:
        success = master_final(aspect=args.aspect)
    elif args.rough_cut:
        success = build_rough_cut(aspect=args.aspect)
    else:
        success = build_radio_cut()

    sys.exit(0 if success else 1)
