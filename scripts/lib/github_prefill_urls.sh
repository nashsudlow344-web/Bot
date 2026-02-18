#!/usr/bin/env bash
# Shared helpers for pre-filled GitHub PR/issue URL generation.

set -euo pipefail

require_repo_root() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "error: not a git repository" >&2
    exit 1
  fi
}

require_docs_templates() {
  if [[ ! -f docs/pr_body.md ]]; then
    echo "error: docs/pr_body.md not found" >&2
    exit 1
  fi

  if [[ ! -f docs/ISSUE_typing_backlog.md ]]; then
    echo "error: docs/ISSUE_typing_backlog.md not found" >&2
    exit 1
  fi
}

urlencode_file() {
  python - "$1" <<'PY'
import sys
import urllib.parse

text = open(sys.argv[1], "r", encoding="utf-8").read()
print(urllib.parse.quote(text))
PY
}

urlencode_text() {
  python - "$1" <<'PY'
import sys
import urllib.parse

print(urllib.parse.quote(sys.argv[1]))
PY
}

parse_github_remote() {
  local remote_url="$1"

  if [[ "$remote_url" =~ ^git@github.com:([^/]+)/([^/]+)(\.git)?$ ]]; then
    printf '%s\n%s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]%\.git}"
    return 0
  fi

  if [[ "$remote_url" =~ ^https?://[^/]+/([^/]+)/([^/]+)(\.git)?$ ]]; then
    printf '%s\n%s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]%\.git}"
    return 0
  fi

  return 1
}

build_prefill_urls() {
  local owner="$1"
  local repo="$2"
  local base_branch="$3"
  local head_branch="$4"

  local pr_title="Harden OHLC dedupe & indicator stability; add env config + stress test; scope CI mypy"
  local issue_title="Typing backlog: pydantic & schema cleanup for full-repo mypy"

  local enc_pr_title
  local enc_pr_body
  local enc_issue_title
  local enc_issue_body

  enc_pr_title="$(urlencode_text "$pr_title")"
  enc_pr_body="$(urlencode_file docs/pr_body.md)"
  enc_issue_title="$(urlencode_text "$issue_title")"
  enc_issue_body="$(urlencode_file docs/ISSUE_typing_backlog.md)"

  local pr_url="https://github.com/${owner}/${repo}/compare/${base_branch}...${head_branch}?expand=1&title=${enc_pr_title}&body=${enc_pr_body}"
  local issue_url="https://github.com/${owner}/${repo}/issues/new?title=${enc_issue_title}&body=${enc_issue_body}"

  printf '%s\n%s\n' "$pr_url" "$issue_url"
}
