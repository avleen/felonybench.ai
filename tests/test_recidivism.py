from scripts.scoring import recidivist_ids


def _pair(make_incident, first_date, second_date, family_a="gpt", family_b="gpt", league="open"):
    a = make_incident(id="a", date=first_date)
    b = make_incident(id="b", date=second_date, league=league)
    for m in a["models"]:
        m["family"] = family_a
    for m in b["models"]:
        m["family"] = family_b
    return [a, b]


def test_repeat_within_window(make_incident, rubric):
    assert recidivist_ids(_pair(make_incident, "2026-06-01", "2026-07-16"), rubric) == {"b"}


def test_outside_window(make_incident, rubric):
    assert recidivist_ids(_pair(make_incident, "2026-01-01", "2026-07-16"), rubric) == set()


def test_different_family(make_incident, rubric):
    assert recidivist_ids(_pair(make_incident, "2026-06-01", "2026-07-16", family_b="o"), rubric) == set()


def test_unknown_family_never_repeats(make_incident, rubric):
    assert recidivist_ids(_pair(make_incident, "2026-06-01", "2026-07-16", None, None), rubric) == set()


def test_leagues_are_separate(make_incident, rubric):
    assert recidivist_ids(_pair(make_incident, "2026-06-01", "2026-07-16", league="sandbox"), rubric) == set()


def test_same_day_is_not_a_repeat(make_incident, rubric):
    assert recidivist_ids(_pair(make_incident, "2026-07-16", "2026-07-16"), rubric) == set()
