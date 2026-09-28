"""Score incidents and build leaderboards, per rubric/v1.yaml."""
import re
from datetime import date, timedelta


def to_date(value) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def model_slug(org: str, name: str) -> str:
    return slugify(f"{org} {name}")


def dwell_points(scoring: dict, rubric: dict) -> int:
    dwell = rubric["dwell"]
    days = scoring["dwell_days"]
    points = 0
    for band in dwell["bands"]:
        upper = band["max_days"]
        if days >= band["min_days"] and (upper is None or days <= upper):
            points = band["points"]
            break
    if scoring["detected_by"] in dwell["outside_detectors"]:
        points += dwell["outside_detection_bonus"]
    return min(points, dwell["max"])


def breakdown(incident: dict, rubric: dict, recidivist: bool = False) -> dict:
    s = incident["scoring"]
    sentence_years = sum(statute["max_years"] for statute in incident["statutes"])
    autonomy = rubric["autonomy"][s["autonomy"]]["multiplier"]
    if incident["league"] == "sandbox":
        blast = rubric["sandbox_league_blast_radius"]
    else:
        blast = rubric["blast_radius"][s["blast_radius"]]["multiplier"]
    base = sentence_years * autonomy * blast
    techniques = rubric["tradecraft"]["techniques"]
    tradecraft = min(
        sum(techniques[t]["points"] for t in set(s["tradecraft"])),
        rubric["tradecraft"]["max"],
    )
    pettiness = rubric["pettiness"]["motives"][s["motive"]]["points"]
    dwell = dwell_points(s, rubric)
    multiplier = rubric["recidivism"]["multiplier"] if recidivist else 1
    total = (base + tradecraft + pettiness + dwell) * multiplier
    return {
        "sentence_years": sentence_years,
        "autonomy": autonomy,
        "blast_radius": blast,
        "base": round(base, 2),
        "tradecraft": tradecraft,
        "pettiness": pettiness,
        "dwell": dwell,
        "recidivist": recidivist,
        "recidivism_multiplier": multiplier,
        "total": round(total, 2),
    }


def _families(incident: dict) -> set:
    return {(incident["org"], m["family"]) for m in incident["models"] if m.get("family")}


def recidivist_ids(incidents: list[dict], rubric: dict) -> set[str]:
    """Incidents whose model family offended earlier in the same league, within the window."""
    window = timedelta(days=rubric["recidivism"]["window_days"])
    repeat = set()
    for incident in incidents:
        families = _families(incident)
        if not families:
            continue
        day = to_date(incident["date"])
        for other in incidents:
            if other is incident or other["league"] != incident["league"]:
                continue
            if day - window <= to_date(other["date"]) < day and families & _families(other):
                repeat.add(incident["id"])
                break
    return repeat
