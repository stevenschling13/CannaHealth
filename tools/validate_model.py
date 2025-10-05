#!/usr/bin/env python3
"""Simple validator ensuring that the model directory contains metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def validate(model_dir: Path) -> int:
    manifest = model_dir / "model.json"
    if not manifest.exists():
        print(f"Missing manifest: {manifest}", file=sys.stderr)
        return 1
    try:
        data = json.loads(manifest.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        print(f"Invalid JSON in manifest: {exc}", file=sys.stderr)
        return 1

    if "labels" not in data or not isinstance(data["labels"], list):
        print("Manifest missing 'labels' list", file=sys.stderr)
        return 1

    print(f"Validated model with {len(data['labels'])} labels")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate model manifest")
    parser.add_argument("--model-dir", type=Path, required=True)
    args = parser.parse_args()
    return validate(args.model_dir)


if __name__ == "__main__":
    raise SystemExit(main())
