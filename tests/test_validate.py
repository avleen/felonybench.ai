import yaml

from scripts.validate import load_validator, validate_dir, validate_incident

STEM = "2026-07-16-openai-exploitgym-huggingface"


def _errors(incident, rubric, stem=STEM):
    return validate_incident(incident, stem, rubric, load_validator())


def test_valid_incident(make_incident, rubric):
    assert _errors(make_incident(), rubric) == []


def test_requires_news_source(make_incident, rubric):
    incident = make_incident()
    incident["sources"] = [s for s in incident["sources"] if s["kind"] != "news"]
    assert any("news" in e for e in _errors(incident, rubric))


def test_verified_requires_primary_or_postmortem(make_incident, rubric):
    incident = make_incident()
    incident["sources"] = [s for s in incident["sources"] if s["kind"] == "news"]
    assert any("verified" in e for e in _errors(incident, rubric))
    incident["tier"] = "alleged"
    assert _errors(incident, rubric) == []


def test_shares_must_sum_to_one(make_incident, rubric):
    incident = make_incident()
    incident["models"][0]["share"] = 0.4
    assert any("shares" in e for e in _errors(incident, rubric))


def test_scoring_values_come_from_rubric(make_incident, rubric):
    assert any("autonomy" in e for e in _errors(make_incident(scoring={"autonomy": "vibes"}), rubric))
    assert any("tradecraft" in e for e in _errors(make_incident(scoring={"tradecraft": ["magic"]}), rubric))


def test_id_matches_filename(make_incident, rubric):
    assert any("filename" in e for e in _errors(make_incident(), rubric, stem="other"))


def test_reported_not_before_date(make_incident, rubric):
    assert any("reported" in e for e in _errors(make_incident(reported="2026-01-01"), rubric))


def test_schema_errors_reported(make_incident, rubric):
    incident = make_incident()
    del incident["summary"]
    assert any("summary" in e for e in _errors(incident, rubric))


def test_validate_dir_accepts_yaml_dates(tmp_path, make_incident, rubric):
    incident = make_incident()
    text = yaml.safe_dump(incident).replace("'2026-07-16'", "2026-07-16").replace("'2026-07-21'", "2026-07-21")
    (tmp_path / f"{STEM}.yaml").write_text(text)
    assert validate_dir(tmp_path, rubric, load_validator()) == {}


def test_validate_dir_flags_duplicate_ids(tmp_path, make_incident, rubric):
    # Named to sort alphabetically after STEM, so it is the second file seen
    # (validate_dir processes files in sorted order; the first occurrence of
    # an id wins, later ones are flagged as duplicates).
    (tmp_path / f"{STEM}.yaml").write_text(yaml.safe_dump(make_incident()))
    (tmp_path / "2026-07-16-zzz-copy.yaml").write_text(yaml.safe_dump(make_incident()))
    results = validate_dir(tmp_path, rubric, load_validator())
    assert any("duplicate" in e for e in results["2026-07-16-zzz-copy.yaml"])


def test_missing_ids_are_not_duplicates(tmp_path, make_incident, rubric):
    for name in ("2026-01-01-a", "2026-01-02-b"):
        incident = make_incident()
        del incident["id"]
        (tmp_path / f"{name}.yaml").write_text(yaml.safe_dump(incident))
    results = validate_dir(tmp_path, rubric, load_validator())
    assert not any("duplicate" in e for errors in results.values() for e in errors)


def test_victim_type_comes_from_rubric(make_incident, rubric):
    incident = make_incident()
    incident["victims"][0]["type"] = "moon_base"
    assert any("victims" in e for e in _errors(incident, rubric))


def test_month_precision_dates_must_be_first_of_month(make_incident, rubric):
    incident = make_incident(id="2026-07-01-openai-x", date="2026-07-01", date_precision="month")
    assert _errors(incident, rubric, stem="2026-07-01-openai-x") == []
    incident = make_incident(id="2026-07-16-openai-x", date_precision="month")
    assert any("date_precision" in e for e in _errors(incident, rubric, stem="2026-07-16-openai-x"))


def test_date_precision_values(make_incident, rubric):
    assert any("date_precision" in e for e in _errors(make_incident(date_precision="year"), rubric))
    assert _errors(make_incident(date_precision="day"), rubric) == []
