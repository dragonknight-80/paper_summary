from __future__ import annotations

import argparse

from core.config import load_config
from core.llm_client import build_llm_client
from core.pipeline import process_all, process_pdf
from core.state import StateStore
from core.indexer import rebuild_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual trigger for paper summarization")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--mode", choices=["incremental", "full"], default="incremental")
    parser.add_argument("--file", default=None, help="Only process one PDF path relative to config root")
    args = parser.parse_args()

    cfg = load_config(args.config)
    llm = build_llm_client(cfg.llm)

    if args.file:
        target = (cfg.root_dir / args.file).resolve()
        store = StateStore(cfg.state_file)
        state = store.load()
        changed = process_pdf(target, cfg, state, llm, force=args.mode == "full")
        rebuild_index(cfg.index_file, cfg.summaries_dir)
        store.save(state)
        print(f"processed_file={target} changed={changed}")
        return

    total, changed = process_all(cfg, incremental=args.mode == "incremental", llm=llm)
    print(f"mode={args.mode} total={total} changed={changed}")


if __name__ == "__main__":
    main()
