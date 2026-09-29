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

- All open PRs from the previous handoff are merged: #19 (Iran Firefox harvester, with RFE/RL
  as its news source), #20 (Russia dual-use procurement; public victims) and #21 (the owner
  decisions below). `python -m pytest -q` passes (167 tests) and `python -m scripts.validate`
  is clean.
- The site is live and deploys on merge.
- Owner preferences: push regularly; PRs for data; the owner merges (they are often remote
  and can't read files, so put everything important in PR descriptions and messages).

### Done on 2026-09-29

- Moonshot (GTG-16002) and DeepSeek (GTG-16001) thinking-signature replay are Accomplice
  incidents (score 19.5 each; both charged 17 USC 1201 via 1204, 18 USC 1832 and 1343).
- SenseTime distillation dropped (rejected lead); OpenAI's 53 uploaded user images rejected
  as a privacy failure.
- The AISI Mythos 5 incident's structured fields and rationale fixed (score 17.5 → 27).
- `scripts/pdf_text.py` lets the CI agent read PDFs (public http(s) URLs only, redirects
  re-checked); it is the only command in the agent's `--allowedTools`.
- `agent/known-leads.yaml` has a `handled` status; the AISI Mythos 5, Moonshot/DeepSeek and
  GTG-34007 leads use it.
- Actions bumped off Node 20: checkout v7, setup-python v7, cache v6, upload-artifact v7.

### Still to do

1. **Trigger and check a sweep** (`gh workflow run sweep.yml`). It's the first run
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
