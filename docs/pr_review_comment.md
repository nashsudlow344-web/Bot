## Reviewer / QA checklist

Please verify the following on this PR:

- [ ] CI checks are green (tests, lint, scoped mypy).
- [ ] OHLC aggregator behavior is still deterministic with bounded dedupe pruning.
- [ ] Indicator signal emission remains stable (no flat-series false positives).
- [ ] CI `mypy` scope change is acceptable for this phase and linked to typing backlog issue.
- [ ] Docs updates (`docs/pr_body.md`, backlog issue template, helper scripts) are clear and usable.

### Suggested spot checks

```bash
pytest -q
ruff check .
black --check .
isort --check-only .
mypy --follow-imports=skip services/event_store/simple_bus.py services/ohlcv services/indicators
```
