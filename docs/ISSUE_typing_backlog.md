## Typing backlog: pydantic and schema cleanup for full-repo mypy

This issue tracks work required to make `mypy .` a full-repo gating check.

### Tasks
- Resolve `pydantic` typing/import issues (install/type config or scoped ignore strategy).
- Refactor duplicate/conditional model definitions in `services/schemas/models.py`.
- Replace problematic annotations and legacy constrained-type usage where needed.
- Incrementally expand CI mypy scope by module group:
  1. `services/event_store`
  2. `services/ohlcv`
  3. `services/indicators`
  4. `services/codex_orchestrator`
  5. remaining services/tests
- Add a non-blocking full-repo mypy run (nightly or separate workflow) to measure progress.

### Suggested acceptance criteria
- `mypy .` passes in CI with no ad-hoc ignores for new code.
- CI mypy scope widened back to full repo.
