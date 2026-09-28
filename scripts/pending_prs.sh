#!/usr/bin/env bash
# Snapshot incidents from open agent PRs so the agent can dedupe against them.
set -euo pipefail
mkdir -p .agent-out/open
gh pr list --label agent --state open --json headRefName --jq '.[].headRefName' |
while read -r branch; do
  id="${branch#agent/}"
  if git fetch -q origin "$branch"; then
    git show "FETCH_HEAD:incidents/$id.yaml" > ".agent-out/open/$id.yaml" 2>/dev/null || rm -f ".agent-out/open/$id.yaml"
  fi
done
ls .agent-out/open
