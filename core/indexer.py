from __future__ import annotations

from pathlib import Path


def rebuild_index(index_file: Path, summaries_dir: Path) -> None:
    summaries = sorted(summaries_dir.glob("*.md"), key=lambda p: p.name.lower())
    lines = ["# Paper Summaries Index", ""]
    for summary in summaries:
        title = summary.stem.replace("_", " ")
        rel = summary.name
        lines.append(f"- [{title}](summaries/{rel})")
    lines.append("")

    index_file.write_text("\n".join(lines), encoding="utf-8")
