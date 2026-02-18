# Branch Protection Status Evidence

Branch protection must be verified against the hosted repository (GitHub/GitLab) and cannot be proven from local git state alone.

## Local check results
- `git remote -v` returned no configured remotes in this environment.
- `gh` CLI is not installed in this environment.

## Required follow-up in hosted repo
Run one of the following in CI or a configured developer machine and save output to this file:

```bash
gh api repos/<owner>/<repo>/branches/main/protection
```

or provide a screenshot of repository settings showing:
- Required pull request reviews
- Status checks required before merge
- Dismiss stale approvals (optional per policy)
- Restrict force pushes/deletions
