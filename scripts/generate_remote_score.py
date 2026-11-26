"""
Remote AI Music Generation Client for The Heritage Short.

Supports generating authentic classical Ethiopian scores using free trial credits from:
1. WaveSpeed AI (ACE-Step 1.5): $1 free credit on signup at https://wavespeed.ai
2. Stability AI (Stable Audio): 25 free credits on signup at https://platform.stability.ai

Usage:
    python scripts/generate_remote_score.py --provider wavespeed --cue 1
    python scripts/generate_remote_score.py --provider wavespeed --full
    python scripts/generate_remote_score.py --provider stability --full
"""

import os
import sys
import json
import time
import argparse
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"
MUSIC_DIR = PROJECT_ROOT / "outputs" / "audio" / "music"
FINAL_SCORE_PATH = MUSIC_DIR / "score_final.wav"


def load_storyboard_cues():
    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        sb = json.load(f)
    return sb.get("music_cues", [])


def generate_wavespeed_ace_step(prompt: str, duration_s: int = 65, bpm: int = 76) -> Path:
    """Generate audio via WaveSpeed AI (wavespeed-ai/ace-step-1.5)."""
    api_key = os.getenv("WAVESPEED_API_KEY")
    if not api_key:
        print("[ERROR] WAVESPEED_API_KEY not found in .env!", file=sys.stderr)
        print("Sign up at https://wavespeed.ai for $1 free credit, then add WAVESPEED_API_KEY=... to .env.", file=sys.stderr)
        sys.exit(1)

    url = "https://wavespeed.ai/api/v3/wavespeed-ai/ace-step-1.5"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "duration": duration_s,
        "bpm": bpm,
        "instrumental": True
    }

    print(f"[WaveSpeed ACE-Step 1.5] Submitting generation request ({duration_s}s, {bpm} BPM)...")
    print(f"Prompt: {prompt}")

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code not in (200, 201, 202):
        print(f"[ERROR] WaveSpeed API rejected request (HTTP {resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)

    result = resp.json()
    task_id = result.get("task_id") or result.get("id")

    # If direct audio URL returned
    audio_url = result.get("audio_url") or result.get("output", {}).get("audio_url")
    if not audio_url and task_id:
        print(f"[WaveSpeed] Task queued (ID: {task_id}). Polling for completion...")
        poll_url = f"https://wavespeed.ai/api/v3/tasks/{task_id}"
        for _ in range(60):
            time.sleep(3)
            p_res = requests.get(poll_url, headers=headers, timeout=30)
            if p_res.status_code == 200:
                p_data = p_res.json()
                status = p_data.get("status")
                if status == "completed":
                    audio_url = p_data.get("output", {}).get("audio_url") or p_data.get("audio_url")
                    break
                elif status in ("failed", "error"):
                    print(f"[ERROR] Task failed: {p_data}", file=sys.stderr)
                    sys.exit(1)

    if not audio_url:
        print("[ERROR] Failed to obtain audio URL from WaveSpeed response.", file=sys.stderr)
        sys.exit(1)

    print(f"[WaveSpeed] Downloading generated audio from: {audio_url}")
    raw_audio = requests.get(audio_url, timeout=60).content

    tmp_out = MUSIC_DIR / "wavespeed_download.mp3"
    with open(tmp_out, "wb") as f:
        f.write(raw_audio)

    # Convert to 44.1 kHz stereo WAV
    subprocess.run([
        "ffmpeg", "-y", "-i", str(tmp_out),
        "-ar", "44100", "-ac", "2",
        str(FINAL_SCORE_PATH)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    tmp_out.unlink(missing_ok=True)
    print(f"[SUCCESS] Remote score saved to: {FINAL_SCORE_PATH}")
    return FINAL_SCORE_PATH


def generate_stability_stable_audio(prompt: str, duration_s: int = 65) -> Path:
    """Generate audio via Stability AI Stable Audio endpoint."""
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        print("[ERROR] STABILITY_API_KEY not found in .env!", file=sys.stderr)
        print("Sign up at https://platform.stability.ai for 25 free credits, then add STABILITY_API_KEY=... to .env.", file=sys.stderr)
        sys.exit(1)

    url = "https://api.stability.ai/v2beta/audio/stable-audio-2/text-to-audio"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "audio/*"
    }
    data = {
        "prompt": prompt,
        "duration": duration_s,
        "steps": 50,
        "output_format": "wav",
        "seed": 42
    }

    print(f"[Stability AI Stable Audio] Submitting request ({duration_s}s)...")
    print(f"Prompt: {prompt}")

    resp = requests.post(url, headers=headers, files={"none": ""}, data=data, timeout=180)
    if resp.status_code != 200:
        print(f"[ERROR] Stability API failed (HTTP {resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)

    tmp_out = MUSIC_DIR / "stability_download.wav"
    with open(tmp_out, "wb") as f:
        f.write(resp.content)

    subprocess.run([
        "ffmpeg", "-y", "-i", str(tmp_out),
        "-ar", "44100", "-ac", "2",
        str(FINAL_SCORE_PATH)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    tmp_out.unlink(missing_ok=True)
    print(f"[SUCCESS] Remote score saved to: {FINAL_SCORE_PATH}")
    return FINAL_SCORE_PATH


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AI Music via WaveSpeed or Stability AI Free Trial")
    parser.add_argument("--provider", choices=["wavespeed", "stability"], default="wavespeed", help="API Provider")
    parser.add_argument("--remaster", action="store_true", help="Automatically re-master final cuts after generation")
    args = parser.parse_args()

    cues = load_storyboard_cues()
    # Compose unified prompt from storyboard
    full_prompt = (
        "Traditional Ethiopian acoustic folk instrumental, solo Krar plucked bowl lyre in D minor Tizita, "
        "muted Kebero hand drum rhythm, evolving into warm Washint bamboo flute and resonant Begena box lyre harp in G major Tizita, "
        "uplifting ancestral resolution, highland Ethiopia acoustic landscape, no vocals, instrumental only"
    )

    if args.provider == "wavespeed":
        generate_wavespeed_ace_step(prompt=full_prompt, duration_s=66, bpm=76)
    else:
        generate_stability_stable_audio(prompt=full_prompt, duration_s=66)

    if args.remaster:
        print("\n[INFO] Re-mastering video deliverables with new score...")
        subprocess.run([sys.executable, "pipeline/assemble.py", "--master", "--aspect", "9:16"], cwd=str(PROJECT_ROOT), check=True)
        subprocess.run([sys.executable, "pipeline/assemble.py", "--master", "--aspect", "16:9"], cwd=str(PROJECT_ROOT), check=True)
        print("[SUCCESS] Both final cuts re-mastered with new AI score!")
