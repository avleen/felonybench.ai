"""Validate incident files against the schema, the rubric and the source rules."""
import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from scripts.rubric import DEFAULT_RUBRIC, ROOT, load_rubric
from scripts.scoring import to_date

SCHEMA = ROOT / "schema" / "incident.schema.json"


def load_validator(path: Path = SCHEMA) -> Draft202012Validator:
    return Draft202012Validator(json.loads(Path(path).read_text()))


def _jsonable(data):
    # YAML turns bare dates into date objects; the schema expects strings.
    return json.loads(json.dumps(data, default=str))


def validate_incident(incident: dict, stem: str, rubric: dict, validator) -> list[str]:
    errors = [
        f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
        for e in validator.iter_errors(_jsonable(incident))
    ]
    if errors:
        return errors

    if incident["id"] != stem:
        errors.append(f"id '{incident['id']}' does not match filename '{stem}'")

    s = incident["scoring"]
    if incident["league"] == "accomplice":
        acc = rubric["accomplice"]
        checks = (
            ("contribution", acc["contribution"]),
            ("guardrails", acc["guardrails"]),
            ("legal_status", acc["legal_status"]),
            ("blast_radius", rubric["blast_radius"]),
        )
    else:
        checks = (
            ("autonomy", rubric["autonomy"]),
            ("blast_radius", rubric["blast_radius"]),
            ("motive", rubric["pettiness"]["motives"]),
        )
        # Co-defendants are only charged when a human used the model.
        if any("modified_by" in m for m in incident["models"]):
            errors.append("models: modified_by is only used in the Accomplice League")
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
        errors.append("sources: at least one 'news' source is required")
    if incident["tier"] == "verified" and not kinds & {"postmortem", "primary"}:
        errors.append("tier: 'verified' requires a 'postmortem' or 'primary' source")

    total_share = sum(m["share"] for m in incident["models"])
    if abs(total_share - 1) > 1e-6:
        errors.append(f"models: shares sum to {total_share}, expected 1")

    if to_date(incident["reported"]) < to_date(incident["date"]):
        errors.append("reported: earlier than date")
    if incident.get("date_precision") == "month" and to_date(incident["date"]).day != 1:
        errors.append("date_precision: 'month' dates must be the first of the month")
    return errors


def validate_dir(directory: Path, rubric: dict, validator) -> dict[str, list[str]]:
    results, seen = {}, {}
    for path in sorted(Path(directory).glob("*.yaml")):
        try:
            incident = yaml.safe_load(path.read_text())
        except yaml.YAMLError as e:
            results[path.name] = [f"YAML: {e}"]
            continue
        if not isinstance(incident, dict):
            results[path.name] = ["not a YAML mapping"]
            continue
        errors = validate_incident(incident, path.stem, rubric, validator)
        incident_id = incident.get("id")
        if incident_id is not None:
            if incident_id in seen:
                errors.append(f"duplicate id, also in {seen[incident_id]}")
            seen.setdefault(incident_id, path.name)
        if errors:
            results[path.name] = errors
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
