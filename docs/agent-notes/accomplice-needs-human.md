# Accomplice League leads needing a human write-up

Leads that are in scope (or genuinely contested) but that an agent did not write up this pass.
Each: title, source URLs, one plain sentence. See
`docs/agent-notes/anthropic-sept-2026-threat-report.md` for the full reasoning.

## GTG-34007 - Iranian surveillance malware (Firefox identity harvester shipped to production)
Sources:
- https://www.anthropic.com/threat-intelligence-report-september-2026
- https://www-cdn.anthropic.com/e50be2e51e7695dc4b1366a37a245a597377d3b5/Anthropic-Detecting-and-countering-091026.pdf
Two Iranian paramilitary/domestic-security units used Claude to build surveillance tooling,
including a malicious Firefox extension ("al-Najm al-thaqib") shipped to production that
mass-harvested real Iranians' identities from social networks - in scope (deployed malware, real
victims), but no dedicated news source was confirmed, and the schema requires one.

## GTG-50027 - Mali national mass-interception platform ("Lakana 360")
Sources:
- https://www.anthropic.com/threat-intelligence-report-september-2026
- https://www-cdn.anthropic.com/e50be2e51e7695dc4b1366a37a245a597377d3b5/Anthropic-Detecting-and-countering-091026.pdf
- https://www.therundown.ai/news/anthropic-claude-misuse-threat-report-september-2026
A Bamako consultant used Claude as the engineering workforce for a ~25M-SIM domestic surveillance
platform for Mali's state intelligence service, deliberately built to remove a warrant requirement
Malian law imposes - contested legality, but the deployed system runs on local models and no
completed surveillance of an identifiable victim is documented.

## GTG-14021 - PRC transnational-repression venue scouting (Vancouver / Oslo)
Sources:
- https://www.anthropic.com/threat-intelligence-report-september-2026
- https://www-cdn.anthropic.com/e50be2e51e7695dc4b1366a37a245a597377d3b5/Anthropic-Detecting-and-countering-091026.pdf
A PRC municipal security actor used Claude to produce pre-operational venue intelligence on lawful
overseas protests (a Vancouver pro-democracy march, Oslo Freedom Forum screenings) - the closest of
the PRC surveillance cases to a chargeable 18 USC 2261A transnational-repression offense, needing a
human call on whether report-generation reaches a completed crime.

## GTG-27006 - Russia sanctions / export-control evasion procurement
Sources:
- https://www.anthropic.com/threat-intelligence-report-september-2026
- https://www-cdn.anthropic.com/e50be2e51e7695dc4b1366a37a245a597377d3b5/Anthropic-Detecting-and-countering-091026.pdf
A Moscow procurement manager used Claude to route dual-use goods to Russian defense customers and
wrote briefings explicitly describing the routing as a way to evade European trade controls - a real
IEEPA/EAR-style crime, but with no discrete victim, so a human should decide scope and scoring.

## Illicit distillation by PRC labs - RESOLVED 2026-09-29
The owner decided that "Claude being the target counts if AI was used to do the work." Written up:
Zhipu (two incidents), Xiaomi and SenseTime, where the report says Claude did the processing,
grading or pipeline-writing work. Rejected: Alibaba, Moonshot, DeepSeek and MiniMax, where the report
shows Claude only producing the stolen output. See the distillation section of
`anthropic-sept-2026-threat-report.md`. One call remains open for the owner: whether Claude
decoding its own thinking signature in Moonshot's and DeepSeek's "cross-session replay" attack
counts as the AI doing the evasion. If it does, both become incidents.
