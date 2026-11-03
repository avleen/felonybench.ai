"""Turn the agent's incident edits into one branch and PR per incident.

Runs in CI after Claude Code. Claude only edits files; this script owns git and gh,
so the agent never needs shell access.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from scripts.diff import render
from scripts.rubric import ROOT, load_rubric, load_incident_yaml
from scripts.run_report import postable
from scripts.score import load_incidents
from scripts.scoring import build_scores
from scripts.validate import NEWS_REQUIRED, load_validator, validate_dir

ALLOWED_PREFIXES = ("incidents/", ".agent-out/", ".agent-state/")
INCIDENT_FILE = re.compile(r"incidents/[^/]+\.yaml")
PR_BODY_LIMIT = 65000


def parse_porcelain(output: str) -> list[tuple[str, str]]:
    """Parse `git status --porcelain -z`, whose paths are unquoted and can't be spoofed by a filename."""
    changes = []
    fields = iter(output.split("\0"))
    for entry in fields:
        if not entry:
            continue
        status, path = entry[:2].strip(), entry[3:]
        changes.append((status, path))
        if "R" in status or "C" in status:  # the original path follows as its own field
            changes.append(("D" if "R" in status else status, next(fields, "")))
    return changes


def disallowed(paths: list[str]) -> list[str]:
    return [p for p in paths if not p.startswith(ALLOWED_PREFIXES)]


def has_label(pr: dict, name: str) -> bool:
    return any(label.get("name") == name for label in pr.get("labels", []))


def add_missing_labels(pr: dict, labels: list[str]) -> None:
    for label in labels:
        if not has_label(pr, label):
            _run("gh", "pr", "edit", str(pr["number"]), "--add-label", label)
            pr.setdefault("labels", []).append({"name": label})


def pr_title(incident: dict, is_new: bool) -> str:
    if not is_new:
        return postable(f"Update: {incident['id']}")
    victims = ", ".join(v.get("name", "?") for v in incident.get("victims") or [])
    return postable(f"New felony: {incident.get('org', '?')} — {victims}")


def awaiting_news(errors: list[str]) -> bool:
    """In scope and otherwise valid, just no news coverage yet: opened as a draft PR."""
    return errors == [NEWS_REQUIRED]


def becomes_ready(pr: dict, errors: list[str]) -> bool:
    """A draft that was awaiting news now validates cleanly: hand it to a human."""
    return bool(pr.get("isDraft")) and not errors


def labels_for(incident: dict, errors: list[str], previously_closed: int | None = None) -> list[str]:
    labels = ["agent"]
    if awaiting_news(errors):
        labels.append("awaiting-news")
    elif errors or incident.get("confidence") == "low":
        labels.append("needs-review")
    if previously_closed and "needs-review" not in labels:  # a rejection needs review even while awaiting news
        labels.append("needs-review")
    return labels


def quote_notes(notes: str) -> str:
    """Agent notes are untrusted: keep them visibly separate."""
    return "\n".join(f"> {line}" for line in notes.strip().splitlines())


def pr_body(
    incident: dict, notes: str, breakdown: dict | None, diff_md: str, errors: list[str], previously_closed: int | None = None,
) -> str:
    """Generated sections come first so agent notes can't bury or imitate them."""
    status = "✅ Passed" if not errors else "❌ Failed\n\n" + "\n".join(f"- {e}" for e in errors)
    parts = [f"## Validation\n\n{status}"]
    confidence = incident.get("confidence", "unknown")
    if confidence == "low":
        parts.append("Confidence: **low**. Hidden by default on the site, so merging won't change the default leaderboard.")
    else:
        parts.append(f"Confidence: **{confidence}**")
    if previously_closed:
        parts.append(f"⚠️ **#{previously_closed} proposed this incident and was closed without merging.** Check what's new.")
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
    summary = str(incident.get("summary", ""))
    parts.append("## Agent notes (unverified)\n\n" + quote_notes(notes.strip() or summary))
    parts.append("_Opened by the FelonyBench agent. Check every source before merging._")
    # The org, victims and validation errors come from the agent too, not just its notes.
    return postable("\n\n".join(parts), PR_BODY_LIMIT)


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

    changes = parse_porcelain(_run("git", "status", "--porcelain", "-z", "--untracked-files=all"))
    bad = disallowed([p for _, p in changes])
    deletions = [p for s, p in changes if "D" in s]
    if bad or deletions:
        print(f"Refusing: agent touched disallowed paths {bad} or deleted {deletions}", file=sys.stderr)
        return 1

    incident_paths = [p for _, p in changes if p.startswith("incidents/")]
    files = [p for p in incident_paths if INCIDENT_FILE.fullmatch(p)]
    skipped = [p for p in incident_paths if p not in files]
    if skipped:
        print(f"Skipped files that aren't incidents/*.yaml: {skipped}", file=sys.stderr)
    if not files:
        print("No incident changes.")
        return 1 if skipped else 0
    failed = bool(skipped)
    contents = {}
    for path in files:
        try:
            contents[path] = (ROOT / path).read_text()
        except (OSError, ValueError) as e:  # ValueError: not UTF-8
            failed = True
            print(f"Failed to read {path}: {e!r}", file=sys.stderr)
    new_files = {p for s, p in changes if s in ("??", "A")}

    _run("git", "reset", "--hard", args.base)
    _run("git", "clean", "-fd", "incidents")
    rubric, validator = load_rubric(), load_validator()
    before = build_scores(load_incidents(ROOT / "incidents"), rubric, "base")
    open_prs = json.loads(_run("gh", "pr", "list", "--state", "open", "--limit", "200", "--json", "number,headRefName,isDraft,labels,isCrossRepository"))
    # A fork can name its branch agent/<id> too, and must not be mistaken for the agent's PR.
    open_heads = {pr["headRefName"]: pr for pr in open_prs if not pr.get("isCrossRepository")}
    closed_prs = json.loads(_run("gh", "pr", "list", "--label", "agent", "--state", "closed", "--limit", "200", "--json", "number,headRefName,mergedAt"))
    closed_heads = {pr["headRefName"]: pr["number"] for pr in sorted(closed_prs, key=lambda pr: pr["number"]) if not pr.get("mergedAt")}

    for path, text in contents.items():
        stem = Path(path).stem
        branch = f"agent/{stem}"
        try:
            incident = load_incident_yaml(text)
            if not isinstance(incident, dict):
                raise ValueError("not a YAML mapping")
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
            notes = notes_path.read_text(errors="replace") if notes_path.exists() else ""
            previously_closed = closed_heads.get(branch)
            body = pr_body(incident, notes, breakdown, diff_md, errors, previously_closed)

            pr = open_heads.get(branch)
            labels = labels_for(incident, errors, previously_closed)
            # Agent PRs get no CI check, so these come before the push: if anything after it fails,
            # the revision can't sit in a mergeable PR without its review label or as a ready PR.
            if pr:
                add_missing_labels(pr, [label for label in labels if label != "agent"])
                if errors and not pr.get("isDraft"):
                    _run("gh", "pr", "ready", str(pr["number"]), "--undo")

            _run("git", "add", path)
            _run("git", "commit", "-m", title)
            _run("git", "push", "--force", "origin", f"HEAD:refs/heads/{branch}")
            if pr:
                number = str(pr["number"])
                _run("gh", "pr", "edit", number, "--title", title, "--body", body)
                _run("gh", "pr", "comment", number, "--body", "Agent updated this incident. The description now reflects the new version.")
                if becomes_ready(pr, errors):
                    _run("gh", "pr", "ready", number)
                    if has_label(pr, "needs-review") and "needs-review" not in labels:
                        _run("gh", "pr", "edit", number, "--remove-label", "needs-review")
                if has_label(pr, "awaiting-news") and "awaiting-news" not in labels:
                    _run("gh", "pr", "edit", number, "--remove-label", "awaiting-news")
            else:
                label_args = [x for label in labels for x in ("--label", label)]
                draft = ["--draft"] if errors else []  # agent PRs get no CI check; a draft can't be merged by accident
                _run("gh", "pr", "create", "--base", "main", "--head", branch, "--title", title, "--body", body, *draft, *label_args)
            print(f"{title} -> {branch}")
        except Exception as e:  # one bad file must not cost the rest of the run its PRs
            failed = True
            print(f"Failed to process {path} (branch {branch}): {e!r}", file=sys.stderr)
            _run("git", "reset", "--hard")
            _run("git", "clean", "-fd", "incidents")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
