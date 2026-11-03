"""Validate incident files against the schema, the rubric and the source rules."""
import argparse
import json
import math
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from scripts.rubric import DEFAULT_RUBRIC, ROOT, load_rubric
from scripts.scoring import model_lab, model_slug, slugify, to_date

SCHEMA = ROOT / "schema" / "incident.schema.json"
NEWS_REQUIRED = "sources: at least one 'news' source is required"
ACCOMPLICE_ONLY = ("contribution", "guardrails", "legal_status")
UNSUPERVISED_ONLY = ("autonomy", "motive")  # Open and Sandbox: what the model did on its own
PUBLISHER_ALIASES = {"Google DeepMind": ("Google",), "Moonshot AI": ("Moonshot",), "Zhipu AI": ("Zhipu",)}
UNDISCLOSED_NAME = "Undisclosed model"  # one spelling, so a lab's unnamed models share one board row


def load_validator(path: Path = SCHEMA) -> Draft202012Validator:
    return Draft202012Validator(json.loads(Path(path).read_text()))


def _jsonable(data):
    # YAML turns bare dates into date objects; the schema expects strings.
    return json.loads(json.dumps(data, default=str))


def _parse_date(value) -> date | None:
    """The schema only checks the shape, so 2026-13-45 reaches here."""
    try:
        return to_date(value)
    except ValueError:
        return None


def _date_errors(incident: dict) -> list[str]:
    errors = []
    occurred, reported = _parse_date(incident["date"]), _parse_date(incident["reported"])
    if occurred is None:
        errors.append(f"date: '{incident['date']}' is not a real date")
    if reported is None:
        errors.append(f"reported: '{incident['reported']}' is not a real date")
    if occurred is None or reported is None:
        return errors
    # A day of grace, because an incident can be dated in a time zone ahead of UTC.
    latest = datetime.now(timezone.utc).date() + timedelta(days=1)
    if occurred > latest:
        errors.append(f"date: {occurred} is in the future")
    if reported > latest:
        errors.append(f"reported: {reported} is in the future")
    if reported < occurred:
        errors.append("reported: earlier than date")
    if incident["date_precision"] == "month" and occurred.day != 1:
        errors.append("date_precision: 'month' dates must be the first of the month")
    if not incident["id"].startswith(f"{occurred}-"):
        errors.append(f"id: '{incident['id']}' must start with its date, {occurred}")
    return errors


def _non_text_values(value, path: str = "") -> list[str]:
    if isinstance(value, dict):
        return [e for k, v in value.items() for e in _non_text_values(v, f"{path}{k}/")]
    if isinstance(value, list):
        return [e for i, v in enumerate(value) for e in _non_text_values(v, f"{path}{i}/")]
    if isinstance(value, date):
        return [f"{path.rstrip('/')}: '{value}' must be quoted, or YAML reads it as a date"]
    if value is None or isinstance(value, (str, int, float, bool)):
        return []
    return [f"{path.rstrip('/')}: YAML reads this as {type(value).__name__}, not as plain data"]


def _yaml_type_errors(incident: dict) -> list[str]:
    """The schema sees everything as text, so a bare 2026-07-16 or a !!binary would crash the checks below."""
    return _non_text_values(
        {k: v for k, v in incident.items() if k not in ("date", "reported") or not isinstance(v, (date, str))}
    )


def _identity_errors(incident: dict) -> list[str]:
    """Slugs become URLs and board rows, so an empty or repeated one breaks the site or merges rows."""
    errors = []
    if not slugify(incident["org"]):
        errors.append(f"org: '{incident['org']}' has no letters or digits in a-z0-9 to build a URL from")
    for m in incident["models"]:
        if not slugify(m["name"]):
            errors.append(f"models: '{m['name']}' has no letters or digits in a-z0-9 to build a URL from")
        if "org" in m and not slugify(m["org"]):
            errors.append(f"models: org '{m['org']}' has no letters or digits in a-z0-9 to build a URL from")
        if re.search(r"undisclosed|unnamed|unknown", m["name"], re.I) and m["name"] != UNDISCLOSED_NAME:
            errors.append(f"models: '{m['name']}' must be exactly '{UNDISCLOSED_NAME}' when the model isn't named")
        # Without a known model, nothing shows it's the same line as an earlier offense.
        if m["name"] == UNDISCLOSED_NAME and m.get("family") is not None:
            errors.append(f"models: '{UNDISCLOSED_NAME}' must have family null, so it can't count as a repeat offense")
    slugs = [model_slug(incident, m) for m in incident["models"]]
    if len(slugs) != len(set(slugs)):
        errors.append("models: the same model is listed twice; give it one entry with the combined share")
    return errors


def _is_lab_publisher(org: str, publisher: str) -> bool:
    """Whole words, so Meta isn't Metasploit. Some labs publish under their parent's name."""
    return any(re.search(rf"\b{re.escape(name)}\b", publisher, re.I) for name in (org, *PUBLISHER_ALIASES.get(org, ())))


def validate_incident(incident: dict, stem: str, rubric: dict, validator) -> list[str]:
    errors = [
        f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
        for e in validator.iter_errors(_jsonable(incident))
    ]
    if errors:
        return errors
    errors = _yaml_type_errors(incident)
    if errors:
        return errors

    if incident["id"] != stem:
        errors.append(f"id '{incident['id']}' does not match filename '{stem}'")

    s = incident["scoring"]
    # NaN gets past the schema's bounds, because every comparison with it is false.
    numbers = [("statutes: max_years", x["max_years"]) for x in incident["statutes"]]
    numbers += [("models: share", m["share"]) for m in incident["models"]]
    not_finite = [label for label, value in numbers if not math.isfinite(value)]
    errors += [f"{label} must be a finite number" for label in not_finite]

    errors += _identity_errors(incident)
    errors += _date_errors(incident)

    if incident["league"] == "accomplice":
        errors += [f"scoring.{f}: only used outside the Accomplice League" for f in UNSUPERVISED_ONLY if f in s]
        acc = rubric["accomplice"]
        checks = (
            ("contribution", acc["contribution"]),
            ("guardrails", acc["guardrails"]),
            ("legal_status", acc["legal_status"]),
            ("blast_radius", rubric["blast_radius"]),
        )
        # `org` is the lead model's lab, and it gets charged, so it must have a model here.
        if all(model_lab(incident, m) != incident["org"] for m in incident["models"]):
            errors.append(f"models: no model belongs to org '{incident['org']}'")
    else:
        errors += [f"scoring.{f}: only used in the Accomplice League" for f in ACCOMPLICE_ONLY if f in s]
        if "human_actor" in incident:
            errors.append("human_actor: only used in the Accomplice League")
        checks = (
            ("autonomy", rubric["autonomy"]),
            ("blast_radius", rubric["blast_radius"]),
            ("motive", rubric["pettiness"]["motives"]),
        )
        # Co-defendants are only charged when a human used the model.
        if any("org" in m for m in incident["models"]):
            errors.append("models: org is only used in the Accomplice League")
    for field, allowed in checks:
        if s[field] not in allowed:
            errors.append(f"scoring.{field}: '{s[field]}' is not one of {sorted(allowed)}")
    for technique in s["tradecraft"]:
        if technique not in rubric["tradecraft"]["techniques"]:
            errors.append(f"scoring.tradecraft: unknown technique '{technique}'")
    for victim in incident["victims"]:
        if victim["type"] not in rubric["blast_radius"]:
            errors.append(f"victims: type '{victim['type']}' is not one of {sorted(rubric['blast_radius'])}")

    kinds = {source["kind"] for source in incident["sources"]}
    if "news" not in kinds:
        errors.append(NEWS_REQUIRED)
    if incident["tier"] == "verified" and not kinds & {"postmortem", "primary"}:
        errors.append("tier: 'verified' requires a 'postmortem' or 'primary' source")
    # Attribution can't be merely alleged when the lab itself published it. A lab's confirmation
    # quoted only in the press doesn't count, so self_disclosed alone doesn't decide this.
    lab_published = any(
        source["kind"] in ("postmortem", "primary") and _is_lab_publisher(incident["org"], source["publisher"])
        for source in incident["sources"]
    )
    if incident["tier"] == "alleged" and lab_published:
        errors.append("tier: 'alleged' can't apply when the lab itself published the incident")

    if not not_finite:
        total_share = sum(m["share"] for m in incident["models"])
        if abs(total_share - 1) > 1e-6:
            errors.append(f"models: shares sum to {total_share}, expected 1")
    return errors


def validate_dir(directory: Path, rubric: dict, validator) -> dict[str, list[str]]:
    results, seen, families = {}, {}, {}
    org_names, model_names = {}, {}  # slug -> spelling -> files
    for path in sorted(Path(directory).glob("*.yaml")):
        try:
            incident = yaml.safe_load(path.read_text())
        except (yaml.YAMLError, ValueError) as e:  # ValueError: not UTF-8, or a date like 2026-13-45
            results[path.name] = [f"YAML: {e}"]
            continue
        if not isinstance(incident, dict):
            results[path.name] = ["not a YAML mapping"]
            continue
        try:
            _jsonable(incident)
        except (TypeError, ValueError, RecursionError) as e:  # a date used as a key, or a YAML alias loop
            results[path.name] = [f"YAML: not plain data: {e}"]
            continue
        errors = validate_incident(incident, path.stem, rubric, validator)
        incident_id = incident.get("id")
        if isinstance(incident_id, str):
            if incident_id in seen:
                errors.append(f"duplicate id, also in {seen[incident_id]}")
            seen.setdefault(incident_id, path.name)
        if errors:
            results[path.name] = errors
        # Other rule errors, like a missing news source, must not hide a misfiled model.
        if validator.is_valid(_jsonable(incident)) and not _yaml_type_errors(incident):
            for name in {incident["org"], *(model_lab(incident, m) for m in incident["models"])}:
                org_names.setdefault(slugify(name), {}).setdefault(name, []).append(path.name)
            for m in incident["models"]:
                if m.get("family"):
                    families.setdefault(m["family"], {}).setdefault(model_lab(incident, m), []).append(path.name)
                spelling = (model_lab(incident, m), m["name"])  # a tuple, so "A: B" + "C" isn't "A" + "B: C"
                model_names.setdefault(model_slug(incident, m), {}).setdefault(spelling, []).append(path.name)
    # A family is one lab's model line, so a second lab usually means a model is missing its `org`.
    for family, labs in families.items():
        if len(labs) > 1:
            message = f"models: family '{family}' is filed under more than one lab: {sorted(labs)}"
            for names in labs.values():
                for name in names:
                    results.setdefault(name, []).append(message)
    # One slug is one board row and one URL, so two spellings would merge or shadow each other.
    for kind, slugs in (("org", org_names), ("model", model_names)):
        for slug, spellings in slugs.items():
            if len(spellings) > 1:
                message = f"{kind} slug '{slug}' has more than one spelling: {sorted(spellings)}"
                for names in spellings.values():
                    for name in names:
                        results.setdefault(name, []).append(message)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incidents", type=Path, default=ROOT / "incidents")
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC)
    args = parser.parse_args(argv)

    results = validate_dir(args.incidents, load_rubric(args.rubric), load_validator())
    for name, errors in results.items():
        print(name)
        for error in errors:
            print(f"  - {error}")
    if not results:
        print("All incidents valid.")
    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
