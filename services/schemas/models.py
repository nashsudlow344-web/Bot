import json
from typing import Any, Dict, List

try:
    from pydantic import BaseModel, Field, ValidationError, confloat, conint

    class GenerateDisplaySignal(BaseModel):
        id: str = Field(..., min_length=8, max_length=64)
        symbol: str
        side: str
        generated_ts_ms: int = Field(..., ge=0)
        entry_price_ticks: int = Field(..., ge=1)
        stop_price_ticks: int = Field(..., ge=1)
        target_price_ticks: List[int] = Field(default_factory=list)
        rr: float | None = Field(default=None, ge=0)
        confidence_pct: conint(ge=0, le=100)
        explanation_short: str | None = Field(default=None, max_length=240)
        explanation_long: str | None = Field(default=None, max_length=2000)
        model_version: str | None = None
        signal_type: str
        source: str | None = None
        ttl_ms: int | None = Field(default=None, ge=0)
        debug: Dict[str, Any] = Field(default_factory=dict)

    class SummarizeNews(BaseModel):
        article_id: str
        analysis_ts_ms: int = Field(..., ge=0)
        sentiment_score: confloat(ge=-1.0, le=1.0)
        relevance_score: confloat(ge=0.0, le=1.0)
        summary: str = Field(..., max_length=4000)
        entities: List[str] = Field(default_factory=list)
        tags: List[str] = Field(default_factory=list)
        model_version: str | None = None
        impact_class: str = Field(default="none")

    class FusionPlan(BaseModel):
        version: str
        weights: Dict[str, float]
        accept_threshold: confloat(ge=0.0, le=100.0)
        conflict_rr_threshold: float = Field(default=0.0, ge=0.0)
        min_contributions: int = Field(default=1, ge=1)
        debug: Dict[str, Any] = Field(default_factory=dict)

except ModuleNotFoundError:

    class ValidationError(Exception):
        def __init__(self, errors: List[Dict[str, Any]]):
            self._errors = errors
            super().__init__("validation error")

        def json(self) -> str:
            return json.dumps(self._errors)

    class _SimpleModel:
        _required: List[str] = []

        def __init__(self, **data: Any):
            self._data = self._validate(data)
            for key, value in self._data.items():
                setattr(self, key, value)

        @classmethod
        def _error(cls, field: str, msg: str, value: Any) -> ValidationError:
            return ValidationError([{"loc": [field], "msg": msg, "input": value}])

        def dict(self) -> Dict[str, Any]:
            return dict(self._data)

    class GenerateDisplaySignal(_SimpleModel):
        _required = [
            "id",
            "symbol",
            "side",
            "generated_ts_ms",
            "entry_price_ticks",
            "stop_price_ticks",
            "confidence_pct",
            "signal_type",
        ]

        def _validate(self, d: Dict[str, Any]) -> Dict[str, Any]:
            for req in self._required:
                if req not in d:
                    raise self._error(req, "field required", None)
            if len(str(d["id"])) < 8:
                raise self._error("id", "id too short", d["id"])
            if d["side"] not in {"LONG", "SHORT"}:
                raise self._error("side", "invalid side", d["side"])
            if int(d["confidence_pct"]) < 0 or int(d["confidence_pct"]) > 100:
                raise self._error("confidence_pct", "out of range", d["confidence_pct"])
            if int(d["entry_price_ticks"]) < 1 or int(d["stop_price_ticks"]) < 1:
                raise self._error(
                    "entry_price_ticks", "must be >= 1", d.get("entry_price_ticks")
                )
            out = dict(d)
            out.setdefault("target_price_ticks", [])
            out.setdefault("debug", {})
            return out

    class SummarizeNews(_SimpleModel):
        _required = [
            "article_id",
            "analysis_ts_ms",
            "sentiment_score",
            "relevance_score",
            "summary",
        ]

        def _validate(self, d: Dict[str, Any]) -> Dict[str, Any]:
            for req in self._required:
                if req not in d:
                    raise self._error(req, "field required", None)
            if float(d["sentiment_score"]) < -1.0 or float(d["sentiment_score"]) > 1.0:
                raise self._error(
                    "sentiment_score", "out of range", d["sentiment_score"]
                )
            if float(d["relevance_score"]) < 0.0 or float(d["relevance_score"]) > 1.0:
                raise self._error(
                    "relevance_score", "out of range", d["relevance_score"]
                )
            out = dict(d)
            out.setdefault("entities", [])
            out.setdefault("tags", [])
            out.setdefault("impact_class", "none")
            return out

    class FusionPlan(_SimpleModel):
        _required = ["version", "weights", "accept_threshold"]

        def _validate(self, d: Dict[str, Any]) -> Dict[str, Any]:
            for req in self._required:
                if req not in d:
                    raise self._error(req, "field required", None)
            if not isinstance(d["weights"], dict) or not d["weights"]:
                raise self._error("weights", "must be a non-empty object", d["weights"])
            if (
                float(d["accept_threshold"]) < 0.0
                or float(d["accept_threshold"]) > 100.0
            ):
                raise self._error(
                    "accept_threshold", "out of range", d["accept_threshold"]
                )
            out = dict(d)
            out.setdefault("conflict_rr_threshold", 0.0)
            out.setdefault("min_contributions", 1)
            out.setdefault("debug", {})
            return out
