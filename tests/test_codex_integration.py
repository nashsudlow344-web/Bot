import json
import shutil

from services.codex_orchestrator.validate_and_publish import (
    validate_and_publish_display,
)
from services.event_store.simple_bus import BUS_DIR, read_all


def clear_bus() -> None:
    if BUS_DIR.exists():
        shutil.rmtree(BUS_DIR)
    BUS_DIR.mkdir(parents=True, exist_ok=True)


def test_parse_validate_publish_audit_full_pipeline() -> None:
    clear_bus()
    raw = (
        '{"id":"82ff9c47ae103735f6aed8ea","symbol":"CBA.ASX","side":"LONG",'
        '"generated_ts_ms":1700000060000,"entry_price_ticks":113420,'
        '"stop_price_ticks":113410,"confidence_pct":62,"signal_type":"DAY"}'
    )

    payload = json.loads(raw)
    result = validate_and_publish_display(payload)

    assert result == {"status": "OK", "signal_id": "82ff9c47ae103735f6aed8ea"}
    signals = list(read_all("signal.display.v1"))
    audits = list(read_all("audit.records.v1"))
    assert len(signals) == 1
    assert signals[0]["symbol"] == "CBA.ASX"
    assert any(a["event_type"] == "codex_validated_signal" for a in audits)


def test_invalid_raw_payload_is_rejected_and_not_published() -> None:
    clear_bus()
    raw = (
        '{"id":"82ff9c47ae103735f6aed8ea","symbol":"CBA.ASX","side":"LONG",'
        '"generated_ts_ms":1700000060000,"entry_price_ticks":113420,'
        '"stop_price_ticks":113410,"confidence_pct":999,"signal_type":"DAY"}'
    )

    payload = json.loads(raw)
    result = validate_and_publish_display(payload)

    assert result["status"] == "REJECT"
    assert list(read_all("signal.display.v1")) == []
    audits = list(read_all("audit.records.v1"))
    assert any(a["event_type"] == "codex_validation_failed" for a in audits)
