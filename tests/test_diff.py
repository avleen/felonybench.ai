from scripts.diff import render


def _scores(rows):
    empty = {"models": [], "orgs": []}
    return {"boards": {
        "open": {"verified": {"models": [], "orgs": rows}, "all": {"models": [], "orgs": rows}},
        "sandbox": {"verified": empty, "all": empty},
    }}


def test_new_org_enters_board():
    after = _scores([{"name": "OpenAI", "score": 87, "rank": 1}])
    out = render(_scores([]), after)
    assert "| OpenAI | 0 → 87 | +87 | — → #1 |" in out


def test_new_accomplice_org_enters_accomplice_board():
    empty = {"models": [], "orgs": []}
    rows = [{"name": "OrcaRouter", "score": 42, "rank": 1}]
    after = {"boards": {"accomplice": {"verified": empty, "all": {"models": [], "orgs": rows}}}}
    out = render(_scores([]), after)
    assert "#### Accomplice League\n\n| Org | Score | Change | Rank |\n|---|---|---|---|\n| OrcaRouter | 0 → 42 | +42 | — → #1 |" in out


def test_no_changes():
    rows = [{"name": "OpenAI", "score": 87, "rank": 1}]
    assert "No change." in render(_scores(rows), _scores(rows))


def test_rank_swap_listed():
    before = _scores([{"name": "A", "score": 100, "rank": 1}, {"name": "B", "score": 50, "rank": 2}])
    after = _scores([{"name": "B", "score": 150, "rank": 1}, {"name": "A", "score": 100, "rank": 2}])
    out = render(before, after)
    assert "| B | 50 → 150 | +100 | #2 → #1 |" in out
    assert "| A | 100 → 100 | +0 | #1 → #2 |" in out


def test_low_confidence_report_only_moves_the_second_section():
    rows = [{"name": "OpenAI", "score": 87, "rank": 1}]
    before = {**_scores([]), "confident": _scores([])}
    after = {**_scores(rows), "confident": _scores([])}
    default, everything = render(before, after).split("### With low-confidence reports shown")
    assert "No change." in default and "OpenAI" not in default
    assert "| OpenAI | 0 → 87 |" in everything


def test_confident_report_shows_in_the_default_view():
    rows = [{"name": "OpenAI", "score": 87, "rank": 1}]
    before = {**_scores([]), "confident": _scores([])}
    after = {**_scores(rows), "confident": _scores(rows)}
    default, _ = render(before, after).split("### With low-confidence reports shown")
    assert "| OpenAI | 0 → 87 |" in default
