import shutil

from services.codex_orchestrator.validate_and_publish import (
    validate_and_publish_display,
    validate_and_publish_fusion_plan,
    validate_and_publish_news,
)
from services.event_store.simple_bus import BUS_DIR, read_all


def clear_bus() -> None:
    if BUS_DIR.exists():
        shutil.rmtree(BUS_DIR)
    BUS_DIR.mkdir(parents=True, exist_ok=True)


def test_validate_and_publish_display_accepts_valid_payload() -> None:
    clear_bus()
    payload = {
        "id": "82ff9c47ae103735f6aed8ea",
        "symbol": "CBA.ASX",
        "side": "LONG",
        "generated_ts_ms": 1700000060000,
        "entry_price_ticks": 113420,
        "stop_price_ticks": 113410,
        "target_price_ticks": [113460, 113500],
        "rr": 2.0,
        "confidence_pct": 62,
        "explanation_short": "day breakout with volume expansion",
        "signal_type": "DAY",
        "model_version": "day_v1",
        "source": "codex",
        "ttl_ms": 3600000,
    }

    result = validate_and_publish_display(payload)

    assert result == {"status": "OK", "signal_id": payload["id"]}
    signal_records = list(read_all("signal.display.v1"))
    assert len(signal_records) == 1
    assert signal_records[0]["id"] == payload["id"]


def test_validate_and_publish_display_rejects_invalid_confidence() -> None:
    clear_bus()
    payload = {
        "id": "82ff9c47ae103735f6aed8ea",
        "symbol": "CBA.ASX",
        "side": "LONG",
        "generated_ts_ms": 1700000060000,
        "entry_price_ticks": 113420,
        "stop_price_ticks": 113410,
        "confidence_pct": 120,
        "signal_type": "DAY",
    }

    result = validate_and_publish_display(payload)

    assert result["status"] == "REJECT"
    assert list(read_all("signal.display.v1")) == []
    assert any(
        r["event_type"] == "codex_validation_failed"
        for r in read_all("audit.records.v1")
    )


def test_validate_and_publish_news_and_fusion_plan() -> None:
    clear_bus()
    news = {
        "article_id": "art-20260101-0001",
        "analysis_ts_ms": 1700001000000,
        "sentiment_score": -0.65,
        "relevance_score": 0.87,
        "summary": "Company X announced an unexpected profit warning.",
        "entities": ["Company X", "CEO"],
        "impact_class": "major",
        "model_version": "news_v1",
    }
    plan = {
        "version": "fusion_plan_v1",
        "weights": {"SCALP": 0.5, "DAY": 1.0, "SWING": 1.5},
        "accept_threshold": 55.0,
        "conflict_rr_threshold": 0.3,
        "min_contributions": 1,
    }

    news_result = validate_and_publish_news(news)
    plan_result = validate_and_publish_fusion_plan(plan)

    assert news_result == {"status": "OK", "article_id": "art-20260101-0001"}
    assert plan_result == {"status": "OK", "plan_version": "fusion_plan_v1"}
    assert len(list(read_all("article.analysis.v1"))) == 1
    assert len(list(read_all("fusion.plan.v1"))) == 1
