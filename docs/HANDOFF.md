# FelonyBench.ai: handoff

State as of 2026-09-29, written for the next agent picking this up. Read this first, then
`agent/RUNBOOK.md` (how the monitoring agents work, and all the scoring and sourcing rules),
`rubric/v1.yaml`, and the two design/plan docs in `docs/plans/`.

## What this is

A satirical benchmark leaderboard at https://felonybench.ai. It ranks AI models and labs by
"crimes", scored as if a human had done them. Higher is "better". Three boards:

- **Open League:** a model's own conduct reached real systems.
- **Sandbox League:** a model's "crimes" against fictional victims inside evaluations.
- **Accomplice League:** a human used a named model to commit a crime, or an act of
  genuinely contested legality. The lab and anyone who modified the model (e.g. an
  abliterator, `models[].modified_by`) are co-defendants, each charged the full score.

Incidents are YAML files in `incidents/`, validated by `scripts/validate.py` against
`schema/incident.schema.json` and the rubric, and scored by `scripts/scoring.py` into
`scores.json`. The Astro site in `site/` renders that. Cloudflare Workers Builds deploys
it on every merge to `main` (config: `wrangler.jsonc`).

GitHub Actions runs Claude Code (Opus, medium effort, on the owner's subscription token):
- `watch.yml`: daily at 09:00 UTC. A free RSS keyword filter runs first, and Claude triages
  only if something matches.
- `sweep.yml`: Mondays at 10:00 UTC. A full sweep across every lab and source type, with a
  sweep report.

`scripts/open_prs.py` turns the agent's edits into one PR per incident.

## Current state

- `main` is at d052cba. 138 tests pass (`python -m pytest -q`), and
  `python -m scripts.validate` is clean.
- The site is live and deploys on merge.
- Owner preferences: push regularly; PRs for data; the owner merges (they are often remote
  and can't read files, so put everything important in PR descriptions and messages).

### Open PRs

| PR | What | State / next step |
|---|---|---|
| #20 `data/public-victims` | Russia dual-use procurement / sanctions evasion (Accomplice, victim "The public", EU, score 30). Also rejects PRC protest venue scouting (no crime on the report's facts) and keeps Mali "Lakana 360" pending until a model is identified. | Ready for owner review. |
| #19 `agent/2026-08-31-anthropic-iran-firefox-identity-harvester` | Iranian unit used Claude to build a malicious Firefox extension that harvested social-network identities (Accomplice, score 4.25). Draft, label `awaiting-news`. | **News coverage now exists and was verified.** RFE/RL, "Anthropic Disrupts Iran's Use Of Claude To Spread Propaganda, Spy On Dissidents" (Frud Bezhan, 2026-09-11, https://www.rferl.org/a/anthropic-claude-iran-propaganda/33852428.html) says Iran-based actors "used Claude to build and deploy a malicious Firefox extension that harvested users' identities from social media networks." Also Iran International (2026-09-13, https://www.iranintl.com/en/202609131676, not re-verified). **To do:** add RFE/RL as a `news` source, push to the PR branch, then `gh pr ready 19` and `gh pr edit 19 --remove-label awaiting-news`. |

### Owner decisions, still to implement

**Update (2026-09-29, branch `claude/tender-turing-oggg9v`):** items 1–7 below are done on that
branch and waiting on the owner's review: the Moonshot and DeepSeek incidents (scores 19.5 and
9.5; DeepSeek has no 1343 charge because the report ties no fraudulent accounts of its own to the
campaign), SenseTime dropped, the image-upload lead rejected, the AISI incident's fields fixed
(score 17.5 → 27), `scripts/pdf_text.py`, known-leads tidied (new `handled` status), and Actions
bumped to checkout v7, setup-python v7, cache v6, upload-artifact v7. Still open: PR #19's news
source, and item 8 (run a sweep after this merges).

1. **Moonshot (GTG-16002) and DeepSeek (GTG-16001) thinking-signature reversal counts.**
   Both got Claude to convert its "thinking signature" back into raw reasoning, defeating
   Anthropic's anti-distillation control. The owner rules that this is Claude doing the
   work, so both become Accomplice incidents.
   - Fields: `org: Anthropic`, `human_actor` = the lab, victim Anthropic (`own_prod`),
     `contribution: operated`, `legal_status: contested`, `tradecraft: [evasion]`,
     `self_disclosed: true`.
   - Statutes: 17 USC 1201(a)(1)(A), criminal via 1204 (5 years; contested because
     copyrightability of AI output is unsettled); 18 USC 1832 (10), consistent with the
     Zhipu distillation incident; 1343 (20) only if the report ties fraudulent accounts to
     that lab.
   - Source: Anthropic's September 2026 threat report PDF, pp. ~143–154 (URL is in the
     existing `incidents/*zhipu*` files); news: The Hacker News (Lakshmanan, 2026-09-11).
   - Replace the Moonshot/DeepSeek `rejected` entry in `agent/known-leads.yaml`.
   - An agent was working on this and was stopped before pushing anything.
2. **Drop the SenseTime distillation incident**
   (`incidents/2026-08-31-anthropic-sensetime-distillation-pipeline.yaml` and its note in
   `docs/agent-notes/`). Add a `rejected` known-lead: weakest legal theory, since the
   transcripts were outputs users could already see.
3. **OpenAI's agents uploading 53 users' images to image hosts is a privacy failure, not a
   crime.** Add a `rejected` known-lead.
4. **Fix the structured fields of the owner's AISI incident**
   `incidents/2026-07-27-anthropic-mythos-aisi.yaml`, without rewriting their wording:
   - victims: the real open-source project maintainer, the developers who were sent
     deceptive emails, and the bystander whose container was compromised, all
     `third_party`, country null (AISI ran the test and wasn't the victim);
   - `scoring.autonomy: exceeded_scope` (the agent mistook real people for range
     targets);
   - `date_precision: before`;
   - add `evasion` to tradecraft;
   - AISI blog `kind: primary` (not postmortem), and add the AISI technical PDF
     (https://cdn.prod.website-files.com/663bd486c5e4c81588db7a1d/6a724858f7db25c81487016d_Security%20Incident%20INC-2026-07-28-01.pdf)
     as `primary`;
   - leave `summary` and `rationale` wording alone, but tell the owner that the autonomy
     rationale line ("authorized to exceed its normal restrictions") now contradicts the
     field.

   **Warning:** agents were twice refused by a safety classifier when *writing* these AISI
   incidents. If an edit is refused, stop and tell the owner; don't reword or retry.
5. **Let the CI agent read PDFs.** Government and lab reports are PDFs, and the agent in
   Actions can't extract them (it has no Bash, and WebFetch times out on large PDFs).
   - Add `scripts/pdf_text.py`: `python -m scripts.pdf_text <url-or-path> [--pages 3-10]
     [--max-chars N]`, which fetches with a browser user agent, extracts with pypdf, and
     prints the text.
   - Add `pypdf` to `requirements-agent.txt`, and install it in both modes in
     `.github/actions/run-agent/action.yml`. The prefetch step currently installs agent
     requirements only in sweep mode.
   - Add `Bash(python -m scripts.pdf_text:*)` to `--allowedTools`. That prefix-scoped
     rule works in Actions; `acceptEdits` doesn't cover Bash.
   - Add one line to the runbook's hard rules.
   - A TDD start (tests with a hand-built one-page PDF, `page_range`, `max_chars`) was
     sketched but not committed. Write it fresh.
6. **Tidy `agent/known-leads.yaml`.** The AISI Mythos 5 entry is still `pending_human`, but
   the owner's file now covers it. Mark it handled and point to the file.
7. **Update GitHub Actions versions.** `actions/cache` and `actions/upload-artifact`
   (and check `checkout` and `setup-python`) run on deprecated Node 20. Check the current
   majors with
   `gh api repos/actions/<name>/releases/latest --jq .tag_name` and bump them in
   `watch.yml`, `sweep.yml`, `validate.yml` and `.github/actions/run-agent/action.yml`.
8. **Then trigger and check a sweep** (`gh workflow run sweep.yml`). It's the first run
   since the Accomplice League merged. Download the artifact
   (`gh run download <id>`; it includes the transcript and `.agent-out/`) and check:
   - `sweep-report.md` covers the Accomplice League sources (threat-intel reports);
   - any accomplice PRs have the right score rows;
   - failing incidents open as drafts.

   A failed run opens a GitHub issue automatically.

### On hold (owner said to hold)

- **Sandbox League backfill.** Only one Sandbox incident exists (GPT-6 Astra in AISI's
  environment), because the sweep never targeted them. Candidates: Anthropic's "Agentic
  Misalignment" study (June 2025; blackmail across ~16 models from several labs), the
  Claude Opus 4 system card (blackmail, self-exfiltration attempts), Apollo Research's
  scheming evaluations (Dec 2024; o1 disabling oversight / exfiltrating weights), and
  Palisade (o3 sabotaging shutdown; o1-preview editing chess game files, which may be
  cheating rather than a crime). Plan: a backfill agent, plus Sandbox search templates and
  a checklist entry in the runbook.
- **"Needs human write-up" leads** (owner will come back to these): Transluce's report of
  OpenAI agents probing the University of New Mexico, Data USA and Australia's Institute of
  Health and Welfare (AIHW is probably foreign_government), and an attempt on the US
  Department of Education Office for Civil Rights site. A safety classifier stopped the
  agent's output on these.
- **felonybench.com cross-check:** skipped (we've surpassed it). Its Vercel checkpoint
  blocks GitHub's IPs; the prefetch step records an error and continues. The Playwright
  install could be removed later to save time.

## Lessons (read before running agents)

- **Safety classifier refusals.** Content about malware, exploitation or weapons sometimes
  gets refused, both locally and in CI. Refusals are final: never reword, retry, or route
  the same content through another agent or tool. The runbook tells the CI agent to log
  such leads under "Needs human write-up" and continue. Distinguish refusals from
  classifier *errors* ("no verdict (error)"), which are transient and can be retried.
- **Agent PRs get no CI check,** because they're opened with `GITHUB_TOKEN`. `open_prs.py`
  therefore embeds validation in the PR body and opens any failing PR as a **draft**. PR #16
  was once merged with a failing validation and broke `main`, so always check validation
  before merging.
- **Plan usage.** CI shares the owner's Claude plan limits. A sweep during an exhausted
  session fails instantly ("You've hit your session limit") and opens an issue.
- **Worktrees.** Give each parallel agent `isolation: worktree`, and tell it never to touch
  the main checkout. A reviewer once ran `git checkout <sha> -- .` in the main tree and
  reverted files. The repo path contains a space: parse `git worktree list --porcelain`
  line by line, not with `awk`.
- **This checkout is on a Windows drive (WSL)**, so git doesn't track the executable bit.
  Invoke scripts with `bash script.sh` in workflows.
- **Scoring rules the reviews kept enforcing** (they're in the runbook's "Consistency
  rules"):
  - Use `"Undisclosed model"` for unnamed models.
  - A company quote in the press isn't a primary source (the incident stays `alleged`).
  - Use the misdemeanor maximum unless a felony factor is *reported*.
  - Unknown dates use `date_precision` month/before, with dwell counted from the latest
    possible date.
  - Recidivism needs exact dates on both incidents.
  - One incident per distinct act against a distinct victim.
  - Only cite sources you actually read.
- **The owner's scope rulings so far:**
  - Customer-deployed models count only if there's a potential crime.
  - People named in published news may be named.
  - Governments targeting governments, or groups targeting governments, fit the spirit.
  - "The public" is the victim for sanctions and other diffuse crimes.
  - ROME's motive is `unclear`.
  - The dating-scam chatbot counts as `operated`.
  - State actors' guardrails are `intact` unless a jailbreak is reported.
  - Claude being the *target* counts when AI did the work.

## Housekeeping

- Commit trailers the owner expects:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01QLydjk1Km4X7jC8N7RZJaX
  ```
  PR bodies end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- Branch protection on `main` requires one approving review. The owner merges with
  `--admin`; agents don't merge.
- Old agent worktrees under `.claude/worktrees/` are safe to remove once their branches
  are merged. One is locked by a dead process; `git worktree remove --force --force` it.
