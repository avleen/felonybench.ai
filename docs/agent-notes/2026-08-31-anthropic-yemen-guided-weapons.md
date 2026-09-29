Anthropic's September 2026 threat report (GTG-87001) describes a guided-weapons engineering cell in northern (Houthi-controlled) Yemen running three programs (a guided rocket, a 2,000km+ ballistic missile, and a multi-variant "R2000" set including a hypersonic-glide variant). The cell used Claude Code "in place of human software engineers" to develop guidance, navigation and control software - writing control/position code, tuning it, running a firmware build pipeline and flight simulation, and managing several Claude instances in parallel roles. Anthropic's safeguards blocked many but not all requests; the actors hid their goals and split work across sessions to evade them. They test-fired a guided rocket, which appears to have failed (they returned to Claude within hours for failure analysis). In scope: a documented real-world act (a live field test, beyond a mere attempt) by a human cell using a named lab's model, constituting material support to a designated FTO.

**Changes:** New incident (Accomplice League). `confidence: low` (victim/blast_radius framing).

**Scoring notes:**
- The task asked whether this was only a blocked attempt (then out of scope) or whether Claude materially helped. Claude materially built the GNC guidance software and a live rocket test occurred - a substantial completed act. So it qualifies.
- `contribution: built_exploit` (developed a working weapons component - the guidance software - rather than merely advising).
- `guardrails: jailbroken`: the actors evaded safeguards by hiding goals and splitting work across sessions.
- `legal_status: crime` (not contested): 18 USC 2339B material support to a designated FTO (Ansarallah/Houthis, per the re-designation) is squarely criminal. 22 USC 2778 (AECA) left out because the actors are not US persons.
- Victim/blast_radius is the awkward field: material support has no single struck victim, so the victim is framed as the United States (whose law the support violates) and `blast_radius: government`. A reviewer may prefer a different framing - flagged. `tradecraft: []`; `dwell_days: 0` (before precision, latest date).

**Sources checked:** report PDF + landing page (read in full); The Washington Post (9/11, title/URL confirmed via search) and Al Jazeera (9/11, fetched). Bloomberg and NBC also covered it (not cited).

**Open questions:** whether to treat the US as victim (government) or the FTO's program as a foreign_government-level international incident; whether a reviewer prefers routing this to accomplice-needs-human given the weapons subject.
