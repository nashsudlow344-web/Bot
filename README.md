# Trading Assistant MVP scaffold

## Local run
1. Create virtualenv and install dependencies (`pytest`, `pydantic`).
2. Run tests: `pytest -q`
3. Optional flow: `python -m services.ingest.ingest tests/fixtures/ticks.csv`

## Deterministic scaffold components
- deterministic event bus: `tmp_event_bus/*.ndjson`
- deterministic feature worker & signal engines
- deterministic fusion trace and candidate output
- codex stub and audit logging
- strict Codex task contract schemas in `schemas/`
- runtime payload validation in `services/schemas/models.py` and `services/codex_orchestrator/validate_and_publish.py`
- prompt contract templates for Codex outputs: `docs/codex_prompts.md`

See `tests/test_determinism.py` for replay determinism, `tests/test_codex_validation.py` for schema/runtime validation checks, and `tests/test_codex_integration.py` for raw-JSON parse → validate → publish integration flow.

## Acceptance artifacts
- Initial scaffold commit hash: `docs/initial_commit_hash.txt`
- Repository tree snapshot (depth 2): `docs/repo_tree.txt`
- Branch protection evidence template: `docs/branch_protection_status.md`
- CI workflow: `.github/workflows/ci.yml`

## Developer tooling
Install locked dependencies and run local quality checks:

```bash
python -m venv .venv
. .venv/bin/activate
pip install --require-hashes -r requirements-dev.lock
ruff check .
black --check .
isort --check-only .
mypy .
```


## Dependency locking
- Runtime lock file: `requirements.lock`
- Dev/tooling lock file: `requirements-dev.lock`
- Regenerate locks after editing `requirements.txt` or `requirements-dev.txt`:

```bash
pip install pip-tools
pip-compile --generate-hashes --output-file=requirements.lock requirements.txt
pip-compile --generate-hashes --output-file=requirements-dev.lock requirements-dev.txt
```

## OHLC + Indicators
- `services/ohlcv/aggregator.py`: deterministic OHLC aggregator (watermarking, dedupe, correction and metrics topics).
- `services/indicators/engine.py`: EMA/ATR indicator builder and simple EMA-crossover scalp signal rule.

Run the new tests:
```bash
pytest tests/test_ohlcv_aggregator.py tests/test_indicators_engine.py -q
```

Topics emitted:
- `ohlcv.bar.v1`, `ohlcv.correction.v1`, `metrics.ohlcv.v1`, `indicators.bar.v1`, `signal.display.v1`

Runtime knobs:
- Aggregator config: `timeframe_ms`, `allowed_lateness_ms`, `dedupe_limit`, `prune_batch`.
- Environment wrapper: `services/ohlcv/config.py` (`AggregatorConfig`) for env-based runtime tuning.
- Aggregator is designed for a single-threaded actor-style worker; add locking if sharing instance across threads.


Additional stress test:
- `tests/test_ohlcv_stress.py` validates bounded dedupe pruning under high-throughput input.

### PR helper
Use the helper script to push the current branch and open a draft PR from `docs/pr_body.md`:

```bash
./scripts/open_pr.sh main
```

### Issue linking helper
Create the typing-backlog issue and append its URL to the current PR body:

```bash
./scripts/create_and_link_typing_issue.sh
```

### PR helper (no gh CLI)
If `gh` is unavailable, use the fallback script to push the current branch and print/open pre-filled GitHub web URLs for PR + typing-backlog issue creation:

```bash
./scripts/open_pr_without_gh.sh main
```

### URL-only PR helper (no push, no gh)
If you only want pre-filled web URLs (without pushing or using `gh`), run:

```bash
./scripts/print_pr_urls.sh main
```

### URL-only PR helper (explicit owner/repo, no origin required)
If your clone has no `origin` remote, generate pre-filled PR/issue URLs by passing owner/repo directly:

```bash
./scripts/print_pr_urls_local.sh <owner> <repo> main
```

