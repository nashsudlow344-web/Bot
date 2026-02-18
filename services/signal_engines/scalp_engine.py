import hashlib

from services.event_store.simple_bus import publish, read_all


def _stable_signal_id(
    symbol: str, signal_type: str, anchor_ts: int, entry: int, stop: int
) -> str:
    payload = f"{symbol}|{signal_type}|{anchor_ts}|{entry}|{stop}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def scalp_rule_minimal(
    symbol: str,
    tick_decimals: int = 2,
    orderbook_topic: str = "orderbook.snap.v1",
    ticks_topic: str = "market.tick.v1",
    output_topic: str = "signal.display.v1",
) -> None:
    _ = tick_decimals
    ticks = [t for t in read_all(ticks_topic) if t.get("symbol") == symbol]
    for ob in read_all(orderbook_topic):
        if ob.get("symbol") != symbol:
            continue
        top = ob.get("levels", [])[0] if ob.get("levels") else None
        if not top:
            continue
        bid = int(top["bid_price_ticks"])
        ask = int(top["ask_price_ticks"])
        spread_ticks = ask - bid
        if spread_ticks <= 1:
            buys, sells = 0, 0
            for t in ticks:
                price = int(t["price_ticks"])
                if price >= ask:
                    buys += 1
                elif price <= bid:
                    sells += 1
            if buys >= max(1, sells * 2):
                anchor_ts = int(ob.get("ts_ms", 0))
                entry = ask
                stop = bid
                target = entry + (spread_ticks * 5)
                signal = {
                    "id": _stable_signal_id(symbol, "SCALP", anchor_ts, entry, stop),
                    "symbol": symbol,
                    "side": "LONG",
                    "generated_ts_ms": anchor_ts,
                    "entry_price_ticks": int(entry),
                    "stop_price_ticks": int(stop),
                    "target_price_ticks": [int(target)],
                    "rr": 1.0,
                    "confidence_pct": 55,
                    "explanation_short": "scalp spread compression + buy prints",
                    "explanation_long": "scalp_engine minimal rule fired",
                    "model_version": "scalp_v1",
                    "signal_type": "SCALP",
                    "source": "scalp_engine",
                    "ttl_ms": 300000,
                    "debug": {"spread_ticks": spread_ticks},
                }
                publish(output_topic, signal)
