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
