"""Web app server for Haq (the AI lawyer): a JSON API around app.pipeline plus the single-page UI.

Run locally:   python -m app.serve            (or: python -m uvicorn app.server:app --port 7860)
Mock (no keys): python -m app.serve --mock

Design notes for running this for many people:
- Stateless across restarts. The browser keeps each chat (messages, case file, history) in
  localStorage and sends that state with every turn, so a restarted or sleeping free-tier host
  continues the conversation. Server-side sessions are only a bounded in-memory cache.
- Real progress. /api/turn/stream sends Server-Sent Events for each pipeline stage
  (understanding, searching, writing, checking, translating), then the result.
- Quota protection. Per-IP sliding-window limits on turns and voice calls (env-tunable), so
  one visitor cannot spend the free model quota for everyone.
- Turns are serialised with a lock because the LLM client keeps per-turn stats in module
  state. For more traffic, run several worker processes behind a load balancer: no state
  is shared between them.
- Feedback (thumbs up/down) goes to outputs/feedback.jsonl for human review. The question
  and answer text are stored only if the person ticks "share this conversation".
"""
import collections
import dataclasses
import json
import os
import queue
import threading
import time
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import llm, pipeline, retrieval, voice
from .config import ROOT, is_mock, load_config

WEB = ROOT / "app" / "web"
FEEDBACK = ROOT / "outputs" / "feedback.jsonl"
app = FastAPI(title="Haq: AI legal help", docs_url="/api/docs", redoc_url=None)
app.mount("/static", StaticFiles(directory=str(WEB)), name="static")

MAX_SESSIONS = 500
_sessions: "collections.OrderedDict[str, pipeline.Session]" = collections.OrderedDict()
_turn_lock = threading.Lock()

LIMITS = {  # (requests, window seconds) per client IP
    "turn": (int(os.environ.get("HAQ_TURNS_PER_10MIN", 40)), 600),
    "voice": (int(os.environ.get("HAQ_VOICE_PER_10MIN", 40)), 600),
    "feedback": (60, 600),
}
_hits: dict[tuple[str, str], collections.deque] = collections.defaultdict(collections.deque)
_hits_lock = threading.Lock()

LANGUAGES = [
    {"code": "", "label": "Auto-detect"},
    {"code": "en-IN", "label": "English"},
    {"code": "hi-IN", "label": "हिन्दी"},
    {"code": "te-IN", "label": "తెలుగు"},
    {"code": "ta-IN", "label": "தமிழ்"},
    {"code": "bn-IN", "label": "বাংলা"},
    {"code": "mr-IN", "label": "मराठी"},
    {"code": "kn-IN", "label": "ಕನ್ನಡ"},
    {"code": "ml-IN", "label": "മലയാളം"},
    {"code": "gu-IN", "label": "ગુજરાતી"},
]

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
       "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; media-src 'self' blob:; "
       "connect-src 'self'; manifest-src 'self'; worker-src 'self'; base-uri 'none'; form-action 'none'")


@app.middleware("http")
async def headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("Permissions-Policy", "microphone=(self), camera=(), geolocation=()")
    if resp.headers.get("content-type", "").startswith("text/html"):
        resp.headers.setdefault("Content-Security-Policy", CSP)
    return resp


# ---------------------------------------------------------------- helpers
class TurnIn(BaseModel):
    text: str
    session_id: str | None = None
    lang: str | None = None
    mode: str = "advice"
    input_mode: str = "text"
    state: dict | None = None   # {"case_file": {...}, "history": [...], "lang": "..."} from the browser


class TTSIn(BaseModel):
    text: str
    lang: str = "en-IN"


class FeedbackIn(BaseModel):
    message_id: str
    rating: str                  # "up" | "down"
    reason: str | None = None
    category: str | None = None
    action: str | None = None
    verifier_status: str | None = None
    citations: list[str] = []
    reply_lang: str | None = None
    share_text: bool = False
    question: str | None = None
    answer: str | None = None


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    return (fwd.split(",")[0].strip() if fwd else "") or (request.client.host if request.client else "unknown")


def _limit(request: Request, kind: str) -> None:
    n, window = LIMITS[kind]
    key, now = (_client_ip(request), kind), time.time()
    with _hits_lock:
        dq = _hits[key]
        while dq and dq[0] < now - window:
            dq.popleft()
        if len(dq) >= n:
            wait = int(dq[0] + window - now) + 1
            raise HTTPException(429, f"Too many requests from this device. Please wait about {max(1, wait // 60)} "
                                     f"minute(s) and try again.")
        dq.append(now)


def _session(t: TurnIn) -> pipeline.Session:
    sid = t.session_id or uuid.uuid4().hex[:12]
    s = _sessions.get(sid)
    if s is None:
        s = pipeline.new_session(t.lang or None)
        s.id = sid
        st = t.state or {}
        if isinstance(st.get("case_file"), dict):
            s.case_file = dict(st["case_file"])
        if isinstance(st.get("history"), list):
            s.history = [h for h in st["history"] if isinstance(h, dict) and "role" in h and "text" in h][-40:]
        if st.get("lang"):
            s.lang = st["lang"]
        _sessions[sid] = s
        while len(_sessions) > MAX_SESSIONS:
            _sessions.popitem(last=False)
    else:
        _sessions.move_to_end(sid)
    s.mode = t.mode if t.mode in ("advice", "draft", "practice") else "advice"
    return s


def _chunk_card(c: dict) -> dict:
    return {k: c.get(k) for k in ("id", "doc_title", "unit", "unit_number", "source_url", "status", "verified",
                                  "fetched_on", "source_type", "status_note", "doc_type", "category")}


def _validate(t: TurnIn) -> str:
    text = (t.text or "").strip()
    if not text:
        raise HTTPException(400, "Type or say what happened first.")
    if len(text) > 4000:
        raise HTTPException(400, "That message is very long. Please keep it under 4,000 characters.")
    return text


MAX_QUEUE = int(os.environ.get("HAQ_MAX_QUEUE", 4))   # turns waiting behind the one running; more → 503 "busy"
_waiting = 0
_waiting_lock = threading.Lock()


def _run_turn(t: TurnIn, text: str) -> dict:
    global _waiting
    with _waiting_lock:
        if _turn_lock.locked() and _waiting >= MAX_QUEUE:
            raise HTTPException(503, "Haq is busy answering other people right now. Please try again in a minute.")
        _waiting += 1
    try:
        _turn_lock.acquire()
    finally:
        with _waiting_lock:
            _waiting -= 1
    try:
        s = _session(t)
        t0 = time.time()
        r = pipeline.handle_turn(s, text, input_mode=t.input_mode, lang_hint=t.lang or None)
        took = round(time.time() - t0, 2)
    finally:
        _turn_lock.release()
    by_id = {c["id"]: c for c in retrieval.get_index()["chunks"]}
    res = dataclasses.asdict(r)
    res["trace"] = json.loads(json.dumps(r.trace, default=str))
    return {
        "session_id": s.id,
        "result": res,
        "sources": {cid: _chunk_card(by_id[cid]) for cid in r.citations if cid in by_id},
        "state": {"case_file": s.case_file, "history": s.history[-40:], "lang": s.lang},
        "missing_facts": (r.trace.get("router") or {}).get("missing_facts") or [],
        "seconds": took,
    }


# ---------------------------------------------------------------- pages
@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(WEB / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return FileResponse(WEB / "sw.js", media_type="text/javascript", headers={"Cache-Control": "no-cache"})


# ---------------------------------------------------------------- API
@app.get("/api/health")
def health():
    return {"ok": True, "mock": is_mock()}


@app.get("/api/meta")
def meta():
    idx = retrieval.get_index()
    cfg = load_config()
    return {"languages": LANGUAGES, "mock": is_mock(), "sample_data": bool(idx.get("has_sample")),
            "chunks": len(idx.get("chunks", [])), "covered_states": cfg.get("covered_states", []),
            "categories": ["consumer", "wages", "tenancy"]}


@app.post("/api/turn")
def turn(t: TurnIn, request: Request):
    text = _validate(t)
    _limit(request, "turn")
    return _run_turn(t, text)


@app.post("/api/turn/stream")
def turn_stream(t: TurnIn, request: Request):
    """Same as /api/turn, but streams each pipeline stage as it starts (Server-Sent Events)."""
    text = _validate(t)
    _limit(request, "turn")
    q: queue.Queue = queue.Queue()

    def work():
        token = pipeline.progress_cb.set(lambda stage: q.put(("stage", {"stage": stage})))
        try:
            if _turn_lock.locked():
                q.put(("stage", {"stage": "waiting"}))
            q.put(("result", _run_turn(t, text)))
        except HTTPException as e:       # e.g. the busy queue: show its plain message, not a crash
            q.put(("error", {"error": str(e.detail)}))
        except Exception as e:  # handle_turn already degrades honestly; this is a last resort
            q.put(("error", {"error": f"The legal engine stopped unexpectedly ({type(e).__name__})."}))
        finally:
            pipeline.progress_cb.reset(token)
            q.put(None)

    threading.Thread(target=work, daemon=True).start()

    def events():
        yield ": stream open\n\n"
        while True:
            try:
                item = q.get(timeout=15)
            except queue.Empty:
                yield ": keep-alive\n\n"      # stops proxies from closing a slow turn
                continue
            if item is None:
                return
            kind, data = item
            yield f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/stt")
async def stt(request: Request, audio: UploadFile = File(...), lang: str = Form("")):
    _limit(request, "voice")
    data = await audio.read()
    if not data:
        raise HTTPException(400, "The recording was empty. Hold the mic button a little longer.")
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(400, "The recording is too long. Please keep it under two minutes.")
    try:
        heard = voice.stt(data, lang or None)
    except voice.VoiceError as e:
        return JSONResponse({"error": "I could not understand the recording. Try again closer to the mic, "
                                      "or type your problem.", "detail": str(e)}, status_code=422)
    return heard


@app.post("/api/tts")
def tts(t: TTSIn, request: Request):
    _limit(request, "voice")
    try:
        out = voice.tts(t.text, t.lang or "en-IN")
    except voice.VoiceError as e:
        return JSONResponse({"error": "This answer could not be read aloud right now.", "detail": str(e)},
                            status_code=503)
    return Response(out["audio"], media_type="audio/wav",
                    headers={"X-Voice-Provider": f"{out['provider']}:{out['model']}",
                             "X-Voice-Truncated": "1" if out["truncated"] else "0",
                             "Cache-Control": "no-store"})


@app.post("/api/feedback")
def feedback(f: FeedbackIn, request: Request):
    _limit(request, "feedback")
    if f.rating not in ("up", "down"):
        raise HTTPException(400, "rating must be 'up' or 'down'")
    rec = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "message_id": f.message_id[:40],
           "rating": f.rating, "reason": (f.reason or "")[:500], "category": f.category, "action": f.action,
           "verifier_status": f.verifier_status, "citations": f.citations[:12], "reply_lang": f.reply_lang,
           "shared": f.share_text}
    if f.share_text:
        rec["question"] = (f.question or "")[:4000]
        rec["answer"] = (f.answer or "")[:8000]
    try:
        FEEDBACK.parent.mkdir(parents=True, exist_ok=True)
        with _hits_lock, open(FEEDBACK, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        return JSONResponse({"ok": False, "error": "Feedback could not be saved right now."}, status_code=503)
    return {"ok": True}


@app.get("/api/stats")
def stats():
    """Operational view: today's model usage against free-tier budgets, plus feedback counts."""
    llm._sync()
    budgets = {}
    for role, chain in (load_config().get("models") or {}).items():
        for e in (chain if isinstance(chain, list) else [chain]):
            k = llm._mkey(e)
            budgets[k] = {"used_today": int(llm._state.get("count", {}).get(k, 0)), "daily_budget": e.get("rpd"),
                          "exhausted": k in llm._state.get("exhausted", {})}
    up = down = 0
    try:
        for line in FEEDBACK.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            up += r.get("rating") == "up"
            down += r.get("rating") == "down"
    except (OSError, ValueError):
        pass
    return {"quota_day": llm._state.get("day"), "models": budgets, "feedback": {"up": up, "down": down},
            "active_sessions": len(_sessions)}
