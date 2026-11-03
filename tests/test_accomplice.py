from scripts.scoring import breakdown, build_scores


def test_worked_example_scores_42(make_accomplice, rubric):
    b = breakdown(make_accomplice(), rubric)
    assert (b["sentence_years"], b["contribution"], b["blast_radius"], b["legal_status"]) == (10, 1.5, 1, 1)
    assert (b["base"], b["tradecraft"], b["guardrails"], b["dwell"], b["total"]) == (15, 6, 10, 11, 42)
    assert b["pettiness"] == 0 and b["autonomy"] is None


def test_contested_halves_base(make_accomplice, rubric):
    assert breakdown(make_accomplice(scoring={"legal_status": "contested"}), rubric)["base"] == 7.5


def test_model_crimes_have_no_accomplice_inputs(make_incident, rubric):
    b = breakdown(make_incident(), rubric)
    assert (b["contribution"], b["legal_status"], b["guardrails"], b["total"]) == (None, None, 0, 87)


def test_co_defendants_each_charged_in_full(make_accomplice, rubric):
    orgs = build_scores([make_accomplice()], rubric, "now")["boards"]["accomplice"]["all"]["orgs"]
    assert {(o["name"], o["score"]) for o in orgs} == {("Alibaba", 42), ("OrcaRouter", 42)}


def test_co_defendant_charged_once_per_incident(make_accomplice, rubric):
    inc = make_accomplice()
    inc["models"] = [{**inc["models"][0], "share": 0.5},
                     {**inc["models"][0], "name": "Qwen3.8-9B-Uncensored", "share": 0.5}]
    orgs = build_scores([inc], rubric, "now")["boards"]["accomplice"]["all"]["orgs"]
    assert {(o["name"], o["score"]) for o in orgs} == {("Alibaba", 42), ("OrcaRouter", 42)}


def test_modifier_is_not_charged_twice_when_it_is_the_lab(make_accomplice, rubric):
    inc = make_accomplice()
    inc["models"][0]["modified_by"] = "Alibaba"
    orgs = build_scores([inc], rubric, "now")["boards"]["accomplice"]["all"]["orgs"]
    assert [(o["name"], o["score"]) for o in orgs] == [("Alibaba", 42)]


def test_modified_model_row(make_accomplice, rubric):
    models = build_scores([make_accomplice()], rubric, "now")["boards"]["accomplice"]["all"]["models"]
    assert [(m["slug"], m["org"], m["base_org"]) for m in models] == [
        ("orcarouter-qwen3-8-27b-uncensored", "OrcaRouter", "Alibaba")]


def test_unmodified_model_row_base_org_is_org(make_accomplice, make_incident, rubric):
    inc = make_accomplice()
    del inc["models"][0]["modified_by"]
    models = build_scores([inc], rubric, "now")["boards"]["accomplice"]["all"]["models"]
    assert [(m["slug"], m["org"], m["base_org"]) for m in models] == [
        ("alibaba-qwen3-8-27b-uncensored", "Alibaba", "Alibaba")]
    models = build_scores([make_incident()], rubric, "now")["boards"]["open"]["all"]["models"]
    assert {(m["org"], m["base_org"]) for m in models} == {("OpenAI", "OpenAI")}


def test_badges(make_accomplice, rubric):
    inc = build_scores([make_accomplice()], rubric, "now")["incidents"][0]
    assert inc["badges"] == ["uncensored"]
    inc = build_scores([make_accomplice(scoring={"guardrails": "jailbroken"})], rubric, "now")["incidents"][0]
    assert inc["badges"] == ["jailbroken"]
    inc = build_scores([make_accomplice(scoring={"guardrails": "intact"})], rubric, "now")["incidents"][0]
    assert inc["badges"] == []


def test_co_defendants_each_get_a_trend_line(make_accomplice, rubric):
    series = build_scores([make_accomplice()], rubric, "now")["trends"]["accomplice"]["all"]
    assert set(series) == {"Alibaba", "OrcaRouter"}
    assert all(points[-1]["cumulative"] == 42 for points in series.values())


def test_accomplice_league_is_separate(make_accomplice, make_incident, rubric):
    boards = build_scores([make_accomplice(), make_incident()], rubric, "now")["boards"]
    assert [o["name"] for o in boards["open"]["all"]["orgs"]] == ["OpenAI"]
    assert "OpenAI" not in {o["name"] for o in boards["accomplice"]["all"]["orgs"]}


def _multi_lab(make_accomplice, **overrides):
    """An Alibaba-led incident that also used another lab's model."""
    inc = make_accomplice(**overrides)
    inc["models"] = [
        {"name": "Qwen", "codename": None, "family": "qwen", "share": 0.5},
        {"name": "Kimi K2", "codename": None, "family": "kimi", "org": "Moonshot AI", "share": 0.5},
    ]
    return inc


def test_model_from_another_lab_is_listed_under_that_lab(make_accomplice, rubric):
    models = build_scores([_multi_lab(make_accomplice)], rubric, "now")["boards"]["accomplice"]["all"]["models"]
    assert {(m["slug"], m["org"], m["base_org"], m["score"]) for m in models} == {
        ("alibaba-qwen", "Alibaba", "Alibaba", 21),
        ("moonshot-ai-kimi-k2", "Moonshot AI", "Moonshot AI", 21)}


def test_every_lab_is_charged_in_full(make_accomplice, rubric):
    orgs = build_scores([_multi_lab(make_accomplice)], rubric, "now")["boards"]["accomplice"]["all"]["orgs"]
    assert {(o["name"], o["score"]) for o in orgs} == {("Alibaba", 42), ("Moonshot AI", 42)}


def test_lab_is_not_charged_twice_when_it_is_the_incident_org(make_accomplice, rubric):
    inc = _multi_lab(make_accomplice)
    inc["models"][1]["org"] = "Alibaba"
    orgs = build_scores([inc], rubric, "now")["boards"]["accomplice"]["all"]["orgs"]
    assert [(o["name"], o["score"]) for o in orgs] == [("Alibaba", 42)]


def test_same_model_shares_one_row_across_incidents(make_accomplice, rubric):
    led_by_other = _multi_lab(make_accomplice, id="a")
    led_by_lab = make_accomplice(id="b", org="Moonshot AI")
    led_by_lab["models"] = [{"name": "Kimi K2", "codename": None, "family": "kimi", "share": 1}]
    models = build_scores([led_by_other, led_by_lab], rubric, "now")["boards"]["accomplice"]["all"]["models"]
    kimi = [m for m in models if m["name"] == "Kimi K2"]
    assert [(m["slug"], m["incidents"], m["score"]) for m in kimi] == [("moonshot-ai-kimi-k2", ["a", "b"], 63)]


def test_modified_model_from_another_lab(make_accomplice, rubric):
    inc = _multi_lab(make_accomplice)
    inc["models"][1].update(modified_by="OrcaRouter", modification="abliterated")
    board = build_scores([inc], rubric, "now")["boards"]["accomplice"]["all"]
    row = next(m for m in board["models"] if m["name"] == "Kimi K2")
    assert (row["slug"], row["org"], row["base_org"]) == ("orcarouter-kimi-k2", "OrcaRouter", "Moonshot AI")
    assert {o["name"] for o in board["orgs"]} == {"Alibaba", "Moonshot AI", "OrcaRouter"}
