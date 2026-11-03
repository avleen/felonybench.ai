"""Free keyword prefilter over RSS feeds. Writes candidates for the agent."""
import argparse
import json
import os
import re
import signal
import socket
import sys
import time
from calendar import timegm
from contextlib import contextmanager
from pathlib import Path

import feedparser
import yaml

from scripts.rubric import ROOT

MAX_SEEN = 5000
MAX_AGE_DAYS = 7  # skip older items: already-seen news, or a newly added feed's backlog
USER_AGENT = "felonybench-watch/1.0 (+https://felonybench.ai/how-it-works)"
FEED_IDLE_SECONDS = 60  # feedparser has no timeout of its own, and a hung feed would stall the run
FEED_TOTAL_SECONDS = 120  # the idle limit never fires on a server that drips a byte at a time
MAX_DEAD_SHARE = 0.2  # one feed down is normal; more than this means we're going blind


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


@contextmanager
def time_limit(seconds: int):
    def expired(signum, frame):
        raise TimeoutError(f"took longer than {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def load_seen(path: Path) -> list[str]:
    """Losing this only means re-reading a week of news, so a corrupt file shouldn't stop the run."""
    try:
        data = json.loads(path.read_text()) if path.exists() else []
    except ValueError as e:  # includes bad JSON and bad UTF-8
        print(f"::warning::Ignoring corrupt {path.name}: {e}")
        return []
    if not isinstance(data, list):
        print(f"::warning::Ignoring corrupt {path.name}: not a list")
        return []
    return [link for link in data if isinstance(link, str)]


def dead_feeds(counts: dict[str, int]) -> list[str]:
    return [name for name, count in counts.items() if count == 0]


def too_many_dead(counts: dict[str, int]) -> bool:
    return bool(counts) and len(dead_feeds(counts)) / len(counts) > MAX_DEAD_SHARE


def feed_summary(counts: dict[str, int]) -> str:
    rows = "\n".join(f"| {name} | {count} |" for name, count in sorted(counts.items(), key=lambda c: c[1]))
    return f"## Feeds\n\n{len(dead_feeds(counts))} of {len(counts)} returned nothing.\n\n| Feed | Entries |\n|---|---:|\n{rows}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feeds", type=Path, default=ROOT / "scripts" / "feeds.yaml")
    parser.add_argument("--seen", type=Path, default=ROOT / ".agent-state" / "seen.json")
    parser.add_argument("--out", type=Path, default=ROOT / ".agent-out" / "candidates.json")
    parser.add_argument("--max-age-days", type=float, default=MAX_AGE_DAYS)
    args = parser.parse_args(argv)

    config = yaml.safe_load(args.feeds.read_text())
    lab_re, trigger_re = compile_patterns(config["labs"], config["triggers"])
    seen_list = load_seen(args.seen)
    seen = set(seen_list)
    socket.setdefaulttimeout(FEED_IDLE_SECONDS)

    entries, counts = [], {}
    for feed in config["feeds"]:
        try:
            with time_limit(FEED_TOTAL_SECONDS):
                got = fetch(feed)
        except Exception as e:  # one bad feed must not stop the run
            print(f"warning: {feed['name']}: {e}", file=sys.stderr)
            got = []
        print(f"{feed['name']}: {len(got)} entries")
        counts[feed["name"]] = len(got)
        entries += got
    for name in dead_feeds(counts):
        print(f"::warning::Feed returned nothing: {name}")

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
            f.write(f"dead_feeds={', '.join(dead_feeds(counts)) if too_many_dead(counts) else 'none'}\n")
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a") as f:
            f.write(feed_summary(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
