import json
import shutil

from services.event_store.simple_bus import BUS_DIR, publish, read_all
from services.feature_worker.feature_worker import run_feature_worker
from services.fusion.fusion_engine import fuse_signals
from services.ingest.ingest import ingest_csv_ticks
from services.signal_engines.day_engine import day_rule_minimal


def clear_bus() -> None:
    if BUS_DIR.exists():
        shutil.rmtree(BUS_DIR)
    BUS_DIR.mkdir(parents=True, exist_ok=True)


def run_once() -> dict:
    clear_bus()
    ingest_csv_ticks("tests/fixtures/ticks.csv")

    prev_bar = {
        "symbol": "CBA.ASX",
        "start_ts_ms": 1699999940000,
        "end_ts_ms": 1700000000000,
        "open_ticks": 113350,
        "high_ticks": 113400,
        "low_ticks": 113340,
        "close_ticks": 113390,
        "volume": 100,
        "vwap_ticks": 113380,
        "source": "csv_agg",
    }
    cur_bar = {
        "symbol": "CBA.ASX",
        "start_ts_ms": 1700000000000,
        "end_ts_ms": 1700000060000,
        "open_ticks": 113410,
        "high_ticks": 113420,
        "low_ticks": 113410,
        "close_ticks": 113420,
        "volume": 175,
        "vwap_ticks": 113415,
        "source": "csv_agg",
    }
    publish("ohlcv.bar.v1", prev_bar)
    publish("ohlcv.bar.v1", cur_bar)

    run_feature_worker("CBA.ASX")
    day_rule_minimal("CBA.ASX")
    fuse_signals("CBA.ASX")

    candidates = list(read_all("candidate.v1"))
    traces = list(read_all("fusion.trace.v1"))
    features = list(read_all("feature.snapshot.v1"))
    return {"candidates": candidates, "traces": traces, "features": features}


def test_deterministic_replay() -> None:
    out1 = run_once()
    out2 = run_once()
    assert json.dumps(out1, sort_keys=True) == json.dumps(out2, sort_keys=True)
