"""CLI for demos and the interview.

  python -m app.cli "mera deposit wapas nahi mila" --lang hi-IN --json
  python -m app.cli --interactive --mock
Swap the model by editing config.yaml only, then rerun the same command.
"""
import argparse
import dataclasses
import json
import os
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.cli", description="AI Lawyer for India (CLI)")
    ap.add_argument("message", nargs="?", help="the user's message")
    ap.add_argument("--lang", help="reply language, e.g. hi-IN or en-IN (default: auto-detect)")
    ap.add_argument("--mode", choices=["advice", "draft", "practice"], default="advice")
    ap.add_argument("--mock", action="store_true", help="no API keys: canned model + hash embeddings")
    ap.add_argument("--json", action="store_true", help="also print the full TurnResult as JSON")
    ap.add_argument("--interactive", action="store_true", help="multi-turn chat in one session")
    ap.add_argument("--corpus", help="corpus path override (e.g. data/corpus)")
    a = ap.parse_args(argv)
    if a.mock:
        os.environ["AI_LAWYER_MOCK"] = "1"
    if not a.message and not a.interactive:
        ap.error("give a message or use --interactive")

    from . import pipeline
    from .config import load_config
    if a.corpus:
        load_config()["corpus"]["path"] = a.corpus
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    session = pipeline.new_session(a.lang)
    session.mode = a.mode

    def one(text: str) -> None:
        r = pipeline.handle_turn(session, text, lang_hint=a.lang)
        print(r.reply_text)
        print(f"\n[action={r.action} category={r.category} citations={r.citations} "
              f"needs_lawyer={r.needs_lawyer} verifier={r.verifier['status']}]")
        if a.json:
            print(json.dumps(dataclasses.asdict(r), ensure_ascii=False, indent=2, default=str))

    if a.message:
        one(a.message)
    if a.interactive:
        print("Interactive mode. Empty line or Ctrl-D to quit.")
        while True:
            try:
                t = input("\nyou> ").strip()
            except EOFError:
                break
            if not t:
                break
            one(t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
