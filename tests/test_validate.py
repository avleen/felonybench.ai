import pytest
import yaml

from scripts.validate import NEWS_REQUIRED, load_validator, validate_dir, validate_incident

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


def test_before_precision_allows_any_day(make_incident, rubric):
    assert _errors(make_incident(date_precision="before"), rubric) == []


ACC = "2026-06-01-alibaba-abliterated-exploit"


def test_accomplice_incident_valid(make_accomplice, rubric):
    assert _errors(make_accomplice(), rubric, stem=ACC) == []


def test_accomplice_requires_human_actor(make_accomplice, rubric):
    inc = make_accomplice()
    del inc["human_actor"]
    assert any("human_actor" in e for e in _errors(inc, rubric, stem=ACC))


def test_accomplice_requires_its_scoring_fields(make_accomplice, rubric):
    for field in ("contribution", "guardrails", "legal_status"):
        inc = make_accomplice()
        del inc["scoring"][field]
        assert any(field in e for e in _errors(inc, rubric, stem=ACC)), field


def test_accomplice_values_come_from_rubric(make_accomplice, rubric):
    for field, bad in (("contribution", "vibes"), ("guardrails", "melted"), ("legal_status", "vibes")):
        assert any(field in e for e in _errors(make_accomplice(scoring={field: bad}), rubric, stem=ACC)), field


def test_model_crime_leagues_still_require_autonomy(make_incident, rubric):
    inc = make_incident()
    del inc["scoring"]["autonomy"]
    assert any("autonomy" in e for e in _errors(inc, rubric))


def test_model_crime_rationale_still_requires_motive(make_incident, rubric):
    inc = make_incident()
    del inc["rationale"]["motive"]
    assert any("motive" in e for e in _errors(inc, rubric))


def test_public_victims_are_allowed(make_accomplice, rubric):
    inc = make_accomplice(scoring={"blast_radius": "public"})
    inc["victims"] = [{"name": "The public", "type": "public", "country": "US"}]
    assert _errors(inc, rubric, stem=ACC) == []


def test_model_org_only_in_accomplice_league(make_incident, make_accomplice, rubric):
    inc = make_incident()
    inc["models"][0]["org"] = "Moonshot AI"
    assert any("models: org" in e for e in _errors(inc, rubric))
    inc = make_accomplice()
    inc["models"] = [{**inc["models"][0], "share": 0.5},
                     {"name": "Kimi K2", "codename": None, "family": "kimi", "org": "Moonshot AI", "share": 0.5}]
    assert _errors(inc, rubric, stem=ACC) == []


def test_a_model_must_belong_to_the_incident_org(make_accomplice, rubric):
    inc = make_accomplice()
    inc["models"][0]["org"] = "Moonshot AI"
    assert any("no model belongs" in e for e in _errors(inc, rubric, stem=ACC))


def test_family_filed_under_two_labs_is_an_error(make_incident, tmp_path, rubric):
    for stem, org in (("2026-07-16-openai-a", "OpenAI"), ("2026-07-17-anthropic-b", "Anthropic")):
        inc = make_incident(id=stem, org=org)
        for m in inc["models"]:
            m["family"] = "gpt"
        (tmp_path / f"{stem}.yaml").write_text(yaml.safe_dump(inc))
    results = validate_dir(tmp_path, rubric, load_validator())
    assert any("family 'gpt'" in e for e in results["2026-07-17-anthropic-b.yaml"])
    assert any("family 'gpt'" in e for e in results["2026-07-16-openai-a.yaml"])


def test_family_under_its_own_lab_in_another_incident_is_fine(make_accomplice, tmp_path, rubric):
    lead = make_accomplice(id="2026-07-16-anthropic-a", org="Anthropic")
    lead["models"] = [{"name": "Claude", "codename": None, "family": "claude", "share": 0.5},
                      {"name": "Kimi K2", "codename": None, "family": "kimi", "org": "Moonshot AI", "share": 0.5}]
    own = make_accomplice(id="2026-07-17-moonshot-b", org="Moonshot AI")
    own["models"] = [{"name": "Kimi K2", "codename": None, "family": "kimi", "share": 1}]
    for inc in (lead, own):
        (tmp_path / f"{inc['id']}.yaml").write_text(yaml.safe_dump(inc))
    assert validate_dir(tmp_path, rubric, load_validator()) == {}


def _conflicting_family(make_incident, tmp_path, **second):
    first = make_incident(id="2026-07-16-openai-a", org="OpenAI")
    other = make_incident(id="2026-07-17-anthropic-b", org="Anthropic", **second)
    for inc in (first, other):
        for m in inc["models"]:
            m["family"] = "gpt"
        (tmp_path / f"{inc['id']}.yaml").write_text(yaml.safe_dump(inc))
    return "2026-07-17-anthropic-b.yaml"


def test_family_check_covers_an_incident_awaiting_news(make_incident, tmp_path, rubric):
    name = _conflicting_family(make_incident, tmp_path, sources=[
        {"url": "https://example.com/a", "kind": "primary", "publisher": "Example", "title": "Report"}])
    errors = validate_dir(tmp_path, rubric, load_validator())[name]
    assert NEWS_REQUIRED in errors and any("family 'gpt'" in e for e in errors)


def test_family_check_covers_an_incident_with_other_rule_errors(make_incident, tmp_path, rubric):
    name = _conflicting_family(make_incident, tmp_path, reported="2020-01-01")
    errors = validate_dir(tmp_path, rubric, load_validator())[name]
    assert any("earlier than date" in e for e in errors) and any("family 'gpt'" in e for e in errors)


def test_family_check_skips_an_incident_with_malformed_models(make_incident, tmp_path, rubric):
    good = make_incident()
    (tmp_path / f"{good['id']}.yaml").write_text(yaml.safe_dump(good))
    bad = make_incident(id="2026-07-17-anthropic-b", models="not a list")
    (tmp_path / "2026-07-17-anthropic-b.yaml").write_text(yaml.safe_dump(bad))
    results = validate_dir(tmp_path, rubric, load_validator())
    assert list(results) == ["2026-07-17-anthropic-b.yaml"]


def test_contested_needs_a_cited_dispute(make_accomplice, rubric):
    incident = make_accomplice()
    incident["scoring"]["legal_status"] = "contested"
    incident["rationale"].pop("legal_status", None)
    assert any("legal_status" in e and "required" in e for e in _errors(incident, rubric, incident["id"]))
    incident["rationale"]["legal_status"] = "A court is weighing this: example v. example."
    assert _errors(incident, rubric, incident["id"]) == []


def test_a_crime_needs_no_dispute(make_accomplice, rubric):
    incident = make_accomplice()
    incident["scoring"]["legal_status"] = "crime"
    incident["rationale"].pop("legal_status", None)
    assert _errors(incident, rubric, incident["id"]) == []


def test_alleged_cannot_apply_to_the_labs_own_account(make_incident, rubric):
    incident = make_incident(tier="alleged", org="OpenAI")
    incident["sources"] = [
        {"url": "https://openai.com/x", "kind": "postmortem", "publisher": "OpenAI", "title": "T"},
        {"url": "https://wired.com/x", "kind": "news", "publisher": "Wired", "title": "T"},
    ]
    assert any("alleged" in e for e in _errors(incident, rubric, incident["id"]))


def test_alleged_allows_a_third_partys_account_and_press_quotes(make_incident, rubric):
    incident = make_incident(tier="alleged", org="OpenAI")
    incident["sources"] = [
        {"url": "https://x.org/x", "kind": "primary", "publisher": "Transluce", "title": "T"},
        {"url": "https://wired.com/x", "kind": "news", "publisher": "Wired on OpenAI", "title": "T"},
    ]
    incident["scoring"]["self_disclosed"] = True
    assert _errors(incident, rubric, incident["id"]) == []


def test_modifier_fields_are_no_longer_accepted(make_accomplice, rubric):
    inc = make_accomplice()
    inc["models"][0]["modified_by"] = "OrcaRouter"
    assert any("modified_by" in e for e in _errors(inc, rubric, inc["id"]))


def _alleged(make_incident, org, publisher):
    return make_incident(org=org, tier="alleged", sources=[
        {"url": "https://a.example/report", "kind": "primary", "publisher": publisher},
        {"url": "https://b.example/story", "kind": "news", "publisher": "Wired"},
    ])


@pytest.mark.parametrize("org, publisher", [
    ("Google DeepMind", "Google Threat Intelligence Group"),
    ("OpenAI", "OpenAI"),
    ("OpenAI", "openai"),
])
def test_alleged_is_rejected_when_the_lab_published_it(make_incident, rubric, org, publisher):
    assert any("'alleged' can't apply" in e for e in _errors(_alleged(make_incident, org, publisher), rubric))


@pytest.mark.parametrize("org, publisher", [("Meta", "Metasploit"), ("OpenAI", "Transluce")])
def test_alleged_is_fine_when_someone_else_published_it(make_incident, rubric, org, publisher):
    assert not any("'alleged' can't apply" in e for e in _errors(_alleged(make_incident, org, publisher), rubric))


@pytest.mark.parametrize("text", ["", "   "])
def test_contested_needs_a_written_dispute(make_accomplice, rubric, text):
    inc = make_accomplice(scoring={"legal_status": "contested"})
    inc["rationale"]["legal_status"] = text
    assert any(e.startswith("rationale/legal_status") for e in _errors(inc, rubric, stem=inc["id"]))
