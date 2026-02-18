## Reviewer / QA checklist

Please verify the following for this PR:

- [ ] CI checks green: tests, lint, scoped mypy run (`--follow-imports=skip`).
- [ ] OHLC aggregator determinism: bounded dedupe pruning under high throughput (`tests/test_ohlcv_stress.py`).
- [ ] Indicator stability: no spurious signals on flat/near-constant series (`tests/test_indicators_engine.py`).
- [ ] `AggregatorConfig` env knobs present and documented (`services/ohlcv/config.py` + README update).
- [ ] `read_all()` generator fix remains generator-safe in `services/event_store/simple_bus.py`.
- [ ] CI mypy scope change is linked to typing backlog (`docs/ISSUE_typing_backlog.md`).
- [ ] PR/issue helpers function in constrained environments (`scripts/open_pr.sh`, `scripts/open_pr_without_gh.sh`, `scripts/print_pr_urls.sh`, `scripts/create_and_link_typing_issue.sh`).
- [ ] Release note draft reviewed (`docs/release_note.md`).

### Suggested spot checks

```bash
pytest -q
ruff check .
black --check .
isort --check-only .
mypy --follow-imports=skip services/event_store/simple_bus.py services/ohlcv services/indicators
```
