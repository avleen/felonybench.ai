import pytest

from scripts.rss_filter import compile_patterns, filter_entries, matches

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
