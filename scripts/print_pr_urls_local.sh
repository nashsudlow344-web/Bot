#!/usr/bin/env bash
set -euo pipefail

OWNER="${1:?owner required}"
REPO="${2:?repo required}"
BASE_BRANCH="${3:-main}"
HEAD_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/github_prefill_urls.sh
source "$SCRIPT_DIR/lib/github_prefill_urls.sh"

require_repo_root
require_docs_templates

mapfile -t URLS < <(build_prefill_urls "$OWNER" "$REPO" "$BASE_BRANCH" "$HEAD_BRANCH")
PR_URL="${URLS[0]}"
ISSUE_URL="${URLS[1]}"

echo
echo "=== PRE-FILLED PR URL (no push, no origin required) ==="
echo "$PR_URL"
echo
echo "=== PRE-FILLED ISSUE URL (typing backlog) ==="
echo "$ISSUE_URL"
echo

echo "Note: this script does NOT push and does NOT read git remotes; supply owner/repo explicitly."
