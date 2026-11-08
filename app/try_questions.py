"""Run real questions through the real pipeline and write every answer to a report you (and Claude) can read.

    python -m app.try_questions                 # all questions in tests/live_questions.jsonl
    python -m app.try_questions L02 L11         # only these ids
    python -m app.try_questions --text "can police arrest me without a warrant"

Writes outputs/live/<timestamp>.md (readable) and .json (raw). Needs GEMINI_API_KEY in .env.
Each question costs about 3 to 6 model calls; the full set is about 150, well inside the free daily quota.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from . import pipeline
from .config import ROOT, is_mock


def _path(r) -> str:
    tr = r.trace or {}
    if tr.get("kind") == "chat":
        return "small talk"
    if tr.get("kind") == "harmful":
        return "refused (harmful request)"
    if tr.get("web"):
        return "live web search"
    if tr.get("general_guidance"):
        return "general information (no library passage, web search failed)"
    if r.action in ("answer",) and r.citations:
        return "law library"
    if r.action == "draft":
        return "draft"
    return f"{r.action}"


def run(cases: list[dict]) -> tuple[Path, Path]:
    out_dir = ROOT / "outputs" / "live"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    md, raw = [f"# Live answers {stamp}\n", f"Mock mode: {is_mock()}\n"], []
    for c in cases:
        s = pipeline.new_session(None)
        md.append(f"\n## {c['id']} ({c.get('from', '')})\n\nExpected: {c.get('expect', '')}\n")
        for t in c["turns"]:
            t0 = time.time()
            r = pipeline.handle_turn(s, t["text"], input_mode="voice" if t.get("voice") else "text",
                                     heard_lang=t.get("heard_lang"))
            sec = round(time.time() - t0, 1)
            tr = r.trace or {}
            md.append(f"\n**User:** {t['text']}\n\n"
                      f"*Path: {_path(r)} · action: {r.action} · reply language: {r.reply_lang} · "
                      f"{sec}s · library top score: {(tr.get('retrieval') or {}).get('top_score', '-')} · "
                      f"models: {', '.join((tr.get('llm') or {}).get('models', [])[:6])}*\n\n"
                      + "\n".join("> " + ln if ln.strip() else ">" for ln in r.reply_text.splitlines()) + "\n")
            if tr.get("web"):
                md.append("\nWeb sources: " + "; ".join(f"[{x['n']}] {x['domain']}" for x in tr["web"]["sources"]) + "\n")
                if tr["web"].get("dropped"):
                    md.append(f"\nDropped as unsupported: {len(tr['web']['dropped'])} sentence(s)\n")
            raw.append({"case": c["id"], "turn": t, "seconds": sec, "path": _path(r), "action": r.action,
                        "reply_lang": r.reply_lang, "reply": r.reply_text, "citations": r.citations,
                        "escalation_reasons": r.escalation_reasons, "verifier": r.verifier,
                        "trace": json.loads(json.dumps(tr, default=str))})
            print(f"{c['id']}: {_path(r)} ({sec}s, {r.reply_lang})", flush=True)
    mdp, jp = out_dir / f"{stamp}.md", out_dir / f"{stamp}.json"
    mdp.write_text("\n".join(md), encoding="utf-8")
    jp.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    return mdp, jp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--text")
    a = ap.parse_args()
    if a.text:
        cases = [{"id": "ADHOC", "turns": [{"text": a.text}]}]
    else:
        f = ROOT / "tests" / "live_questions.jsonl"
        cases = [json.loads(ln) for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if a.ids:
            cases = [c for c in cases if c["id"] in set(a.ids)]
    if not is_mock() and not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY is not set (put it in .env)")
        return 1
    mdp, jp = run(cases)
    print(f"\nreport: {mdp}\nraw: {jp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
