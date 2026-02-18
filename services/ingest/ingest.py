import csv
from pathlib import Path

from services.event_store.simple_bus import publish

# Example CSV columns: ts_ms,symbol,price_ticks,size,venue


def ingest_csv_ticks(csv_path: str, topic: str = "market.tick.v1") -> None:
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(csv_path)
    with p.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            msg = {
                "source_id": "csv_ingest",
                "symbol": row["symbol"],
                "seq_no": int(row.get("seq_no", 0)),
                "ts_ms": int(row["ts_ms"]),
                "recv_ts_ms": int(row.get("recv_ts_ms", row["ts_ms"])),
                "price_ticks": int(row["price_ticks"]),
                "size": int(row["size"]),
                "venue": row.get("venue", "CSV"),
            }
            publish(topic, msg)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--topic", default="market.tick.v1")
    args = parser.parse_args()
    ingest_csv_ticks(args.csv_path, args.topic)
