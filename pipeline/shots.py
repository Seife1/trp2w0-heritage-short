"""
Moving Shots Engine for The Heritage Short.

Supports dual-mode motion generation:
1. Mode B (Default / Deterministic Fallback): High-fidelity FFmpeg Ken Burns
   dynamic camera engine translating storyboard motion prompts (push-in, strike tremor,
   macro drift, pedestal settle, lateral track, tilt, arcing swing, and crane pull-back)
   into smooth 24fps motion clips with zero aspect distortion.
2. Mode A (Remote Video GPU): Wan 2.2 TI2V-5B generation runner / loader from Kaggle/Colab.

Features:
- Dual aspect ratio support (9:16 vertical 1080x1920, 16:9 horizontal 1920x1080).
- SHA-256 caching per shot (`outputs/shots/<shot_id>_<aspect>.hash`).
- Telemetry logging to `runs.jsonl`.
"""

import os
import sys
import json
import time
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from schema.validate import validate_storyboard

STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"
CURATED_KEYFRAMES_DIR = PROJECT_ROOT / "outputs" / "keyframes_curated"
DEFAULT_KEYFRAMES_DIR = CURATED_KEYFRAMES_DIR if CURATED_KEYFRAMES_DIR.exists() else (PROJECT_ROOT / "outputs" / "keyframes")
SHOTS_DIR = PROJECT_ROOT / "outputs" / "shots"
WAN_DIR = SHOTS_DIR / "wan"
RUNS_LOG_PATH = PROJECT_ROOT / "runs.jsonl"


# Ken Burns motion definitions per shot based on storyboard motion_prompt
# Formula expressions use:
# 'on': frame number (0 to total_frames - 1)
# 'iw', 'ih': input width, input height
# 'zoom': current zoom
KEN_BURNS_PROFILES = {
    "shot_01": {
        # Slow steady push-in across the terraced field
        "desc": "Slow aerial push-in (zoom 1.0 -> 1.15 centered)",
        "z": "min(zoom+0.00096, 1.15)",
        "x": "iw/2-(iw/zoom/2)",
        "y": "ih/2-(ih/zoom/2)"
    },
    "shot_02": {
        # Heavy downward swing ending in jarring thud, slight handheld camera tremor
        "desc": "Heavy downward strike with handheld tremor and strike settle",
        "z": "min(zoom+0.0005, 1.08)",
        "x": "iw/2-(iw/zoom/2) + sin(on/4)*2.5",
        "y": "(ih - ih/zoom) * (on/{total_frames}) + cos(on/3)*2.0"
    },
    "shot_03": {
        # Subtle trembling of fatigued fingers loosening their rigid grip, static camera
        "desc": "Macro focus drift on trembling hands",
        "z": "min(zoom+0.0004, 1.07)",
        "x": "iw/2-(iw/zoom/2) + sin(on/8)*1.5",
        "y": "ih/2-(ih/zoom/2) + cos(on/10)*1.5"
    },
    "shot_04": {
        # Slow gentle downward camera settle, Kaleb catching breath
        "desc": "Gentle pedestal settle toward resting figure",
        "z": "1.05",
        "x": "iw/2-(iw/zoom/2)",
        "y": "(ih - ih/zoom) * (0.25 + 0.5 * (on/{total_frames}))"
    },
    "shot_05": {
        # Slow steady tracking shot as elder approaches with unhurried steps
        "desc": "Steady lateral tracking across the field",
        "z": "1.10",
        "x": "(iw - iw/zoom) * (0.2 + 0.6 * (on/{total_frames}))",
        "y": "ih/2-(ih/zoom/2)"
    },
    "shot_06": {
        # Smooth, deliberate sliding adjustment of hands along the wooden shaft
        "desc": "Slow macro tilt along the wooden handle",
        "z": "1.12",
        "x": "iw/2-(iw/zoom/2)",
        "y": "(ih - ih/zoom) * (0.2 + 0.6 * (on/{total_frames}))"
    },
    "shot_07": {
        # Smooth arcing camera motion following downward drop of pickaxe
        "desc": "Fluid arcing swing following blade momentum",
        "z": "1.06 + 0.06 * sin(on/{total_frames} * 3.14159)",
        "x": "(iw - iw/zoom) * (0.3 + 0.4 * (on/{total_frames}))",
        "y": "(ih - ih/zoom) * (0.2 + 0.6 * (on/{total_frames}))"
    },
    "shot_08": {
        # Smooth lateral pan following Kaleb's rhythmic, unhurried swing
        "desc": "Smooth lateral tracking with rhythmic sway",
        "z": "1.08",
        "x": "(iw - iw/zoom) * (0.7 - 0.5 * (on/{total_frames}))",
        "y": "ih/2-(ih/zoom/2) + sin(on/12)*2.0"
    },
    "shot_09": {
        # Slow graceful pull-back and slight crane up into dusk sky
        "desc": "Slow crane-up and pull-back into dusk sky",
        "z": "max(1.15 - (0.15 * on/{total_frames}), 1.0)",
        "x": "iw/2-(iw/zoom/2)",
        "y": "(ih - ih/zoom) * (1.0 - (on/{total_frames}))"
    }
}


def log_run(shot_id: str, mode: str, aspect: str, duration_s: float, latency_s: float, status: str, details: dict):
    """Log execution run metrics to runs.jsonl."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stage": "shots",
        "model": f"kenburns-ffmpeg-8.0" if mode == "kenburns" else "wan-2.2-ti2v-5b",
        "params": {
            "mode": mode,
            "aspect": aspect,
            "duration_s": duration_s,
            "fps": 24
        },
        "latency_s": round(latency_s, 3),
        "status": status,
        "details": {
            "shot_id": shot_id,
            **details
        }
    }
    with open(RUNS_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def compute_shot_hash(keyframe_path: Path, motion_prompt: str, duration_s: float, aspect: str) -> str:
    """Compute deterministic SHA-256 content hash."""
    hasher = hashlib.sha256()
    if keyframe_path.exists():
        with open(keyframe_path, "rb") as f:
            hasher.update(f.read())
    hasher.update(motion_prompt.encode("utf-8"))
    hasher.update(f"{duration_s:.2f}".encode("utf-8"))
    hasher.update(aspect.encode("utf-8"))
    return hasher.hexdigest()


# Shot-specific framing offsets to prevent anatomical clipping across 9:16 and 16:9
# Values define normalized crop center offset (0.0=left/top, 0.5=center, 1.0=right/bottom)
FRAMING_PROFILES = {
    "shot_01": {
        "desc": "Wide terraced landscape - centered on Kaleb at dawn",
        "crop_center_x": 0.50,
        "crop_center_y": 0.48
    },
    "shot_02": {
        "desc": "Downward strike - slight top bias to preserve raised tool head",
        "crop_center_x": 0.52,
        "crop_center_y": 0.40
    },
    "shot_03": {
        "desc": "Extreme close-up torn palm - focused on blistered center",
        "crop_center_x": 0.50,
        "crop_center_y": 0.50
    },
    "shot_04": {
        "desc": "Kaleb forehead resting on doma - centered on head and handle",
        "crop_center_x": 0.48,
        "crop_center_y": 0.42
    },
    "shot_05": {
        "desc": "Ato Berhanu and Kaleb - bias toward center-left to capture elder's dialogue gesture",
        "crop_center_x": 0.45,
        "crop_center_y": 0.46
    },
    "shot_06": {
        "desc": "Macro shared hands on handle - strict center on intertwined grips",
        "crop_center_x": 0.50,
        "crop_center_y": 0.50
    },
    "shot_07": {
        "desc": "Ato Berhanu demonstrating doma swing - bias slightly right to include elder and falling blade",
        "crop_center_x": 0.54,
        "crop_center_y": 0.42
    },
    "shot_08": {
        "desc": "Kaleb smiling with effortless swing - upper body and furrow",
        "crop_center_x": 0.50,
        "crop_center_y": 0.44
    },
    "shot_09": {
        "desc": "Two figures walking into sunset - wide center keeping both silhouettes intact",
        "crop_center_x": 0.50,
        "crop_center_y": 0.52
    }
}


def render_kenburns_shot(keyframe_path: Path, output_path: Path, shot_cfg: dict, aspect: str = "9:16") -> bool:
    """
    Render a single shot using FFmpeg Ken Burns engine with aspect-aware safe framing.
    For 9:16: crop to safe vertical pillar, targeting focal action without lopping heads or tools.
    For 16:9: crop to safe horizontal letterbox, ensuring full landscape horizon and tool swing headroom.
    """
    shot_id = shot_cfg["shot_id"]
    duration_s = float(shot_cfg["duration_s"])
    total_frames = int(round(duration_s * 24))

    profile = KEN_BURNS_PROFILES.get(shot_id, {
        "desc": "Default slow push-in",
        "z": "min(zoom+0.0008, 1.12)",
        "x": "iw/2-(iw/zoom/2)",
        "y": "ih/2-(ih/zoom/2)"
    })

    framing = FRAMING_PROFILES.get(shot_id, {
        "crop_center_x": 0.5,
        "crop_center_y": 0.5
    })

    z_expr = profile["z"].format(total_frames=total_frames)
    x_expr = profile["x"].format(total_frames=total_frames)
    y_expr = profile["y"].format(total_frames=total_frames)

    # Ingest image dimensions via FFprobe or default 1024x1024 / 1024x576
    # Calculate aspect-aware crop with padding protection
    if aspect == "9:16":
        out_w, out_h = 1080, 1920
        # Horizontal crop window: 9/16 aspect ratio relative to input height
        # in_w * (9/16) or in_h * (9/16)
        crop_x_offset = f"(in_w - in_h*9/16)*{framing['crop_center_x']}"
        pre_crop = f"crop=in_h*9/16:in_h:{crop_x_offset}:0"
    else:  # 16:9
        out_w, out_h = 1920, 1080
        # Vertical crop window: 16/9 aspect ratio relative to input width
        crop_y_offset = f"(in_h - in_w*9/16)*{framing['crop_center_y']}"
        pre_crop = f"crop=in_w:in_w*9/16:0:{crop_y_offset}"

    vf_filter = (
        f"{pre_crop},"
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s={out_w}x{out_h}:fps=24"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(keyframe_path),
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "24",
        "-t", f"{duration_s:.3f}",
        str(output_path)
    ]

    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"[ERROR] FFmpeg failed for {shot_id}: {res.stderr[-300:]}", file=sys.stderr)
        return False
    return True


def generate_shots(mode: str = "kenburns", aspect: str = "9:16", target_shot: str = "all", force: bool = False, keyframes_dir: Path = None) -> bool:
    """Generate motion video clips for all storyboard shots."""
    if not validate_storyboard(str(STORYBOARD_PATH)):
        return False

    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    shots = storyboard.get("shots", [])
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    kf_dir = keyframes_dir or DEFAULT_KEYFRAMES_DIR

    print(f"\n{'='*70}")
    print(f"🎬 MOVING SHOTS PIPELINE (Mode: {mode.upper()} | Aspect: {aspect})")
    print(f"   Keyframes Source: {kf_dir.name}")
    print(f"{'='*70}")

    success_count = 0
    total_shots = len(shots) if target_shot == "all" else 1

    for shot in shots:
        shot_id = shot["shot_id"]
        if target_shot != "all" and shot_id != target_shot:
            continue

        duration_s = float(shot["duration_s"])
        motion_prompt = shot.get("motion_prompt", "")
        keyframe_path = kf_dir / f"{shot_id}.png"

        if not keyframe_path.exists():
            print(f"[ERROR] Missing keyframe for {shot_id}: {keyframe_path}", file=sys.stderr)
            print("Run python pipeline/keyframes.py first.", file=sys.stderr)
            return False

        # Output paths
        aspect_slug = "v9_16" if aspect == "9:16" else "h16_9"
        out_mp4 = SHOTS_DIR / f"{shot_id}_{aspect_slug}.mp4"
        hash_file = SHOTS_DIR / f"{shot_id}_{aspect_slug}.hash"

        # Check for Wan-generated remote video if mode is wan or auto
        wan_candidate = WAN_DIR / f"{shot_id}.mp4"
        if mode == "wan" and wan_candidate.exists():
            print(f"[{shot_id}] Using remote Wan 2.2 TI2V video: {wan_candidate.name}")
            # Transcode to target aspect ratio and frame rate
            wan_cmd = [
                "ffmpeg", "-y",
                "-i", str(wan_candidate),
                "-vf", f"scale={1080 if aspect == '9:16' else 1920}:{1920 if aspect == '9:16' else 1080}:force_original_aspect_ratio=decrease,"
                       f"pad={1080 if aspect == '9:16' else 1920}:{1920 if aspect == '9:16' else 1080}:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                "-an", str(out_mp4)
            ]
            wan_res = subprocess.run(wan_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if wan_res.returncode != 0:
                print(f"[ERROR] Failed to transcode Wan clip for {shot_id}: {wan_res.stderr[-200:]}", file=sys.stderr)
                return False
            success_count += 1
            continue

        # Content hash check
        current_hash = compute_shot_hash(keyframe_path, motion_prompt, duration_s, aspect)
        if not force and out_mp4.exists() and hash_file.exists():
            with open(hash_file, "r", encoding="utf-8") as hf:
                cached_hash = hf.read().strip()
            if cached_hash == current_hash:
                print(f"[{shot_id}] [CACHE HIT] {out_mp4.name} (SHA-256 match, skipping)")
                success_count += 1
                continue

        profile = KEN_BURNS_PROFILES.get(shot_id, {})
        desc = profile.get("desc", "Dynamic camera motion")
        print(f"[{shot_id}] Generating {aspect} motion clip ({duration_s}s, 24fps)...")
        print(f"          Direction: {desc}")

        start_time = time.time()
        ok = render_kenburns_shot(keyframe_path, out_mp4, shot, aspect=aspect)
        latency = time.time() - start_time

        if ok:
            with open(hash_file, "w", encoding="utf-8") as hf:
                hf.write(current_hash)

            file_size_kb = out_mp4.stat().st_size / 1024
            print(f"[{shot_id}] [RENDERED] {out_mp4.name} ({file_size_kb:.1f} KB in {latency:.2f}s)")
            log_run(shot_id, "kenburns", aspect, duration_s, latency, "success", {
                "size_kb": round(file_size_kb, 1),
                "motion": desc
            })
            success_count += 1
        else:
            log_run(shot_id, "kenburns", aspect, duration_s, latency, "error", {"error": "FFmpeg render failed"})
            return False

    print(f"\n[DONE] Successfully processed {success_count}/{total_shots} moving shot clips.\n")
    return success_count == total_shots


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The Heritage Short - Moving Shots Engine")
    parser.add_argument("--mode", choices=["kenburns", "wan"], default="kenburns", help="Motion generation mode")
    parser.add_argument("--aspect", choices=["9:16", "16:9"], default="9:16", help="Target aspect ratio")
    parser.add_argument("--shot", default="all", help="Target shot ID (e.g. shot_01) or 'all'")
    parser.add_argument("--force", action="store_true", help="Force re-rendering even if cached")
    parser.add_argument("--keyframes-dir", default=None, help="Directory containing input keyframes")

    args = parser.parse_args()
    kf_path = Path(args.keyframes_dir) if args.keyframes_dir else None
    success = generate_shots(mode=args.mode, aspect=args.aspect, target_shot=args.shot, force=args.force, keyframes_dir=kf_path)
    if not success:
        sys.exit(1)
