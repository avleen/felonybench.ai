"""Turn the agent's incident edits into one branch and PR per incident.

Runs in CI after Claude Code. Claude only edits files; this script owns git and gh,
so the agent never needs shell access.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

from scripts.diff import render
from scripts.rubric import ROOT, load_rubric
from scripts.score import load_incidents
from scripts.scoring import build_scores
from scripts.validate import NEWS_REQUIRED, load_validator, validate_dir

ALLOWED_PREFIXES = ("incidents/", ".agent-out/", ".agent-state/")
PR_BODY_LIMIT = 65000


def parse_porcelain(output: str) -> list[tuple[str, str]]:
    changes = []
    for line in output.splitlines():
        status, path = line[:2].strip(), line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changes.append((status, path.strip('"')))
    return changes


def disallowed(paths: list[str]) -> list[str]:
    return [p for p in paths if not p.startswith(ALLOWED_PREFIXES)]


def pr_title(incident: dict, is_new: bool) -> str:
    if not is_new:
        return f"Update: {incident['id']}"
    victims = ", ".join(v["name"] for v in incident.get("victims", []))
    return f"New felony: {incident['org']} — {victims}"


def awaiting_news(errors: list[str]) -> bool:
    """In scope and otherwise valid, just no news coverage yet: opened as a draft PR."""
    return errors == [NEWS_REQUIRED]


def becomes_ready(pr: dict, errors: list[str]) -> bool:
    """A draft that was awaiting news now validates cleanly: hand it to a human."""
    return bool(pr.get("isDraft")) and not errors


def labels_for(incident: dict, errors: list[str]) -> list[str]:
    labels = ["agent"]
    if awaiting_news(errors):
        labels.append("awaiting-news")
    elif errors or incident.get("confidence") == "low":
        labels.append("needs-review")
    return labels


def pr_body(incident: dict, notes: str, breakdown: dict | None, diff_md: str, errors: list[str]) -> str:
    parts = [notes.strip() or incident.get("summary", "")]
    if breakdown:
        if incident.get("league") == "accomplice":
            middle = [
                ("× Contribution", breakdown["contribution"]),
                ("× Blast Radius", breakdown["blast_radius"]),
                ("× Legal status", breakdown["legal_status"]),
                ("+ Tradecraft", breakdown["tradecraft"]),
                ("+ Guardrails", breakdown["guardrails"]),
            ]
        else:
            middle = [
                ("× Autonomy", breakdown["autonomy"]),
                ("× Blast Radius", breakdown["blast_radius"]),
                ("+ Tradecraft", breakdown["tradecraft"]),
                ("+ Pettiness", breakdown["pettiness"]),
            ]
        rows = [
            ("Sentence-Years", breakdown["sentence_years"]),
            *middle,
            ("+ Dwell", breakdown["dwell"]),
            ("× Recidivism", breakdown["recidivism_multiplier"]),
        ]
        table = "\n".join(f"| {k} | {v:g} |" for k, v in rows)
        parts.append(f"## Score\n\n| Component | Value |\n|---|---|\n{table}\n| **Total** | **{breakdown['total']:g}** |")
    if diff_md:
        parts.append(diff_md.strip())
    status = "✅ Passed" if not errors else "❌ Failed\n\n" + "\n".join(f"- {e}" for e in errors)
    parts.append(f"## Validation\n\n{status}")
    parts.append(f"Confidence: **{incident.get('confidence', 'unknown')}**")
    parts.append("_Opened by the FelonyBench agent. Check every source before merging._")
    body = "\n\n".join(parts)
    if len(body) > PR_BODY_LIMIT:
        suffix = "\n\n_…truncated._"
        body = body[: PR_BODY_LIMIT - len(suffix)] + suffix
    return body


def _run(*cmd: str) -> str:
    try:
        return subprocess.run(cmd, check=True, text=True, capture_output=True, cwd=ROOT).stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notes", type=Path, default=ROOT / ".agent-out")
    parser.add_argument("--base", default="origin/main")
    args = parser.parse_args(argv)

    changes = parse_porcelain(_run("git", "status", "--porcelain", "--untracked-files=all"))
    bad = disallowed([p for _, p in changes])
    deletions = [p for s, p in changes if "D" in s]
    if bad or deletions:
        print(f"Refusing: agent touched disallowed paths {bad} or deleted {deletions}", file=sys.stderr)
        return 1

    files = [p for _, p in changes if p.startswith("incidents/") and p.endswith(".yaml")]
    if not files:
        print("No incident changes.")
        return 0
    contents = {p: (ROOT / p).read_text() for p in files}
    new_files = {p for s, p in changes if s in ("??", "A")}

    _run("git", "reset", "--hard", args.base)
    _run("git", "clean", "-fd", "incidents")
    rubric, validator = load_rubric(), load_validator()
    before = build_scores(load_incidents(ROOT / "incidents"), rubric, "base")
    open_prs = json.loads(_run("gh", "pr", "list", "--state", "open", "--json", "number,headRefName,isDraft,labels"))
    open_heads = {pr["headRefName"]: pr for pr in open_prs}

    failed = False
    for path, text in contents.items():
        stem = Path(path).stem
        branch = f"agent/{stem}"
        try:
            incident = yaml.safe_load(text) or {}
            _run("git", "switch", "-C", branch, args.base)
            (ROOT / path).write_text(text)

            errors = validate_dir(ROOT / "incidents", rubric, validator).get(Path(path).name, [])
            breakdown, diff_md = None, "## Leaderboard impact\n\nNot scored: validation failed."
            if not errors or awaiting_news(errors):  # otherwise valid; just no news yet
                after = build_scores(load_incidents(ROOT / "incidents"), rubric, "head")
                breakdown = next(i["breakdown"] for i in after["incidents"] if i["id"] == incident["id"])
                diff_md = render(before, after)

            title = pr_title(incident, is_new=path in new_files)
            notes_path = args.notes / f"{stem}.md"
            notes = notes_path.read_text() if notes_path.exists() else ""
            body = pr_body(incident, notes, breakdown, diff_md, errors)

            _run("git", "add", path)
            _run("git", "commit", "-m", title)
            _run("git", "push", "--force", "origin", f"HEAD:refs/heads/{branch}")
            if branch in open_heads:
                pr = open_heads[branch]
                _run("gh", "pr", "comment", str(pr["number"]), "--body", "Agent updated this incident.\n\n" + body)
                if becomes_ready(pr, errors):
                    _run("gh", "pr", "ready", str(pr["number"]))
                    if any(label.get("name") == "awaiting-news" for label in pr.get("labels", [])):
                        _run("gh", "pr", "edit", str(pr["number"]), "--remove-label", "awaiting-news")
            else:
                label_args = [x for label in labels_for(incident, errors) for x in ("--label", label)]
                draft = ["--draft"] if errors else []  # agent PRs get no CI check; a draft can't be merged by accident
                _run("gh", "pr", "create", "--base", "main", "--head", branch, "--title", title, "--body", body, *draft, *label_args)
            print(f"{title} -> {branch}")
        except subprocess.CalledProcessError as e:
            failed = True
            print(f"Failed to process {path} (branch {branch}): {e}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
