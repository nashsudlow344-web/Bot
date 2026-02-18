#!/usr/bin/env bash
set -euo pipefail

BASE_BRANCH="${1:-main}"
HEAD_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI is required" >&2
  exit 1
fi

if [[ ! -f docs/pr_body.md ]]; then
  echo "error: docs/pr_body.md not found" >&2
  exit 1
fi

echo "Pushing branch: ${HEAD_BRANCH}"
git push origin "${HEAD_BRANCH}"

echo "Creating draft PR against ${BASE_BRANCH}"
gh pr create \
  --title "Harden OHLC dedupe & indicator stability; add env config + stress test; scope CI mypy" \
  --body-file docs/pr_body.md \
  --base "${BASE_BRANCH}" \
  --head "${HEAD_BRANCH}" \
  --label "area:ohlcv" \
  --label "area:indicators" \
  --label "ci" \
  --draft

echo "PR created. Opening in browser..."
gh pr view --web
