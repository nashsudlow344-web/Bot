from __future__ import annotations

import time
from collections import deque
from typing import Dict, Optional

from services.codex_orchestrator.validate_and_publish import (
    validate_and_publish_display,
)
from services.event_store.simple_bus import publish

INDICATORS_TOPIC = "indicators.bar.v1"
SIGNAL_TOPIC = "signal.display.v1"
EMA_SHORT = 9
EMA_LONG = 21
ATR_PERIOD = 14


def _ema(alpha: float, prev: float, value: float) -> float:
    return alpha * value + (1 - alpha) * prev


class IndicatorState:
    def __init__(
        self, short: int = EMA_SHORT, long: int = EMA_LONG, atr_period: int = ATR_PERIOD
    ):
        self.short = short
        self.long = long
        self.atr_period = atr_period
        self.prices: deque[float] = deque(maxlen=max(self.long, self.atr_period) + 10)
        self.ema_short: Optional[float] = None
        self.ema_long: Optional[float] = None
        self.prev_ema_short: Optional[float] = None
        self.prev_ema_long: Optional[float] = None
        self.trs: deque[float] = deque(maxlen=self.atr_period)
        self.atr: Optional[float] = None
        self.last_close: Optional[float] = None

    def update_from_bar(self, bar: Dict[str, int]) -> Dict[str, Optional[float]]:
        close = float(bar["close"])
        high = float(bar["high"])
        low = float(bar["low"])

        if self.last_close is None:
            self.last_close = close

        self.prices.append(close)

        self.prev_ema_short = self.ema_short
        self.prev_ema_long = self.ema_long

        if self.ema_short is None and len(self.prices) >= self.short:
            self.ema_short = sum(list(self.prices)[-self.short :]) / self.short
        elif self.ema_short is not None:
            alpha_short = 2 / (self.short + 1)
            self.ema_short = _ema(alpha_short, self.ema_short, close)

        if self.ema_long is None and len(self.prices) >= self.long:
            self.ema_long = sum(list(self.prices)[-self.long :]) / self.long
        elif self.ema_long is not None:
            alpha_long = 2 / (self.long + 1)
            self.ema_long = _ema(alpha_long, self.ema_long, close)

        tr = max(high - low, abs(high - self.last_close), abs(low - self.last_close))
        self.trs.append(tr)
        if self.atr is None and len(self.trs) >= self.atr_period:
            self.atr = sum(self.trs) / len(self.trs)
        elif self.atr is not None:
            self.atr = (self.atr * (self.atr_period - 1) + tr) / self.atr_period

        self.last_close = close
        return {"ema_short": self.ema_short, "ema_long": self.ema_long, "atr": self.atr}


class IndicatorEngine:
    def __init__(self, stop_atr_multiplier: float = 1.5):
        self._states: Dict[str, IndicatorState] = {}
        self.stop_atr_multiplier = stop_atr_multiplier

    def handle_bar(self, bar: Dict[str, int]) -> None:
        symbol = str(bar["symbol"])
        state = self._states.setdefault(symbol, IndicatorState())
        indicators = state.update_from_bar(bar)

        publish(
            INDICATORS_TOPIC,
            {
                "symbol": symbol,
                "timeframe_start_ms": bar["timeframe_start_ms"],
                "indicators": indicators,
                "bar": bar,
                "emitted_ts_ms": int(time.time() * 1000),
            },
        )

        e_short = indicators.get("ema_short")
        e_long = indicators.get("ema_long")
        atr = indicators.get("atr")
        if e_short is None or e_long is None or atr is None:
            return

        crossed_up = (
            state.prev_ema_short is not None
            and state.prev_ema_long is not None
            and (state.prev_ema_short - state.prev_ema_long) <= 1e-9
            and (e_short - e_long) > 1e-9
        )
        if not crossed_up or atr <= 0:
            return

        entry_price_ticks = int(bar["close"])
        stop_offset = int(self.stop_atr_multiplier * atr)
        stop_price_ticks = max(1, entry_price_ticks - stop_offset)

        # Normalize crossover magnitude in volatility units for more stable confidence.
        magnitude = (e_short - e_long) / max(1e-6, atr)
        confidence_pct = int(min(95, max(30, 50 + magnitude * 10)))

        signal = {
            "id": f"signal-{symbol}-{bar['timeframe_start_ms']}",
            "symbol": symbol,
            "side": "LONG",
            "generated_ts_ms": int(time.time() * 1000),
            "entry_price_ticks": entry_price_ticks,
            "stop_price_ticks": stop_price_ticks,
            "target_price_ticks": [
                entry_price_ticks + int(1.5 * (entry_price_ticks - stop_price_ticks))
            ],
            "confidence_pct": confidence_pct,
            "explanation_short": "ema_short crossover above ema_long with ATR stop",
            "signal_type": "SCALP",
            "model_version": "ind_engine_v1",
            "source": "indicators_engine",
            "ttl_ms": 300000,
            "debug": {
                "ema_short": round(e_short, 6),
                "ema_long": round(e_long, 6),
                "atr": round(atr, 6),
                "magnitude_atr": round(magnitude, 6),
            },
        }

        result = validate_and_publish_display(signal)
        if result.get("status") != "OK":
            publish(SIGNAL_TOPIC, signal)
