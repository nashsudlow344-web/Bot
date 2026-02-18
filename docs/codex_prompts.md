# Codex Prompt Contracts

Use these prompt fragments when requesting machine-generated outputs. Always enforce server-side validation with `services/codex_orchestrator/validate_and_publish.py`.

## GENERATE_DISPLAY_SIGNAL

```text
You are generating a trading display signal.
Output ONLY JSON (no markdown, no prose) that validates against:
- schemas/generate_display_signal.schema.json
Rules:
- Use integer tick prices only.
- Do not include additional properties.
- `confidence_pct` must be 0..100.
```

## SUMMARIZE_NEWS

```text
You are generating article analysis.
Output ONLY JSON (no markdown, no prose) that validates against:
- schemas/summarize_news.schema.json
Rules:
- `sentiment_score` must be in [-1, 1].
- `relevance_score` must be in [0, 1].
- Set `impact_class` to `market-moving` when relevance_score > 0.8 and abs(sentiment_score) > 0.6.
```

## FUSION_PLAN

```text
You are generating a fusion configuration.
Output ONLY JSON (no markdown, no prose) that validates against:
- schemas/fusion_plan.schema.json
Rules:
- `min_contributions` must be >= 1.
- All horizon weights must be non-negative.
- `accept_threshold` must be 0..100.
```

## Enforcement snippet (server-side)

```python
import json
from services.codex_orchestrator.validate_and_publish import validate_and_publish_display

raw = '{"id":"82ff9c47ae103735f6aed8ea","symbol":"CBA.ASX","side":"LONG","generated_ts_ms":1700000060000,"entry_price_ticks":113420,"stop_price_ticks":113410,"confidence_pct":62,"signal_type":"DAY"}'
payload = json.loads(raw)
result = validate_and_publish_display(payload)
print(result)
```
