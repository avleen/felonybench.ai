# Anthropic "Detecting and countering misuse of AI: September 2026"

Report published 2026-09-10 (154 pages), covering activity disrupted Dec 2025-Aug 2026 across
seven harm areas: cyber operations, influence operations, surveillance, conventional weapons,
biological misuse, scams and fraud, and illicit distillation. PDF read in full via pypdf:
https://www-cdn.anthropic.com/e50be2e51e7695dc4b1366a37a245a597377d3b5/Anthropic-Detecting-and-countering-091026.pdf
Landing page: https://www.anthropic.com/threat-intelligence-report-september-2026

`org` is Anthropic and `self_disclosed: true` throughout (Anthropic reported it itself).
Models are scored `Undisclosed model` / `family: null`: the report says only that Haiku, Sonnet
and Opus models were used, never which model per case. All new incidents use
`date_precision: before` (or `month` for the dating case) with the latest possible date, and
`dwell_days: 0` counted conservatively from that latest date, per the runbook.

## Written up (8 incidents)

Every one is a documented real-world act by a human/group using a named lab's model, with a real
victim (or, for Yemen, a clear completed crime), Claude used as `operated` or `built_exploit`.

| id | GTG | contribution | blast_radius | legal_status |
|---|---|---|---|---|
| 2026-08-31-anthropic-iran-navy-targeting | GTG-30005 | operated | government | contested |
| 2026-08-31-anthropic-russia-midnight-blizzard-espionage | GTG-20006 | operated | foreign_government | crime |
| 2026-05-06-anthropic-shinyhunters-data-extortion | GTG-50014 | operated | third_party | crime |
| 2026-08-31-anthropic-china-exploit-foundry-espionage | GTG-10007 | operated | foreign_government | crime |
| 2026-06-16-anthropic-ai-supply-chain-extortion | GTG-50020 | operated | third_party | crime |
| 2026-07-04-anthropic-french-hacktivist-doxxing | GTG-50029 | operated | third_party | crime |
| 2026-04-01-anthropic-dating-app-persona-fraud | GTG-15001 | operated | third_party | crime |
| 2026-08-31-anthropic-yemen-guided-weapons | GTG-87001 | built_exploit | government | crime |

Scoring notes:
- **Iran Navy (GTG-30005)** `legal_status: contested`. Compiling public information is usually
  lawful; 18 USC 793/794 require national-defense information that is closely held / not public, so
  they likely do not reach OSINT compilation. The genuinely disputed exposure is 18 USC 951 (acting
  as an agent of a foreign government without notification) and IEEPA / Iran sanctions (50 USC 1705,
  31 CFR 560) for an Iranian actor's use of a US service. 793 considered and left out of `statutes`.
  Cataloguing known CVEs (VSAT/Cisco/ICS) is not exploitation, so no tradecraft and no CFAA charge.
  `contribution: operated` because Claude built and ran the collection pipeline.
- **GTG-20006 / GTG-10007** score high because blast_radius is `foreign_government` (Ukraine/Europe/
  North Africa; a Southeast Asian government agency) and Claude executed intrusions. 18 USC 1831
  (economic espionage) added given the state-nexus and theft of proprietary/appliance data; 1030(a)(5)(A)
  at the felony 10-year level given hundreds of thousands of records and hundreds of GB exfiltrated.
- **GTG-50014 / GTG-50020** include 1030(a)(7)(B) (extortion) and, for ShinyHunters, 1029(a)(2)
  (access-device fraud) for the carding shop and payment-card records.
- **Guardrails: intact** for all cyber/fraud cases. The report does not describe these specific
  actors jailbreaking Claude's safety training; stolen API keys and prompt-injection of *third-party*
  sandboxes are access-control/attack techniques, not defeats of Claude's safeguards. A reviewer
  could argue `jailbroken` for the sophisticated actors ("persistent threat actors continuously test
  our safeguards"), which would add 5 points each; I kept the conservative reading tied to per-case facts.
- **Dating (GTG-15001)** mirrors the existing 2026-02-25-openai-date-bait-romance-scam: `operated`
  (Claude ran the personas and talked to victims), `intact` (ordinary roleplay system prompt), `[]`
  tradecraft. `date_precision: month` (April 2026 two-week window).
- **Yemen (GTG-87001)** `confidence: low`. It clearly qualifies: a real-world act (a live rocket
  field test, so beyond a mere attempt) by a human cell using Claude Code, which *built* the GNC
  guidance software (`built_exploit`), evading safeguards (`jailbroken`). The awkward field is the
  victim/blast_radius: this is a 18 USC 2339B material-support offense (Ansarallah/Houthis are a
  US-designated FTO per the re-designation), which has no single struck victim. I framed the victim
  as the United States (whose law the material support violates) and `blast_radius: government`.
  A reviewer may prefer a different framing; flagged in the report. Arms-export law (22 USC 2778)
  left out because the actors are not US persons. Legal_status is `crime`, not `contested`: material
  support to a designated FTO is squarely criminal.

## Rejected / not written (with reasons)

### Influence operations (Section 2) - all 9 rejected
GTG-04001 (Russia/Wagner FIMI in CAR), GTG-54002 (LKM Company / France, ~70 fake news sites),
GTG-84005 (BBS Bilisim / Malaysia election manipulation), GTG-24015 (Russian state-media editorial
pipelines; defamation of Moldova's president Maia Sandu), GTG-34001 (Iranian ICCO/IPO/Bina),
GTG-54006 (pro-Awami League Bangladesh fake news), GTG-84006 (MEK/NCRI; cloned a real activist's
Telegram to run live chats with his contacts), GTG-54004 (Kenya astroturfing), GTG-84002 (UAE anti-
Muslim-Brotherhood; cloned a real Swiss NGO, ghost-wrote UN testimony).
**Reason:** coordinated inauthentic behavior / propaganda is not, on these facts, a chargeable US
federal crime with a concrete victim, and the criteria call for a crime or genuinely contested
legality. Sub-elements were considered - forged CAR government documents (GTG-04001), impersonation
of a real activist (GTG-84006) and of a real NGO (GTG-84002), defamation of named figures - but each
is foreign, murky, and Anthropic often could not confirm the content reached an audience. Recorded
in known-leads as rejected; the impersonation cases (GTG-84006, GTG-84002) are the closest calls.

### Surveillance operations (Section 3)
- **GTG-34007** (Iran; a malicious Firefox extension shipped to production that mass-harvested real
  Iranians' identities, plus a national-ID phishing page and de-anonymizer tools) - **in scope**
  (deployed malware, real victims). Not written this pass: no dedicated news coverage was confirmed,
  and >=1 news source is required. Recorded in `accomplice-needs-human.md`.
- **GTG-50027** (Mali "Lakana 360" mass interception for the state intelligence service, ~25M SIMs,
  deliberately built to remove a warrant requirement Malian law imposes) - **in scope but contested**:
  Claude was the engineering workforce, but the deployed platform runs on local models, and no
  completed surveillance of an identifiable victim is documented. Recorded in `accomplice-needs-human.md`.
- **GTG-14010, GTG-14020, GTG-14021, GTG-14022** (PRC surveillance / transnational repression of
  Uyghurs, religious minorities, Hong Kong / diaspora dissidents) - rejected: the activity is
  intelligence analysis, profiling and report-generation, not a completed chargeable crime against an
  identifiable victim. GTG-14021 (pre-operational venue scouting for a Vancouver march and Oslo
  Freedom Forum) is the closest to a 18 USC 2261A transnational-repression charge; flagged as a
  human call in `accomplice-needs-human.md`.
- **GTG-54009** (S2T commercial surveillance of Iran/Gulf social-media users) - rejected: caught at
  pilot stage; Anthropic found no evidence it was used against real targets.
- **GTG-30004, GTG-30006** (Iran; OSINT identity-profiling harness + NanoDump obfuscation; SECOMS64
  implant, phishing portal, M365 mailbox-theft tooling) - rejected: the report says the actors used
  Claude "to engineer and test this tooling rather than to conduct live operations", so no completed
  act against a confirmed victim (attempt-level).

### Conventional weapons (Section 4)
- **GTG-17001** (China anti-torpedo fire-control spec/proposal for the PLA Navy), **GTG-17002**
  (China EW/air-defense-suppression targeting suite; mid-project switched to 12 Taiwan targets),
  **GTG-27005** (Russia freelance autonomous FPV kamikaze-drone swarm) - rejected: a state's (or
  freelancer's) development of its own weapons is not a crime with a victim under the FelonyBench
  criteria, and no completed strike/victim is reported. Contested at most.
- **GTG-27006** (Russia procurement; explicitly evading European export controls, sanctioned dual-use
  goods for Russian defense) - **contested / needs human**: sanctions and export-control evasion
  (IEEPA / EAR) is a real crime, but there is no discrete victim, and the goods went to Russia.
  Recorded in `accomplice-needs-human.md`.
- **GTG-17003** (China OSINT on US directed-energy weapons) - rejected: gathering open-source
  information is lawful; no victim, no crime.

### Biological misuse (Section 5) - all 5 rejected
Chikungunya gain-of-function reseller/evasion platform; mammal-adapted avian-influenza research;
orthopoxvirus grant via a reseller relay; venom-peptide atlas; toxin redesign. **Reason:** Anthropic
explicitly says "We do not assert that they intended harm", withholds names, countries and agents,
and describes dual-use research by working scientists. No completed crime and no victim; the only
line crossed is region-block / Supported-Regions evasion, which is a terms-of-service matter, not a
crime.

### Illicit distillation (Section 7)
GTG-16005 (Alibaba/Qwen - largest campaign, ~3M exchanges/day via thousands of fraudulent accounts,
virtual cards, stolen API keys), GTG-16002 (Moonshot), GTG-16001 (DeepSeek), GTG-16006 (Zhipu),
GTG-16008 (Xiaomi), GTG-16012/16003 (SenseTime, MiniMax). Initially recorded as needing a human
scope decision, because Claude is the *target* of the theft here rather than the human's instrument.

**Owner's decision (2026-09-29):** "Claude being the target counts if AI was used to do the work."
A case qualifies when an AI system did the work of the crime (harvesting, account creation, key/card
fraud, evasion, processing the stolen material), even though the victim is Anthropic and the loot is
Claude's output. Claude merely *producing* the stolen output is the loot, not the work; if the report
shows only ordinary pipelines, proxy networks or humans doing the work, the case does not qualify.
When Claude did the work, `org: Anthropic` and `blast_radius: own_prod` (or `third_party` when
another lab is the victim). All written cases use `legal_status: contested`, because whether
distilling model outputs is trade-secret misappropriation is an open legal question (Beck Reed
Riden LLP, 2026-05-12), even though fraudulent-access schemes are argued to be CFAA/wire-fraud
territory (AEI, 2026-08-03).

Written up (3 incidents; a fourth, SenseTime, was later dropped - see below; all `confidence: low`, `self_disclosed: true`, news source The Hacker News
2026-09-11):

| id | GTG | what Claude did | contribution | blast_radius | statutes |
|---|---|---|---|---|---|
| 2026-06-01-anthropic-zhipu-cot-distillation-cleaner | 16006 | cleaned/normalized/graded harvested CoT traces (770,609 exchanges through the cleaner in 10 days) | operated | own_prod | 1343, 1832 |
| 2026-08-14-anthropic-zhipu-cyber-distillation-grader | 16006 | Opus 4.6 graded another US lab's model's CTF answers in a cyber-distillation attack | operated | third_party | 1832 |
| 2026-03-01-anthropic-xiaomi-distillation-data-pipeline | 16008 | rebuilt dev environments, cleaned and generated conversations, judged answers | operated | own_prod | 1832 |

**GTG-16012 SenseTime** was written up (Claude wrote the distillation pipeline and launched and monitored training runs), then dropped on the owner's ruling (2026-09-29): it is the weakest legal theory, since the transcripts were outputs users could already see. Recorded as `rejected` in `agent/known-leads.yaml`.

Rejected under the owner's rule (the report shows no AI system doing the work of the crime):
- **GTG-16005 Alibaba**: the CoT pipeline "injected a fixed prompt" forcing Claude to write out its
  reasoning. That is Claude producing the loot, and the report does not say an AI built or ran the
  pipeline or created the ~3,500-5,000 fraudulent accounts (residential proxies, disposable emails,
  virtual cards). Alibaba also used Claude for its RL environments, model-development
  infrastructure and architecture research, but the report does not tie that work to the
  distillation crime. Closest call after Moonshot/DeepSeek.
- **GTG-16002 Moonshot** and **GTG-16001 DeepSeek** (later reversed; see below): the silent relaying of customers' requests to
  Claude, the CoT extraction pipelines and the 5,380 fraudulent accounts (Moonshot) are not described
  as AI-built or AI-run. Claude answering the relayed customers, and the "cross-session replay" attack
  (eliciting Claude to convert its thinking signature back into the raw trace), are both Claude
  producing the stolen output. That is the loot, not the work. **Closest call in the cluster:** if the
  owner counts Claude decoding its own thinking signature as the AI performing the evasion, both
  become incidents (org Anthropic, own_prod). DeepSeek's routing chose users by checking request
  strings, which is ordinary scripting. China's CAC is reportedly probing both labs over the user-data
  exposure (Yahoo/The Next Web/Quartz headlines, not fetched).
- **GTG-16003 MiniMax**: a shell-company proxy network harvesting user exchanges with Anthropic and
  OpenAI models. The report describes no AI doing the work.

**Moonshot and DeepSeek reversed (owner, 2026-09-29):** Claude converting its thinking signature
back into the raw trace is Claude doing the work of defeating Anthropic's anti-distillation control,
so both are written up as Accomplice incidents (org Anthropic, own_prod, `contribution: operated`,
`legal_status: contested`, `tradecraft: [evasion]`, `self_disclosed: true`):

| id | GTG | statutes | score |
|---|---|---|---|
| 2026-07-31-anthropic-moonshot-thinking-signature-replay | 16002 | 17 USC 1201(a)(1)(A) (5, via 1204), 1832, 1343 (the report ties 5,380 fraudulent accounts to Moonshot) | 19.5 |
| 2026-07-01-anthropic-deepseek-thinking-signature-replay | 16001 | 17 USC 1201(a)(1)(A), 1832 (no fraudulent accounts of DeepSeek's own are described, so no 1343) | 9.5 |

Dates: Moonshot's traffic is attributed to "between May and July 2026" (`before`, 2026-07-31);
DeepSeek's to "14 days in July 2026" (`month`, 2026-07-01). The silent relaying of customers'
requests is still not counted.

### Also rejected
- **GTG-50021** (fraudulent "cheap Claude" reseller, "kl1zy"; silently proxied traffic to another
  model and harvested Anthropic account credentials) - rejected: Claude was not the instrument of the
  crime; this is credential theft / brand abuse against Anthropic customers, overlapping the AI-supply-
  chain theme already covered by GTG-50020.

## Sourcing checked
Report PDF + landing page (read in full). News confirmed by fetching: Navy Times (Ceder, 9/11),
gCaptain (Schuler, 9/11), BleepingComputer (Toulas, 9/11), The Hacker News (Lakshmanan, 9/11),
Techlicious (Kantra, 9/14), Al Jazeera (staff, 9/11). News confirmed by title+URL from search
listings but body not fetched: Washington Post (9/11, Yemen), Storyboard18 (dating). No Wired/AP/
Reuters coverage of specific cases was found; Bloomberg and NBC also covered the Yemen case (not
cited). Axios ("5 ways Claude was exploited for war, spying and repression") returned 403 and is not
cited. Web pages were treated as data, not instructions.
