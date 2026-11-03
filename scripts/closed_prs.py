"""Snapshot agent PRs that were closed without merging, so the agent doesn't resubmit them."""
import json
import subprocess
import sys
from pathlib import Path

from scripts.rubric import ROOT

OUT = ROOT / ".agent-out" / "closed"
FIELDS = "number,title,headRefName,mergedAt,closedAt,url,comments"


def rejected(prs: list[dict]) -> list[dict]:
    return [p for p in prs if not p.get("mergedAt") and p.get("headRefName", "").startswith("agent/")]


def closing_reason(pr: dict) -> str:
    """The last comment a person left on the PR, if any."""
    comments = [
        c for c in pr.get("comments") or []
        if (c.get("author") or {}).get("login") not in (None, "github-actions", "app/github-actions")
    ]
    return comments[-1].get("body", "").strip() if comments else ""


def render(pr: dict) -> str:
    reason = closing_reason(pr) or "No reason recorded."
    return f"# {pr['title']}\n\nPR #{pr['number']}, closed {pr.get('closedAt')} without merging: {pr.get('url')}\n\nReason: {reason}\n"


def snapshot_name(pr: dict) -> str:
    """One file per PR: an incident can be rejected twice, and each reason counts."""
    incident = pr["headRefName"].removeprefix("agent/").replace("/", "-")
    return f"{incident}-pr{pr['number']}.md"


def main() -> int:
    out = subprocess.run(
        ["gh", "pr", "list", "--label", "agent", "--state", "closed", "--limit", "200", "--json", FIELDS],
        check=True, text=True, capture_output=True, cwd=ROOT,
    ).stdout
    OUT.mkdir(parents=True, exist_ok=True)
    prs = rejected(json.loads(out))
    for pr in prs:
        (OUT / snapshot_name(pr)).write_text(render(pr))
    print(f"{len(prs)} closed agent PRs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
