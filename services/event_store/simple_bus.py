import json
from pathlib import Path
from typing import Iterable

BUS_DIR = Path("tmp_event_bus")
BUS_DIR.mkdir(parents=True, exist_ok=True)


def topic_path(topic: str) -> Path:
    p = BUS_DIR / f"{topic}.ndjson"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("")
    return p


def publish(topic: str, message: dict) -> None:
    p = topic_path(topic)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(message, separators=(",", ":"), sort_keys=True) + "\n")


def read_all(topic: str) -> Iterable[dict]:
    p = topic_path(topic)
    if not p.exists():
        return
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
