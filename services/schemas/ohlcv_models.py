from typing import Any, Dict

try:
    from pydantic import BaseModel

    class OhlcvBar(BaseModel):
        symbol: str
        timeframe_ms: int
        timeframe_start_ms: int
        open: int
        high: int
        low: int
        close: int
        volume: int
        trade_count: int
        version: int = 1

    class OhlcvMetrics(BaseModel):
        symbol: str
        timeframe_start_ms: int
        timeframe_ms: int
        trade_count: int
        volume: int
        emitted_ts_ms: int
        counters: Dict[str, int]

except ModuleNotFoundError:

    class OhlcvBar:
        def __init__(self, **data: Any):
            required = [
                "symbol",
                "timeframe_ms",
                "timeframe_start_ms",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "trade_count",
            ]
            for key in required:
                if key not in data:
                    raise ValueError(f"missing {key}")
            self.__dict__.update(data)

    class OhlcvMetrics:
        def __init__(self, **data: Any):
            self.__dict__.update(data)
