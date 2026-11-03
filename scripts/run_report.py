"""Report how an agent run went: why it failed, and what a sweep found.

Failures open or update one issue, and the next good run closes it. Sweep reports go to the
job summary and a rolling issue, because a 30-day artifact is easy to never read.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

COMMENT_LIMIT = 60000
SWEEP_ISSUE = "Sweep reports"


_URL = re.compile(r"https?://\S*", re.I)
_AT_ENTITY = re.compile(r"&(?:#0*64(?![0-9])|#x0*40(?![0-9a-f])|commat;);?", re.I)  # GitHub renders these as @


def neutralize(text: str) -> str:
    """Agent text is untrusted: stop it notifying people when it's posted to GitHub.

    Leaves no bare @ at all, written plainly or as an entity, because predicting what Markdown will
    link is how mentions slip through. In a URL it becomes %40, which keeps the link working on most
    sites, though a few treat it differently. A wrong link is better than a stray notification.
    """
    text = _AT_ENTITY.sub("@", text)
    return _URL.sub(lambda m: m[0].replace("@", "%40"), text).replace("@", "@\u200b")


def agent_result(transcript: Path | None) -> dict | None:
    """The final result record from the transcript, numbers and known fields only."""
    try:
        records = json.loads(transcript.read_text())
    except (AttributeError, OSError, ValueError):
        return None
    if not isinstance(records, list):
        return None
    for record in reversed(records):
        if isinstance(record, dict) and record.get("type") == "result":
            return record
    return None


def describe(result: dict | None) -> str:
    if result is None:
        return "The agent left no result, so it probably never finished starting."
    turns = result.get("num_turns")
    turns = turns if isinstance(turns, int) else "unknown"
    subtype = result.get("subtype") if isinstance(result.get("subtype"), str) else "unknown"
    return f"Agent result: `{neutralize(subtype)[:60]}` after {turns} turns."


def failure_body(url: str, agent: str, publish: str, result: dict | None) -> str:
    return (
        f"Run: {url}\n\n- Agent job: `{agent}`\n- Opening PRs: `{publish}`\n- {describe(result)}\n\n"
        "Incidents the agent finished are still opened as PRs when the agent job fails. "
        "The transcript is attached to the run."
    )


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, text=True, capture_output=True).stdout


def _find_issue(title: str) -> int | None:
    issues = json.loads(_gh("issue", "list", "--state", "open", "--limit", "100", "--search", f'in:title "{title}"', "--json", "number,title"))
    return next((i["number"] for i in issues if i["title"] == title), None)


def _post(title: str, body: str) -> None:
    existing = _find_issue(title)
    if existing:
        _gh("issue", "comment", str(existing), "--body", body)
    else:
        _gh("issue", "create", "--title", title, "--body", body)


def failed(agent: str, publish: str) -> bool:
    """Publishing has to have actually succeeded: if it was skipped, nothing got published."""
    return agent in ("failure", "cancelled") or publish != "success"


def report(workflow: str, url: str, agent: str, publish: str, result: dict | None, sweep_report: str) -> None:
    title = f"Agent run failed: {workflow}"
    if failed(agent, publish):
        _post(title, failure_body(url, agent, publish, result))
    else:
        existing = _find_issue(title)
        if existing:
            _gh("issue", "close", str(existing), "--comment", f"Recovered: {url}")
    if sweep_report.strip():
        _post(SWEEP_ISSUE, neutralize(f"Run: {url}\n\n{sweep_report}")[:COMMENT_LIMIT])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True, help="result of the agent job")
    parser.add_argument("--publish", required=True, help="outcome of opening PRs")
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--sweep-report", type=Path)
    args = parser.parse_args(argv)

    result = agent_result(args.transcript)
    sweep = args.sweep_report.read_text(errors="replace") if args.sweep_report and args.sweep_report.is_file() else ""
    url = f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(f"{describe(result)}\n\n{neutralize(sweep)[:COMMENT_LIMIT]}\n")
    report(os.environ["GITHUB_WORKFLOW"], url, args.agent, args.publish, result, sweep)
    return 1 if failed(args.agent, args.publish) else 0


if __name__ == "__main__":
    sys.exit(main())
