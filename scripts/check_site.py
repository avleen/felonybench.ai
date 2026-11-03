"""Check the built site: no broken values in its pages, and every redirect complete and live."""
import argparse
import re
import sys
from pathlib import Path

from scripts.rubric import ROOT

DIST = ROOT / "site" / "dist"
BROKEN = re.compile(r"\bNaN\b|\bundefined\b|Invalid Date|\[object Object\]")
SCRIPT = re.compile(r"<script\b.*?</script>", re.S)  # scripts can legitimately say `undefined`


def broken_values(dist: Path) -> list[str]:
    errors = []
    for page in sorted(dist.rglob("*.html")):
        found = set(BROKEN.findall(SCRIPT.sub("", page.read_text())))
        if found:
            errors.append(f"{page.relative_to(dist)}: contains {sorted(found)}")
    return errors


def _target_exists(dist: Path, target: str) -> bool:
    path = dist / target.lstrip("/")
    return path.is_file() or (path / "index.html").is_file()


def redirect_errors(dist: Path) -> list[str]:
    """Pages redirect with and without a trailing slash, because Cloudflare treats them as different paths."""
    rules = {}
    file = dist / "_redirects"
    for line in file.read_text().splitlines() if file.exists() else []:
        if line.strip() and not line.startswith("#"):
            source, target, *_ = line.split()
            rules[source] = target
    errors = []
    for source, target in rules.items():
        if not _target_exists(dist, target):
            errors.append(f"_redirects: {source} goes to {target}, which doesn't exist")
        if _target_exists(dist, source):
            errors.append(f"_redirects: {source} is also a real page, so it would never redirect")
        if not Path(source).suffix:
            twin = source.removesuffix("/") if source.endswith("/") else f"{source}/"
            if twin not in rules:
                errors.append(f"_redirects: {source} has no rule for {twin}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=DIST)
    args = parser.parse_args(argv)
    if not (args.dist / "index.html").is_file():
        print(f"No built site at {args.dist}", file=sys.stderr)
        return 1
    errors = broken_values(args.dist) + redirect_errors(args.dist)
    for error in errors:
        print(error, file=sys.stderr)
    print(f"Built site: {len(errors)} problems.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
