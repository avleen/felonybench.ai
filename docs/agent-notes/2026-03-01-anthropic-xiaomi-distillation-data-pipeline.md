Anthropic's September 2026 threat report (GTG-16008) says Xiaomi replayed user conversations and coding sessions from its own MiMo models to Claude (often run through OpenClaw and OpenCode harnesses), with more than 400k requests routed across more than 1,500 accounts via proxy services over 20 days in March and April 2026, to generate SFT and RL data. "Claude was used to reconstruct the developer environments from exchange transcripts. It also converted multi-turn conversations into cleaner exchanges. Claude was also used to generate both the inputted request and the returned response... Finally, Xiaomi used Claude to judge the quality of certain answers." The relayed traffic contained names, contact information and corporate data of hundreds of Xiaomi users. In scope under the owner's rule: Claude did the data-processing work.

**Changes:** New incident (Accomplice League).

**Scoring notes:**
- `org: Anthropic`, `Undisclosed model` (the report does not name the model), `blast_radius: own_prod`.
- `contribution: operated`. A reviewer could argue that generating the training pairs is just the loot and the rest is `wrote_content`-level.
- `statutes`: 18 USC 1832 (10) only. Unlike Zhipu/Alibaba/Moonshot, the Xiaomi section does not call the accounts fraudulent; the report's stolen-card/stolen-key description is about proxy services in general, so 1343/1029 were not charged. `legal_status: contested`.
- Xiaomi users' data exposure: the report says such practices are "likely inconsistent with privacy laws and the labs' own terms of service" and that it has "no indication US persons' data was exposed". That is not a clear US crime, so users are not listed as victims.
- `date_precision: month` (2026-03-01), `dwell_days: 0`.

**Sources checked:**
- Report PDF pp. 151-152 (read).
- The Hacker News (fetched): names Xiaomi, GTG-16008, 400,000 exchanges. Cited.

**Open questions:** whether the owner treats Claude's generation of the training pairs as "doing the work".
