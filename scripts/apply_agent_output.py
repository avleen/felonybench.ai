"""Copy the agent's output into a clean checkout, keeping only what it may produce.

The agent runs in its own job with no write access. This runs in the job that can write,
from trusted code, so nothing the agent did to its checkout can reach the write token.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

from scripts.rubric import ROOT

_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def _names(directory: Path, suffix: str) -> list[Path]:
    if not directory.is_dir() or directory.is_symlink():
        return []
    return sorted(
        p for p in directory.iterdir()
        if p.is_file() and not p.is_symlink() and p.suffix == suffix and _NAME.fullmatch(p.name)
    )


def apply_output(source: Path, target: Path) -> list[str]:
    """Copy incidents/*.yaml and .agent-out/*.md. Deletions and anything else are dropped."""
    copied = []
    for sub, suffix in (("incidents", ".yaml"), (".agent-out", ".md")):
        (target / sub).mkdir(parents=True, exist_ok=True)
        for path in _names(source / sub, suffix):
            shutil.copyfile(path, target / sub / path.name)
            copied.append(f"{sub}/{path.name}")
    return copied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args(argv)
    print(f"Copied {len(apply_output(args.source, ROOT))} files from the agent's output.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
