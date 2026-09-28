"""Load the versioned scoring rubric."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUBRIC = ROOT / "rubric" / "v1.yaml"


def load_rubric(path: Path = DEFAULT_RUBRIC) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)
