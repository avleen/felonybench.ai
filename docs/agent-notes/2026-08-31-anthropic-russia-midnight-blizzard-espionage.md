Anthropic's September 2026 threat report (GTG-20006) describes a Russian state-nexus espionage actor, attribution consistent with Midnight Blizzard, one operator using the handle "JackPoterz". It used Claude to run near-automated intrusions against 20+ organizations concentrated in Ukraine and Europe - government ministries, embassies, defense/intelligence bodies, think tanks and drone-industry firms - plus a North African government technology authority (300,000+ national identity records and half a million companies' registry data exfiltrated). Claude fingerprinted systems, ran device-code phishing, executed commands, harvested credentials, moved laterally, auto-registered rogue devices for persistence, and rebuilt malware to evade detection. In scope: a documented real-world intrusion campaign by a human actor using a named lab's model against real (foreign-government) victims.

**Changes:** New incident (Accomplice League).

**Scoring notes:**
- `contribution: operated` (Anthropic: the actor used AI to build and operate the intrusion platform and executed intrusions directly).
- `blast_radius: foreign_government` (Ukraine/Europe/North Africa) -> international_incident badge.
- `guardrails: intact`: no jailbreak of Claude's safety training described for this actor (a reviewer could argue jailbroken for a sophisticated state actor; +5).
- `statutes`: 1030(a)(2)(C) 5y; 1030(a)(5)(A) at felony 10y (hundreds of GB, 300k+ records); 18 USC 1831 economic espionage 15y (state-nexus theft of a proprietary drone SDK). Foreign victims but foreign_government blast already earns the international badge, so foreign_laws left [] (no specific foreign statute confirmed).
- `tradecraft: [credentials, lateral_movement, persistence, evasion]`.

**Sources checked:** report PDF + landing page (read in full); The Hacker News (Ravie Lakshmanan, 9/11, fetched, covers GTG-20006) and Al Jazeera (9/11, fetched, names Midnight Blizzard/APT29). Microsoft's July 2026 "CaptiveCrunch" report is referenced by Anthropic but not fetched or cited.

**Open questions:** guardrails intact vs jailbroken; whether the hotel-WiFi guests and drone makers warrant a separate third_party file (kept as one campaign).
