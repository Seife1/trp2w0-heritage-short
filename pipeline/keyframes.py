"""
Keyframe generation pipeline using Cloudflare Workers AI.
Supports A/B testing between:
- Model A (Baseline): FLUX.1 schnell (@cf/black-forest-labs/flux-1-schnell) -> outputs/keyframes/
- Model B (A/B Test): Leonardo AI Phoenix 1.0 (@cf/leonardo/phoenix-1.0) -> outputs/keyframes_leonardo/

Conditions each shot on storyboard.json prompts, root character references,
and fixed style block, enforcing deterministic SHA-256 input-hash caching.
"""

import os
import sys
import json
import time
import base64
import hashlib
import requests
import argparse
from contextlib import ExitStack
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from schema.validate import validate_storyboard

STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"
RUNS_LOG_PATH = PROJECT_ROOT / "runs.jsonl"

MODELS_CONFIG = {
    "flux": {
        "model_id": "@cf/black-forest-labs/flux-1-schnell",
        "output_dir": PROJECT_ROOT / "outputs" / "keyframes",
        "name": "FLUX.1 schnell",
        "multipart": False,
    },
    "leonardo": {
        "model_id": "@cf/leonardo/phoenix-1.0",
        "output_dir": PROJECT_ROOT / "outputs" / "keyframes_leonardo",
        "name": "Leonardo AI Phoenix 1.0",
        "multipart": False,
    },
    "klein": {
        "model_id": "@cf/black-forest-labs/flux-2-klein-4b",
        "output_dir": PROJECT_ROOT / "outputs" / "keyframes_klein",
        "name": "FLUX.2 [klein] 4B (Multi-Ref)",
        "multipart": True,
    },
}


def resolve_reference_tokens(refs_involved: list[str], keyframe_prompt: str = "", shot_type: str = "") -> list[tuple[str, Path]]:
    """
    Resolve up to 4 visual reference token files (<=512x512) for image-conditioned generation.
    Prioritizes explicit character_refs, then adds doma/landscape tokens when relevant.
    """
    ordered_names = list(refs_involved or [])
    prompt_lower = keyframe_prompt.lower()
    if ("doma" in prompt_lower or "pickaxe" in prompt_lower or "handle" in prompt_lower) and "doma" not in ordered_names:
        ordered_names.append("doma")
    if shot_type == "wide" and "landscape" not in ordered_names:
        ordered_names.append("landscape")

    resolved = []
    seen = set()
    for name in ordered_names:
        if name in seen:
            continue
        t_path = PROJECT_ROOT / "outputs" / "references" / f"token_{name}.jpg"
        if t_path.exists():
            resolved.append((name, t_path))
            seen.add(name)
        if len(resolved) >= 4:
            break
    return resolved


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


def compute_keyframe_hash(prompt: str, style_block: str, seed: int, model_id: str, ref_tokens: list[str] = None) -> str:
    """
    Deterministic input-hash caching.
    Incorporates prompt, style block, seed, model parameters, and content hashes
    of extracted visual reference tokens (Kaleb, Ato Berhanu, Doma, Landscape).
    """
    hasher = hashlib.sha256()
    hasher.update(prompt.encode("utf-8"))
    hasher.update(style_block.encode("utf-8"))
    hasher.update(str(seed).encode("utf-8"))
    hasher.update(model_id.encode("utf-8"))

    if ref_tokens:
        for token_name in sorted(ref_tokens):
            token_path = PROJECT_ROOT / "outputs" / "references" / f"token_{token_name}.jpg"
            if token_path.exists():
                with open(token_path, "rb") as tf:
                    hasher.update(tf.read())
            else:
                hasher.update(token_name.encode("utf-8"))

    return hasher.hexdigest()


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


def generate_keyframe(
    prompt: str,
    output_path: Path,
    account_id: str,
    token: str,
    model_type: str = "flux",
    ref_tokens: list[tuple[str, Path]] = None,
    max_retries: int = 3,
) -> tuple[bool, float]:
    cfg = MODELS_CONFIG[model_type]
    model_id = cfg["model_id"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_id}"
    is_multipart = cfg.get("multipart", False)

    total_latency = 0.0
    for attempt in range(1, max_retries + 1):
        start_time = time.time()
        try:
            if is_multipart:
                headers = {"Authorization": f"Bearer {token}"}
                with ExitStack() as stack:
                    files = {
                        "prompt": (None, prompt),
                        "width": (None, "1024"),
                        "height": (None, "1024"),
                    }
                    for idx, (_, ref_path) in enumerate((ref_tokens or [])[:4]):
                        fh = stack.enter_context(open(ref_path, "rb"))
                        files[f"input_image_{idx}"] = (ref_path.name, fh, "image/jpeg")
                    resp = requests.post(url, headers=headers, files=files, timeout=90)
            else:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                payload = {"prompt": prompt}
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
            latency = time.time() - start_time
            total_latency += latency

            if resp.status_code == 200:
                c_type = resp.headers.get("content-type", "")
                if c_type.startswith("image/"):
                    # Direct binary image response (e.g. Leonardo Phoenix)
                    with open(output_path, "wb") as f:
                        f.write(resp.content)
                    return True, total_latency
                else:
                    # JSON base64 encoded response (e.g. FLUX)
                    data = resp.json()
                    img_b64 = data.get("result", {}).get("image")
                    if img_b64:
                        raw_bytes = base64.b64decode(img_b64)
                        with open(output_path, "wb") as f:
                            f.write(raw_bytes)
                        return True, total_latency
                    print(f"[WARN] No image bytes returned in JSON response: {data}", file=sys.stderr)
                    return False, total_latency

            elif resp.status_code == 429:
                wait_sec = 10 * attempt
                print(f"[WARN] Cloudflare 429 rate limit (attempt {attempt}/{max_retries}). Retrying in {wait_sec}s...", file=sys.stderr)
                time.sleep(wait_sec)

            elif resp.status_code >= 500:
                wait_sec = 6 * attempt
                print(f"[WARN] Cloudflare HTTP {resp.status_code} server error. Retrying in {wait_sec}s...", file=sys.stderr)
                time.sleep(wait_sec)

            else:
                print(f"[ERROR] Cloudflare AI failed HTTP {resp.status_code}: {resp.text[:300]}", file=sys.stderr)
                return False, total_latency

        except Exception as e:
            latency = time.time() - start_time
            total_latency += latency
            print(f"[ERROR] Exception calling Cloudflare AI (attempt {attempt}): {e}", file=sys.stderr)
            time.sleep(5)

    return False, total_latency


def run_keyframe_pipeline(model_type: str = "flux", force: bool = False, shot_filter: str = None) -> bool:
    if not validate_storyboard(str(STORYBOARD_PATH)):
        print("[ERROR] Storyboard validation failed. Aborting keyframes.", file=sys.stderr)
        return False

    cfg = MODELS_CONFIG[model_type]
    out_dir = cfg["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    account_id, token = get_cloudflare_creds()

    if not account_id or not token:
        print("[ERROR] CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN missing.", file=sys.stderr)
        return False

    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        sb = json.load(f)

    style_block = sb.get("style_block", "")
    char_refs = sb.get("character_refs", {})
    shots = sb.get("shots", [])

    print(f"\n{'='*70}")
    print(f"🖼️ KEYFRAME GENERATION: {cfg['name']} ({model_type.upper()})")
    print(f"Target Directory: {out_dir}")
    print(f"{'='*70}\n")

    all_ok = True
    for shot in shots:
        shot_id = shot["shot_id"]
        if shot_filter and shot_id != shot_filter:
            continue

        ext = ".png" if model_type == "flux" else ".jpg"  # klein → .jpg (direct binary from CF)
        out_file = out_dir / f"{shot_id}{ext}"
        hash_file = out_dir / f"{shot_id}.hash"

        # Build conditioned prompt linking character anchor + shot visual prompt + style block
        refs_involved = shot.get("character_refs", [])
        resolved_tokens = resolve_reference_tokens(refs_involved, shot.get("keyframe_prompt", ""), shot.get("shot_type", ""))
        char_descriptions = []
        for r in refs_involved:
            if r in char_refs:
                char_descriptions.append(char_refs[r])

        char_context = " ".join(char_descriptions)
        if char_context:
            full_prompt = f"{shot['keyframe_prompt']}, Character appearance: {char_context}, {style_block}"
        else:
            full_prompt = f"{shot['keyframe_prompt']}, {style_block}"

        if cfg.get("multipart") and resolved_tokens:
            ref_legend = ", ".join(f"image {i} shows {name}" for i, (name, _) in enumerate(resolved_tokens))
            full_prompt = f"{full_prompt}. Maintain strict visual consistency with reference tokens ({ref_legend})."

        token_names_for_hash = [name for name, _ in resolved_tokens] if cfg.get("multipart") else refs_involved
        content_hash = compute_keyframe_hash(
            full_prompt,
            style_block,
            shot.get("seed", 42),
            cfg["model_id"],
            token_names_for_hash,
        )

        # Cache check
        if not force and out_file.exists() and hash_file.exists():
            with open(hash_file, "r", encoding="utf-8") as hf:
                if hf.read().strip() == content_hash:
                    print(f"  [CACHE HIT] {shot_id}: already generated with {model_type}. Skipping.")
                    continue

        ref_note = f" [refs: {', '.join(n for n, _ in resolved_tokens)}]" if cfg.get("multipart") and resolved_tokens else ""
        print(f"  [GENERATING] {shot_id} ({shot['shot_type']}) with {cfg['name']}{ref_note}...")
        ok, latency = generate_keyframe(
            full_prompt,
            out_file,
            account_id,
            token,
            model_type=model_type,
            ref_tokens=resolved_tokens,
        )

        if ok:
            with open(hash_file, "w", encoding="utf-8") as hf:
                hf.write(content_hash)
            file_kb = round(out_file.stat().st_size / 1024, 1)
            print(f"  [OK] {shot_id} -> {out_file.name} ({file_kb} KB, latency: {latency:.2f}s)")
            log_run(
                stage="keyframes",
                model=cfg["model_id"],
                params={"shot_type": shot["shot_type"], "seed": shot.get("seed", 42), "model_type": model_type},
                latency_s=latency,
                status="success",
                details={"shot_id": shot_id, "size_kb": file_kb}
            )
            time.sleep(3)
        else:
            all_ok = False
            log_run(
                stage="keyframes",
                model=cfg["model_id"],
                params={"shot_type": shot["shot_type"], "seed": shot.get("seed", 42), "model_type": model_type},
                latency_s=latency,
                status="error",
                details={"shot_id": shot_id}
            )

    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keyframe Generation Engine")
    parser.add_argument("--model", choices=["flux", "leonardo", "klein"], default="flux", help="Model family to run")
    parser.add_argument("--force", action="store_true", help="Force re-generation even if cached")
    parser.add_argument("--shot", default=None, help="Specific shot to generate (e.g. shot_01)")

    args = parser.parse_args()
    success = run_keyframe_pipeline(model_type=args.model, force=args.force, shot_filter=args.shot)
    sys.exit(0 if success else 1)
