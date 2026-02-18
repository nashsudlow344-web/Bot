from __future__ import annotations

import os
from typing import Any, Dict, Optional


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class AggregatorConfig:
    """Environment-driven runtime knobs for DeterministicAggregator."""

    timeframe_ms: int
    allowed_lateness_ms: int
    dedupe_limit: int
    prune_batch: int

    def __init__(self, prefix: Optional[str] = None):
        p = (prefix + "_") if prefix else ""
        self.timeframe_ms = _int_env(p + "OHLC_TIMEFRAME_MS", 60_000)
        self.allowed_lateness_ms = _int_env(p + "OHLC_ALLOWED_LATENESS_MS", 1_000)
        self.dedupe_limit = _int_env(p + "OHLC_DEDUPE_LIMIT", 10_000)
        self.prune_batch = _int_env(p + "OHLC_PRUNE_BATCH", 1_000)

    def as_kwargs(self) -> Dict[str, Any]:
        return {
            "timeframe_ms": self.timeframe_ms,
            "allowed_lateness_ms": self.allowed_lateness_ms,
            "dedupe_limit": self.dedupe_limit,
            "prune_batch": self.prune_batch,
        }
