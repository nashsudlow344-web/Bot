import json
import time
import uuid
from typing import Any, Dict

from services.event_store.simple_bus import publish
from services.schemas.models import (
    FusionPlan,
    GenerateDisplaySignal,
    SummarizeNews,
    ValidationError,
)

AUDIT_TOPIC = "audit.records.v1"


def _dump_model(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _publish_audit(event_type: str, payload: Dict[str, Any]) -> None:
    publish(
        AUDIT_TOPIC,
        {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "ts_ms": int(time.time() * 1000),
            "payload_json": json.dumps(payload, sort_keys=True),
        },
    )


def validate_and_publish_display(signal_payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        signal = GenerateDisplaySignal(**signal_payload)
    except ValidationError as exc:
        err = {"status": "REJECT", "errors": json.loads(exc.json())}
        _publish_audit("codex_validation_failed", err)
        return {"status": "REJECT", "errors": err}

    canonical = _dump_model(signal)
    publish("signal.display.v1", canonical)
    _publish_audit("codex_validated_signal", canonical)
    return {"status": "OK", "signal_id": signal.id}


def validate_and_publish_news(news_payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        news = SummarizeNews(**news_payload)
    except ValidationError as exc:
        err = {"status": "REJECT", "errors": json.loads(exc.json())}
        _publish_audit("codex_news_validate_failed", err)
        return {"status": "REJECT", "errors": err}

    canonical = _dump_model(news)
    publish("article.analysis.v1", canonical)
    _publish_audit("codex_validated_news", canonical)
    return {"status": "OK", "article_id": news.article_id}


def validate_and_publish_fusion_plan(plan_payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        plan = FusionPlan(**plan_payload)
    except ValidationError as exc:
        err = {"status": "REJECT", "errors": json.loads(exc.json())}
        _publish_audit("codex_fusion_plan_failed", err)
        return {"status": "REJECT", "errors": err}

    canonical = _dump_model(plan)
    publish("fusion.plan.v1", canonical)
    _publish_audit("codex_validated_fusion_plan", canonical)
    return {"status": "OK", "plan_version": plan.version}
