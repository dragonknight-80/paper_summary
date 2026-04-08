from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
import os

from .config import AppConfig
from .indexer import rebuild_index
from .llm_client import BaseLLMClient
from .pdf_reader import extract_pdf_text
from .state import StateStore


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def chunk_text(text: str, chunk_chars: int, overlap_chars: int) -> list[str]:
    if not text:
        return []
    chunks: list[str] = []
    step = max(1, chunk_chars - overlap_chars)
    for start in range(0, len(text), step):
        part = text[start : start + chunk_chars]
        if part:
            chunks.append(part)
        if start + chunk_chars >= len(text):
            break
    return chunks


def _build_summary_markdown(*, pdf_rel: str, digest: str, provider: str, model: str, body: str) -> str:
    now = datetime.now(timezone.utc).isoformat()
    header = [
        "---",
        f"source: {pdf_rel}",
        f"sha256: {digest}",
        f"updated_at: {now}",
        f"provider: {provider}",
        f"model: {model}",
        "---",
        "",
    ]
    return "\n".join(header) + body.strip() + "\n"


def summarize_pdf(pdf_path: Path, cfg: AppConfig, llm: BaseLLMClient) -> str:
    text = extract_pdf_text(pdf_path)
    if not text:
        return "# 摘要\n\n原文提取为空，无法生成摘要。\n"

    chunks = chunk_text(text, cfg.chunk_chars, cfg.overlap_chars)
    template = cfg.prompt.get("template", "请总结以下论文内容：")
    system_prompt = cfg.prompt.get("system", "你是科研助手。")

    partials: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        user_content = f"{template}\n\n[第 {idx}/{len(chunks)} 块]\n{chunk}"
        partials.append(llm.summarize(system_prompt=system_prompt, user_content=user_content))

    merge_prompt = (
        "请将以下分块摘要整合为一个最终摘要，保持结构化且不编造信息：\n\n"
        + "\n\n".join(partials)
    )
    final = llm.summarize(system_prompt=system_prompt, user_content=merge_prompt)
    return final


def _path_for_state(path: Path, root: Path) -> str:
    """Return a stable path key even when target is outside root."""
    return os.path.relpath(path, root)


def process_pdf(pdf_path: Path, cfg: AppConfig, state: dict, llm: BaseLLMClient, force: bool = False) -> bool:
    pdf_rel = _path_for_state(pdf_path, cfg.root_dir)
    digest = sha256_file(pdf_path)
    files = state.setdefault("files", {})
    old = files.get(pdf_rel, {})

    if (not force) and old.get("sha256") == digest:
        return False

    summary_body = summarize_pdf(pdf_path, cfg, llm)
    summary_name = f"{pdf_path.stem}.md"
    summary_path = cfg.summaries_dir / summary_name
    provider = str(cfg.llm.get("provider", "openai_compatible"))
    model = str(cfg.llm.get("model", ""))

    summary_md = _build_summary_markdown(
        pdf_rel=pdf_rel,
        digest=digest,
        provider=provider,
        model=model,
        body=summary_body,
    )
    cfg.summaries_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary_md, encoding="utf-8")

    files[pdf_rel] = {
        "sha256": digest,
        "summary": _path_for_state(summary_path, cfg.root_dir),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return True


def process_all(cfg: AppConfig, *, incremental: bool, llm: BaseLLMClient) -> tuple[int, int]:
    cfg.raw_dir.mkdir(parents=True, exist_ok=True)
    cfg.summaries_dir.mkdir(parents=True, exist_ok=True)

    store = StateStore(cfg.state_file)
    state = store.load()

    changed = 0
    total = 0

    for pdf_path in sorted(cfg.raw_dir.glob("*.pdf")):
        total += 1
        did_change = process_pdf(
            pdf_path,
            cfg,
            state,
            llm,
            force=not incremental,
        )
        if did_change:
            changed += 1

    rebuild_index(cfg.index_file, cfg.summaries_dir)
    store.save(state)
    return total, changed
