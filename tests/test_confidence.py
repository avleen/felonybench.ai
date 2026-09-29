from scripts.scoring import build_scores


def _pair(make_incident, low_date="2026-06-01", high_date="2026-07-16"):
    """A low-confidence OpenAI incident and a high-confidence one, same model family."""
    low = make_incident(id="low", date=low_date, confidence="low")
    high = make_incident(id="high", date=high_date)
    return [low, high]


def test_confident_view_leaves_out_low_confidence_incidents(make_incident, rubric):
    scores = build_scores(_pair(make_incident), rubric, "now")
    everything = scores["boards"]["open"]["verified"]["orgs"][0]
    confident = scores["confident"]["boards"]["open"]["verified"]["orgs"][0]
    assert everything["incidents"] == ["low", "high"]
    assert confident["incidents"] == ["high"]


def test_medium_confidence_counts_in_the_confident_view(make_incident, rubric):
    incident = make_incident(confidence="medium")
    orgs = build_scores([incident], rubric, "now")["confident"]["boards"]["open"]["verified"]["orgs"]
    assert [o["incidents"] for o in orgs] == [[incident["id"]]]


def test_a_low_confidence_incident_cannot_make_another_a_repeat_offense(make_incident, rubric):
    # 45 days apart, same family: with everything counted, "high" is a repeat offense.
    scores = build_scores(_pair(make_incident), rubric, "now")
    everything = {r["slug"]: r for r in scores["boards"]["open"]["verified"]["models"]}
    confident = {r["slug"]: r for r in scores["confident"]["boards"]["open"]["verified"]["models"]}
    single = build_scores([make_incident(id="high", date="2026-07-16")], rubric, "now")
    alone = {r["slug"]: r for r in single["boards"]["open"]["verified"]["models"]}
    assert "repeat_offender" in everything["openai-model-a"]["badges"]
    assert confident["openai-model-a"]["score"] == alone["openai-model-a"]["score"]
    assert "repeat_offender" not in confident["openai-model-a"]["badges"]


def test_confident_trends_and_last_incident_date(make_incident, rubric):
    scores = build_scores(_pair(make_incident, low_date="2026-08-01"), rubric, "now")
    assert scores["last_incident_date"]["open"] == "2026-08-01"
    assert scores["confident"]["last_incident_date"]["open"] == "2026-07-16"
    points = scores["confident"]["trends"]["open"]["verified"]["OpenAI"]
    assert [p["incident_id"] for p in points] == ["high"]


def test_confident_view_lists_the_ids_it_counts(make_incident, rubric):
    scores = build_scores(_pair(make_incident), rubric, "now")
    assert scores["confident"]["incident_ids"] == ["high"]


def test_confident_view_carries_each_incidents_rescored_breakdown_and_badges(make_incident, rubric):
    scores = build_scores(_pair(make_incident), rubric, "now")
    full = {i["id"]: i for i in scores["incidents"]}
    rescored = scores["confident"]["scored"]
    assert set(rescored) == {"high"}
    assert full["high"]["breakdown"]["recidivist"] is True
    assert rescored["high"]["breakdown"]["recidivist"] is False
    assert rescored["high"]["breakdown"]["total"] < full["high"]["breakdown"]["total"]
    assert "repeat_offender" in full["high"]["badges"]
    assert "repeat_offender" not in rescored["high"]["badges"]
