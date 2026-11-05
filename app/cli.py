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
    ap.add_argument("--audio", help="voice input: transcribe this audio file (WAV/MP3/...) and use it as the message")
    ap.add_argument("--speak", metavar="OUT.wav", help="voice output: save the reply as speech to this WAV file")
    a = ap.parse_args(argv)
    if a.mock:
        os.environ["AI_LAWYER_MOCK"] = "1"
    if not a.message and not a.interactive and not a.audio:
        ap.error("give a message, --audio FILE, or --interactive")

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

    def one(text: str, input_mode: str = "text", lang: str | None = None) -> None:
        r = pipeline.handle_turn(session, text, input_mode=input_mode, lang_hint=lang or a.lang)
        print(r.reply_text)
        print(f"\n[action={r.action} category={r.category} citations={r.citations} "
              f"needs_lawyer={r.needs_lawyer} verifier={r.verifier['status']}]")
        if a.speak:
            from . import voice
            try:
                out = voice.tts(r.reply_text, r.reply_lang)
                with open(a.speak, "wb") as f:
                    f.write(out["audio"])
                print(f"[speech saved to {a.speak}: {out['model']}, {out['chars']} chars"
                      f"{', truncated' if out['truncated'] else ''}]")
            except voice.VoiceError as ex:
                print(f"[speech failed: {ex}]")
        if a.json:
            print(json.dumps(dataclasses.asdict(r), ensure_ascii=False, indent=2, default=str))

    if a.audio:
        from . import voice
        with open(a.audio, "rb") as f:
            heard = voice.stt(f.read(), a.lang)
        print(f"[heard via {heard['provider']}:{heard['model']} ({heard.get('language')}): {heard['text']}]\n")
        one(heard["text"], "voice", a.lang or heard.get("language"))
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
