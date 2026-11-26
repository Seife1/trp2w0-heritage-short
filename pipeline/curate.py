"""
Keyframe Curation Engine for The Heritage Short.

Assembles the optimal hybrid master keyframe sequence into outputs/keyframes_curated/
by evaluating results across three generation models:
  - Model A (flux):     FLUX.1 schnell          — text-to-image, no reference images
  - Model B (leonardo): Leonardo AI Phoenix 1.0  — text-to-image, no reference images
  - Model C (klein):    FLUX.2 [klein] 4B        — image-conditioned via multipart/form-data
                        (up to 4 reference images: input_image_0..3)

Curated Selection (v2 — klein promoted to primary for character-critical shots):
- Shot 01: FLUX.2 klein 4B  (kaleb + landscape refs → landscape depth with consistent Kaleb silhouette)
- Shot 02: FLUX.2 klein 4B  (kaleb + doma refs → downward strike with correct tool form)
- Shot 03: FLUX.2 klein 4B  (kaleb + doma refs → strained grip with consistent hand anatomy)
- Shot 04: FLUX.2 klein 4B  (kaleb + doma refs → exhaustion pose with consistent figure)
- Shot 05: FLUX.2 klein 4B  (ato_berhanu ref → lifelike Gabi fabric and elder bearing)
- Shot 06: FLUX.2 klein 4B  (ato_berhanu + kaleb + doma refs → mentorship hands on shaft)
- Shot 07: FLUX.2 klein 4B  (ato_berhanu + doma refs → effortless demonstration)
- Shot 08: FLUX.2 klein 4B  (kaleb + doma refs → realization swing with consistent figure)
- Shot 09: FLUX.2 klein 4B  (ato_berhanu + kaleb + doma + landscape refs → sunset walk)
"""

import json
import sys
import shutil
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KEYFRAMES_FLUX_DIR = PROJECT_ROOT / "outputs" / "keyframes"
KEYFRAMES_LEO_DIR = PROJECT_ROOT / "outputs" / "keyframes_leonardo"
KEYFRAMES_KLEIN_DIR = PROJECT_ROOT / "outputs" / "keyframes_klein"
CURATED_DIR = PROJECT_ROOT / "outputs" / "keyframes_curated"

CURATION_MAP = {
    "shot_01": {
        "model": "FLUX.2 [klein] 4B",
        "source": KEYFRAMES_KLEIN_DIR / "shot_01.jpg",
        "rationale": "Image-conditioned on kaleb + landscape tokens: consistent Kaleb silhouette anchored in authentic terraced highland setting."
    },
    "shot_02": {
        "model": "FLUX.2 [klein] 4B",
        "source": KEYFRAMES_KLEIN_DIR / "shot_02.jpg",
        "rationale": "Image-conditioned on kaleb + doma tokens: correct tool form (single iron adze blade) and consistent figure identity."
    },
    "shot_03": {
        "model": "FLUX.2 [klein] 4B",
        "source": KEYFRAMES_KLEIN_DIR / "shot_03.jpg",
        "rationale": "Image-conditioned on kaleb + doma tokens: strained grip with consistent Kaleb hand anatomy and tool handle."
    },
    "shot_04": {
        "model": "FLUX.2 [klein] 4B",
        "source": KEYFRAMES_KLEIN_DIR / "shot_04.jpg",
        "rationale": "Image-conditioned on kaleb + doma tokens: pivotal exhaustion pose with deterministic character appearance."
    },
    "shot_05": {
        "model": "FLUX.2 [klein] 4B",
        "source": KEYFRAMES_KLEIN_DIR / "shot_05.jpg",
        "rationale": "Image-conditioned on ato_berhanu token: lifelike Gabi fabric weave and elder bearing locked to reference sheet."
    },
    "shot_06": {
        "model": "FLUX.2 [klein] 4B",
        "source": KEYFRAMES_KLEIN_DIR / "shot_06.jpg",
        "rationale": "Image-conditioned on ato_berhanu + kaleb + doma tokens (3 refs): closest to authentic mentorship hand anatomy on correct tool."
    },
    "shot_07": {
        "model": "FLUX.2 [klein] 4B",
        "source": KEYFRAMES_KLEIN_DIR / "shot_07.jpg",
        "rationale": "Image-conditioned on ato_berhanu + doma tokens: consistent elder identity demonstrating effortless technique."
    },
    "shot_08": {
        "model": "FLUX.2 [klein] 4B",
        "source": KEYFRAMES_KLEIN_DIR / "shot_08.jpg",
        "rationale": "Image-conditioned on kaleb + doma tokens: realization swing with deterministic figure and correct single-blade tool."
    },
    "shot_09": {
        "model": "FLUX.2 [klein] 4B",
        "source": KEYFRAMES_KLEIN_DIR / "shot_09.jpg",
        "rationale": "Image-conditioned on ato_berhanu + kaleb + doma + landscape tokens (4 refs): grandfather and grandson sunset walk with full scene anchoring."
    }
}


def assemble_curated_keyframes():
    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}

    print(f"\n{'='*70}")
    print("🎨 ASSEMBLING CURATED HYBRID KEYFRAME SEQUENCE")
    print(f"{'='*70}\n")

    for shot_id, info in CURATION_MAP.items():
        src = info["source"]
        dest = CURATED_DIR / f"{shot_id}.png"

        if not src.exists():
            print(f"[ERROR] Source missing for {shot_id}: {src}", file=sys.stderr)
            print(f"        Run 'python pipeline/keyframes.py --model klein' to generate keyframes first.", file=sys.stderr)
            return False

        # Standardize format to high-quality PNG
        with Image.open(src) as img:
            img = img.convert("RGB")
            img.save(dest, "PNG")

        manifest[shot_id] = {
            "model": info["model"],
            "source_file": src.name,
            "curated_file": dest.name,
            "dimensions": f"{img.width}x{img.height}",
            "rationale": info["rationale"]
        }
        print(f"[{shot_id}] Selected: {info['model']} ({src.name} -> {dest.name})")
        print(f"          Rationale: {info['rationale']}")

    manifest_path = CURATED_DIR / "curation_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[SUCCESS] Curated sequence assembled in: {CURATED_DIR}")
    print(f"          Manifest saved to: {manifest_path.name}\n")


if __name__ == "__main__":
    assemble_curated_keyframes()
