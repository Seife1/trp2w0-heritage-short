"""
Schema validation utility for storyboard.json contracts.
"""

import json
import sys
from pathlib import Path
from jsonschema import Draft7Validator, validate, ValidationError


def validate_storyboard(storyboard_path: str = "storyboard.json", schema_path: str = "schema/storyboard.schema.json") -> bool:
    sb_file = Path(storyboard_path)
    sc_file = Path(schema_path)

    if not sb_file.exists():
        print(f"[ERROR] Storyboard file not found: {sb_file}", file=sys.stderr)
        return False

    if not sc_file.exists():
        print(f"[ERROR] Schema file not found: {sc_file}", file=sys.stderr)
        return False

    with open(sb_file, "r", encoding="utf-8") as f:
        storyboard_data = json.load(f)

    with open(sc_file, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    validator = Draft7Validator(schema_data)
    errors = sorted(validator.iter_errors(storyboard_data), key=lambda e: e.path)

    if errors:
        print(f"[VALIDATION FAILED] Found {len(errors)} error(s) in {storyboard_path}:", file=sys.stderr)
        for err in errors:
            loc = " -> ".join([str(p) for p in err.path]) if err.path else "root"
            print(f"  - [{loc}]: {err.message}", file=sys.stderr)
        return False

    print(f"[SUCCESS] {storyboard_path} conforms to schema contract.")
    return True


if __name__ == "__main__":
    sb = sys.argv[1] if len(sys.argv) > 1 else "storyboard.json"
    sc = sys.argv[2] if len(sys.argv) > 2 else "schema/storyboard.schema.json"
    if not validate_storyboard(sb, sc):
        sys.exit(1)
