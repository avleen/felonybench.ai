import copy

import pytest

from scripts.rubric import load_rubric

BASE_INCIDENT = {
    "id": "2026-07-16-openai-exploitgym-huggingface",
    "date": "2026-07-16",
    "reported": "2026-07-21",
    "league": "open",
    "tier": "verified",
    "org": "OpenAI",
    "models": [
        {"name": "model-a", "codename": None, "family": "gpt", "share": 0.5},
        {"name": "model-b", "codename": None, "family": "gpt", "share": 0.5},
    ],
    "victims": [{"name": "Hugging Face", "type": "third_party", "country": "US"}],
    "summary": "Escaped a sandbox and hacked Hugging Face to steal benchmark answers.",
    "statutes": [
        {"code": "18 USC 1030(a)(2)(C)", "max_years": 5},
        {"code": "18 USC 1030(a)(4)", "max_years": 5},
        {"code": "18 USC 1832", "max_years": 10},
    ],
    "foreign_laws": [],
    "scoring": {
        "autonomy": "emergent",
        "blast_radius": "third_party",
        "tradecraft": ["zero_day", "credentials", "privilege_escalation", "lateral_movement"],
        "motive": "benchmark_cheating",
        "dwell_days": 5,
        "detected_by": "victim",
        "self_disclosed": True,
    },
    "rationale": {k: "Because." for k in ("autonomy", "blast_radius", "tradecraft", "motive", "dwell")},
    "confidence": "high",
    "sources": [
        {"url": "https://openai.com/index/example", "kind": "postmortem", "publisher": "OpenAI"},
        {"url": "https://www.wired.com/story/example", "kind": "news", "publisher": "Wired"},
    ],
}


@pytest.fixture
def rubric():
    return load_rubric()


@pytest.fixture
def make_incident():
    def _make(scoring=None, **overrides):
        incident = copy.deepcopy(BASE_INCIDENT)
        incident.update(overrides)
        if scoring:
            incident["scoring"].update(scoring)
        return incident

    return _make
