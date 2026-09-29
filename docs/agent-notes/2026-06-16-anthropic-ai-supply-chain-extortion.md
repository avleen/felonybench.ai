Anthropic's September 2026 threat report (GTG-50020) describes a Russian-speaking, financially-motivated actor that historically hit hotel-booking and fintech platforms (in one intrusion, ~26GB exfiltrated and $1.5-2.5M extortion demands), then redirected the same tradecraft at the AI supply chain: by prompt-injecting an AI vendor's evaluation sandbox it stole production API keys, then ran a follow-on campaign against ~30 AI companies in about four days, aiming (unsuccessfully) to reach a pre-release Claude model. An autonomous exploitation pipeline ran injection/XSS/auth-bypass/SSRF against production systems without supervision. In scope: a documented real-world intrusion-and-extortion campaign by a human actor using a named lab's model against real victims.

**Changes:** New incident (Accomplice League).

**Scoring notes:**
- `contribution: operated` (autonomous exploitation pipeline against production, under the actor's direction).
- `guardrails: intact`: the actor's technique was prompt-injecting a *third-party* sandbox, not defeating Claude's own safeguards; the ambition to reach a pre-release Claude model was never realized (an attempt, not scored).
- `statutes`: 1030(a)(2)(C) 5y; 1030(a)(7)(B) extortion 5y; 1030(a)(5)(A) 10y. `tradecraft: [credentials, persistence]`. `blast_radius: third_party`.
- `date 2026-06-16` = latest actor egress-IP date; `date_precision: before`; `dwell_days: 0`.

**Sources checked:** report PDF + landing page (read in full); The Hacker News (9/11, fetched, covers GTG-50020).

**Open questions:** whether the ~30-AI-company follow-on warrants separate victim entries (kept as one campaign; the pre-release-model access never succeeded).
