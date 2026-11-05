"""Offline check of the web server in mock mode (no keys, no network).

  python -m app.selfcheck_server
"""
import io
import os
import wave

os.environ["AI_LAWYER_MOCK"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

from . import server, voice  # noqa: E402


def main() -> None:
    c = TestClient(server.app)
    checks = []

    def check(name, cond):
        checks.append((name, bool(cond)))

    r = c.get("/")
    check("GET / serves the page", r.status_code == 200 and "Haq" in r.text)
    for f in ("app.css", "app.js"):
        check(f"static {f} served", c.get(f"/static/{f}").status_code == 200)
    m = c.get("/api/meta").json()
    check("meta lists languages incl. Telugu", any(l["code"] == "te-IN" for l in m["languages"]))
    check("meta reports mock + real corpus", m["mock"] and not m["sample_data"] and m["chunks"] > 50)

    r = c.post("/api/turn", json={"text": "landlord not returning my 25000 deposit, Lucknow"}).json()
    sid = r["session_id"]
    check("turn returns result + session", r["result"]["reply_text"] and sid)
    check("citations come with source cards", all(cid in r["sources"] for cid in r["result"]["citations"]))
    check("state carries case file + history", "case_file" in r["state"] and len(r["state"]["history"]) == 2)

    r2 = c.post("/api/turn", json={"text": "I have the rent agreement", "session_id": sid}).json()
    check("second turn keeps the session", r2["session_id"] == sid and len(r2["state"]["history"]) == 4)

    server._sessions.clear()  # simulate a server restart: the browser sends its saved state back
    r3 = c.post("/api/turn", json={"text": "what next?", "session_id": sid, "state": r2["state"]}).json()
    check("restart: session restored from browser state", len(r3["state"]["history"]) == 6)

    d = c.post("/api/turn", json={"text": "my employer has not paid 40000 salary, Kanpur", "mode": "draft"}).json()
    check("draft mode returns a draft + file name", d["result"]["draft_text"] and
          d["result"]["trace"]["draft"]["file_name"].endswith(".txt"))
    check("empty message rejected", c.post("/api/turn", json={"text": "  "}).status_code == 400)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(b"\0\0" * 16000)
    voice.stt = lambda data, lang=None: {"text": "mera deposit wapas nahi mila", "language": "hi-IN",
                                         "provider": "gemini", "model": "test", "pieces": 1, "errors": []}
    s = c.post("/api/stt", files={"audio": ("r.webm", buf.getvalue(), "audio/webm")}, data={"lang": ""})
    check("STT endpoint returns transcript", s.status_code == 200 and "deposit" in s.json()["text"])
    voice.tts = lambda text, lang: {"audio": buf.getvalue(), "provider": "gemini", "model": "test-tts",
                                    "truncated": False}
    t = c.post("/api/tts", json={"text": "hello", "lang": "en-IN"})
    check("TTS endpoint returns WAV + provider header", t.status_code == 200 and t.content[:4] == b"RIFF"
          and t.headers.get("X-Voice-Provider") == "gemini:test-tts")

    # streaming: real stages, then the result
    with c.stream("POST", "/api/turn/stream", json={"text": "landlord kept my 20000 deposit, Lucknow"}) as s:
        body = "".join(s.iter_text())
    events = [ln[7:] for ln in body.splitlines() if ln.startswith("event: ")]
    check("stream sends stages before the result", "stage" in events and events[-1] == "result")
    check("stream stages are real pipeline steps", '"understanding"' in body and '"searching"' in body)

    page = c.get("/")
    check("security headers on the page", "Content-Security-Policy" in page.headers and
          page.headers.get("X-Content-Type-Options") == "nosniff")
    check("PWA manifest + service worker served", c.get("/manifest.webmanifest").status_code == 200 and
          c.get("/sw.js").status_code == 200 and c.get("/static/i18n.js").status_code == 200)

    import tempfile
    from pathlib import Path
    server.FEEDBACK = Path(tempfile.mkdtemp()) / "feedback.jsonl"
    fb = c.post("/api/feedback", json={"message_id": "m1", "rating": "down", "reason": "wrong section",
                                       "share_text": False, "question": "secret question"})
    saved = server.FEEDBACK.read_text(encoding="utf-8") if server.FEEDBACK.exists() else ""
    check("feedback saved without text unless shared", fb.json().get("ok") and "wrong section" in saved
          and "secret question" not in saved)
    st = c.get("/api/stats").json()
    check("stats report model budgets + feedback", "models" in st and st["feedback"]["down"] >= 1)

    server.LIMITS["turn"] = (2, 600)
    server._hits.clear()
    codes = [c.post("/api/turn", json={"text": f"deposit question {i}"}).status_code for i in range(3)]
    check("rate limit: third request in window gets 429", codes == [200, 200, 429])

    width = max(len(n) for n, _ in checks)
    for n, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {n.ljust(width)}")
    failed = [n for n, ok in checks if not ok]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
