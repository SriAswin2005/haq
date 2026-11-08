"""Embed the law library ahead of time, so the server never embeds on a user's request.

    python -m app.build_index           # embeds only new or changed passages, writes data/index/
    python -m app.build_index --force   # re-embeds everything

Free-tier embedding quota is about 100 passages a minute and 1,000 a day, so a big library may take more
than one day: run it again the next day and it continues where it stopped (finished passages are cached).
"""
import argparse
import sys
import time

from . import retrieval
from .config import load_config


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    chunks, problems = retrieval.load_corpus()
    print(f"library: {len(chunks)} passages ({len(problems)} skipped as invalid)")
    t0 = time.time()
    try:
        idx = retrieval.build_index(force=a.force)
    except Exception as e:  # noqa: BLE001
        print(f"stopped: {e}\nFinished passages are cached; run again later to continue.")
        return 1
    print(f"embedded now: {idx['embedded_now']} in {time.time() - t0:.0f}s; cache: {retrieval._cache_file()}")
    print(f"embedding model: {load_config()['embeddings']['model']}, dims: {load_config()['embeddings'].get('dims')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
