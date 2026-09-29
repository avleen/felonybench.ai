"""Markdown summary of org leaderboard changes between two scores.json files."""
import argparse
import json
import sys
from pathlib import Path

BOARDS = (
    ("open", "verified", "Open League (Verified)"),
    ("open", "all", "Open League (incl. Alleged)"),
    ("sandbox", "all", "Sandbox League"),
    ("accomplice", "all", "Accomplice League"),
)


def _orgs(scores: dict, league: str, tier: str) -> dict:
    rows = scores.get("boards", {}).get(league, {}).get(tier, {}).get("orgs", [])
    return {row["name"]: row for row in rows}


def _rank(row) -> str:
    return f"#{row['rank']}" if row else "—"


def render(before: dict, after: dict) -> str:
    sections = []
    for league, tier, title in BOARDS:
        old, new = _orgs(before, league, tier), _orgs(after, league, tier)
        lines = []
        for name in sorted(set(old) | set(new), key=lambda n: new.get(n, {}).get("rank", 1_000_000)):
            o, n = old.get(name), new.get(name)
            old_score, new_score = (o or {}).get("score", 0), (n or {}).get("score", 0)
            if old_score == new_score and _rank(o) == _rank(n):
                continue
            lines.append(f"| {name} | {old_score:g} → {new_score:g} | {new_score - old_score:+g} | {_rank(o)} → {_rank(n)} |")
        if lines:
            sections.append("\n".join([f"### {title}", "", "| Org | Score | Change | Rank |", "|---|---|---|---|", *lines]))
    return "## Leaderboard impact\n\n" + ("\n\n".join(sections) or "No leaderboard changes.") + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    print(render(json.loads(args.before.read_text()), json.loads(args.after.read_text())), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
