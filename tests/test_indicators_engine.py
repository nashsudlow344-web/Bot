import shutil

from services.event_store.simple_bus import BUS_DIR, read_all
from services.indicators.engine import IndicatorEngine


def clear_bus() -> None:
    if BUS_DIR.exists():
        shutil.rmtree(BUS_DIR)
    BUS_DIR.mkdir(parents=True, exist_ok=True)


def test_indicator_builds_and_emits_indicator_events() -> None:
    clear_bus()
    engine = IndicatorEngine(stop_atr_multiplier=1.0)
    base = 1_700_000_000_000

    for i in range(40):
        close = 1000 + i * 2
        bar = {
            "symbol": "AAA",
            "timeframe_start_ms": base + i * 60_000,
            "open": close - 1,
            "high": close + 2,
            "low": close - 2,
            "close": close,
            "volume": 100 + i,
            "trade_count": 5 + i,
        }
        engine.handle_bar(bar)

    indicators = list(read_all("indicators.bar.v1"))
    assert len(indicators) >= 1

    signals = list(read_all("signal.display.v1"))
    assert isinstance(signals, list)


def test_indicator_flat_series_does_not_crash_or_emit_invalid_signal() -> None:
    clear_bus()
    engine = IndicatorEngine(stop_atr_multiplier=1.0)
    base = 1_700_000_000_000

    for i in range(45):
        bar = {
            "symbol": "FLAT",
            "timeframe_start_ms": base + i * 60_000,
            "open": 1000,
            "high": 1000,
            "low": 1000,
            "close": 1000,
            "volume": 100,
            "trade_count": 10,
        }
        engine.handle_bar(bar)

    signals = [s for s in read_all("signal.display.v1") if s["symbol"] == "FLAT"]
    # Flat series should not create crossover signals.
    assert signals == []


def test_indicator_signal_confidence_bounds() -> None:
    clear_bus()
    engine = IndicatorEngine(stop_atr_multiplier=1.0)
    base = 1_700_000_000_000

    for i in range(60):
        close = 1000 + i * 4
        bar = {
            "symbol": "BOUNDS",
            "timeframe_start_ms": base + i * 60_000,
            "open": close - 1,
            "high": close + 3,
            "low": close - 3,
            "close": close,
            "volume": 100 + i,
            "trade_count": 10 + i,
        }
        engine.handle_bar(bar)

    signals = [s for s in read_all("signal.display.v1") if s["symbol"] == "BOUNDS"]
    for signal in signals:
        assert 30 <= int(signal["confidence_pct"]) <= 95
