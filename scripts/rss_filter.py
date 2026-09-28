"""Free keyword prefilter over RSS feeds. Writes candidates for the agent."""
import argparse
import json
import os
import re
import sys
import time
from calendar import timegm
from pathlib import Path

import feedparser
import yaml

from scripts.rubric import ROOT

MAX_SEEN = 5000
MAX_AGE_DAYS = 7  # skip older items: already-seen news, or a newly added feed's backlog
USER_AGENT = "felonybench-watch/1.0 (+https://felonybench.ai/how-it-works)"


def compile_patterns(labs: list[str], triggers: list[str]):
    lab_re = re.compile(r"\b(" + "|".join(re.escape(x) for x in labs) + r")\b", re.I)
    trigger_re = re.compile(r"\b(" + "|".join(re.escape(x) for x in triggers) + r")", re.I)
    return lab_re, trigger_re


def matches(text: str, lab_re, trigger_re) -> bool:
    return bool(lab_re.search(text) and trigger_re.search(text))


def filter_entries(entries: list[dict], seen: set, lab_re, trigger_re, min_ts: float | None = None) -> list[dict]:
    return [
        e for e in entries
        if e["link"] not in seen
        and (min_ts is None or e.get("published_ts") is None or e["published_ts"] >= min_ts)
        and matches(f"{e['title']} {e['summary']}", lab_re, trigger_re)
    ]


def _timestamp(entry) -> float | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    return timegm(parsed) if parsed else None


def fetch(feed: dict) -> list[dict]:
    parsed = feedparser.parse(feed["url"], agent=USER_AGENT)
    if parsed.bozo and not parsed.entries:
        print(f"warning: {feed['name']}: {parsed.get('bozo_exception')}", file=sys.stderr)
    return [
        {
            "feed": feed["name"],
            "title": e.get("title", ""),
            "link": e["link"],
            "summary": re.sub(r"<[^>]+>", " ", e.get("summary", "")),
            "published": e.get("published", ""),
            "published_ts": _timestamp(e),
        }
        for e in parsed.entries
        if e.get("link")
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feeds", type=Path, default=ROOT / "scripts" / "feeds.yaml")
    parser.add_argument("--seen", type=Path, default=ROOT / ".agent-state" / "seen.json")
    parser.add_argument("--out", type=Path, default=ROOT / ".agent-out" / "candidates.json")
    parser.add_argument("--max-age-days", type=float, default=MAX_AGE_DAYS)
    args = parser.parse_args(argv)

    config = yaml.safe_load(args.feeds.read_text())
    lab_re, trigger_re = compile_patterns(config["labs"], config["triggers"])
    seen_list = json.loads(args.seen.read_text()) if args.seen.exists() else []
    seen = set(seen_list)

    entries = []
    for feed in config["feeds"]:
        try:
            got = fetch(feed)
        except Exception as e:  # one bad feed must not stop the run
            print(f"warning: {feed['name']}: {e}", file=sys.stderr)
            continue
        print(f"{feed['name']}: {len(got)} entries")
        entries += got

    candidates = list({c["link"]: c for c in filter_entries(entries, seen, lab_re, trigger_re, time.time() - args.max_age_days * 86400)}.values())
    for entry in entries:
        if entry["link"] not in seen:
            seen.add(entry["link"])
            seen_list.append(entry["link"])

    args.seen.parent.mkdir(parents=True, exist_ok=True)
    args.seen.write_text(json.dumps(seen_list[-MAX_SEEN:]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(candidates, indent=2))
    print(f"{len(candidates)} candidates")

    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a") as f:
            f.write(f"has_candidates={'true' if candidates else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
