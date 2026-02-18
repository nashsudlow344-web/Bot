import hashlib
import time

from services.event_store.simple_bus import publish, read_all


def _stable_signal_id(
    symbol: str, signal_type: str, anchor_ts: int, entry: int, stop: int
) -> str:
    payload = f"{symbol}|{signal_type}|{anchor_ts}|{entry}|{stop}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def swing_rule_minimal(
    symbol: str,
    bars_topic: str = "ohlcv.bar.v1",
    articles_topic: str = "article.analysis.v1",
    output_topic: str = "signal.display.v1",
) -> None:
    bars = [b for b in read_all(bars_topic) if b.get("symbol") == symbol]
    if not bars:
        return
    window = bars[-20:] if len(bars) >= 20 else bars
    swing_high = (
        max(int(b["high_ticks"]) for b in window[:-1])
        if len(window) > 1
        else int(window[-1]["high_ticks"])
    )
    swing_low = min(int(b["low_ticks"]) for b in window)
    last = window[-1]
    last_close = int(last["close_ticks"])
    if last_close > swing_high:
        now_ms = int(last.get("end_ts_ms", int(time.time() * 1000)))
        recent_analysis = [
            a
            for a in read_all(articles_topic)
            if a.get("analysis_ts_ms") and now_ms - int(a["analysis_ts_ms"]) < 3600000
        ]
        if any(float(a.get("sentiment_score", 0)) < -0.5 for a in recent_analysis):
            return
        entry = last_close
        stop = swing_low
        target = entry + (entry - stop) * 2
        signal = {
            "id": _stable_signal_id(symbol, "SWING", now_ms, entry, stop),
            "symbol": symbol,
            "side": "LONG",
            "generated_ts_ms": now_ms,
            "entry_price_ticks": entry,
            "stop_price_ticks": stop,
            "target_price_ticks": [target],
            "rr": 2.0,
            "confidence_pct": 66,
            "explanation_short": "swing breakout above structure",
            "explanation_long": "swing_engine minimal structure rule fired",
            "model_version": "swing_v1",
            "signal_type": "SWING",
            "source": "swing_engine",
            "ttl_ms": 86400000,
            "debug": {"swing_high": swing_high, "swing_low": swing_low},
        }
        publish(output_topic, signal)
