"""Load the versioned scoring rubric."""
from pathlib import Path

import yaml
from yaml.composer import ComposerError

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUBRIC = ROOT / "rubric" / "v1.yaml"


def load_rubric(path: Path = DEFAULT_RUBRIC) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


class _NoAliases(yaml.SafeLoader):
    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise ComposerError(None, None, "aliases aren't allowed in incident files", self.peek_event().start_mark)
        return super().compose_node(parent, index)


def load_incident_yaml(text: str):
    """safe_load for incident files. None needs an alias, and a small file of them expands to gigabytes."""
    return yaml.load(text, Loader=_NoAliases)
