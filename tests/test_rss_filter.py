import json
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import yaml

from scripts import rss_filter
from scripts.rss_filter import compile_patterns, dead_feeds, feed_summary, filter_entries, load_seen, matches, too_many_dead

LABS = ["OpenAI", "Meta", "GPT", "Claude"]
TRIGGERS = ["sandbox", "escape", "breach", "exfiltrat"]


@pytest.fixture
def patterns():
    return compile_patterns(LABS, TRIGGERS)


@pytest.mark.parametrize("text, expected", [
    ("OpenAI model escaped its sandbox", True),
    ("GPT-6 agent exfiltrated data", True),
    ("OpenAI announces new pricing", False),
    ("Sandbox game gets an update", False),
    ("Huge metadata breach at retailer", False),   # 'Meta' must be a whole word
    ("Meta confirms breach by its own agent", True),
])
def test_matches(patterns, text, expected):
    assert matches(text, *patterns) is expected


def test_filter_skips_seen(patterns):
    entries = [
        {"link": "https://a", "title": "OpenAI sandbox escape", "summary": ""},
        {"link": "https://b", "title": "Claude breach", "summary": ""},
    ]
    assert [e["link"] for e in filter_entries(entries, {"https://a"}, *patterns)] == ["https://b"]


@pytest.fixture(scope="module")
def real_patterns():
    import yaml

    from scripts.rubric import ROOT

    config = yaml.safe_load((ROOT / "scripts" / "feeds.yaml").read_text())
    return compile_patterns(config["labs"], config["triggers"])


@pytest.mark.parametrize("text, expected", [
    # Incident shapes earlier sweeps missed
    ("Alibaba's ROME agent mined cryptocurrency on its training GPUs", True),
    ("ROME agent opened a reverse SSH tunnel during a training run", True),
    ("AISI incident report on unsanctioned agent behaviour during cyber testing", True),
    ("AI Security Institute: agent sent phishing emails and used sockpuppets", True),
    ("METR finds agent opened a pull request to an open-source project", True),
    ("Agent in an Irregular CTF exploited a real website", True),
    ("Claude cancelled other people's gym classes via an API flaw", True),
    ("Agent in an Apollo Research eval went rogue", True),
    ("Dependabot PR opened by a GPT agent", True),
    ("Palisade Research: model misuse of shutdown script", True),
    ("Third-party cyber evaluations involving OpenAI models", True),
    # Consumer-harm headlines often don't name the lab
    ("AI agent hacks gym booking system to get its user a spot", True),
    ("An AI assistant cancelled other people's gym classes", True),
    ("AI agent market expected to grow 40% this year", False),
    # Must stay quiet
    ("Crypto prices fall as bitcoin slides", False),
    ("Meta shares fall as crypto prices slide", False),
    ("OpenAI announces new pricing", False),
    ("Concert cancelled due to rain", False),
    ("Tourists stranded in Rome as flights cancelled", False),
    ("Gold mining stocks rally", False),
    # Accomplice League: humans using a named model for a crime
    ("Threat actor used Gemini to develop zero-day exploit", True),
    ("Criminals used abliterated Qwen model to write ransomware", True),
    ("Hackers sell WormGPT subscriptions to write malware", True),
    ("Fraudsters used ChatGPT to run a romance-scam operation", True),
    ("Cybercriminals used Claude Code in data-extortion campaign", True),
    ("GhostGPT sold on Telegram to cybercriminals", True),
    ("Iran-Linked Actor Leveraged Claude AI to Target U.S. Navy Data", True),
    ("State-sponsored hackers used DeepSeek for espionage", True),
    ("Attackers used Gemini to automate a cyberattack on hospitals", True),
    # An uncensored model *release* is not an incident
    ("OrcaRouter releases uncensored Qwen model", False),
    ("Abliterated Llama model tops Hugging Face downloads", False),
    ("Musk renews fraud claims against OpenAI", False),
])
def test_real_config_shapes(real_patterns, text, expected):
    assert matches(text, *real_patterns) is expected


def test_filter_skips_stale_entries(patterns):
    entries = [
        {"link": "https://old", "title": "OpenAI sandbox escape", "summary": "", "published_ts": 1_000},
        {"link": "https://new", "title": "OpenAI sandbox escape", "summary": "", "published_ts": 9_000},
        {"link": "https://undated", "title": "OpenAI sandbox escape", "summary": "", "published_ts": None},
    ]
    kept = filter_entries(entries, set(), *patterns, min_ts=5_000)
    assert [e["link"] for e in kept] == ["https://new", "https://undated"]


FEEDS = yaml.safe_load((Path(__file__).parent.parent / "scripts" / "feeds.yaml").read_text())
# Words that scope a search rather than name an incident: results still have to hit a trigger.
SCOPING_TERMS = {"artificial intelligence", "ai model", "third-party", "real website", "real system",
                 "threat intelligence", "google threat intelligence group", "ai office"}


def _real_patterns():
    return compile_patterns(FEEDS["labs"], FEEDS["triggers"])


@pytest.mark.parametrize("headline", [
    "AI agent deleted customer database",
    "AI agent booked flights without asking",
    "AI agent purchased goods on a stolen card",
    "OpenAI model caught reward hacking",
])
def test_consumer_harm_headlines_reach_the_agent(headline):
    assert matches(headline, *_real_patterns())


@pytest.mark.parametrize("headline", ["OpenAI purchased a startup", "Meta deleted old posts", "Anthropic booked a venue"])
def test_ordinary_lab_news_stays_out(headline):
    assert not matches(headline, *_real_patterns())


def test_feeds_are_unique_and_https():
    names = [f["name"] for f in FEEDS["feeds"]]
    urls = [f["url"] for f in FEEDS["feeds"]]
    assert len(names) == len(set(names)) and len(urls) == len(set(urls))
    assert all(u.startswith("https://") for u in urls)


def test_every_phrase_we_search_for_can_pass_the_filter():
    """A search for a phrase the filter drops costs a fetch and finds nothing."""
    lab_re, trigger_re = _real_patterns()
    for feed in FEEDS["feeds"]:
        query = parse_qs(urlparse(feed["url"]).query).get("q", [""])[0]
        for term in re.findall(r'"([^"]+)"', query):
            assert lab_re.search(term) or trigger_re.search(term) or term.lower() in SCOPING_TERMS, (feed["name"], term)


@pytest.mark.parametrize("content", ["{not json", '{"a": 1}', "null"])
def test_corrupt_seen_file_starts_fresh(tmp_path, content):
    path = tmp_path / "seen.json"
    path.write_text(content)
    assert load_seen(path) == []


def test_seen_file_that_is_not_utf8_starts_fresh(tmp_path):
    path = tmp_path / "seen.json"
    path.write_bytes(b"\xff\xfe")
    assert load_seen(path) == []


def test_seen_file_keeps_only_links(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text('["https://a", 1, ["x"]]')
    assert load_seen(path) == ["https://a"]


def test_missing_seen_file_is_empty(tmp_path):
    assert load_seen(tmp_path / "nope.json") == []


@pytest.mark.parametrize("counts, expected", [
    ({}, False),
    ({"a": 5}, False),
    ({"a": 0}, True),
    ({"a": 0, "b": 1, "c": 1, "d": 1, "e": 1}, False),  # exactly a fifth
    ({"a": 0, "b": 0, "c": 1, "d": 1, "e": 1}, True),
])
def test_too_many_dead(counts, expected):
    assert too_many_dead(counts) is expected


def test_summary_lists_dead_feeds_first():
    out = feed_summary({"Good": 5, "Dead": 0})
    assert "1 of 2 returned nothing" in out and out.index("Dead") < out.index("Good")


def _run_main(tmp_path, monkeypatch, fetch):
    feeds = tmp_path / "feeds.yaml"
    feeds.write_text(yaml.safe_dump({"labs": ["OpenAI"], "triggers": ["breach"], "feeds": [{"name": "A", "url": "https://a"}, {"name": "B", "url": "https://b"}]}))
    output, summary = tmp_path / "output", tmp_path / "summary"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setattr(rss_filter, "fetch", fetch)
    code = rss_filter.main(["--feeds", str(feeds), "--seen", str(tmp_path / "seen.json"), "--out", str(tmp_path / "out.json")])
    return code, output.read_text(), summary.read_text()


def test_main_keeps_going_when_a_feed_raises_and_counts_it_dead(tmp_path, monkeypatch, capsys):
    def fetch(feed):
        if feed["name"] == "A":
            raise OSError("down")
        return [{"feed": "B", "title": "OpenAI breach", "link": "https://b/1", "summary": ""}]

    code, output, summary = _run_main(tmp_path, monkeypatch, fetch)
    assert code == 0
    assert "has_candidates=true" in output and "dead_feeds=A\n" in output
    assert "| A | 0 |" in summary
    assert "::warning::Feed returned nothing: A" in capsys.readouterr().out
    assert [c["link"] for c in json.loads((tmp_path / "out.json").read_text())] == ["https://b/1"]


def test_main_reports_healthy_feeds(tmp_path, monkeypatch):
    fetch = lambda feed: [{"feed": feed["name"], "title": "nothing", "link": f"{feed['url']}/1", "summary": ""}]
    _, output, _ = _run_main(tmp_path, monkeypatch, fetch)
    assert "has_candidates=false" in output and "dead_feeds=none\n" in output


def test_time_limit_stops_a_feed_that_never_finishes():
    with pytest.raises(TimeoutError):
        with rss_filter.time_limit(1):
            time.sleep(5)


def test_time_limit_clears_itself():
    with rss_filter.time_limit(1):
        pass
    time.sleep(1.1)  # would raise here if the alarm were still set


def test_main_counts_a_timed_out_feed_as_dead(tmp_path, monkeypatch):
    monkeypatch.setattr(rss_filter, "FEED_TOTAL_SECONDS", 1)

    def fetch(feed):
        if feed["name"] == "A":
            time.sleep(5)
        return [{"feed": feed["name"], "title": "x", "link": f"{feed['url']}/1", "summary": ""}]

    _, output, _ = _run_main(tmp_path, monkeypatch, fetch)
    assert "dead_feeds=A\n" in output
