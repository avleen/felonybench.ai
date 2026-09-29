# Search: documented crimes using uncensored or abliterated open-weight models

**Result:** no qualifying incident found. I found no documented real-world crime, with a victim, where the sources name an uncensored or abliterated model and the organization that modified it. So the co-defendant (`modified_by`) path has no seed incident yet.

## Searches run (Sept 29, 2026)
- abliterated model used in cyberattack / malware / fraud; uncensored Qwen / Llama / DeepSeek real-world
- threat intelligence report attacker used "abliterated" OR "uncensored" local model / Ollama
- WormGPT variants built on Mixtral / Grok; uncensored LLM arrest or charges

## Near misses (read, and why each fails)
- **Sysdig TRT, "LLMjacking evolved" (June 2026)**, https://www.sysdig.com/blog/llmjacking-evolved-attackers-are-using-stolen-ai-compute-to-build-offensive-agentic-tools (read). An actor, apparently operating from India, used someone else's exposed, unauthenticated Ollama server as the engine of an autonomous exploitation pipeline ("VAPT"). The tool asked for seven models by name, including "in its first probes, an 'abliterated' (guardrail-removed) Llama-3.3-70B". It fails for three reasons. Every target was a private practice range (RFC 1918 addresses, fictitious apps, HackTheBox's 10.129.0.0/16), and Sysdig says "no public host appeared as a target", so no victim of the AI's work. The only crime (using the exposed server without authorization) was the human's, not something the model did. And neither the abliteration's author nor whether that model actually answered is documented. Worth rechecking if Sysdig reports the tool being used on real targets.
- **Cato CTRL, WormGPT variants on Grok and Mixtral (June 2025)**: coverage seen in search results (Cato's blog, CyberScoop, CSO, TechRepublic); not fetched. These are criminal *tools for sale* made by system-prompt jailbreaks (and possibly fine-tuning) of hosted Grok and Mixtral. They're not abliterated weights, and no documented attack on a named victim is tied to them. That makes them out of scope under the plan ("uncensored model releases with no documented misuse").
- Blogs, benchmarks and papers on abliterated Qwen3.8-27B builds, the "Millions are downloading dangerous uncensored models" piece, and the arXiv paper "Uncensored Open-weight Models: Redistribution as the Persistence Layer" (2609.05241): search results only, not read. All are releases or capability measurements, which the plan excludes.
- Lead **not** verified: US federal prosecutions for AI-generated child sexual abuse material have named open-weight image models (e.g. Stable Diffusion in a May 2024 DOJ case). The DOJ page returned an empty body to both fetch tools, so I verified nothing, and I found no source saying the model was modified by a named third party. Whether CSAM cases belong on a satirical leaderboard at all is a human editorial decision; I didn't pursue it.

Reopen when a threat report or court filing names a specific modified build (e.g. "<model>-abliterated by <org>") used against a real victim.
