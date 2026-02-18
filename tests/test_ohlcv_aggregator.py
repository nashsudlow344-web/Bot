import shutil

from services.event_store.simple_bus import BUS_DIR, read_all
from services.ohlcv.aggregator import DeterministicAggregator


def clear_bus() -> None:
    if BUS_DIR.exists():
        shutil.rmtree(BUS_DIR)
    BUS_DIR.mkdir(parents=True, exist_ok=True)


def test_basic_bar_publish_and_metrics() -> None:
    clear_bus()
    agg = DeterministicAggregator(timeframe_ms=1000, allowed_lateness_ms=10)
    base = 1_700_000_000_000

    agg.handle_tick(
        "SYM",
        {"ts_ms": base + 10, "price_ticks": 1000, "size": 1, "trade_id": "t1"},
        now_ms=base + 11,
    )
    agg.handle_tick(
        "SYM",
        {"ts_ms": base + 200, "price_ticks": 1010, "size": 1, "trade_id": "t2"},
        now_ms=base + 201,
    )
    agg.handle_tick(
        "SYM",
        {"ts_ms": base + 800, "price_ticks": 1005, "size": 1, "trade_id": "t3"},
        now_ms=base + 801,
    )
    agg.handle_tick(
        "SYM",
        {"ts_ms": base + 2000, "price_ticks": 1100, "size": 1, "trade_id": "t4"},
        now_ms=base + 3_100,
    )

    records = list(read_all("ohlcv.bar.v1"))
    assert len(records) >= 1
    bar = records[0]
    assert bar["symbol"] == "SYM"
    assert bar["open"] == 1000

    metrics = list(read_all("metrics.ohlcv.v1"))
    assert len(metrics) >= 1


def test_late_tick_causes_correction() -> None:
    clear_bus()
    agg = DeterministicAggregator(timeframe_ms=1000, allowed_lateness_ms=0)
    base = 1_700_000_000_000

    agg.handle_tick(
        "X",
        {"ts_ms": base + 10, "price_ticks": 500, "size": 1, "trade_id": "a"},
        now_ms=base + 11,
    )
    agg.handle_tick(
        "X",
        {"ts_ms": base + 20, "price_ticks": 510, "size": 1, "trade_id": "b"},
        now_ms=base + 21,
    )
    agg.handle_tick(
        "X",
        {"ts_ms": base + 2000, "price_ticks": 400, "size": 1, "trade_id": "c"},
        now_ms=base + 3_000,
    )

    published = list(read_all("ohlcv.bar.v1"))
    assert published

    late = {"ts_ms": base + 50, "price_ticks": 520, "size": 1, "trade_id": "late1"}
    agg.handle_tick("X", late, now_ms=base + 4_000)

    corrections = list(read_all("ohlcv.correction.v1"))
    assert len(corrections) >= 1


def test_duplicates_are_dropped() -> None:
    clear_bus()
    agg = DeterministicAggregator(timeframe_ms=1000, allowed_lateness_ms=0)
    base = 1_700_000_000_000

    first = {"ts_ms": base + 10, "price_ticks": 200, "size": 1, "trade_id": "dup"}
    agg.handle_tick("D", first, now_ms=base + 11)
    agg.handle_tick("D", first, now_ms=base + 12)
    agg.handle_tick(
        "D",
        {"ts_ms": base + 2000, "price_ticks": 300, "size": 1, "trade_id": "after"},
        now_ms=base + 3_000,
    )

    audits = list(read_all("audit.records.v1"))
    assert any(a["event_type"] == "tick_duplicate" for a in audits)


def test_dedupe_pruning_is_bounded() -> None:
    clear_bus()
    agg = DeterministicAggregator(
        timeframe_ms=1000,
        allowed_lateness_ms=0,
        dedupe_limit=100,
        prune_batch=10,
    )
    base = 1_700_000_000_000

    for i in range(130):
        agg.handle_tick(
            "PRUNE",
            {
                "ts_ms": base + i,
                "price_ticks": 1000 + i,
                "size": 1,
                "trade_id": f"id-{i}",
            },
            now_ms=base + i + 2000,
        )

    assert len(agg._dedupe["PRUNE"]) <= 100


def test_flush_orders_bars_by_timeframe_start() -> None:
    clear_bus()
    agg = DeterministicAggregator(timeframe_ms=1000, allowed_lateness_ms=5000)
    base = 1_700_000_000_000

    # Create two bars and flush them; output should be sorted by timeframe_start_ms.
    agg.handle_tick(
        "ORD",
        {"ts_ms": base + 1100, "price_ticks": 101, "size": 1, "trade_id": "a"},
        now_ms=base + 1200,
    )
    agg.handle_tick(
        "ORD",
        {"ts_ms": base + 100, "price_ticks": 100, "size": 1, "trade_id": "b"},
        now_ms=base + 1300,
    )
    agg.flush()

    bars = [b for b in read_all("ohlcv.bar.v1") if b["symbol"] == "ORD"]
    starts = [b["timeframe_start_ms"] for b in bars]
    assert starts == sorted(starts)
