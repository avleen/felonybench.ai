"""Compute scores.json from incidents/ and the rubric."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts.rubric import DEFAULT_RUBRIC, ROOT, load_rubric
from scripts.scoring import build_scores


def load_incidents(directory: Path) -> list[dict]:
    if not directory.is_dir():
        return []
    return [yaml.safe_load(p.read_text()) for p in sorted(directory.glob("*.yaml"))]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incidents", type=Path, default=ROOT / "incidents")
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC)
    parser.add_argument("--out", type=Path, default=ROOT / "scores.json")
    args = parser.parse_args(argv)

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    scores = build_scores(load_incidents(args.incidents), load_rubric(args.rubric), generated_at)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(scores, indent=2, default=str))
    print(f"Wrote {args.out} ({len(scores['incidents'])} incidents)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
