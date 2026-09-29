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


# Worked example from docs/plans/2026-09-29-accomplice-league.md: scores exactly 42.
ACCOMPLICE_INCIDENT = {
    **{k: v for k, v in BASE_INCIDENT.items() if k not in ("scoring", "rationale")},
    "id": "2026-06-01-alibaba-abliterated-exploit",
    "date": "2026-06-01",
    "reported": "2026-06-20",
    "league": "accomplice",
    "org": "Alibaba",
    "human_actor": "A financially motivated threat actor tracked by a vendor",
    "models": [{"name": "Qwen3.8-27B-Uncensored", "codename": None, "family": "qwen", "share": 1,
                "modified_by": "OrcaRouter", "modification": "abliterated"}],
    "victims": [{"name": "A software company", "type": "third_party", "country": "US"}],
    "statutes": [{"code": "18 USC 1030(a)(5)(A)", "max_years": 10}],
    "scoring": {"contribution": "built_exploit", "guardrails": "removed", "legal_status": "crime",
                "blast_radius": "third_party", "tradecraft": ["zero_day"], "dwell_days": 10,
                "detected_by": "victim", "self_disclosed": False},
    "rationale": {k: "Because." for k in ("contribution", "guardrails", "blast_radius", "tradecraft", "dwell")},
}


@pytest.fixture
def make_accomplice():
    def _make(scoring=None, **overrides):
        incident = copy.deepcopy(ACCOMPLICE_INCIDENT)
        incident.update(overrides)
        if scoring:
            incident["scoring"].update(scoring)
        return incident

    return _make
