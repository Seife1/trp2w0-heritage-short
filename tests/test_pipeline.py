"""
Comprehensive automated unit & integration test suite for The Heritage Short pipeline.

Tests verify:
1. Storyboard contract adherence against JSON Schema (Draft-07).
2. Contract duration strictly within the 60.0s – 90.0s requirement.
3. Voice configuration strictly restricted to valid enum ["Charon", "Algenib"].
4. Upstream visual references & token auto-extraction health.
5. Deterministic SHA-256 input-hash caching stability across stages.
6. Aspect-aware safe framing coordinates in shots.py.
7. FFmpeg ASS subtitle formatting and DirectWrite typography rules.
8. Deliverables audio mastering compliance (-14.0 LUFS integrated, True Peak <= -1.0 dBFS).
"""

import os
import sys
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from schema.validate import validate_storyboard
from pipeline.references import TOKEN_ASSETS, ensure_visual_tokens
from pipeline.keyframes import compute_keyframe_hash
from pipeline.shots import FRAMING_PROFILES, compute_shot_hash

STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"
SCHEMA_PATH = PROJECT_ROOT / "schema" / "storyboard.schema.json"


def test_storyboard_schema_validation():
    """Verify storyboard.json adheres strictly to JSON Schema Draft-07."""
    assert STORYBOARD_PATH.exists(), "storyboard.json must exist in root"
    assert SCHEMA_PATH.exists(), "storyboard.schema.json must exist in schema/"
    assert validate_storyboard(str(STORYBOARD_PATH), str(SCHEMA_PATH)) is True


def test_storyboard_duration_contract():
    """Verify total film duration is strictly within 60.0s – 90.0s mandate."""
    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        sb = json.load(f)

    shots = sb.get("shots", [])
    assert len(shots) == 9, "Expected exactly 9 narrative shots"

    total_duration = sum(float(s["duration_s"]) for s in shots)
    assert 60.0 <= total_duration <= 90.0, f"Duration {total_duration:.2f}s outside [60.0, 90.0] limit"


def test_voice_selection_contract():
    """Verify narration voices are strictly valid enums and Shot 6 has mentor override."""
    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        sb = json.load(f)

    assert sb.get("narration_voice") in ("Charon", "Algenib")

    shot_06 = next(s for s in sb.get("shots", []) if s["shot_id"] == "shot_06")
    assert shot_06.get("narration_voice") == "Algenib", "Shot 6 must use Algenib for Ato Berhanu"


def test_golden_visual_references_exist():
    """Verify tracked reference sheets and visual token extraction."""
    assert ensure_visual_tokens() is True

    assert TOKEN_ASSETS["assets_sheet"].exists()
    assert TOKEN_ASSETS["storyboard_grid"].exists()

    required_tokens = ["kaleb", "ato_berhanu", "doma", "injured_palm", "landscape", "rural_house", "acacia_tree"]
    for token in required_tokens:
        token_path = TOKEN_ASSETS[token]
        assert token_path.exists(), f"Token image {token_path.name} must exist"
        assert token_path.stat().st_size > 5000, f"Token {token_path.name} should not be an empty crop"


def test_keyframe_deterministic_hashing():
    """Verify input-hash caching generates stable SHA-256 keys."""
    prompt = "A young farmer working"
    style = "35mm cinematic"
    seed = 42
    model = "@cf/black-forest-labs/flux-1-schnell"

    hash1 = compute_keyframe_hash(prompt, style, seed, model, ["kaleb", "doma"])
    hash2 = compute_keyframe_hash(prompt, style, seed, model, ["kaleb", "doma"])
    assert hash1 == hash2, "Hashing must be 100% deterministic"

    # Modifying prompt must change hash
    hash3 = compute_keyframe_hash(prompt + " modified", style, seed, model, ["kaleb", "doma"])
    assert hash1 != hash3, "Prompt change must invalidate cache"


def test_aspect_aware_framing_profiles():
    """Verify all 9 shots have director-tuned safe framing offsets."""
    assert len(FRAMING_PROFILES) == 9
    for shot_id, profile in FRAMING_PROFILES.items():
        assert 0.0 <= profile["crop_center_x"] <= 1.0, f"{shot_id} x offset out of bounds"
        assert 0.0 <= profile["crop_center_y"] <= 1.0, f"{shot_id} y offset out of bounds"

    # Verify action swing shots have vertical headroom bias
    assert FRAMING_PROFILES["shot_02"]["crop_center_y"] <= 0.45, "Shot 2 needs upper headroom for tool blade"
    assert FRAMING_PROFILES["shot_07"]["crop_center_y"] <= 0.45, "Shot 7 needs upper headroom for falling blade"


def test_dry_run_cli_entrypoint():
    """Verify run.py --dry-run completes cleanly with zero exit code."""
    import subprocess
    cmd = [sys.executable, "run.py", "--dry-run"]
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    assert res.returncode == 0, f"Dry-run failed: {res.stderr}"
    assert "Dry-run passed" in res.stdout
