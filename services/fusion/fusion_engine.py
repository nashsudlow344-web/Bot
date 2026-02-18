import hashlib

from services.event_store.simple_bus import publish, read_all

FUSION_PLAN = {
    "weights": {"SCALP": 0.5, "DAY": 1.0, "SWING": 1.5},
    "accept_threshold": 55,
    "conflict_rr_threshold": 0.3,
    "version": "fusion_plan_v1",
}


def _stable_fusion_id(symbol: str, signal_ids: list[str]) -> str:
    payload = f"{symbol}|{'|'.join(sorted(signal_ids))}|{FUSION_PLAN['version']}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def fuse_signals(
    symbol: str,
    input_topic: str = "signal.display.v1",
    trace_topic: str = "fusion.trace.v1",
    out_topic: str = "candidate.v1",
) -> None:
    signals = [s for s in read_all(input_topic) if s.get("symbol") == symbol]
    if not signals:
        return

    contributions = []
    total_weighted = 0.0
    total_weight = 0.0
    dominant = None
    for s in sorted(signals, key=lambda v: str(v.get("id", ""))):
        horizon = s.get("signal_type", "UNKNOWN")
        conf = int(s.get("confidence_pct", 0))
        weight = FUSION_PLAN["weights"].get(horizon, 1.0)
        weighted = conf * weight
        contributions.append(
            {
                "horizon": horizon,
                "signal_id": s.get("id"),
                "confidence_pct": conf,
                "weight": weight,
                "weighted_score": weighted,
                "rationale": [s.get("explanation_short", "")[:200]],
            }
        )
        total_weighted += weighted
        total_weight += weight
        if dominant is None or weighted > dominant[1]:
            dominant = (horizon, weighted)

    composite = (total_weighted / total_weight) if total_weight > 0 else 0.0
    resolution = (
        "ACCEPTED" if composite >= FUSION_PLAN["accept_threshold"] else "CONFLICT"
    )
    signal_ids = [str(s.get("id")) for s in signals]
    fusion_id = _stable_fusion_id(symbol, signal_ids)
    created_ts = max(int(s.get("generated_ts_ms", 0)) for s in signals)

    trace = {
        "fusion_id": fusion_id,
        "symbol": symbol,
        "created_ts_ms": created_ts,
        "contributions": contributions,
        "composite_score": composite,
        "resolution": resolution,
        "dominant_horizon": dominant[0] if dominant else None,
        "fusion_plan_version": FUSION_PLAN["version"],
        "debug_json": "",
    }
    publish(trace_topic, trace)

    candidate = {
        "id": fusion_id,
        "symbol": symbol,
        "composite_score": composite,
        "resolution": resolution,
        "created_ts_ms": created_ts,
        "dominant_horizon": trace["dominant_horizon"],
        "signals": sorted(signal_ids),
    }
    publish(out_topic, candidate)
