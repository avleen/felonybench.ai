# Accomplice League Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or superpowers:subagent-driven-development) to implement this plan task-by-task.

**Goal:** Add a third board, the Accomplice League, for real-world crimes (and legally contested acts) where a *human* used an AI model, with labs and model modifiers (e.g. abliterators) charged as co-defendants.

**Architecture:** A new `league: accomplice` value in the incident schema, with its own scoring inputs (`contribution`, `guardrails`, `legal_status`) in place of the model-crime inputs (`autonomy`, `motive`). Scoring branches on league; boards gain a third league; org rollups charge every co-defendant the full incident score. The site adds the league as a third tab and explains it on the rubric page. The sweep learns a new source class: labs' and vendors' threat-intelligence reports.

**Tech Stack:** unchanged (Python scoring + validator, Astro site, GitHub Actions agents).

**Conventions:** run from repo root; `python -m pytest -q`; TDD for every Python change; commit per task ending with the session's attribution lines; push after each commit (branch `feature/accomplice-league`, one PR at the end).

---

## Design

### What qualifies
A **documented real-world** act by a human (or group) who used a **named AI model or lab** to do it, where the act is a crime, or its legality is genuinely contested (e.g. DMCA §1201 anti-circumvention). Out of scope: capability claims, benchmarks, uncensored model *releases* with no documented misuse, jailbreak demos, and acts that are plainly lawful (e.g. a normal bug-bounty report).

### Co-defendants
- `org` is the base model's lab.
- A model entry may carry `modified_by` (the organization that altered it, e.g. `OrcaRouter`) and `modification` (e.g. `abliterated`).
- **Joint and several liability:** the incident's full score is charged to the base lab *and* to every distinct `modified_by` organization on the org board. On the model board the row belongs to the modified model, e.g. "Qwen3.8-27B-Uncensored (OrcaRouter)".
- Only in the Accomplice League. Model crimes (Open/Sandbox) keep single-org attribution.

### Scoring (`rubric/v1.yaml` → `accomplice:` section; rubric version → 1.1)

```
accomplice incident = Sentence-Years × Contribution × Blast Radius × Legal status
                    + Tradecraft + Guardrails + Dwell
                    × 1.25 if recidivist (same family, exact dates, same league)
```

| Input | Values |
|---|---|
| **Sentence-Years** | the *human's* statutory exposure, as today |
| **Contribution** (what the AI did) | advised ×0.25 · wrote_content ×0.5 · found_vulnerability ×1 · built_exploit ×1.5 · operated ×2 |
| **Blast Radius** | same scale as the Open League |
| **Legal status** | crime ×1 · contested ×0.5 |
| **Tradecraft** | same technique list (techniques the AI supplied or carried out) |
| **Guardrails** (aggravating factor) | intact +0 · jailbroken +5 · removed +10 |
| **Dwell** | same bands and outside-detection bonus |
| Pettiness, Autonomy | not used (they describe the model's own choices) |

Badges: `uncensored` (guardrails removed) and `jailbroken` (guardrails jailbroken), plus the existing `cooperating_witness` (the lab disclosed the misuse, e.g. in its threat report) and `international_incident`.

### Worked example (tests use it)
A threat actor used an abliterated Qwen model (modified by OrcaRouter) to build a working exploit and breach a third-party company; 18 USC 1030(a)(5)(A) (10 years); detected by the victim after 10 days; lab didn't disclose.
`10 × 1.5 × 1 × 1 = 15` + tradecraft `zero_day` 6 + guardrails 10 + dwell (8 + 3) = **42**. Charged in full to both Alibaba and OrcaRouter.

### PS5 hypervisor case (test of "contested")
Jordy's team found the bug with AI tools and reported it to Sony's bug bounty. Reporting is lawful; the only arguable exposure is §1201 circumvention during the research, which the good-faith security-research exemption likely covers. The seeding task decides between `legal_status: contested` (a few points) and a `rejected` entry in `agent/known-leads.yaml`, with reasoning either way, for human review.

---

### Task 1: Rubric

**Files:** Modify `rubric/v1.yaml`, `tests/test_rubric.py`

**Step 1: failing tests** (append to `tests/test_rubric.py`):
```python
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
```
Update `test_rubric_version` to expect `"1.1"`.

**Step 2:** run, expect FAIL (KeyError `accomplice`).

**Step 3:** add to `rubric/v1.yaml` (keep existing keys; bump `version: "1.1"` and append a changelog entry "Added the Accomplice League."):
```yaml
accomplice:
  contribution:
    advised: {multiplier: 0.25, label: Advised, description: Answered questions or explained techniques.}
    wrote_content: {multiplier: 0.5, label: Wrote the content, description: Wrote phishing lures, malware components or scripts that a human deployed.}
    found_vulnerability: {multiplier: 1, label: Found the vulnerability, description: Found the flaw the human exploited.}
    built_exploit: {multiplier: 1.5, label: Built the exploit, description: Developed a working exploit or attack tool.}
    operated: {multiplier: 2, label: Ran the operation, description: Carried out the attack itself under a human's direction.}
  guardrails:
    intact: {points: 0, label: Guardrails intact, description: Used as shipped; the lab's safeguards didn't stop it.}
    jailbroken: {points: 5, label: Jailbroken, description: The human talked or tricked the model past its safeguards.}
    removed: {points: 10, label: Safety removed, description: Run with its safety training stripped out, e.g. an abliterated model.}
  legal_status:
    crime: {multiplier: 1, label: Crime}
    contested: {multiplier: 0.5, label: Legality contested}
```
and to `badges:`:
```yaml
  uncensored: {label: Uncensored, description: Used with its safety training removed.}
  jailbroken: {label: Jailbroken, description: A human got it past its safeguards.}
```

**Step 4:** tests pass. **Step 5:** commit "Rubric 1.1: Accomplice League scoring".

---

### Task 2: Schema and validator

**Files:** Modify `schema/incident.schema.json`, `scripts/validate.py`, `tests/conftest.py`, `tests/test_validate.py`

**Step 1: fixture + failing tests.** In `tests/conftest.py` add:
```python
ACCOMPLICE_INCIDENT = {
    **{k: v for k, v in BASE_INCIDENT.items() if k not in ("scoring", "rationale")},
    "id": "2026-06-01-alibaba-abliterated-exploit",
    "date": "2026-06-01", "reported": "2026-06-20",
    "league": "accomplice", "org": "Alibaba",
    "human_actor": "A financially motivated threat actor tracked by a vendor",
    "models": [{"name": "Qwen3.8-27B-Uncensored", "codename": None, "family": "qwen", "share": 1,
                "modified_by": "OrcaRouter", "modification": "abliterated"}],
    "victims": [{"name": "A software company", "type": "third_party", "country": "US"}],
    "statutes": [{"code": "18 USC 1030(a)(5)(A)", "max_years": 10}],
    "scoring": {"contribution": "built_exploit", "guardrails": "removed", "legal_status": "crime",
                "blast_radius": "third_party", "tradecraft": ["zero_day"], "dwell_days": 10,
                "detected_by": "victim", "self_disclosed": False},
    "rationale": {k: "Because." for k in ("contribution", "guardrails", "blast_radius", "tradecraft", "dwell")},
}

@pytest.fixture
def make_accomplice():
    def _make(scoring=None, **overrides):
        incident = copy.deepcopy(ACCOMPLICE_INCIDENT)
        incident.update(overrides)
        if scoring:
            incident["scoring"].update(scoring)
        return incident
    return _make
```
Tests (append to `tests/test_validate.py`):
```python
ACC = "2026-06-01-alibaba-abliterated-exploit"

def test_accomplice_incident_valid(make_accomplice, rubric):
    assert _errors(make_accomplice(), rubric, stem=ACC) == []

def test_accomplice_requires_human_actor(make_accomplice, rubric):
    inc = make_accomplice(); del inc["human_actor"]
    assert any("human_actor" in e for e in _errors(inc, rubric, stem=ACC))

def test_accomplice_values_come_from_rubric(make_accomplice, rubric):
    for field, bad in (("contribution", "vibes"), ("guardrails", "melted"), ("legal_status", "vibes")):
        assert any(field in e for e in _errors(make_accomplice(scoring={field: bad}), rubric, stem=ACC))

def test_model_crime_leagues_still_require_autonomy(make_incident, rubric):
    inc = make_incident(); del inc["scoring"]["autonomy"]
    assert any("autonomy" in e for e in _errors(inc, rubric))

def test_modified_by_only_in_accomplice_league(make_incident, rubric):
    inc = make_incident(); inc["models"][0]["modified_by"] = "OrcaRouter"
    assert any("modified_by" in e for e in _errors(inc, rubric))
```

**Step 2:** run, expect FAILs.

**Step 3:** schema changes:
- `league` enum → `["open", "sandbox", "accomplice"]`.
- top-level optional `"human_actor": {"type": "string", "minLength": 3}`.
- model items: optional `"modified_by": {"type": "string", "minLength": 1}`, `"modification": {"type": "string", "minLength": 1}`.
- `scoring.properties` gains `contribution`, `guardrails`, `legal_status` (strings); `scoring.required` shrinks to the shared fields `["blast_radius", "tradecraft", "dwell_days", "detected_by", "self_disclosed"]`.
- `rationale.required` shrinks to `["blast_radius", "tradecraft", "dwell"]`.
- An `allOf` with two `if/then` blocks:
  - if `league` is `accomplice` → require `human_actor`, `scoring.required += [contribution, guardrails, legal_status]`, `rationale.required += [contribution, guardrails]`.
  - else → `scoring.required += [autonomy, motive]`, `rationale.required += [autonomy, motive]`.

`scripts/validate.py`: make the rubric-value checks league-aware:
```python
    if incident["league"] == "accomplice":
        acc = rubric["accomplice"]
        checks = [("contribution", acc["contribution"]), ("guardrails", acc["guardrails"]),
                  ("legal_status", acc["legal_status"]), ("blast_radius", rubric["blast_radius"])]
    else:
        checks = [("autonomy", rubric["autonomy"]), ("blast_radius", rubric["blast_radius"]),
                  ("motive", rubric["pettiness"]["motives"])]
    for field, allowed in checks:
        ...  # existing error message
    if incident["league"] != "accomplice":
        for m in incident["models"]:
            if "modified_by" in m:
                errors.append("models: modified_by is only used in the Accomplice League")
```

**Step 4:** all tests pass (existing ones unchanged). **Step 5:** commit "Schema: Accomplice League incidents".

---

### Task 3: Scoring

**Files:** Modify `scripts/scoring.py`, create `tests/test_accomplice.py`

**Step 1: failing tests:**
```python
from scripts.scoring import breakdown, build_scores


def test_worked_example_scores_42(make_accomplice, rubric):
    b = breakdown(make_accomplice(), rubric)
    assert (b["sentence_years"], b["contribution"], b["blast_radius"], b["legal_status"]) == (10, 1.5, 1, 1)
    assert (b["base"], b["tradecraft"], b["guardrails"], b["dwell"], b["total"]) == (15, 6, 10, 11, 42)
    assert b["pettiness"] == 0 and b["autonomy"] is None


def test_contested_halves_base(make_accomplice, rubric):
    assert breakdown(make_accomplice(scoring={"legal_status": "contested"}), rubric)["base"] == 7.5


def test_co_defendants_each_charged_in_full(make_accomplice, rubric):
    orgs = build_scores([make_accomplice()], rubric, "now")["boards"]["accomplice"]["all"]["orgs"]
    assert {(o["name"], o["score"]) for o in orgs} == {("Alibaba", 42), ("OrcaRouter", 42)}


def test_modified_model_row(make_accomplice, rubric):
    models = build_scores([make_accomplice()], rubric, "now")["boards"]["accomplice"]["all"]["models"]
    assert [(m["slug"], m["org"], m["base_org"]) for m in models] == [
        ("orcarouter-qwen3-8-27b-uncensored", "OrcaRouter", "Alibaba")]


def test_badges(make_accomplice, rubric):
    inc = build_scores([make_accomplice()], rubric, "now")["incidents"][0]
    assert inc["badges"] == ["uncensored"]
    inc = build_scores([make_accomplice(scoring={"guardrails": "jailbroken"})], rubric, "now")["incidents"][0]
    assert inc["badges"] == ["jailbroken"]


def test_accomplice_league_is_separate(make_accomplice, make_incident, rubric):
    boards = build_scores([make_accomplice(), make_incident()], rubric, "now")["boards"]
    assert [o["name"] for o in boards["open"]["all"]["orgs"]] == ["OpenAI"]
    assert "OpenAI" not in {o["name"] for o in boards["accomplice"]["all"]["orgs"]}
```

**Step 2:** run, expect FAIL.

**Step 3:** implement in `scripts/scoring.py`:
- `LEAGUES = ("open", "sandbox", "accomplice")`.
- In `breakdown`, branch on league:
```python
    if incident["league"] == "accomplice":
        acc = rubric["accomplice"]
        contribution = acc["contribution"][s["contribution"]]["multiplier"]
        legal = acc["legal_status"][s["legal_status"]]["multiplier"]
        blast = rubric["blast_radius"][s["blast_radius"]]["multiplier"]
        base = sentence_years * contribution * blast * legal
        guardrails = acc["guardrails"][s["guardrails"]]["points"]
        autonomy, pettiness = None, 0
    else:
        ...existing autonomy/blast/pettiness...
        contribution = legal = None
        guardrails = 0
    total = (base + tradecraft + pettiness + guardrails + dwell) * multiplier
```
  and return the extra keys `contribution`, `legal_status`, `guardrails` (alongside the existing ones).
- `badges_for`: add `uncensored` / `jailbroken` from `scoring.guardrails`.
- `score_all`: model slug uses `m.get("modified_by") or incident["org"]`.
- `board`: for each incident, charge the org row for `incident["org"]` **and** each distinct `m["modified_by"]` with share 1 (joint and several). Model rows use `org = m.get("modified_by") or incident["org"]` and add `base_org = incident["org"]` (set on every row; equals `org` when unmodified).
- `trends`: charge every co-defendant org the same way, so each has its own step line.

**Step 4:** all tests pass (existing `test_boards` etc. unchanged; update `test_empty_input` if it enumerates leagues). **Step 5:** commit "Score the Accomplice League; charge co-defendants jointly".

---

### Task 4: Leaderboard diff

**Files:** Modify `scripts/diff.py`, `tests/test_diff.py`

Add `("accomplice", "all", "Accomplice League")` to `BOARDS`; add a test that a new accomplice org appears under that heading. Commit "Diff: include the Accomplice League".

---

### Task 5: Site

**Files:** Modify `site/src/lib/data.ts`, `site/src/pages/index.astro`, `site/src/pages/trends.astro`, `site/src/pages/incident/[id].astro`, `site/src/pages/rubric.astro`, `site/src/pages/how-it-works.astro`, `site/src/pages/model/[slug].astro`, `site/src/pages/og/[slug].png.ts`, `site/src/components/BoardTable.astro`

- `LEAGUES` gains `{ key: "accomplice", label: "Accomplice League" }`. Every `getStaticPaths` that loops `["open","sandbox"]` uses `LEAGUES` instead.
- Incident page: when `league === "accomplice"`, show "Human actor", the co-defendants ("Alibaba, with OrcaRouter (abliterated)"), and a breakdown with Contribution / Legal status / Guardrails rows instead of Autonomy / Pettiness.
- Model page: show "Base model by {base_org}" when it differs from `org`.
- BoardTable: in the model view, show the modifier under the model name.
- Rubric page: a new "Accomplice League" section rendered from `rubric.accomplice` (tables for contribution, guardrails, legal status), explaining joint and several liability and what doesn't qualify.
- How it works: one paragraph on the league and the threat-report sources.
- Tone: deadpan; the human actor is described as sources describe them, never named unless named in news coverage.

Verify: `npm run build` with zero accomplice incidents and with a temporary sample (the conftest fixture as YAML, not committed); screenshot the incident, board and rubric pages at 375px and 1280px, light and dark. Commit "Site: Accomplice League tab, incident and rubric pages".

---

### Task 6: Agent instructions and feeds

**Files:** Modify `agent/RUNBOOK.md`, `agent/incident-template.yaml`, `agent/known-leads.yaml`, `scripts/feeds.yaml`, `tests/test_rss_filter.py`

- Runbook **Scope**: replace "humans using AI as a tool for their own crimes" in *Out of scope* with a pointer to the Accomplice League; add its qualification rules (above), the co-defendant rule, and consistency rules (contribution levels; `contested` only when legality is genuinely disputed, with the dispute cited).
- Runbook **Source types**: add threat-intelligence reports: OpenAI's "Disrupting malicious uses of AI" reports, Anthropic's threat intelligence reports, Google Threat Intelligence Group (GTIG) AI misuse reports, Microsoft Threat Intelligence, plus vendor reports (CrowdStrike, Mandiant, Unit 42, Check Point, ESET, Recorded Future). Each case in those reports is a candidate.
- Runbook **Search templates**: "threat actor used ChatGPT/Claude/Gemini/Qwen/DeepSeek", "AI-generated malware", "AI-developed exploit", "uncensored model" + attack, "abliterated" + malware, "WormGPT/GhostGPT", "LLM-assisted" + exploit/jailbreak/DMCA.
- Template: document the accomplice fields.
- Feeds: Google News queries for "AI-generated malware", "threat actor" + (ChatGPT OR Claude OR Gemini), "abliterated OR uncensored model" + attack; the labs' threat-report pages if they have feeds. TDD a filter test that "Threat actor used Gemini to develop zero-day exploit" matches.
- Commit "Agents: find Accomplice League incidents".

---

### Task 7: Seed incidents (research agent, Opus)

Research and write up, one file each, with full sourcing:
1. Google GTIG's May 2026 report of a threat actor using an AI-developed zero-day in a real attack.
2. Anthropic's August 2025 threat report case of a criminal using Claude Code for a data-extortion campaign against ~17 organizations (verify details from Anthropic's report).
3. Two or three concrete cases from OpenAI's "Disrupting malicious uses of AI" reports (pick ones with real victims and a clear crime).
4. The PS5 hypervisor case: decide `legal_status: contested` vs. a `rejected` known-lead, with reasoning.
5. Any documented misuse of an uncensored/abliterated model (co-defendant test); if none, record that in the notes.

If a safety system refuses a write-up, log it under "Needs human write-up" and move on. Commit the incidents and `docs/agent-notes/`; open as part of the PR.

---

### Task 8: Docs and PR

Update the design doc (scope, leagues, scoring) and README. Run `python -m pytest -q`, `python -m scripts.validate`, site build. Open one PR `feature/accomplice-league` with the summary, the worked example, and the seed incidents' scores.

---

## Expected size
Threat-intel reports alone describe tens of cases a year (each OpenAI report lists ~10; Anthropic's and GTIG's similar). Only cases with a real victim, a crime (or genuine legal dispute) and a named model/lab qualify; expect roughly 10–30 incidents in the first backfill, then a few a month.
