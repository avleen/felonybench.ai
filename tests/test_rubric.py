from scripts.rubric import load_rubric


def test_rubric_version():
    assert load_rubric()["version"] == "1.0"


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
