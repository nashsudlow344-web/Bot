#!/usr/bin/env bash
set -euo pipefail

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
mapfile -t URLS < <(build_prefill_urls "$OWNER" "$REPO" "$BASE_BRANCH" "$HEAD_BRANCH")
PR_URL="${URLS[0]}"
ISSUE_URL="${URLS[1]}"

echo
echo "=== PRE-FILLED PR URL (no push) ==="
echo "$PR_URL"
echo
echo "=== PRE-FILLED ISSUE URL (typing backlog) ==="
echo "$ISSUE_URL"
echo
echo "Note: This script does NOT push the current branch. Push manually before opening the PR page if required."
