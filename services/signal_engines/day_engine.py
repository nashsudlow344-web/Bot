import hashlib

from services.event_store.simple_bus import publish, read_all


def _stable_signal_id(
    symbol: str, signal_type: str, anchor_ts: int, entry: int, stop: int
) -> str:
    payload = f"{symbol}|{signal_type}|{anchor_ts}|{entry}|{stop}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def day_rule_minimal(
    symbol: str,
    tick_decimals: int = 2,
    features_topic: str = "feature.snapshot.v1",
    bars_topic: str = "ohlcv.bar.v1",
    output_topic: str = "signal.display.v1",
) -> None:
    _ = tick_decimals, features_topic
    recent_bars = [bar for bar in read_all(bars_topic) if bar.get("symbol") == symbol]
    if len(recent_bars) < 2:
        return
    prev = recent_bars[-2]
    cur = recent_bars[-1]
    prev_high = int(prev["high_ticks"])
    cur_close = int(cur["close_ticks"])
    if (
        cur_close > prev_high
        and int(cur.get("volume", 0)) > int(prev.get("volume", 0)) * 1.2
    ):
        entry = cur_close
        stop = int(prev["low_ticks"])
        target = entry + (entry - stop) * 2
        anchor_ts = int(cur["end_ts_ms"])
        signal = {
            "id": _stable_signal_id(symbol, "DAY", anchor_ts, entry, stop),
            "symbol": symbol,
            "side": "LONG",
            "generated_ts_ms": anchor_ts,
            "entry_price_ticks": int(entry),
            "stop_price_ticks": int(stop),
            "target_price_ticks": [int(target)],
            "rr": 2.0,
            "confidence_pct": 62,
            "explanation_short": "day breakout with volume expansion",
            "explanation_long": "day_engine minimal breakout rule fired",
            "model_version": "day_v1",
            "signal_type": "DAY",
            "source": "day_engine",
            "ttl_ms": 3600000,
            "debug": {"prev_high": prev_high},
        }
        publish(output_topic, signal)
