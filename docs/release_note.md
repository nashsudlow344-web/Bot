## Release note (draft)

- Hardened OHLC aggregation with bounded dedupe/pruning and deterministic timestamp injection support.
- Improved indicator signal stability via ATR gating and crossover normalization.
- Added stress and edge-case test coverage for OHLC/indicator flows.
- Added PR/issue helper docs and a script-driven PR opening flow.
- Updated CI to run scoped `mypy` on hardened modules while full-repo typing cleanup is tracked in backlog.
