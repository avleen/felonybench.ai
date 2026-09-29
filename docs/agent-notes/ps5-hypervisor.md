# PS5 hypervisor bug reported to Sony (Sept 2026): rejected

**Decision:** not an incident. Added to `agent/known-leads.yaml` as `rejected`, for human review.

## What happened (per sources read)
On September 15, 2026, a PS5 hacker known as Jordy (@couldbeautism) reported a PS5 hypervisor bug to Sony's PlayStation bug bounty on HackerOne. Jordy says he found it independently with his "trusty AI clanker machine". Andy "TheFlow" Nguyen, who had found the same bug earlier and was holding it for the PS5 Linux project until after GTA 6's release, had asked him to wait; Jordy says he agreed, but reported it after "someone found the bug with ai a few hours later". Nguyen then quit PS5 hacking and PS5 Linux ("Slop kiddies found the only hypervisor bug left… and decided to report to Sony"). Sony shipped a firmware update that week.

## Why it's rejected
1. **No named AI model or lab.** None of the sources I read names the tool: Kotaku, GamingOnLinux, Slashdot, VideoCardz and It's FOSS all say only "AI", "LLMs" or Jordy's "AI clanker machine". The Accomplice League requires a named model or lab (`org`), so it can't be an incident even if it were contested.
2. **Plainly lawful on the facts reported.** Reporting a vulnerability to the vendor's own bug bounty is the plan's example of a "normal bug-bounty report". The only arguable exposure is 17 USC 1201(a)(1) circumvention while researching on his own console:
   - The current security-research exemption is at **37 CFR 201.40(b)(18)** (the task brief cited (b)(7), an older paragraph number; checked on eCFR, current text). It covers circumvention of "computer programs" on "a lawfully acquired device or machine on which the computer program operates… solely for the purpose of good-faith security research", defined as testing or investigating "a security flaw or vulnerability" in a safe environment, where the information "is used primarily to promote the security or safety of the class of devices… and is not used or maintained in a manner that facilitates copyright infringement."
   - It has **no video-game-console carve-out**. Where the Copyright Office meant to exclude consoles, it said so: (b)(22) (FOSS-licence investigations) is limited to devices "other than a video game console", and (b)(15) limits console "repair" to optical drives. (b)(18) has no such limit.
   - Reporting to Sony is the textbook case of using the information "primarily to promote the security" of the device. If anything, the unreported use (PS5 Linux, or a public jailbreak) is the one that might raise the "facilitates copyright infringement" question, and that wasn't Jordy's act.
   - The criminal provision (17 USC 1204) also requires wilful violation "for purposes of commercial advantage or private financial gain". A bounty is financial gain, but the exemption applies first, and no source suggests Sony objected, threatened action or disputes the report.
   - (b)(18)(iii) notes the exemption isn't a CFAA safe harbour, but research on your own console isn't unauthorized access to someone else's computer.
   - I couldn't read Sony's HackerOne programme page (it renders with JavaScript), so its safe-harbour wording is unverified. It isn't needed for the conclusion.
3. The dispute that exists is ethical and community drama (disclosure timing, GTA 6, PS5 Linux), not a legal dispute. No source reports any legal claim or threat by anyone.

A `contested` entry would need a cited legal dispute, which doesn't exist. If a source later names the AI tool **and** Sony or anyone else claims the research was unlawful, reopen it.

## Sources read
- https://kotaku.com/popular-playstation-hacker-calling-it-quits-due-to-ai-using-slop-kiddies-reporting-important-bug-to-sony-2000735105 (Kotaku): the timeline, Jordy's tweet (Sept 16, 2026) and TheFlow's statement.
- https://www.gamingonlinux.com/2026/09/ps5-linux-dev-quits-after-the-only-hypervisor-bug-left-was-reported-to-sony/ (GamingOnLinux, Sept 17, 2026)
- https://games.slashdot.org/story/26/09/19/222229/developer-abandons-ps5-linux-project-after-sony-patches-ai-discovered-exploit (Slashdot, Sept 19, 2026)
- https://videocardz.com/newz/ps5-linux-developer-drops-project-after-last-hypervisor-bug-is-reported-to-sony and https://itsfoss.com/news/ps5-linux-lead-quits/: fetched and checked for a named AI tool; none found.
- https://www.ecfr.gov/current/title-37/chapter-II/subchapter-A/part-201/section-201.40 (read through the eCFR renderer API): current text of 201.40(b)(15), (b)(18), (b)(19) and (b)(22).
- Cybernews (https://cybernews.com/tech/andy-nguyen-quits-ps5-linux-project/): 403, and the Wayback copy was empty, so not read or cited.
- https://hackerone.com/playstation: JavaScript-only, so not read.
