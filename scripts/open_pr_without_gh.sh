#!/usr/bin/env bash
set -euo pipefail

# Fallback PR + Issue helper (no gh required)
# Usage: ./scripts/open_pr_without_gh.sh [base-branch]
# Example: ./scripts/open_pr_without_gh.sh main

BASE_BRANCH="${1:-main}"
HEAD_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/github_prefill_urls.sh
source "$SCRIPT_DIR/lib/github_prefill_urls.sh"

require_repo_root
require_docs_templates

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "error: no 'origin' remote found" >&2
  exit 1
fi

REMOTE_URL="$(git remote get-url origin)"
if ! mapfile -t REMOTE_PARTS < <(parse_github_remote "$REMOTE_URL"); then
  echo "error: unrecognized origin URL format: $REMOTE_URL" >&2
  exit 1
fi

OWNER="${REMOTE_PARTS[0]}"
REPO="${REMOTE_PARTS[1]}"

echo "Pushing branch ${HEAD_BRANCH} -> origin/${HEAD_BRANCH}"
git push origin "$HEAD_BRANCH"

mapfile -t URLS < <(build_prefill_urls "$OWNER" "$REPO" "$BASE_BRANCH" "$HEAD_BRANCH")
PR_URL="${URLS[0]}"
ISSUE_URL="${URLS[1]}"

echo
echo "=== PRE-FILLED PR URL ==="
echo "$PR_URL"
echo
echo "=== PRE-FILLED ISSUE URL (typing backlog) ==="
echo "$ISSUE_URL"
echo

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$PR_URL" >/dev/null 2>&1 || true
  xdg-open "$ISSUE_URL" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then
  open "$PR_URL" || true
  open "$ISSUE_URL" || true
else
  echo "Note: no xdg-open/open available — copy the URLs above into a browser to proceed."
fi

echo "Done. Complete draft/reviewers/labels in the GitHub web UI."
