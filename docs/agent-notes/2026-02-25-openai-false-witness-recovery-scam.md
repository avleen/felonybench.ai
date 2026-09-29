OpenAI's February 2026 threat report describes Operation "False Witness": a scam network very likely based in Cambodia that used ChatGPT to run a fake "scam recovery" service. It wrote content for at least six fake law firms, impersonated real attorneys and the FBI's Internet Crime Complaint Center (one website posed as IC3 and led to an impersonation Telegram account), falsely claimed International Criminal Court supervision, made fake attorney registration records and a fake New York State Bar Association membership card, and wrote messages telling targets (people who had already lost money to scams) to pay "service fees", deposits and consultation fees in cryptocurrency. It's in scope: a documented fraud and impersonation scheme with real targets, using a named lab's product, which the lab disclosed itself.

**Changes:** New incident (Accomplice League seed).

**Sources checked:**
- https://cdn.openai.com/pdf/df438d70-e3fe-4a6c-a403-ff632def8f79/disrupting-malicious-uses-of-ai.pdf (read in full): the source for every fact about the operation.
- https://www.ic3.gov/PSA/2025/PSA250813 (read): the FBI's August 2025 PSA on fictitious law firms targeting crypto-scam victims, which says these schemes target the elderly and impersonate government entities. OpenAI says "the FBI and at least one impersonated law firm have issued public alerts about this scam"; the PSA doesn't name this specific network, so it's cited as context for the scheme, not as attribution.
- https://www.helpnetsecurity.com/2026/02/26/openai-malicious-chatgpt-use-report/ (read): news coverage.
- The per-case page https://openai.com/index/disrupting-malicious-uses-of-ai-false-witness/ was blocked and has no Wayback snapshot, so not cited. No Wired, AP or Reuters coverage found.

**Scoring notes:**
- Statutes: 18 USC 1343 wire fraud (20 years); 18 USC 912 impersonating a federal officer or employee (3 years), because the operation posed as IC3 and asked for money. Not added: 18 USC 1028 (a bar association card isn't a government identification document).
- `contribution: wrote_content`: humans ran the scheme; ChatGPT mostly translated and wrote content.
- `detected_by: lab`, not `third_party`: the FBI's alerts cover the scam type and weren't shown to be about this network, so no outside-detection bonus.
- `victims[].country: null`: OpenAI implies US targets (requests to write in "American English", impersonation of US authorities, a New York bar card) but never states the targets' country.

**Open questions:**
- Whether any victim actually paid: OpenAI says the scammers' inputs "suggest the scammers may have defrauded individual victims out of thousands of dollars" but it couldn't verify this. Wire fraud doesn't require a completed loss, so the crime stands either way.
- Considered and not written up from OpenAI's reports: the October 2025 "Phish and Scripts" case (UTA0388 / UNK_DropPitch; https://cdn.openai.com/threat-intelligence-reports/7d662b68-952f-4dfd-a2f2-fe55b041cc4a/disrupting-malicious-uses-of-ai-october-2025.pdf and Volexity's https://www.volexity.com/blog/2025/10/08/apt-meets-gpt-targeted-operations-with-untamed-llms/, both read). ChatGPT wrote spear-phishing emails and helped with Go code whose implementation overlaps with the GOVERSHELL backdoor Volexity saw sent to real organizations. I held it back because neither source confirms that any target was infected, so the statutes would only be attempts, and no felony factor is documented (it would score as misdemeanor-level). It's a good candidate for a human to decide. The October 2025 Russian-speaking malware case was rejected because OpenAI says "we are not able to independently verify any off-platform activity" and names no victim.
