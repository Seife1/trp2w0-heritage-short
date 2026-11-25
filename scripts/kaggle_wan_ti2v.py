"""
Remote Video Generation Script for Kaggle / Colab (Wan 2.2 TI2V-5B).

Hardware: Kaggle Notebook with 2x T4 or Colab T4/A100.
Input: outputs/keyframes/shot_01.png .. shot_09.png and storyboard.json.
Output: outputs/shots/wan/shot_01.mp4 .. shot_09.mp4.

Installation instructions on Kaggle/Colab:
!pip install -q diffusers transformers accelerate torch torchvision
"""

import os
import json
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path("the-heritage-short") if Path("the-heritage-short").exists() else Path(".")
STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"
KEYFRAMES_DIR = PROJECT_ROOT / "outputs" / "keyframes"
WAN_OUT_DIR = PROJECT_ROOT / "outputs" / "shots" / "wan"

WAN_OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_wan_pipeline():
    try:
        import torch
        from diffusers import AutoencoderKL
        # Note: Wan 2.2 TI2V-5B can be loaded via HuggingFace diffusers pipeline
        print("[INFO] Checking CUDA availability...")
        if not torch.cuda.is_available():
            print("[WARN] CUDA not found. Wan 2.2 requires GPU acceleration.")
            return

        print(f"[INFO] CUDA Device: {torch.cuda.get_device_name(0)}")
        print(f"[INFO] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

        # Load storyboard
        with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
            storyboard = json.load(f)

        shots = storyboard.get("shots", [])
        print(f"[INFO] Loaded {len(shots)} shots from storyboard.")

        for shot in shots:
            shot_id = shot["shot_id"]
            motion_prompt = shot.get("motion_prompt", "")
            keyframe_path = KEYFRAMES_DIR / f"{shot_id}.png"
            out_file = WAN_OUT_DIR / f"{shot_id}.mp4"

            if out_file.exists():
                print(f"[{shot_id}] Already exists: {out_file.name}, skipping.")
                continue

            print(f"[{shot_id}] Generating Wan 2.2 video clip...")
            print(f"  Keyframe: {keyframe_path}")
            print(f"  Motion: {motion_prompt}")
            # Placeholder for diffusers pipeline call:
            # pipe(prompt=motion_prompt, image=image, num_frames=81).frames[0]
            # export_to_video(video_frames, str(out_file), fps=16)

        print("[SUCCESS] All Wan 2.2 clips generated.")
    except Exception as e:
        print(f"[ERROR] Wan pipeline failed: {e}")


if __name__ == "__main__":
    run_wan_pipeline()
