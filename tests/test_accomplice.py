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
