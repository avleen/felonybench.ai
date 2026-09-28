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


LEAGUES = ("open", "sandbox")
TIERS = {"verified": ("verified",), "all": ("verified", "alleged")}


def badges_for(incident: dict) -> set[str]:
    badges = set()
    if incident["breakdown"]["recidivist"]:
        badges.add("repeat_offender")
    if incident["scoring"].get("self_disclosed"):
        badges.add("cooperating_witness")
    if incident.get("foreign_laws") or incident["scoring"]["blast_radius"] == "foreign_government":
        badges.add("international_incident")
    return badges


def score_all(incidents: list[dict], rubric: dict) -> list[dict]:
    repeat = recidivist_ids(incidents, rubric)
    scored = []
    for incident in incidents:
        item = {
            **incident,
            "models": [{**m, "slug": model_slug(incident["org"], m["name"])} for m in incident["models"]],
            "breakdown": breakdown(incident, rubric, incident["id"] in repeat),
        }
        item["badges"] = sorted(badges_for(item))
        scored.append(item)
    return sorted(scored, key=lambda i: (to_date(i["date"]), i["id"]))


def _select(scored: list[dict], league: str, tier: str) -> list[dict]:
    return [i for i in scored if i["league"] == league and i["tier"] in TIERS[tier]]


def _new_row(slug: str, name: str, org: str) -> dict:
    return {"slug": slug, "name": name, "org": org, "score": 0.0, "sentence_years": 0.0,
            "incidents": [], "alleged": 0, "peak_blast": -1, "badges": set()}


def _add(row: dict, incident: dict, share: float, blast_rank: int) -> None:
    row["score"] += incident["breakdown"]["total"] * share
    row["sentence_years"] += incident["breakdown"]["sentence_years"] * share
    row["incidents"].append(incident["id"])
    row["alleged"] += incident["tier"] == "alleged"
    row["peak_blast"] = max(row["peak_blast"], blast_rank)
    row["badges"] |= set(incident["badges"])


def _finish(rows: dict, blast_order: list[str]) -> list[dict]:
    ranked = sorted(rows.values(), key=lambda r: (-r["score"], r["name"]))
    for rank, row in enumerate(ranked, 1):
        row["rank"] = rank
        row["score"] = round(row["score"], 2)
        row["sentence_years"] = round(row["sentence_years"], 2)
        row["peak_blast_radius"] = blast_order[row.pop("peak_blast")]
        row["badges"] = sorted(row["badges"])
    return ranked


def board(scored: list[dict], rubric: dict, league: str, tier: str) -> dict:
    blast_order = list(rubric["blast_radius"])
    models, orgs = {}, {}
    for incident in _select(scored, league, tier):
        blast_rank = blast_order.index(incident["scoring"]["blast_radius"])
        org = orgs.setdefault(incident["org"], _new_row(slugify(incident["org"]), incident["org"], incident["org"]))
        _add(org, incident, 1, blast_rank)
        for m in incident["models"]:
            row = models.setdefault(m["slug"], _new_row(m["slug"], m["name"], incident["org"]))
            _add(row, incident, m["share"], blast_rank)
    return {"models": _finish(models, blast_order), "orgs": _finish(orgs, blast_order)}


def trends(scored: list[dict], league: str, tier: str) -> dict:
    series = {}
    for incident in _select(scored, league, tier):
        points = series.setdefault(incident["org"], [])
        previous = points[-1]["cumulative"] if points else 0
        total = incident["breakdown"]["total"]
        points.append({
            "date": str(to_date(incident["date"])),
            "incident_id": incident["id"],
            "delta": total,
            "cumulative": round(previous + total, 2),
        })
    return series


def build_scores(incidents: list[dict], rubric: dict, generated_at: str) -> dict:
    scored = score_all(incidents, rubric)
    return {
        "rubric_version": rubric["version"],
        "generated_at": generated_at,
        "rubric": rubric,
        "incidents": scored,
        "boards": {lg: {t: board(scored, rubric, lg, t) for t in TIERS} for lg in LEAGUES},
        "trends": {lg: {t: trends(scored, lg, t) for t in TIERS} for lg in LEAGUES},
        "last_incident_date": {
            lg: max((str(to_date(i["date"])) for i in scored if i["league"] == lg), default=None)
            for lg in LEAGUES
        },
    }
