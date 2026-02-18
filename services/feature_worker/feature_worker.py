from decimal import ROUND_HALF_UP, Decimal, getcontext

from services.event_store.simple_bus import publish, read_all

getcontext().prec = 28


def decimal_from_ticks(ticks: int, tick_decimals: int) -> Decimal:
    return (Decimal(ticks) / (Decimal(10) ** tick_decimals)).quantize(
        Decimal("0.00000001")
    )


def to_ticks_from_decimal(value: Decimal, tick_decimals: int) -> int:
    mult = Decimal(10) ** tick_decimals
    return int((value * mult).to_integral_value(rounding=ROUND_HALF_UP))


class EMA:
    def __init__(self, period: int, tick_decimals: int):
        self.period = period
        self.alpha = Decimal(2) / (Decimal(period) + Decimal(1))
        self.value = None
        self.tick_decimals = tick_decimals

    def update(self, price_ticks: int):
        price = decimal_from_ticks(price_ticks, self.tick_decimals)
        if self.value is None:
            self.value = price
        else:
            self.value = (self.alpha * price) + ((Decimal(1) - self.alpha) * self.value)
        return self.value


class ATR:
    def __init__(self, period: int, tick_decimals: int):
        self.period = period
        self.tick_decimals = tick_decimals
        self.trs = []
        self.prev_close = None
        self.value = None

    def update(self, high_ticks: int, low_ticks: int, close_ticks: int):
        high = decimal_from_ticks(high_ticks, self.tick_decimals)
        low = decimal_from_ticks(low_ticks, self.tick_decimals)
        close = decimal_from_ticks(close_ticks, self.tick_decimals)
        tr = max(
            high - low,
            (high - self.prev_close) if self.prev_close is not None else high - low,
            (self.prev_close - low) if self.prev_close is not None else high - low,
        )
        if self.prev_close is None:
            self.trs.append(tr)
        else:
            if len(self.trs) < self.period:
                self.trs.append(tr)
            else:
                if self.value is None:
                    self.value = sum(self.trs) / Decimal(len(self.trs))
                self.value = ((self.value * (self.period - 1)) + tr) / Decimal(
                    self.period
                )
        self.prev_close = close
        return self.value


class VWAP:
    def __init__(self, tick_decimals: int):
        self.tick_decimals = tick_decimals
        self.cum_pv = Decimal(0)
        self.cum_vol = Decimal(0)

    def update(self, price_ticks: int, size: int):
        price = decimal_from_ticks(price_ticks, self.tick_decimals)
        self.cum_pv += price * Decimal(size)
        self.cum_vol += Decimal(size)
        if self.cum_vol == 0:
            return None
        return self.cum_pv / self.cum_vol


def run_feature_worker(
    symbol: str,
    tick_decimals: int = 2,
    input_topic: str = "ohlcv.bar.v1",
    output_topic: str = "feature.snapshot.v1",
    version: str = "features_v1.0.0",
) -> None:
    ema20 = EMA(20, tick_decimals)
    atr14 = ATR(14, tick_decimals)
    vwap = VWAP(tick_decimals)
    for bar in read_all(input_topic):
        if bar.get("symbol") != symbol:
            continue
        as_of = int(bar["end_ts_ms"])
        ema_val = ema20.update(int(bar["close_ticks"]))
        atr_val = atr14.update(
            int(bar["high_ticks"]), int(bar["low_ticks"]), int(bar["close_ticks"])
        )
        vwap_val = vwap.update(int(bar["close_ticks"]), int(bar.get("volume", 0)))
        features = {
            "ema_20": str(ema_val) if ema_val is not None else "null",
            "atr_14": str(atr_val) if atr_val is not None else "null",
            "vwap": str(vwap_val) if vwap_val is not None else "null",
            "close": str(decimal_from_ticks(int(bar["close_ticks"]), tick_decimals)),
            "volume": str(int(bar.get("volume", 0))),
        }
        snapshot = {
            "symbol": symbol,
            "as_of_ts_ms": as_of,
            "computed_at_ms": as_of,
            "uses_up_to_ts_ms": as_of,
            "features": features,
            "version": version,
            "provenance": "feature_worker",
        }
        publish(output_topic, snapshot)
