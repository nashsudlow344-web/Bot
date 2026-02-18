from __future__ import annotations

import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple

from services.event_store.simple_bus import publish

AUDIT_TOPIC = "audit.records.v1"
OHLCV_TOPIC = "ohlcv.bar.v1"
OHLCV_CORRECTION_TOPIC = "ohlcv.correction.v1"
METRICS_TOPIC = "metrics.ohlcv.v1"


@dataclass
class Tick:
    ts_ms: int
    price_ticks: int
    size: int = 1
    trade_id: Optional[str] = None
    seq: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Bar:
    symbol: str
    timeframe_ms: int
    timeframe_start_ms: int
    open: int
    high: int
    low: int
    close: int
    volume: int
    trade_count: int
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe_ms": self.timeframe_ms,
            "timeframe_start_ms": self.timeframe_start_ms,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "trade_count": self.trade_count,
            "version": self.version,
        }


class DeterministicAggregator:
    """Deterministic OHLCV aggregator with dedupe, watermarking, and correction support.

    Notes:
      - This class is designed for a single-threaded worker loop.
      - `time_source` can be injected in tests for deterministic emitted timestamps.
    """

    def __init__(
        self,
        timeframe_ms: int = 60_000,
        allowed_lateness_ms: int = 1_000,
        dedupe_limit: int = 10_000,
        prune_batch: int = 1_000,
        time_source: Optional[Callable[[], int]] = None,
    ):
        self.timeframe_ms = timeframe_ms
        self.allowed_lateness_ms = allowed_lateness_ms
        self.dedupe_limit = dedupe_limit
        self.prune_batch = prune_batch
        self._time_source = time_source or (lambda: int(time.time() * 1000))
        self._bars: Dict[Tuple[str, int], Bar] = {}
        self._published: Dict[Tuple[str, int], Bar] = {}
        self._dedupe: Dict[str, OrderedDict[str, int]] = {}
        self._counters: Dict[str, int] = {
            "bars_published": 0,
            "corrections": 0,
            "duplicates": 0,
        }

    def _now_ms(self) -> int:
        return self._time_source()

    def _floor_start(self, ts_ms: int) -> int:
        return (ts_ms // self.timeframe_ms) * self.timeframe_ms

    def _audit(self, event_type: str, payload: Dict[str, Any]) -> None:
        now_ms = self._now_ms()
        publish(
            AUDIT_TOPIC,
            {
                "id": f"audit-{event_type}-{now_ms}",
                "event_type": event_type,
                "ts_ms": now_ms,
                "payload_json": json.dumps(payload, sort_keys=True),
            },
        )

    def _is_duplicate(self, symbol: str, tick: Tick) -> bool:
        if not tick.trade_id and tick.seq is None:
            return False

        dedupe_key = (
            tick.trade_id
            if tick.trade_id
            else f"{tick.seq}:{tick.ts_ms}:{tick.price_ticks}:{tick.size}"
        )
        symbol_seen = self._dedupe.setdefault(symbol, OrderedDict())

        if dedupe_key in symbol_seen:
            self._counters["duplicates"] += 1
            return True

        symbol_seen[dedupe_key] = self._now_ms()
        if len(symbol_seen) > self.dedupe_limit:
            to_prune = min(self.prune_batch, len(symbol_seen))
            for _ in range(to_prune):
                symbol_seen.popitem(last=False)
        return False

    def _publish_bar(self, bar: Bar, replaced: bool = False) -> None:
        payload = bar.to_dict()
        payload["replaced"] = replaced
        payload["emitted_ts_ms"] = self._now_ms()
        publish(OHLCV_CORRECTION_TOPIC if replaced else OHLCV_TOPIC, payload)
        self._audit(
            "ohlcv_bar_corrected" if replaced else "ohlcv_bar_published", payload
        )
        if replaced:
            self._counters["corrections"] += 1
        else:
            self._counters["bars_published"] += 1

    def _emit_metrics(self, symbol: str, bar: Bar) -> None:
        payload = {
            "symbol": symbol,
            "timeframe_start_ms": bar.timeframe_start_ms,
            "timeframe_ms": bar.timeframe_ms,
            "trade_count": bar.trade_count,
            "volume": bar.volume,
            "emitted_ts_ms": self._now_ms(),
            "counters": dict(self._counters),
        }
        publish(METRICS_TOPIC, payload)
        self._audit("ohlcv_metrics", payload)

    def _recompute_bar_from_new_tick(
        self, published_bar: Bar, tick: Tick
    ) -> Optional[Bar]:
        new_bar = Bar(**published_bar.to_dict())
        changed = False

        if tick.price_ticks > new_bar.high:
            new_bar.high = tick.price_ticks
            changed = True
        if tick.price_ticks < new_bar.low:
            new_bar.low = tick.price_ticks
            changed = True

        new_bar.volume += tick.size
        new_bar.trade_count += 1
        if (
            new_bar.volume != published_bar.volume
            or new_bar.trade_count != published_bar.trade_count
        ):
            changed = True

        if not changed:
            return None

        new_bar.version = published_bar.version + 1
        return new_bar

    def _finalize_expired(self, now_ms: int) -> None:
        expirables = []
        for key, bar in self._bars.items():
            bar_end_ms = bar.timeframe_start_ms + bar.timeframe_ms
            if now_ms >= bar_end_ms + self.allowed_lateness_ms:
                expirables.append((key, bar))

        for key, bar in sorted(expirables, key=lambda x: x[0][1]):
            self._publish_bar(bar, replaced=False)
            self._published[key] = bar
            self._bars.pop(key, None)
            self._emit_metrics(bar.symbol, bar)

    def handle_tick(
        self, symbol: str, tick_payload: Dict[str, Any], now_ms: Optional[int] = None
    ) -> None:
        tick = Tick(
            ts_ms=int(tick_payload["ts_ms"]),
            price_ticks=int(tick_payload["price_ticks"]),
            size=int(tick_payload.get("size", 1)),
            trade_id=tick_payload.get("trade_id"),
            seq=tick_payload.get("seq"),
            raw=tick_payload,
        )

        if self._is_duplicate(symbol, tick):
            self._audit("tick_duplicate", tick_payload)
            return

        timeframe_start = self._floor_start(tick.ts_ms)
        key = (symbol, timeframe_start)

        if key in self._published:
            replacement = self._recompute_bar_from_new_tick(self._published[key], tick)
            if replacement is not None:
                self._published[key] = replacement
                self._publish_bar(replacement, replaced=True)
            return

        bar = self._bars.get(key)
        if bar is None:
            bar = Bar(
                symbol=symbol,
                timeframe_ms=self.timeframe_ms,
                timeframe_start_ms=timeframe_start,
                open=tick.price_ticks,
                high=tick.price_ticks,
                low=tick.price_ticks,
                close=tick.price_ticks,
                volume=tick.size,
                trade_count=1,
            )
            self._bars[key] = bar
        else:
            bar.high = max(bar.high, tick.price_ticks)
            bar.low = min(bar.low, tick.price_ticks)
            bar.close = tick.price_ticks
            bar.volume += tick.size
            bar.trade_count += 1

        self._finalize_expired(now_ms if now_ms is not None else self._now_ms())

    def flush(self) -> None:
        for key, bar in sorted(self._bars.items(), key=lambda x: x[0][1]):
            self._publish_bar(bar, replaced=False)
            self._published[key] = bar
            self._emit_metrics(bar.symbol, bar)
        self._bars.clear()
