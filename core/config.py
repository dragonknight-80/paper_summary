from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AppConfig:
    root_dir: Path
    raw_dir: Path
    summaries_dir: Path
    index_file: Path
    state_file: Path
    chunk_chars: int
    overlap_chars: int
    language: str
    llm: dict[str, Any]
    prompt: dict[str, str]
    runtime: dict[str, Any]


def _resolve_path(root_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root_dir / path)


def load_config(config_path: str | Path = "config.yaml") -> AppConfig:
    path = Path(config_path).resolve()
    root_dir = path.parent

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    paths = data.get("paths", {})
    processing = data.get("processing", {})

    return AppConfig(
        root_dir=root_dir,
        raw_dir=_resolve_path(root_dir, paths.get("papers_dir", "./raw")),
        summaries_dir=_resolve_path(root_dir, paths.get("summaries_dir", "./summaries")),
        index_file=_resolve_path(root_dir, paths.get("index_file", "./summary_index.md")),
        state_file=_resolve_path(root_dir, paths.get("state_file", "./.state.json")),
        chunk_chars=int(processing.get("chunk_chars", 9000)),
        overlap_chars=int(processing.get("overlap_chars", 500)),
        language=str(processing.get("language", "zh")),
        llm=data.get("llm", {}),
        prompt=data.get("prompt", {}),
        runtime=data.get("runtime", {}),
    )
