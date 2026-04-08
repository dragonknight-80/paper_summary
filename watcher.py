from __future__ import annotations

import argparse
import time

from core.config import load_config
from core.llm_client import build_llm_client
from core.pipeline import process_all


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch paper/raw and auto-summarize")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    llm = build_llm_client(cfg.llm)
    poll_seconds = int(cfg.runtime.get("poll_seconds", 10))

    print(f"Watching: {cfg.raw_dir} (poll={poll_seconds}s)")
    while True:
        total, changed = process_all(cfg, incremental=True, llm=llm)
        if changed:
            print(f"updated: changed={changed}/{total}")
        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
