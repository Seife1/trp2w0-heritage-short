"""
Keyframe Curation Engine for The Heritage Short.

Assembles the optimal hybrid master keyframe sequence into outputs/keyframes_curated/
by evaluating the A/B test results between FLUX.1 schnell and Leonardo AI Phoenix 1.0:

Curated Selection:
- Shot 01: Leonardo Phoenix (Expansive terraced highland landscape depth)
- Shot 02: Leonardo Phoenix (Clear downward agricultural strike into rocky soil)
- Shot 03: FLUX.1 schnell (Strained knuckle grip and sweat glistening under tension)
- Shot 04: FLUX.1 schnell (Authentic physical exhaustion and resting on doma)
- Shot 05: Leonardo Phoenix (Detailed handwoven Gabi fabric texture and dignified elder poise)
- Shot 06: Leonardo Phoenix (Mentor & apprentice holding wooden shaft with anatomical clarity)
- Shot 07: FLUX.1 schnell (Ato Berhanu demonstrating fluid effortless momentum)
- Shot 08: Leonardo Phoenix (Clear figure contouring and clean soil turnover)
- Shot 09: Leonardo Phoenix (Grandfather & grandson walking along dirt path into twilight)
"""

import json
import shutil
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KEYFRAMES_FLUX_DIR = PROJECT_ROOT / "outputs" / "keyframes"
KEYFRAMES_LEO_DIR = PROJECT_ROOT / "outputs" / "keyframes_leonardo"
CURATED_DIR = PROJECT_ROOT / "outputs" / "keyframes_curated"

CURATION_MAP = {
    "shot_01": {
        "model": "Leonardo AI Phoenix 1.0",
        "source": KEYFRAMES_LEO_DIR / "shot_01.jpg",
        "rationale": "Superior panoramic terraced landscape depth and natural acacia tree distribution."
    },
    "shot_02": {
        "model": "Leonardo AI Phoenix 1.0",
        "source": KEYFRAMES_LEO_DIR / "shot_02.jpg",
        "rationale": "Clear downward strike momentum cutting into rocky furrow."
    },
    "shot_03": {
        "model": "FLUX.1 schnell",
        "source": KEYFRAMES_FLUX_DIR / "shot_03.png",
        "rationale": "Strongest emotional tension, strained knuckle grip, and authentic fatigue."
    },
    "shot_04": {
        "model": "FLUX.1 schnell",
        "source": KEYFRAMES_FLUX_DIR / "shot_04.png",
        "rationale": "Pivotal exhaustion pose resting on doma, matching proverb delivery perfectly."
    },
    "shot_05": {
        "model": "Leonardo AI Phoenix 1.0",
        "source": KEYFRAMES_LEO_DIR / "shot_05.jpg",
        "rationale": "Lifelike coarse cotton weave on Ato Berhanu's Gabi with fringed borders."
    },
    "shot_06": {
        "model": "Leonardo AI Phoenix 1.0",
        "source": KEYFRAMES_LEO_DIR / "shot_06.jpg",
        "rationale": "Intimate mentorship beat with elder and youth sharing the wooden handle."
    },
    "shot_07": {
        "model": "FLUX.1 schnell",
        "source": KEYFRAMES_FLUX_DIR / "shot_07.png",
        "rationale": "Wise elder expression and poised demonstration of effortless technique."
    },
    "shot_08": {
        "model": "Leonardo AI Phoenix 1.0",
        "source": KEYFRAMES_LEO_DIR / "shot_08.jpg",
        "rationale": "Clean figure separation and dark fertile soil breaking open smoothly."
    },
    "shot_09": {
        "model": "Leonardo AI Phoenix 1.0",
        "source": KEYFRAMES_LEO_DIR / "shot_09.jpg",
        "rationale": "Atmospheric evening twilight walk, strong companionship, 9:16 safe framing."
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
            print(f"[ERROR] Source missing for {shot_id}: {src}")
            continue

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
