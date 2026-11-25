#!/usr/bin/env python3
"""
The Heritage Short — Single-Command Pipeline Entrypoint (run.py).

Provides one-command reproducibility for Assignment 1 (20 pts):
1. Validates storyboard.json against JSON Schema (Draft-07).
2. Generates line-by-line speech narration with caching (Gemini 3.8 Flash TTS).
3. Generates/auditions culturally authentic original score (Acoustic Ethiopian synthesis).
4. Curates winning multi-model keyframes (FLUX.1 schnell + Leonardo Phoenix).
5. Renders 24fps motion clips with SHA-256 caching (FFmpeg Ken Burns / Wan 2.2).
6. Masters vertical (9:16) and horizontal (16:9) cuts (-14 LUFS, True Peak <= -1.0 dBFS, 2.5s AI End Card).

Usage:
    python run.py                   # Run end-to-end production master
    python run.py --dry-run         # Validate contract & check asset availability
    python run.py --stage narration # Run specific stage (schema, narration, music, curate, shots, master)
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from schema.validate import validate_storyboard

STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"
SCHEMA_PATH = PROJECT_ROOT / "schema" / "storyboard.schema.json"


def step_banner(step_num: int, total_steps: int, title: str):
    print(f"\n{'='*75}")
    print(f"[{step_num}/{total_steps}] 🚀 {title}")
    print(f"{'='*75}\n")


def run_stage_script(cmd_args: list, stage_name: str) -> bool:
    """Executes a pipeline stage script and handles return codes cleanly."""
    print(f"[STAGE: {stage_name}] Running: {' '.join(cmd_args)}")
    proc = subprocess.run(cmd_args, cwd=str(PROJECT_ROOT))
    if proc.returncode != 0:
        print(f"\n[ERROR] Stage '{stage_name}' failed with exit code {proc.returncode}!", file=sys.stderr)
        return False
    return True


def dry_run():
    """Validates contract and checks asset health without invoking external APIs."""
    print("\n" + "="*75)
    print("🔍 PERFORMING PIPELINE DRY-RUN & CONTRACT AUDIT")
    print("="*75 + "\n")

    # 1. Validate Schema
    print("[1/5] Validating storyboard.json against schema...")
    if not validate_storyboard(str(STORYBOARD_PATH), str(SCHEMA_PATH)):
        return False
    print("      ✓ Storyboard contract is strictly valid.")

    # 2. Check storyboard metrics
    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        sb = json.load(f)
    shots = sb.get("shots", [])
    total_dur = sum(float(s["duration_s"]) for s in shots)
    print(f"[2/5] Storyboard Structure: {len(shots)} narrative shots, {total_dur:.2f}s total duration.")
    if total_dur < 60.0 or total_dur > 90.0:
        print(f"[ERROR] Duration {total_dur:.2f}s violates the 60–90s contract!", file=sys.stderr)
        return False
    print("      ✓ Duration conforms strictly to the 60.0s – 90.0s requirement.")

    # 3. Check audio cache health
    narration_dir = PROJECT_ROOT / "outputs" / "audio"
    existing_stems = list(narration_dir.glob("narration_*.wav")) if narration_dir.exists() else []
    print(f"[3/5] Narration Stems: Found {len(existing_stems)} cached audio files in outputs/audio.")

    # 4. Check keyframe pools
    curated_dir = PROJECT_ROOT / "outputs" / "keyframes_curated"
    flux_dir = PROJECT_ROOT / "outputs" / "keyframes"
    leo_dir = PROJECT_ROOT / "outputs" / "keyframes_leonardo"
    print(f"[4/5] Visual Keyframes:")
    print(f"      - Curated master frames: {len(list(curated_dir.glob('*.png')))} found in outputs/keyframes_curated")
    print(f"      - FLUX.1 pool: {len(list(flux_dir.glob('*.png')))} found in outputs/keyframes")
    print(f"      - Leonardo Phoenix pool: {len(list(leo_dir.glob('*.jpg')))} found in outputs/keyframes_leonardo")

    # 5. Check master outputs
    final_dir = PROJECT_ROOT / "outputs" / "final"
    v_master = final_dir / "final_master_9_16.mp4"
    h_master = final_dir / "final_master_16_9.mp4"
    print(f"[5/5] Final Deliverables:")
    print(f"      - Vertical Master (9:16): {'EXISTS (' + str(round(v_master.stat().st_size / 1e6, 2)) + ' MB)' if v_master.exists() else 'NOT BUILT'}")
    print(f"      - Horizontal Master (16:9): {'EXISTS (' + str(round(h_master.stat().st_size / 1e6, 2)) + ' MB)' if h_master.exists() else 'NOT BUILT'}")

    print("\n[SUCCESS] Dry-run passed. System is ready for full production runs.\n")
    return True


def run_pipeline(stage_filter: str = None, aspect: str = "both") -> bool:
    """Executes the full end-to-end production pipeline."""
    total_steps = 6

    # Step 1: Validate Schema
    if stage_filter in (None, "schema"):
        step_banner(1, total_steps, "Validating Storyboard Contract")
        if not validate_storyboard(str(STORYBOARD_PATH), str(SCHEMA_PATH)):
            return False
        if stage_filter == "schema":
            return True

    # Step 2: Narration Stems
    if stage_filter in (None, "narration"):
        step_banner(2, total_steps, "Synthesizing Dual-Voice Amharic Narration")
        if not run_stage_script([sys.executable, "pipeline/narration.py"], "Narration"):
            return False
        if stage_filter == "narration":
            return True

    # Step 3: Acoustic Score Track
    if stage_filter in (None, "music"):
        step_banner(3, total_steps, "Synthesizing Culturally Authentic Ethiopian Acoustic Score")
        if not run_stage_script([sys.executable, "pipeline/music.py"], "Score Synthesis"):
            return False
        if stage_filter == "music":
            return True

    # Step 4: Keyframe Curation
    if stage_filter in (None, "curate"):
        step_banner(4, total_steps, "Curating Multi-Model Keyframes (FLUX + Leonardo)")
        if not run_stage_script([sys.executable, "pipeline/curate.py"], "Curation"):
            return False
        if stage_filter == "curate":
            return True

    # Step 5: Render Motion Clips
    if stage_filter in (None, "shots"):
        step_banner(5, total_steps, "Rendering 24fps Dynamic Motion Shots (9:16 and 16:9)")
        if not run_stage_script([sys.executable, "pipeline/shots.py"], "Motion Shots"):
            return False
        if stage_filter == "shots":
            return True

    # Step 6: Mastering & AI End Card
    if stage_filter in (None, "master"):
        step_banner(6, total_steps, "Two-Pass -14 LUFS Mastering & Ethical AI End Card")
        aspects_to_run = ["9:16", "16:9"] if aspect == "both" else [aspect]
        for asp in aspects_to_run:
            if not run_stage_script([sys.executable, "pipeline/assemble.py", "--master", "--aspect", asp], f"Master ({asp})"):
                return False
        if stage_filter == "master":
            return True

    print("\n" + "="*75)
    print("🎉 FULL PRODUCTION PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*75)
    print("Delivered Master Media:")
    print("  • Vertical Master (9:16):   outputs/final/final_master_9_16.mp4")
    print("  • Horizontal Master (16:9): outputs/final/final_master_16_9.mp4\n")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The Heritage Short — Master Production Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Audit contract and asset health without external calls")
    parser.add_argument("--stage", choices=["schema", "narration", "music", "curate", "shots", "master"], help="Execute only a specific pipeline stage")
    parser.add_argument("--aspect", choices=["9:16", "16:9", "both"], default="both", help="Target aspect ratio for assembly (default: both)")

    args = parser.parse_args()

    if args.dry_run:
        success = dry_run()
    else:
        success = run_pipeline(stage_filter=args.stage, aspect=args.aspect)

    sys.exit(0 if success else 1)
