import subprocess
import sys
from datetime import date

import pytest
import yaml

from scripts.rubric import ROOT
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


def _write(directory, incident):
    (directory / f"{incident['id']}.yaml").write_text(yaml.safe_dump(incident))


def _dir_errors(directory, rubric):
    return validate_dir(directory, rubric, load_validator())


@pytest.mark.parametrize("field, value", [("date", "2026-13-45"), ("date", "2026-02-30"), ("reported", "2026-02-30"), ("date", "2026-07-16\n")])
def test_impossible_dates_are_errors_not_crashes(make_incident, rubric, field, value):
    errors = _errors(make_incident(**{field: value}), rubric)
    assert any(e.startswith(f"{field}:") for e in errors)


@pytest.mark.parametrize("field", ["date", "reported"])
def test_future_dates_are_errors(make_incident, rubric, field):
    incident = make_incident(id="2999-01-01-openai-x", date="2999-01-01", reported="2999-01-01")
    assert f"{field}: 2999-01-01 is in the future" in _errors(incident, rubric, stem=incident["id"])


def test_id_must_start_with_the_date(make_incident, rubric):
    assert any("must start with its date" in e for e in _errors(make_incident(date="2026-07-15"), rubric))


def test_date_precision_is_required(make_incident, rubric):
    incident = make_incident()
    del incident["date_precision"]
    assert "(root): 'date_precision' is a required property" in _errors(incident, rubric)


def test_statute_years_must_be_finite(make_incident, rubric):
    incident = make_incident()
    incident["statutes"][0]["max_years"] = float("nan")
    assert "statutes: max_years must be a finite number" in _errors(incident, rubric)


@pytest.mark.parametrize("value", [float("inf"), 10 ** 400, 1e308])
def test_statute_years_have_a_ceiling(make_incident, rubric, value):
    incident = make_incident()
    incident["statutes"][0]["max_years"] = value
    assert any(e.startswith("statutes/0/max_years") for e in _errors(incident, rubric))


def test_share_must_be_finite(make_incident, rubric):
    incident = make_incident()
    incident["models"][0]["share"] = float("nan")
    assert "models: share must be a finite number" in _errors(incident, rubric)


@pytest.mark.parametrize("name", ["模型一", "---", "   "])
def test_model_name_must_make_a_slug(make_incident, rubric, name):
    incident = make_incident()
    incident["models"][0]["name"] = name
    assert any(e.startswith(f"models: '{name}' has no letters") for e in _errors(incident, rubric))


@pytest.mark.parametrize("org", ["深度求索", "   "])
def test_org_must_make_a_slug(make_incident, rubric, org):
    assert any(e.startswith(f"org: '{org}' has no letters") for e in _errors(make_incident(org=org), rubric))


def test_co_defendant_org_must_make_a_slug(make_accomplice, rubric):
    inc = make_accomplice()
    inc["models"] = [{**inc["models"][0], "share": 0.5}, {"name": "Kimi", "family": "kimi", "org": "月之暗面", "share": 0.5}]
    assert any("org '月之暗面' has no letters" in e for e in _errors(inc, rubric, stem=inc["id"]))


def test_same_model_twice_in_one_incident_is_an_error(make_incident, rubric):
    incident = make_incident()
    incident["models"][1]["name"] = "Model A"  # same slug as model-a
    assert any("listed twice" in e for e in _errors(incident, rubric))


@pytest.mark.parametrize("field", ["contribution", "guardrails", "legal_status"])
def test_accomplice_fields_are_rejected_elsewhere(make_incident, rubric, field):
    assert f"scoring.{field}: only used in the Accomplice League" in _errors(make_incident(scoring={field: "crime"}), rubric)


def test_human_actor_is_rejected_outside_accomplice(make_incident, rubric):
    assert "human_actor: only used in the Accomplice League" in _errors(make_incident(human_actor="Someone"), rubric)


@pytest.mark.parametrize("field", ["autonomy", "motive"])
def test_unsupervised_fields_are_rejected_in_accomplice(make_accomplice, rubric, field):
    inc = make_accomplice(scoring={field: "emergent"})
    assert f"scoring.{field}: only used outside the Accomplice League" in _errors(inc, rubric, stem=inc["id"])


def test_two_spellings_of_one_org_are_errors_in_both_files(make_incident, tmp_path, rubric):
    a, b = make_incident(id="2026-07-16-openai-a"), make_incident(id="2026-07-17-openai-b", org="Openai")
    _write(tmp_path, a), _write(tmp_path, b)
    results = _dir_errors(tmp_path, rubric)
    assert any("org slug 'openai'" in e for e in results[f"{a['id']}.yaml"])
    assert any("org slug 'openai'" in e for e in results[f"{b['id']}.yaml"])


def test_two_spellings_of_one_model_are_errors(make_incident, tmp_path, rubric):
    a, b = make_incident(id="2026-07-16-openai-a"), make_incident(id="2026-07-17-openai-b")
    b["models"][0]["name"] = "Model A"
    _write(tmp_path, a), _write(tmp_path, b)
    assert any("model slug 'openai-model-a'" in e for e in _dir_errors(tmp_path, rubric)[f"{b['id']}.yaml"])


def test_lab_and_name_that_run_together_into_one_slug_are_errors(make_accomplice, tmp_path, rubric):
    a = make_accomplice(id="2026-07-16-acme-a", org="Acme Labs")
    a["models"] = [{"name": "One", "family": None, "share": 1}]
    b = make_accomplice(id="2026-07-17-acme-b", org="Acme")
    b["models"] = [{"name": "Labs One", "family": None, "share": 1}]
    _write(tmp_path, a), _write(tmp_path, b)
    assert any("model slug 'acme-labs-one'" in e for e in _dir_errors(tmp_path, rubric)[f"{a['id']}.yaml"])


def test_same_spelling_across_files_is_fine(make_incident, tmp_path, rubric):
    _write(tmp_path, make_incident(id="2026-07-16-openai-a")), _write(tmp_path, make_incident(id="2026-07-17-openai-b"))
    assert _dir_errors(tmp_path, rubric) == {}


@pytest.mark.parametrize("content", [
    b"{", b"[1, 2]", b"", b"just text", b"\xff\xfe not utf-8", b"date: 2026-13-45\n", b"id: [a, b]\n",
    b"2026-07-16: a date as a key\n", b"a: &a {b: *a}\n",
])
def test_bad_files_are_reported_per_file_not_raised(tmp_path, rubric, make_incident, content):
    (tmp_path / "2026-01-01-bad.yaml").write_bytes(content)
    good = make_incident(id="2026-07-16-openai-a")
    _write(tmp_path, good)
    results = _dir_errors(tmp_path, rubric)
    assert results["2026-01-01-bad.yaml"]
    assert f"{good['id']}.yaml" not in results


def _cli(directory):
    return subprocess.run(
        [sys.executable, "-m", "scripts.validate", "--incidents", str(directory)],
        cwd=ROOT, capture_output=True, text=True,
    )


def test_cli_exits_nonzero_on_a_bad_incident(tmp_path):
    (tmp_path / "2026-01-01-bad.yaml").write_text("{")
    result = _cli(tmp_path)
    assert result.returncode == 1 and "2026-01-01-bad.yaml" in result.stdout


def test_cli_exits_zero_when_valid(make_incident, tmp_path):
    _write(tmp_path, make_incident())
    result = _cli(tmp_path)
    assert result.returncode == 0 and "All incidents valid." in result.stdout


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


@pytest.mark.parametrize(
    "where",
    ["model name", "model org", "org", "publisher", "summary"],
)
def test_an_unquoted_date_outside_the_date_fields_is_an_error_not_a_crash(make_incident, make_accomplice, tmp_path, rubric, where):
    incident = make_accomplice() if where == "model org" else make_incident()
    bare = date(2026, 7, 16)
    if where == "model name":
        incident["models"][0]["name"] = bare
    elif where == "model org":
        incident["models"][0]["share"] = 0.5
        incident["models"].append({"name": "Other", "codename": None, "family": None, "org": bare, "share": 0.5})
    elif where == "org":
        incident["org"] = bare
    elif where == "publisher":
        incident["sources"][0]["publisher"] = bare
    else:
        incident["summary"] = bare
    (tmp_path / f"{incident['id']}.yaml").write_text(yaml.safe_dump(incident))
    errors = validate_dir(tmp_path, rubric, load_validator())[f"{incident['id']}.yaml"]
    assert any("must be quoted" in e and "2026-07-16" in e for e in errors)


def _write_yaml_with(tmp_path, incident, field, tagged):
    """Write YAML by hand, because safe_dump would never produce these tags from a test's data."""
    text = yaml.safe_dump(incident)
    current = f"{field}: {yaml.safe_dump(incident[field]).splitlines()[0]}"
    assert current in text
    (tmp_path / f"{incident['id']}.yaml").write_text(text.replace(current, f"{field}: {tagged}", 1))


@pytest.mark.parametrize("tagged", ["!!binary TW9kZWw=", "!!set {a, b}", "!!omap [a: 1]"])
@pytest.mark.parametrize("field", ["org", "summary", "date"])
def test_a_tagged_yaml_value_is_reported_without_crashing(make_incident, tmp_path, rubric, field, tagged):
    incident = make_incident()
    _write_yaml_with(tmp_path, incident, field, tagged)
    assert validate_dir(tmp_path, rubric, load_validator())[f"{incident['id']}.yaml"]


def test_a_binary_model_name_is_reported_without_crashing(make_incident, tmp_path, rubric):
    incident = make_incident()
    name = incident["models"][0]["name"]
    text = yaml.safe_dump(incident)
    assert f"name: {name}" in text
    (tmp_path / f"{incident['id']}.yaml").write_text(text.replace(f"name: {name}", "name: !!binary TW9kZWw=", 1))
    errors = validate_dir(tmp_path, rubric, load_validator())[f"{incident['id']}.yaml"]
    assert any("bytes" in e for e in errors)


@pytest.mark.parametrize("text", ["org: !!bool foo\n", 'org: !!int ""\n', 'org: !!float ""\n', "org: !!timestamp foo\n", "[" * 3000, "org: " + ":".join(["1"] * 180) + ".0\n"])
def test_yaml_that_pyyaml_cant_construct_is_reported_without_crashing(tmp_path, rubric, text):
    (tmp_path / "bad.yaml").write_text(text)
    (tmp_path / "other.yaml").write_text("{}\n")
    results = validate_dir(tmp_path, rubric, load_validator())
    assert results["bad.yaml"][0].startswith("YAML: ")
    assert results["other.yaml"]


@pytest.mark.parametrize("text", [
    "a: &a [*a]\n",
    "a0: &a0 [x, x]\n" + "".join(f"a{n}: &a{n} [*a{n - 1}, *a{n - 1}]\n" for n in range(1, 41)),
])
def test_yaml_aliases_are_reported_without_expanding_them(tmp_path, rubric, text):
    (tmp_path / "bad.yaml").write_text(text)
    assert "aliases" in validate_dir(tmp_path, rubric, load_validator())["bad.yaml"][0]


def test_the_date_fields_may_stay_unquoted(make_incident, tmp_path, rubric):
    incident = make_incident(date=date(2026, 1, 1), reported=date(2026, 1, 2), id="2026-01-01-openai-a")
    (tmp_path / f"{incident['id']}.yaml").write_text(yaml.safe_dump(incident))
    assert validate_dir(tmp_path, rubric, load_validator()) == {}


def test_model_spellings_that_only_match_when_joined_still_collide(make_incident, tmp_path, rubric):
    one = make_incident(id="2026-01-01-a", org="Acme: Labs", models=[{"name": "One", "codename": None, "family": None, "share": 1}])
    two = make_incident(id="2026-01-02-b", org="Acme", models=[{"name": "Labs: One", "codename": None, "family": None, "share": 1}])
    for incident in (one, two):
        (tmp_path / f"{incident['id']}.yaml").write_text(yaml.safe_dump(incident))
    results = validate_dir(tmp_path, rubric, load_validator())
    message = "model slug 'acme-labs-one' has more than one spelling"
    assert any(message in e for e in results[f"{one['id']}.yaml"])
    assert any(message in e for e in results[f"{two['id']}.yaml"])
