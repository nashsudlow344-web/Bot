### Summary
This PR hardens the OHLC aggregator and indicators engine, adds runtime environment config for the aggregator, expands test coverage (including stress testing), and scopes CI type-checking to the modules hardened in this change.

Key changes:
- `services/ohlcv/aggregator.py`
  - `OrderedDict`-based dedupe with configurable `dedupe_limit` / `prune_batch`.
  - Injectable `time_source` / `_now_ms()` for deterministic testing.
  - Late-tick correction and metrics/audit emit flow retained.
- `services/indicators/engine.py`
  - Stabilized crossover behavior (epsilon checks + ATR gating).
  - ATR-normalized confidence.
  - `symbol` normalized to `str` before dict-key usage.
  - Added debug payload fields in emitted signals.
- `services/ohlcv/config.py`
  - New `AggregatorConfig` env wrapper and `as_kwargs()` helper.
- Tests
  - Expanded `tests/test_ohlcv_aggregator.py`.
  - Expanded `tests/test_indicators_engine.py`.
  - Added `tests/test_ohlcv_stress.py`.
- CI
  - Scoped `mypy` to `services/event_store/simple_bus.py`, `services/ohlcv`, `services/indicators` with `--follow-imports=skip`.
- Tooling
  - Generator-safe `read_all()` branch fix in `services/event_store/simple_bus.py`.
  - Formatting/import alignment (`black`/`isort`/`ruff`) and `.isort.cfg` (`profile = black`).

### Rationale
- Bounded dedupe behavior under throughput is required for predictable memory and stable runtime.
- Deterministic time injection improves replay/testing reliability.
- Indicator signal gating prevents degenerate emissions on flat-series/low-information cases.
- Scoped mypy keeps CI actionable while full-repo typing debt is tracked separately.

### Testing
- `pytest -q` (15 passed)
- `ruff check .`
- `black --check .`
- `isort --check-only .`
- `mypy --follow-imports=skip services/event_store/simple_bus.py services/ohlcv services/indicators`

### Post-merge
- Link and track the typing backlog issue (`docs/ISSUE_typing_backlog.md`).
- Expand module-by-module mypy coverage as backlog is reduced.
