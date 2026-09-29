Anthropic's September 2026 threat report (GTG-16006) says Zhipu (Z.ai) ran a chain-of-thought extraction pipeline against Claude Opus 4.8, rotating through 273 fraudulent accounts to evade Anthropic's model restrictions, and replayed the captured Claude reasoning traces "back through Claude to clean them for training its GLM models": 770,609 exchanges passed through the CoT-extraction cleaner in a 10-day period in June 2026, and over 3 million exchanges were attributed to Zhipu in the same period, "most of which were used for cleaning the distilled outputs". Zhipu also used Claude to judge model outputs, clean and normalize harvested reasoning transcripts, score and filter training data, write tasks, provide solutions and implement testing. In scope under the owner's 2026-09-29 decision ("Claude being the target counts if AI was used to do the work"): Claude itself did the processing work of the extraction pipeline.

**Changes:** New incident (Accomplice League), written under the owner's scope decision on the distillation cluster.

**Scoring notes:**
- `org: Anthropic` because Claude did the work; `human_actor` is Zhipu as the report names it. `blast_radius: own_prod` (the victim is Anthropic itself).
- `contribution: operated`: Claude ran the cleaning/grading stage of the pipeline at scale. A reviewer could argue this is post-processing of the loot rather than "the attack", which would lower it to `wrote_content` (0.5x). The report does not say an AI created the accounts or ran the extraction harness.
- `models: Undisclosed model`: the extraction targeted Opus 4.8, but the report does not say which Claude model did the cleaning.
- `statutes`: 18 USC 1343 (20) for the scheme using fraudulent accounts (Anthropic's word) to obtain access; 18 USC 1832 (10) because raw reasoning traces are something Anthropic deliberately withholds (summaries, thinking signatures). 1029(a)(2) not charged: the report's stolen-card/stolen-key language is about proxy services generally, not Zhipu specifically. 1030(a)(4) not charged (ToS/region evasion as "without authorization" is unsettled). 1831 not charged: no foreign-government benefit is reported.
- `legal_status: contested`: whether harvesting model outputs is trade-secret misappropriation is an open question (Beck Reed Riden LLP, Sarah Tishler, "Understanding AI Distillation In The Trade Secret Context", 2026-05-12: "to my knowledge, an open question"), while AEI's Ryan Fedasiuk ("How to Stop China from Freeriding on American AI", 2026-08-03) argues fraudulent-access schemes fall under the CFAA and wire-fraud statutes. China's Commerce Ministry rejected the claims as having "no factual or legal basis" (per Better Stack's write-up). No prosecution exists.
- `guardrails: intact`, `tradecraft: []` (the account rotation was Zhipu's, not Claude's). `date_precision: month` (June 2026), `dwell_days: 0`.

**Sources checked:**
- Report PDF pp. 143-154 (downloaded and read in full via pypdf) and landing page.
- The Hacker News (Lakshmanan, 2026-09-11, fetched): names Zhipu, GTG-16006, 3.4M exchanges, the replay-through-Claude cleaner. Cited.
- TechCrunch (Brandom, 2026-09-10, fetched): covers only Alibaba/Moonshot/DeepSeek. Not cited.
- Better Stack (Ulili, fetched): names Zhipu only in passing. Not cited.
- Beck Reed Riden and AEI (fetched): legal context only, not cited as sources.
- Quartz (403). Not cited.

**Open questions:** whether processing harvested traces counts as the AI "doing the work" under the owner's rule; whether `operated` or `wrote_content` fits better.
