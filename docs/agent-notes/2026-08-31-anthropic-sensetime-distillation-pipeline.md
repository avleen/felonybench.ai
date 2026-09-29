Anthropic's September 2026 threat report (GTG-16012) says "SenseTime's distillation pipeline included transcripts of user exchanges with Claude purchased from third-party data vendors", harvested from users who accessed Claude through intermediaries that logged and sold the transcripts, and that "SenseTime also used Claude to write the distillation pipeline and to launch and monitor training runs." In scope under the owner's rule: Claude wrote the pipeline.

**Changes:** New incident (Accomplice League).

**Scoring notes:**
- `org: Anthropic`, `Undisclosed model`, `blast_radius: own_prod`, `contribution: built_exploit` (Claude wrote the tool; launching and monitoring training runs is not the crime).
- `statutes`: 18 USC 1832 (10), on a receipt/possession theory for purchased harvested transcripts. This is the weakest theory in the cluster: the transcripts are user-visible outputs, not withheld reasoning, so `legal_status: contested` and `confidence: low`. No fraud statute: the report does not say SenseTime itself used fraudulent accounts.
- No date: `date_precision: before`, `2026-08-31` (the report's coverage ends August 2026), `dwell_days: 0`.

**Sources checked:**
- Report PDF pp. 152-153 (read).
- The Hacker News (fetched): names SenseTime/GTG-16012 and the purchased transcripts, but not Claude writing the pipeline. Cited.

**Open questions:** whether buying logged transcripts is a crime at all. A reviewer may prefer to reject this one on the legal-status ground.
