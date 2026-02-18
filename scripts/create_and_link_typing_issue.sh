#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI is required" >&2
  exit 1
fi

if [[ ! -f docs/ISSUE_typing_backlog.md ]]; then
  echo "error: docs/ISSUE_typing_backlog.md not found" >&2
  exit 1
fi

ISSUE_URL=$(gh issue create \
  --title "Typing backlog: pydantic & schema cleanup for full-repo mypy" \
  --body-file docs/ISSUE_typing_backlog.md \
  --label "tech-debt" \
  --label "priority:high")

echo "Created issue: ${ISSUE_URL}"

echo "Linking issue to current PR..."
PR_NUMBER=$(gh pr view --json number -q .number)
gh pr edit "${PR_NUMBER}" --add-body "\n\nRelated typing backlog: ${ISSUE_URL}"

echo "Linked issue to PR #${PR_NUMBER}."
