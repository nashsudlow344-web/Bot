import json
import time
import uuid

from services.event_store.simple_bus import publish


def validate_generate_display_payload(payload: dict) -> bool:
    required = [
        "symbol",
        "side",
        "entry_price_ticks",
        "stop_price_ticks",
        "confidence_pct",
    ]
    if any(r not in payload for r in required):
        return False
    return 0 <= int(payload.get("confidence_pct")) <= 100


def call_codex_generate_display(task_request: dict):
    tco = task_request.get("tco", {})
    if tco.get("force_reject"):
        resp = {
            "task_id": task_request.get("task_id"),
            "status": "REJECT",
            "response_ts_ms": int(time.time() * 1000),
            "payload": {},
            "debug": {"reason": "forced reject"},
        }
        publish(
            "audit.records.v1",
            {
                "id": str(uuid.uuid4()),
                "event_type": "codex_response",
                "ts_ms": int(time.time() * 1000),
                "payload_json": json.dumps(resp),
            },
        )
        return resp

    entry = int(tco.get("market_state", {}).get("mid_price_ticks", 1000))
    stop = max(1, entry - int(tco.get("risk_state", {}).get("stop_ticks", 10)))
    payload = {
        "symbol": tco.get("instrument", {}).get("symbol", "UNKNOWN"),
        "side": "LONG",
        "entry_price_ticks": entry,
        "stop_price_ticks": stop,
        "target_price_ticks": [entry + (entry - stop) * 2],
        "confidence_pct": 60,
        "explanation_short": "codex_stub generated signal",
        "feature_contributions": [{"feature": "ema_20", "score": 0.3}],
        "model_seed": 42,
    }
    status = "OK" if validate_generate_display_payload(payload) else "REJECT"
    resp = {
        "task_id": task_request.get("task_id"),
        "status": status,
        "response_ts_ms": int(time.time() * 1000),
        "payload": payload,
        "debug": {"model_seed": 42},
    }
    publish(
        "audit.records.v1",
        {
            "id": str(uuid.uuid4()),
            "event_type": "codex_response",
            "ts_ms": int(time.time() * 1000),
            "payload_json": json.dumps(resp),
        },
    )
    return resp
