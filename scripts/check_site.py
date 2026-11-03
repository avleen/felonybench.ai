"""Check the built site: no broken values in its pages, and every redirect complete and live."""
import argparse
import re
import sys
from pathlib import Path

from scripts.rubric import ROOT

DIST = ROOT / "site" / "dist"
# `undefined` only counts as a whole value: prose can fairly say "undefined behavior".
BROKEN = re.compile(r"\bNaN\b|(?<=[>\"/])\s*undefined\s*(?=[<\"/])|Invalid Date|\[object Object\]")
SCRIPT = re.compile(r"<script\b.*?</script>", re.S)  # scripts can legitimately say `undefined`


def broken_values(dist: Path) -> list[str]:
    errors = []
    for page in sorted(dist.rglob("*.html")):
        found = {match.strip() for match in BROKEN.findall(SCRIPT.sub("", page.read_text()))}
        if found:
            errors.append(f"{page.relative_to(dist)}: contains {sorted(found)}")
    return errors


def structure_errors(dist: Path) -> list[str]:
    """An unclosed <noscript> or <script> swallows the rest of the page, and everything above still passes."""
    errors = []
    for page in sorted(dist.rglob("*.html")):
        html = page.read_text()
        name = page.relative_to(dist)
        for tag in ("noscript", "script"):
            if len(re.findall(rf"<{tag}\b", html)) != html.count(f"</{tag}>"):
                errors.append(f"{name}: unclosed <{tag}>")
        visible = re.sub(r"<noscript\b.*?</noscript>", "", html, flags=re.S)
        if not re.search(r"<main\b.*<h1\b.*</main>", visible, re.S):
            errors.append(f"{name}: no <h1> inside <main>")
    return errors


def sitemap_errors(dist: Path) -> list[str]:
    """A page can't both ask search engines to skip it and be advertised to them."""
    errors = []
    if not (dist / "sitemap-index.xml").is_file():
        errors.append("sitemap-index.xml is missing, but robots.txt points at it")
    home_listed = False
    for path in sorted(dist.glob("sitemap-[0-9]*.xml")):
        for url in re.findall(r"<loc>https?://[^/]+(/[^<]*)</loc>", path.read_text()):
            home_listed = home_listed or url == "/"
            page = dist / url.strip("/") / "index.html"
            if not page.is_file():
                errors.append(f"{path.name}: {url} has no page")
            elif re.search(r'<meta name="?robots"? content="?noindex', page.read_text()):
                errors.append(f"{path.name}: {url} is marked noindex")
    if not home_listed:
        errors.append("the sitemap doesn't list the homepage")
    return errors


def _target_exists(dist: Path, target: str) -> bool:
    path = dist / target.lstrip("/")
    return path.is_file() or (path / "index.html").is_file()


def redirect_errors(dist: Path) -> list[str]:
    """Pages redirect with and without a trailing slash, because Cloudflare treats them as different paths."""
    file = dist / "_redirects"
    if not file.exists():
        return ["_redirects: missing from the build, so every old link would 404"]
    rules, errors = {}, []
    for line in file.read_text().splitlines():
        fields = line.split()
        if not fields or fields[0].startswith("#"):
            continue
        if len(fields) < 2:
            errors.append(f"_redirects: '{line}' has no target")
        elif fields[0] in rules:  # Cloudflare uses the first match, so the later rule never fires
            errors.append(f"_redirects: {fields[0]} is listed twice")
        else:
            rules[fields[0]] = fields[1]
    for source, target in rules.items():
        if "*" in source or ":" in source:
            continue  # a pattern has no single path to check
        if target.startswith("/") and not _target_exists(dist, target):
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
    errors = broken_values(args.dist) + structure_errors(args.dist) + sitemap_errors(args.dist) + redirect_errors(args.dist)
    for error in errors:
        print(error, file=sys.stderr)
    print(f"Built site: {len(errors)} problems.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
