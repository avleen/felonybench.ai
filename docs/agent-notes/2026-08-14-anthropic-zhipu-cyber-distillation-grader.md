Anthropic's September 2026 threat report (GTG-16006) says that "ahead of the release of its GLM 5.3 model" Zhipu researchers built capture-the-flag challenges from public vulnerability datasets and "launched a distillation attack against the top model of another leading US frontier lab" to target its cyber capabilities: "Our Claude Opus 4.6 model was separately targeted in this distillation attack, primarily to evaluate and grade the responses of the other US frontier model." Zhipu first tried Anthropic's Fable, gave up after Fable's cyber safeguards degraded the attack, and switched to Opus 4.6 and the other lab's model "expressly because they assessed the safeguards were weaker". In scope under the owner's rule: Claude Opus 4.6 did the grading work of a distillation attack against a third-party lab.

**Changes:** New incident, split from the Zhipu CoT-extraction incident because the report describes it as a separate campaign with a different victim (runbook: one incident per distinct act against a distinct victim).

**Scoring notes:**
- `org: Anthropic`, `models: Claude Opus 4.6` (the report names it), `blast_radius: third_party` (the unnamed US lab; the report does not name it, and I did not guess).
- `contribution: operated` (Claude was the grader in the attack pipeline). `guardrails: intact` (picking a less-guarded model is not a jailbreak).
- `statutes`: 18 USC 1832 (10) only. The report does not say this campaign used fraudulent accounts, so no 1343/1029. `legal_status: contested` (see the trade-secret dispute in the cleaner incident's notes).
- Date: GLM-5.3 was announced 2026-08-14 (MLQ News, fetched), so `date_precision: before`, `date: 2026-08-14`, `dwell_days: 0`.

**Sources checked:**
- Report PDF p. 151 (read).
- The Hacker News (fetched): covers GTG-16006 as a whole, not this sub-campaign specifically. Cited.
- MLQ News GLM-5.3 release article (fetched): used for the date bound. Cited.

**Open questions:** no news source describes the cyber sub-campaign specifically. The unnamed "other leading US frontier lab" was not identified in anything I read.
