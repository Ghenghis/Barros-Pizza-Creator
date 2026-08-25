from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any


class HistoryStore:
    def __init__(self, path: str | Path, max_entries: int = 300):
        self.path = Path(path)
        self.max_entries = max_entries
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, mode: str, prompt: str, response: dict[str, Any]) -> None:
        entry = {
            "timestamp": time.time(),
            "mode": mode,
            "prompt": prompt,
            "response": response,
        }
        with self._lock:
            entries = self.read()
            entries.append(entry)
            entries = entries[-self.max_entries :]
            temp = self.path.with_suffix(self.path.suffix + ".tmp")
            temp.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(self.path)

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (OSError, json.JSONDecodeError):
            return []

