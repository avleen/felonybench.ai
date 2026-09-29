# Accomplice League leads needing a human write-up

Leads that are in scope (or genuinely contested) but that an agent did not write up this pass.
Each: title, source URLs, one plain sentence. See
`docs/agent-notes/anthropic-sept-2026-threat-report.md` for the full reasoning.

## GTG-34007 - Iranian surveillance malware (Firefox identity harvester) - DRAFT PR, AWAITING NEWS
Sources:
- https://www.anthropic.com/threat-intelligence-report-september-2026
- https://www-cdn.anthropic.com/e50be2e51e7695dc4b1366a37a245a597377d3b5/Anthropic-Detecting-and-countering-091026.pdf
Written up on 2026-09-29 as `2026-08-31-anthropic-iran-firefox-identity-harvester` (victim "The
public", IR; `built_exploit`, `intact`, `crime`, tradecraft `evasion`, 18 USC 1030(a)(2)(C) at the
1-year misdemeanor level, `confidence: low`), with primary sources only, in draft PR
https://github.com/avleen/felonybench.ai/pull/19 labelled `awaiting-news`. Coverage that was found and
fetched while writing it is listed in the PR for the owner to add: RFE/RL (2026-09-11,
https://www.rferl.org/a/anthropic-claude-iran-propaganda/33852428.html) and Iran International
(2026-09-13, https://www.iranintl.com/en/202609131676).

## GTG-50027 - Mali national mass-interception platform ("Lakana 360") - WAITING FOR A MODEL
Sources:
- https://www.anthropic.com/threat-intelligence-report-september-2026
- https://www-cdn.anthropic.com/e50be2e51e7695dc4b1366a37a245a597377d3b5/Anthropic-Detecting-and-countering-091026.pdf
- https://www.therundown.ai/news/anthropic-claude-misuse-threat-report-september-2026
A Bamako consultant used Claude as the engineering workforce for a ~25M-SIM domestic surveillance
platform for Mali's state intelligence service, deliberately built to remove a warrant requirement
Malian law imposes. The owner decided on 2026-09-29 to wait until a model is identified: the
deployed platform runs fully on-premises on unnamed local models. It stays `pending_human` in
`agent/known-leads.yaml` with the reason "waiting for an identifiable model".

## GTG-14021 - PRC venue scouting of overseas protests (Vancouver / Turkey / Oslo) - REJECTED 2026-09-29
The owner asked whether the act was criminal (if so, the victim could be "the public"). On the
report's facts, it was not. The bureau worked from inside the PRC and compiled the gathering point,
route and terminus of a Vancouver march, Uyghur cultural-event venues in Turkey and Oslo Freedom
Forum screenings. The report itself calls these "lawful overseas protests", and such details are
normally public. The report documents no operation, contact, threat or harassment that followed.
- 18 USC 2261A needs a course of conduct against a specific person that causes fear or substantial
  emotional distress.
- 18 USC 951 needs someone acting in the US as a foreign agent.
- Host-country foreign-interference and harassment offences need intimidation, covert or unlawful
  means, or an act on their territory. None of these is reported.

Recorded as rejected in `agent/known-leads.yaml`. Revisit if a source documents an operation.

## GTG-27006 - Russia sanctions / export-control evasion procurement - WRITTEN UP 2026-09-29
Written up as `2026-08-31-anthropic-russia-dual-use-procurement`. The victim is "The public" (EU),
because the briefings describe evading European trade controls. Scoring: `blast_radius: public`,
`wrote_content`, `intact`, `crime`, IEEPA 50 USC 1705 (20y) plus ECRA 50 USC 4819 (20y), and
Regulation (EU) 833/2014 as the foreign law.

## Illicit distillation by PRC labs - RESOLVED 2026-09-29
The owner decided that "Claude being the target counts if AI was used to do the work." Written up:
Zhipu (two incidents), Xiaomi and SenseTime, where the report says Claude did the processing,
grading or pipeline-writing work. Rejected: Alibaba, Moonshot, DeepSeek and MiniMax, where the report
shows Claude only producing the stolen output. See the distillation section of
`anthropic-sept-2026-threat-report.md`. One call remains open for the owner: whether Claude
decoding its own thinking signature in Moonshot's and DeepSeek's "cross-session replay" attack
counts as the AI doing the evasion. If it does, both become incidents.
