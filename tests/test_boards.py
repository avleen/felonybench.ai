from scripts.scoring import build_scores


def _incidents(make_incident):
    openai = make_incident()
    anthropic = make_incident(
        id="2026-08-01-anthropic-example",
        date="2026-08-01",
        reported="2026-08-02",
        org="Anthropic",
        tier="alleged",
        models=[{"name": "claude-x", "codename": None, "family": "claude", "share": 1}],
        scoring={"self_disclosed": False, "blast_radius": "foreign_government"},
    )
    return [anthropic, openai]


def test_verified_board_excludes_alleged(make_incident, rubric):
    boards = build_scores(_incidents(make_incident), rubric, "now")["boards"]
    orgs = boards["open"]["verified"]["orgs"]
    assert [o["name"] for o in orgs] == ["OpenAI"]
    assert orgs[0]["score"] == 87
    assert orgs[0]["rank"] == 1


def test_all_board_includes_alleged(make_incident, rubric):
    orgs = build_scores(_incidents(make_incident), rubric, "now")["boards"]["open"]["all"]["orgs"]
    assert [o["name"] for o in orgs] == ["Anthropic", "OpenAI"]
    assert orgs[0]["alleged"] == 1
    assert orgs[0]["peak_blast_radius"] == "foreign_government"


def test_model_shares_split_points(make_incident, rubric):
    models = build_scores(_incidents(make_incident), rubric, "now")["boards"]["open"]["verified"]["models"]
    assert [(m["slug"], m["score"]) for m in models] == [("openai-model-a", 43.5), ("openai-model-b", 43.5)]
    assert models[0]["sentence_years"] == 10


def test_org_counts_multi_model_incident_once(make_incident, rubric):
    orgs = build_scores(_incidents(make_incident), rubric, "now")["boards"]["open"]["verified"]["orgs"]
    assert orgs[0]["incidents"] == ["2026-07-16-openai-exploitgym-huggingface"]


def test_badges(make_incident, rubric):
    scores = build_scores(_incidents(make_incident), rubric, "now")
    orgs = {o["name"]: o for o in scores["boards"]["open"]["all"]["orgs"]}
    assert orgs["OpenAI"]["badges"] == ["cooperating_witness"]
    assert orgs["Anthropic"]["badges"] == ["international_incident"]


def test_trends_are_cumulative_and_sorted(make_incident, rubric):
    second = make_incident(id="2026-09-01-openai-again", date="2026-09-01", reported="2026-09-02")
    scores = build_scores([second, make_incident()], rubric, "now")
    points = scores["trends"]["open"]["verified"]["OpenAI"]
    assert [p["date"] for p in points] == ["2026-07-16", "2026-09-01"]
    assert points[0]["cumulative"] == 87
    assert points[1]["cumulative"] == 87 + 108.75  # second one is a repeat offense


def test_scored_incidents_carry_model_slugs_and_rubric(make_incident, rubric):
    scores = build_scores([make_incident()], rubric, "now")
    assert scores["incidents"][0]["models"][0]["slug"] == "openai-model-a"
    assert scores["incidents"][0]["breakdown"]["total"] == 87
    assert scores["rubric"]["version"] == "1.1"
    assert scores["last_incident_date"] == {"open": "2026-07-16", "sandbox": None, "accomplice": None}


def test_empty_input(rubric):
    scores = build_scores([], rubric, "now")
    assert scores["boards"]["open"]["verified"] == {"models": [], "orgs": []}


def test_sandbox_board_is_separate_with_fixed_blast_radius(make_incident, rubric):
    sandbox = make_incident(id="2026-08-01-openai-sandbox", league="sandbox", scoring={"blast_radius": "government"})
    scores = build_scores([sandbox, make_incident()], rubric, "now")
    orgs = scores["boards"]["sandbox"]["verified"]["orgs"]
    assert [(o["name"], o["score"]) for o in orgs] == [("OpenAI", 87)]  # blast fixed at ×1, not ×2
    assert orgs[0]["peak_blast_radius"] == "government"
    assert scores["boards"]["open"]["verified"]["orgs"][0]["incidents"] == ["2026-07-16-openai-exploitgym-huggingface"]
