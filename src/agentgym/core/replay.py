import json
from pathlib import Path
from typing import Dict, List


class EventRecorder:
    def __init__(self):
        self.events: List[Dict] = []

    def record(self, event_dict: Dict) -> None:
        self.events.append(event_dict)

    def dump_jsonl(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            for e in self.events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")


def load_jsonl(path: str) -> List[Dict]:
    p = Path(path)
    out: List[Dict] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            out.append(json.loads(line))
    return out
