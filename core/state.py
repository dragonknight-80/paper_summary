from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StateStore:
    path: Path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"files": {}}
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
