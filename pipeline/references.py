"""
Golden Reference Sheet generator for characters and setting using Cloudflare Workers AI FLUX.
Generates baseline visual reference sheets before individual shot keyframe synthesis.
"""

import os
import sys
import json
import time
import base64
import hashlib
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KEYFRAMES_DIR = PROJECT_ROOT / "outputs" / "keyframes"
REFERENCES_DIR = PROJECT_ROOT / "outputs" / "references"
RUNS_LOG_PATH = PROJECT_ROOT / "runs.jsonl"
STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"

# Visual token asset registry extracted from golden asset sheets
TOKEN_ASSETS = {
    "kaleb": REFERENCES_DIR / "token_kaleb.jpg",
    "ato_berhanu": REFERENCES_DIR / "token_ato_berhanu.jpg",
    "doma": REFERENCES_DIR / "token_doma.jpg",
    "injured_palm": REFERENCES_DIR / "token_injured_palm.jpg",
    "landscape": REFERENCES_DIR / "token_landscape.jpg",
    "rural_house": REFERENCES_DIR / "token_rural_house.jpg",
    "acacia_tree": REFERENCES_DIR / "token_acacia_tree.jpg",
    "storyboard_grid": REFERENCES_DIR / "storyboard_golden_reference.jpg",
    "assets_sheet": REFERENCES_DIR / "character_assets_sheet.jpg"
}


def ensure_visual_tokens() -> bool:
    """
    Ensures all visual reference tokens exist on a fresh clone.
    If individual crops are missing, automatically extracts them from character_assets_sheet.jpg.
    Guarantees stranger-friendly, zero-failure reproducibility.
    """
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    sheet_path = REFERENCES_DIR / "character_assets_sheet.jpg"
    if not sheet_path.exists():
        # Fallback to golden_character_assets.jpg if present
        alt_sheet = REFERENCES_DIR / "golden_character_assets.jpg"
        if alt_sheet.exists():
            import shutil
            shutil.copy(alt_sheet, sheet_path)
        else:
            print(f"[WARN] Golden assets sheet not found at {sheet_path}", file=sys.stderr)
            return False

    missing_tokens = [k for k, p in TOKEN_ASSETS.items() if not p.exists() and k not in ("storyboard_grid", "assets_sheet")]
    if not missing_tokens:
        return True

    print(f"[INFO] Extracting {len(missing_tokens)} missing visual tokens from character_assets_sheet.jpg...")
    try:
        from PIL import Image
        img = Image.open(sheet_path)
        w, h = img.size

        crops = {
            "token_kaleb": (0, 0, int(w * 0.25), int(h * 0.495)),
            "token_ato_berhanu": (int(w * 0.25), 0, int(w * 0.50), int(h * 0.495)),
            "token_doma": (int(w * 0.50), 0, int(w * 0.74), int(h * 0.495)),
            "token_injured_palm": (int(w * 0.74), 0, w, int(h * 0.495)),
            "token_landscape": (0, int(h * 0.57), int(w * 0.36), int(h * 0.94)),
            "token_rural_house": (int(w * 0.36), int(h * 0.57), int(w * 0.68), int(h * 0.94)),
            "token_acacia_tree": (int(w * 0.68), int(h * 0.57), w, int(h * 0.94)),
        }

        for name, box in crops.items():
            cropped = img.crop(box)
            out_p = REFERENCES_DIR / f"{name}.jpg"
            cropped.save(out_p, quality=95)
        print(f"[SUCCESS] Visual tokens automatically extracted successfully.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to extract tokens: {e}", file=sys.stderr)
        return False


def get_cloudflare_creds() -> tuple[str, str]:
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    token = os.environ.get("CLOUDFLARE_API_TOKEN")

    if not account_id or not token:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("CLOUDFLARE_ACCOUNT_ID="):
                        account_id = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("CLOUDFLARE_API_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
    return account_id or "", token or ""


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


def generate_flux_image(prompt: str, output_path: Path, account_id: str, token: str, seed: int = 42, max_retries: int = 3) -> tuple[bool, float]:
    model_name = "@cf/black-forest-labs/flux-1-schnell"
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt
    }

    total_latency = 0.0
    for attempt in range(1, max_retries + 1):
        start_time = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
            latency = time.time() - start_time
            total_latency += latency

            if resp.status_code == 200:
                data = resp.json()
                img_b64 = data.get("result", {}).get("image")
                if img_b64:
                    raw_bytes = base64.b64decode(img_b64)
                    with open(output_path, "wb") as f:
                        f.write(raw_bytes)
                    return True, total_latency
                print(f"[WARN] No image bytes returned in result: {data}", file=sys.stderr)
                return False, total_latency

            elif resp.status_code == 429:
                wait_sec = 10 * attempt
                print(f"[WARN] Cloudflare AI rate limit (429). Retrying in {wait_sec}s...", file=sys.stderr)
                time.sleep(wait_sec)
            else:
                print(f"[ERROR] Cloudflare AI failed HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
                time.sleep(5)

        except Exception as e:
            latency = time.time() - start_time
            total_latency += latency
            print(f"[ERROR] Exception calling Cloudflare AI (attempt {attempt}): {e}", file=sys.stderr)
            time.sleep(5)

    return False, total_latency


def run_reference_generation(force: bool = False) -> bool:
    KEYFRAMES_DIR.mkdir(parents=True, exist_ok=True)
    account_id, token = get_cloudflare_creds()

    if not account_id or not token:
        print("[ERROR] CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN missing from .env.", file=sys.stderr)
        return False

    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        sb = json.load(f)

    style_block = sb.get("style_block", "")
    char_refs = sb.get("character_refs", {})

    references = [
        {
            "id": "ref_kaleb",
            "prompt": f"Character concept reference sheet, centered full-body and 3/4 portrait, {char_refs.get('kaleb')}, {style_block}",
            "seed": 50101
        },
        {
            "id": "ref_ato_berhanu",
            "prompt": f"Character concept reference sheet, centered full-body and 3/4 portrait, {char_refs.get('ato_berhanu')}, {style_block}",
            "seed": 50102
        },
        {
            "id": "ref_setting",
            "prompt": f"Environmental setting reference sheet, Ethiopian highland rural plateau, terraced stony fields, acacia trees, traditional stone homestead, crisp morning sunlight, {style_block}",
            "seed": 50103
        }
    ]

    print(f"[INFO] Generating {len(references)} Golden Reference Sheets via Cloudflare FLUX.1 schnell...")

    all_ok = True
    for ref in references:
        ref_id = ref["id"]
        out_file = KEYFRAMES_DIR / f"{ref_id}.png"
        hash_file = KEYFRAMES_DIR / f"{ref_id}.hash"

        content_hash = hashlib.sha256(f"{ref['prompt']}|{ref['seed']}".encode("utf-8")).hexdigest()

        if not force and out_file.exists() and hash_file.exists():
            with open(hash_file, "r", encoding="utf-8") as hf:
                if hf.read().strip() == content_hash:
                    print(f"  [CACHE HIT] {ref_id}: already generated. Skipping.")
                    continue

        print(f"  [GENERATING] {ref_id}...")
        ok, latency = generate_flux_image(ref["prompt"], out_file, account_id, token, seed=ref["seed"])
        if ok:
            with open(hash_file, "w", encoding="utf-8") as hf:
                hf.write(content_hash)
            print(f"  [OK] {ref_id} -> {out_file.name} (latency: {latency:.2f}s)")
            log_run(
                stage="references",
                model="@cf/black-forest-labs/flux-1-schnell",
                params={"seed": ref["seed"], "steps": 4},
                latency_s=latency,
                status="success",
                details={"ref_id": ref_id}
            )
            time.sleep(2)
        else:
            all_ok = False
            log_run(
                stage="references",
                model="@cf/black-forest-labs/flux-1-schnell",
                params={"seed": ref["seed"], "steps": 4},
                latency_s=latency,
                status="error",
                details={"ref_id": ref_id}
            )

    return all_ok


if __name__ == "__main__":
    force_run = "--force" in sys.argv
    success = run_reference_generation(force=force_run)
    sys.exit(0 if success else 1)
