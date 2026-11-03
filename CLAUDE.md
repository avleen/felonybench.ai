# Working in this repo

## Before calling a change ready

Run `bash scripts/check.sh` before pushing. It's the same check CI runs: tests, data validation, site build and built-site checks.

Passing that on today's data doesn't show a change is correct. Do all of this before opening a PR or saying it's ready:

1. **Review your own diff as a skeptic.** For each changed function, ask what input would break it, then try that input. Run `/code-review` as well.
2. **Test cases the data doesn't contain.** The incidents exercise very little: only one is a repeat offense, for example, so checking the real site says nothing about that path. Build the case by hand.
3. **Read the whole sort key before relying on an order.** Incidents sort by `(date, id)`, so a later position doesn't mean a later date.
4. **When adding a schema field, list the rules it could break, and enforce them in `scripts/validate.py`.** A rule that lives only in the runbook isn't enforced. Check your tests too: they shouldn't build a record the rules forbid and call it valid.
5. **When a value can play two roles, test both at once.** Sharing one "seen" set between the roles loses information.
6. **Test site helpers directly.** Pure helpers live in `site/src/lib/incidents.ts`, with tests beside them. Test new ones with hand-built incidents, not only by reading the built pages.
7. **Run Cloudflare behavior locally rather than asking the user to check it after merging.** Copy `wrangler.jsonc` and the build to a scratch directory, keeping the build at `<scratch>/site/dist` because the config expects that path, then run `wrangler dev` from there. This keeps `.wrangler/` out of the repo. For URL changes, try each path with and without a trailing slash.

## After opening a PR

Copilot reviews each PR within a few minutes. CI passing doesn't mean the review is finished. Wait for the review and read it with `gh api repos/avleen/felonybench.ai/pulls/<n>/comments` before telling the user a PR is ready to merge.

Copilot doesn't automatically review later pushes, and old comments can move onto the new commit and look new. Check `/pulls/<n>/reviews` to see which commit was actually reviewed.

## Why these rules exist

In PRs #79 and #80, Copilot found four real problems after the PRs had been called ready to merge:

| Problem | How it was missed |
|---|---|
| A same-day hidden report counted as "newer" | Used array position, despite having read the `(date, id)` sort; the real data gave the right answer anyway |
| Slashless old model URLs returned 404 | Left the redirects for the user to check after merging, though `wrangler dev` would have shown it |
| An incident could charge an org that had no model in it | The rule was written in the runbook but not the validator, and a new test asserted such a record was valid |
| A modifier's description was dropped when the org was also a lab | The tests covered scoring but not the display helper, and no incident has this combination |
