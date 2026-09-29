from scripts.rubric import load_rubric


def test_rubric_version():
    assert load_rubric()["version"] == "1.1"


def test_tradecraft_points_sum_to_max():
    tc = load_rubric()["tradecraft"]
    assert sum(t["points"] for t in tc["techniques"].values()) == tc["max"]


def test_dwell_bands_are_contiguous():
    bands = load_rubric()["dwell"]["bands"]
    for prev, nxt in zip(bands, bands[1:]):
        assert nxt["min_days"] == prev["max_days"] + 1
    assert bands[-1]["max_days"] is None


def test_blast_radius_order_is_ascending():
    multipliers = [b["multiplier"] for b in load_rubric()["blast_radius"].values()]
    assert multipliers == sorted(multipliers)


def test_accomplice_section():
    a = load_rubric()["accomplice"]
    assert [c["multiplier"] for c in a["contribution"].values()] == [0.25, 0.5, 1, 1.5, 2]
    assert [g["points"] for g in a["guardrails"].values()] == [0, 5, 10]
    assert a["legal_status"] == {"crime": {"multiplier": 1, "label": "Crime"},
                                 "contested": {"multiplier": 0.5, "label": "Legality contested"}}


def test_rubric_version_bumped():
    r = load_rubric()
    assert r["version"] == "1.1"
    assert r["changelog"][-1]["version"] == "1.1"
