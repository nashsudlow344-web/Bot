import shutil
import time

from services.event_store.simple_bus import BUS_DIR, read_all
from services.ohlcv.aggregator import DeterministicAggregator


def clear_bus() -> None:
    if BUS_DIR.exists():
        shutil.rmtree(BUS_DIR)
    BUS_DIR.mkdir(parents=True, exist_ok=True)


def test_high_throughput_pruning_and_stability() -> None:
    """Force dedupe pruning and verify bounded memory behavior under load."""
    clear_bus()
    agg = DeterministicAggregator(
        timeframe_ms=1000,
        allowed_lateness_ms=0,
        dedupe_limit=500,
        prune_batch=50,
    )
    base = int(time.time() * 1000)

    for i in range(1200):
        ts_ms = base + (i % 10)
        agg.handle_tick(
            "STRESS",
            {
                "ts_ms": ts_ms,
                "price_ticks": 1000 + (i % 100),
                "size": 1,
                "trade_id": f"t-{i}",
            },
            now_ms=base + 5000 + i,
        )

    dedupe_map = agg._dedupe.get("STRESS")
    assert dedupe_map is not None
    assert len(dedupe_map) <= 500

    agg.flush()
    bars = [b for b in read_all("ohlcv.bar.v1") if b["symbol"] == "STRESS"]
    assert isinstance(bars, list)
