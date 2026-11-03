# Reviewing FelonyBench

Rules in `agent/RUNBOOK.md` bind the automated agent, not people. An incident or note edited by a
person in `docs/agent-notes/`, or a change outside `incidents/` and `.agent-out/`, isn't an agent
path violation, so don't flag it as one.

Incidents sort by `(date, id)`. `scripts/validate.py` is where data rules are enforced, and a rule
that lives only in prose isn't enforced: flag those.
