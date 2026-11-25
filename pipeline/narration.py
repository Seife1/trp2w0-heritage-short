"""
Line-by-line narration generation stage using Google Gemini TTS API.
Enforces SHA-256 caching and append-only logging to runs.jsonl.
"""

import os
import sys
import json
import time
import hashlib
import wave
import requests
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from schema.validate import validate_storyboard

STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"
AUDIO_DIR = PROJECT_ROOT / "outputs" / "audio"
RUNS_LOG_PATH = PROJECT_ROOT / "runs.jsonl"


def get_gemini_api_key() -> str:
    # Check environment variable or .env file
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()
    
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def get_audio_duration_seconds(file_path: Path) -> float:
    try:
        with wave.open(str(file_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return round(frames / float(rate), 2)
    except Exception:
        return 0.0


def log_run(stage: str, model: str, params: dict, latency_s: float, status: str, details: dict):
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stage": stage,
        "model": model,
        "params": params,
        "latency_s": round(latency_s, 3),
        "status": status,
        "details": details
    }
    with open(RUNS_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def generate_tts_gemini(text: str, output_wav: Path, api_key: str, voice_name: str = "Puck", max_retries: int = 3) -> tuple[bool, float, str]:
    """
    Call Gemini Speech Generation / Flash TTS endpoint.
    Cascades through fallback models: gemini-3.8-flash-tts -> gemini-3.8-flash-lite-tts -> gemini-2.5-flash-preview-tts.
    """
    candidate_models = [
        "gemini-3.8-flash-tts",
        "gemini-3.8-flash-lite-tts",
        "gemini-2.5-flash-preview-tts"
    ]
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": text}
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name
                    }
                }
            }
        }
    }

    total_latency = 0.0
    for model_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        for attempt in range(1, max_retries + 1):
            start_time = time.time()
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
                latency = time.time() - start_time
                total_latency += latency

                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            if "inlineData" in part and part["inlineData"].get("mimeType", "").startswith("audio/"):
                                import base64
                                raw_audio = base64.b64decode(part["inlineData"]["data"])
                                if not raw_audio.startswith(b"RIFF"):
                                    with wave.open(str(output_wav), "wb") as wf:
                                        wf.setnchannels(1)
                                        wf.setsampwidth(2)
                                        wf.setframerate(24000)
                                        wf.writeframes(raw_audio)
                                else:
                                    with open(output_wav, "wb") as f:
                                        f.write(raw_audio)
                                return True, total_latency, model_name
                    print(f"[WARN] No audio bytes returned in response: {data}", file=sys.stderr)
                    break

                elif resp.status_code == 429:
                    err_msg = resp.text
                    if "per day limit exceeded" in err_msg or "daily" in err_msg.lower():
                        print(f"[WARN] Model {model_name} exceeded daily quota. Falling back to next model...", file=sys.stderr)
                        break  # Fall back immediately to next candidate model
                    wait_sec = 15
                    print(f"[WARN] {model_name} rate limit on attempt {attempt}/{max_retries}. Backing off {wait_sec}s...", file=sys.stderr)
                    time.sleep(wait_sec)

                elif resp.status_code == 503:
                    wait_sec = attempt * 5
                    print(f"[WARN] {model_name} 503 unavailable. Retrying in {wait_sec}s...", file=sys.stderr)
                    time.sleep(wait_sec)

                else:
                    print(f"[ERROR] {model_name} failed HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
                    break

            except Exception as e:
                latency = time.time() - start_time
                total_latency += latency
                print(f"[ERROR] Exception calling {model_name}: {e}", file=sys.stderr)
                time.sleep(3)

    return False, total_latency, ""


def run_narration_pipeline(force: bool = False) -> bool:
    if not validate_storyboard(str(STORYBOARD_PATH)):
        print("[ERROR] Storyboard validation failed. Aborting narration.", file=sys.stderr)
        return False

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    api_key = get_gemini_api_key()

    if not api_key:
        print("[ERROR] GEMINI_API_KEY not found in environment or .env file.", file=sys.stderr)
        print("Please set your GEMINI_API_KEY in the-heritage-short/.env", file=sys.stderr)
        return False

    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    shots = storyboard.get("shots", [])
    print(f"[INFO] Generating narration for {len(shots)} shots using Gemini Flash TTS...")

    all_success = True
    for shot in shots:
        shot_id = shot["shot_id"]
        text = shot["narration_text"]
        out_file = AUDIO_DIR / f"narration_{shot_id}.wav"
        hash_file = AUDIO_DIR / f"narration_{shot_id}.hash"

        # Compute SHA-256 of text + voice settings
        voice_name = "Puck"
        content_hash = hashlib.sha256(f"{text}|{voice_name}".encode("utf-8")).hexdigest()

        # Check Cache
        if not force and out_file.exists() and hash_file.exists():
            with open(hash_file, "r", encoding="utf-8") as hf:
                cached_hash = hf.read().strip()
            if cached_hash == content_hash:
                dur = get_audio_duration_seconds(out_file)
                print(f"  [CACHE HIT] {shot_id}: already generated ({dur}s). Skipping.")
                continue

        print(f"  [GENERATING] {shot_id}: '{text}'...")
        success, latency, used_model = generate_tts_gemini(text, out_file, api_key, voice_name=voice_name)

        if success:
            with open(hash_file, "w", encoding="utf-8") as hf:
                hf.write(content_hash)
            dur = get_audio_duration_seconds(out_file)
            print(f"  [OK] {shot_id} -> {out_file.name} (model: {used_model}, latency: {latency:.2f}s, duration: {dur}s)")
            log_run(
                stage="narration",
                model=used_model,
                params={"voice": voice_name, "language": "am"},
                latency_s=latency,
                status="success",
                details={"shot_id": shot_id, "text": text, "duration_s": dur}
            )
            # Polite pacing between generation calls
            time.sleep(12)
        else:
            all_success = False
            log_run(
                stage="narration",
                model="gemini-3.8-flash-tts",
                params={"voice": voice_name, "language": "am"},
                latency_s=latency,
                status="error",
                details={"shot_id": shot_id, "text": text}
            )

    return all_success


if __name__ == "__main__":
    force_run = "--force" in sys.argv
    success = run_narration_pipeline(force=force_run)
    sys.exit(0 if success else 1)
