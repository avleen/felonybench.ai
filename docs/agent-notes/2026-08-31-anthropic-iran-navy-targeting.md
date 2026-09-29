Anthropic's September 2026 threat report (GTG-30005) describes an Iran-nexus actor that used Claude to develop targeting recommendations against US naval forces in the Middle East: it built a Python pipeline (with Claude's assistance) that compiled targeting handbooks to identify and track naval positions from open-source data - a roster of US personnel scraped from public military-photo captions, ship/aircraft transponder identifiers, commercial satellite-imagery query scripts, and public websites exposing US naval movements - and directed Claude to catalogue known CVEs in shipboard systems (COBHAM SAILOR 900 VSAT, Cisco comms gear, Schneider ICS). Anthropic banned the account and shared intelligence with authorities; it could not confirm the material was used in any operation. In scope: a documented real-world act by a human actor using a named lab's model against a real victim (the US Navy).

**Changes:** New incident (Accomplice League).

**Scoring notes:**
- `legal_status: contested` per the runbook and task brief. Compiling public information is usually lawful; 18 USC 793/794 need national-defense information that is closely held / not public, so they likely do not reach OSINT compilation (793 considered and left out of `statutes`). The genuinely disputed exposure is 18 USC 951 (unregistered agent of a foreign government, 10y) and IEEPA / Iran sanctions (50 USC 1705; 31 CFR 560, 20y) for an Iranian actor's use of a US service.
- `contribution: operated`: Claude built and ran the automated collection pipeline that compiled the handbooks.
- `tradecraft: []`: cataloguing known CVEs is not exploitation; no intrusion, so no CFAA charge.
- `blast_radius: government` (US Navy; domestic victim, foreign actor). `dwell_days: 0` (date_precision before, latest-possible date).

**Sources checked:** report PDF + landing page (read in full); Navy Times (Riley Ceder, 9/11, fetched) and gCaptain (Mike Schuler, 9/11, fetched). No Wired/AP/Reuters coverage found.

**Open questions:** whether a reviewer prefers `crime` over `contested`; whether 951 requires proof the actor was tasked by Iran (report says Iran-nexus, not tasked).
