OpenAI's February 2026 threat report ("Disrupting malicious uses of our models: an update, February 2026") describes Operation "Date Bait": a scam network very likely based in Cambodia that used ChatGPT accounts and one API customer to run a semi-automated romance and task scam against Indonesian men. ChatGPT wrote ads for a fake luxury dating agency ("Klub Romantis"). An AI chatbot receptionist sent targets to Telegram, where "mentors" used ChatGPT to write and translate manipulative messages pushing targets through paid "missions", ending with a final "kill" payment, after which victims were blocked. The scammers' own inputs suggest hundreds of targets at a time and thousands of dollars a day (OpenAI couldn't verify this). It's in scope: a documented fraud with real victims, carried out with a named lab's product, which the lab disclosed itself.

**Changes:** New incident (Accomplice League seed).

**Sources checked:**
- https://cdn.openai.com/pdf/df438d70-e3fe-4a6c-a403-ff632def8f79/disrupting-malicious-uses-of-ai.pdf (read in full via text extraction): the source for every fact.
- https://openai.com/index/disrupting-malicious-ai-uses/ (403 to direct fetch; read via the Wayback Machine snapshot of 2026-08-28): the Feb 25, 2026 landing page linking the PDF.
- https://www.helpnetsecurity.com/2026/02/26/openai-malicious-chatgpt-use-report/ (read): news coverage of Date Bait.
- https://openai.com/index/disrupting-malicious-uses-of-ai-date-bait/ (the per-case page): appeared in search results, but direct fetch was blocked and there's no Wayback snapshot, so not cited.
- No Wired, AP or Reuters coverage of this case was found.

**Scoring notes:**
- `contribution: wrote_content`, not `operated`: humans ran the funnel, and ChatGPT's main role was writing and translating. But OpenAI says the operation "blended human operators using ChatGPT with API-powered automation" and that the chatbot receptionist talked to targets, so part of the victim contact was model-operated. A reviewer could reasonably pick `operated` (it would raise the base from 10 to 40).
- Statutes: 18 USC 1343 wire fraud, 20 years. Indonesian fraud law is listed without an article number because Indonesia's new Criminal Code (Law 1/2023) took effect in January 2026, and the operation's dates are unknown, so it's unclear whether the old (Art. 378) or new numbering applies.
- `models`: OpenAI doesn't name the model(s) → `Undisclosed model`.
- `dwell_days: 0` from the report date (`date_precision: before`).

**Open questions:**
- OpenAI's caption of the letter to a victim reads "Rp 20,500,000 ($12,000)". Rp 20.5 million is roughly $1,200, not $12,000, so the dollar figure in OpenAI's report looks wrong. The YAML quotes only the rupiah amount.
- A similar, later OpenAI case (Jul 31, 2026, "Disrupting a Criminal Scam Operation", a Poipet, Cambodia network running investment, romance, gambling and police-impersonation scams; read via https://web.archive.org/web/2026/https://openai.com/index/disrupting-malicious-uses-of-ai-criminal-scam-operation/) wasn't written up: victims' countries aren't given, and it would be a near-duplicate pattern. It's a lead for the next sweep.
