Anthropic's September 2026 threat report (GTG-50014) describes operators suspected to be ShinyHunters affiliates, including a French-speaking operator (aliases MeowSHA/frkoo/blazespider) who ran a credential-harvesting pipeline across 10 AWS EC2 workers that downloaded 1.8M Android APKs and scanned them for secrets. AI agents "performed nearly all of the work" across intrusions: a technology provider (>1TB, hundreds of thousands of national IDs and millions of payment-card records staged publicly for extortion), an airline (tens of millions of passenger records), an energy company, a SaaS provider (~200 downstream customers), and a French retail chain. In scope: a documented real-world data-theft-and-extortion campaign by human operators using a named lab's model against real victims.

**Changes:** New incident (Accomplice League).

**Scoring notes:**
- `contribution: operated` (Anthropic: "AI agents performed nearly all of the work"; single-token-to-admin in ~3 hours).
- `statutes`: 1030(a)(2)(C) 5y; 1030(a)(7)(B) extortion 5y (pay-or-leak); 1029(a)(2) access-device fraud 10y (carding autoshop, payment-card records).
- `tradecraft: [credentials, privilege_escalation, lateral_movement, persistence]`. `blast_radius: third_party`.
- `date 2026-05-06` = latest actor egress-IP date in the report; `date_precision: before`; `dwell_days: 0`.

**Sources checked:** report PDF + landing page (read in full); BleepingComputer (Bill Toulas, 9/11, fetched) and The Hacker News (9/11, fetched), both name GTG-50014 / frkoo.

**Open questions:** whether the carding shop impersonating the French national police adds a distinct charge (left as branding, per Anthropic); victim countries mostly not stated.
