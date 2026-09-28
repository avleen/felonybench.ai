from scripts.scoring import breakdown, dwell_points


def test_worked_example_scores_87(make_incident, rubric):
    b = breakdown(make_incident(), rubric)
    assert b["sentence_years"] == 20
    assert b["base"] == 40
    assert b["tradecraft"] == 15
    assert b["pettiness"] == 25
    assert b["dwell"] == 7
    assert b["total"] == 87


def test_recidivism_multiplies_total(make_incident, rubric):
    assert breakdown(make_incident(), rubric, recidivist=True)["total"] == 108.75


def test_sandbox_league_fixes_blast_radius(make_incident, rubric):
    b = breakdown(make_incident(league="sandbox", scoring={"blast_radius": "sandbox"}), rubric)
    assert b["blast_radius"] == 1
    assert b["base"] == 40


def test_open_league_sandbox_blast_radius(make_incident, rubric):
    b = breakdown(make_incident(scoring={"blast_radius": "sandbox"}), rubric)
    assert b["base"] == 4


def test_duplicate_tradecraft_counts_once(make_incident, rubric):
    b = breakdown(make_incident(scoring={"tradecraft": ["zero_day", "zero_day"]}), rubric)
    assert b["tradecraft"] == 6


def test_dwell_bands(rubric):
    assert dwell_points({"dwell_days": 0, "detected_by": "lab"}, rubric) == 0
    assert dwell_points({"dwell_days": 6, "detected_by": "lab"}, rubric) == 4
    assert dwell_points({"dwell_days": 7, "detected_by": "lab"}, rubric) == 8
    assert dwell_points({"dwell_days": 45, "detected_by": "victim"}, rubric) == 15
