# GTIG: criminal zero-day "developed with AI" (May 2026): not an incident

**Decision:** skipped, because the AI isn't identified. Added to `agent/known-leads.yaml` as `rejected`.

Google Threat Intelligence Group's "GTIG AI Threat Tracker: Adversaries Leverage AI for Vulnerability Exploitation, Augmented Operations, and Initial Access" (May 11, 2026; https://cloud.google.com/blog/topics/threat-intelligence/ai-vulnerability-exploitation-initial-access, read in full) says that "for the first time, GTIG has identified a threat actor using a zero-day exploit that we believe was developed with AI". Prominent cybercrime actors, planning a mass exploitation operation, had a Python 2FA bypass (it still needs valid credentials) for "a popular open-source, web-based system administration tool". GTIG worked with the vendor to disclose and disrupt it, and says its "proactive counter discovery may have prevented its use".

On which AI was used, GTIG says: "**Although we do not believe Gemini was used**, based on the structure and content of these exploits, we have high confidence that the actor leveraged an AI model". The evidence is educational docstrings, a hallucinated CVSS score and textbook Pythonic structure. No model or lab is named. Secondary coverage (e.g. search snippets from the Cloud Security Alliance note) adds that neither Gemini nor Anthropic's Mythos was used and suggests open-weight models, but I didn't read or verify a primary source for that, and it still names no model.

Two reasons this can't be an Accomplice League incident:
1. No named model or lab, so no `org`.
2. Per GTIG, the exploit may never have been used against a victim, and neither the victim vendor nor the actor is named.

Reopen if GTIG or the vendor later names the model or confirms exploitation.

Other cases in the same GTIG report involve Gemini by name (e.g. UNC2814's persona-prompting for embedded-device vulnerability research, and APT45's thousands of CVE-analysis prompts). These are vulnerability *research*, with no documented victim or completed crime in the report, so they weren't written up here. A future sweep could check GTIG's later reports for Gemini-linked cases that have a victim.
