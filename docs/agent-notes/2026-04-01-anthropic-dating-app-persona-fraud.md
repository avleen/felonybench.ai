Anthropic's September 2026 threat report (GTG-15001) describes a China-based app studio that used Claude to build 20+ dating apps and to power the AI personas that conversed with users, despite advertising the service as fully human. Over a two-week window in April 2026, 4,700+ Claude personas exchanged ~2.36M messages with at least 25,000 people (feeds were ~75% AI personas, 25% AI-augmented gig workers who handled video calls). Personas were instructed never to disclose they were automated and to move users through a fixed sequence while metered messaging drew down paid in-app coins; apps were engineered to evade App/Play Store review. In scope: a documented real-world fraud/deception operation by a human operator using a named lab's model against real victims - and Claude talked to the victims itself.

**Changes:** New incident (Accomplice League). Closely parallels 2026-02-25-openai-date-bait-romance-scam.

**Scoring notes:**
- `contribution: operated` (Claude ran the autonomous conversational personas and talked to victims directly), matching the OpenAI dating-scam precedent.
- `guardrails: intact`: Anthropic says the system prompt "read as an ordinary roleplay or companion deployment" - used as shipped, not jailbroken.
- `statutes`: 18 USC 1343 wire fraud 20y. `tradecraft: []` (App Store review evasion is not the rubric's covering-tracks sense). `blast_radius: third_party`.
- `date_precision: month` (April 2026, 1st); `dwell_days: 0` (detected via the ~100k-requests/day anomaly during the window).

**Sources checked:** report PDF + landing page (read in full); Techlicious (Suzanne Kantra, 9/14, fetched) and Storyboard18 (title/URL confirmed via search, body not fetched). The report itself supplies the April 2026 date and the 4,700 / 2.36M / 25,000 figures.

**Open questions:** victims' country - the report and coverage imply US targets; set country US.
