"""Voice in and out, free Google models first, paid Sarvam last.

stt(audio_bytes, lang_hint=None) -> {"text", "language", "provider", "model", "pieces", "errors"}
tts(text, lang)                  -> {"audio": wav bytes, "provider", "model", "chars", "truncated", "errors"}

Both walk an ordered chain from config.yaml (`voice.stt_chain`, `voice.tts_chain`). Each entry is
{provider: gemini|sarvam, model: ..., [rpm/rpd/voice]}. The first entry that works wins; any error
(429, quota, 5xx, unknown model, bad key, empty result) moves to the next. Default order:
  STT: Gemini transcription / Flash-Lite audio input (free tier), then Sarvam saaras (paid credits)
  TTS: Gemini TTS models (free tier), then Sarvam bulbul (paid credits)
Gemini calls go through app/llm.py's paced client, so they share its per-model budgets.

Gemini takes a whole recording in one request. Sarvam's REST STT handles ~30 s, so for Sarvam
recordings are split into ~28 s pieces. Gemini TTS returns raw 24 kHz 16-bit mono PCM, which is
wrapped into WAV here. Replies are cleaned for speaking (no source lines or URLs, amounts with
Indian commas, helplines read digit by digit), split at sentence ends, and the pieces joined.
Only the first `voice.tts_max_chars` characters are spoken; the full answer stays on screen.

Sarvam's docs differ between pages on the TTS language field ("language_code" in the current
reference, "target_language_code" in older guides), so a 400/422 naming it is retried once
with the other name.
"""
import base64
import io
import os
import re
import wave

import requests

from . import llm
from .config import load_config

SARVAM = "https://api.sarvam.ai"
SUPPORTED = {"en-IN", "hi-IN", "bn-IN", "gu-IN", "kn-IN", "ml-IN", "mr-IN", "od-IN", "pa-IN", "ta-IN", "te-IN"}

DEFAULT_STT = [{"provider": "gemini", "model": "gemini-3.1-flash-lite"},
               {"provider": "sarvam", "model": "saaras:v3"}]
DEFAULT_TTS = [{"provider": "gemini", "model": "gemini-2.5-flash-preview-tts", "voice": "Kore"},
               {"provider": "sarvam", "model": "bulbul:v3"}]


class VoiceError(Exception):
    pass


def _vcfg() -> dict:
    v = load_config().get("voice", {}) or {}
    return {
        "stt_chain": [e for e in (v.get("stt_chain") or DEFAULT_STT) if isinstance(e, dict) and e.get("model")],
        "tts_chain": [e for e in (v.get("tts_chain") or DEFAULT_TTS) if isinstance(e, dict) and e.get("model")],
        "tts_chunk_chars": int(v.get("tts_chunk_chars", 1400)),
        "tts_max_chars": int(v.get("tts_max_chars", 1800)),
        "max_piece_s": float(v.get("max_piece_s", 28)),
        "sarvam_speaker": v.get("sarvam_speaker"),
    }


def _sarvam_key() -> str:
    k = os.environ.get("SARVAM_API_KEY", "").strip()
    if not k:
        raise VoiceError("missing SARVAM_API_KEY")
    return k


# ---------------------------------------------------------------- WAV helpers
def split_wav(data: bytes, max_s: float) -> list[bytes]:
    """Split a PCM WAV into pieces of at most max_s seconds. Non-WAV input is returned whole."""
    try:
        with wave.open(io.BytesIO(data), "rb") as w:
            params, rate, n = w.getparams(), w.getframerate(), w.getnframes()
            frames = w.readframes(n)
    except (wave.Error, EOFError):
        return [data]
    width = params.sampwidth * params.nchannels
    step = int(max_s * rate) * width
    if len(frames) <= step:
        return [data]
    out = []
    for i in range(0, len(frames), step):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as o:
            o.setparams(params)
            o.writeframes(frames[i:i + step])
        out.append(buf.getvalue())
    return out


def join_wavs(pieces: list[bytes]) -> bytes:
    if len(pieces) == 1:
        return pieces[0]
    frames, params = [], None
    for p in pieces:
        with wave.open(io.BytesIO(p), "rb") as w:
            if params is None:
                params = w.getparams()
            elif (w.getframerate(), w.getsampwidth(), w.getnchannels()) != \
                    (params.framerate, params.sampwidth, params.nchannels):
                raise VoiceError("TTS pieces have different audio formats")
            frames.append(w.readframes(w.getnframes()))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as o:
        o.setparams(params)
        o.writeframes(b"".join(frames))
    return buf.getvalue()


def pcm_to_wav(pcm: bytes, rate: int = 24000, channels: int = 1, width: int = 2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as o:
        o.setnchannels(channels)
        o.setsampwidth(width)
        o.setframerate(rate)
        o.writeframes(pcm)
    return buf.getvalue()


def wav_seconds(data: bytes) -> float | None:
    try:
        with wave.open(io.BytesIO(data), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except (wave.Error, EOFError, ZeroDivisionError):
        return None


# ---------------------------------------------------------------- text helpers
def _indian_commas(digits: str) -> str:
    if len(digits) <= 3:
        return digits
    head, last3 = digits[:-3], digits[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join(groups + [last3])


_AMOUNT = re.compile(r"(₹|Rs\.?|INR)\s?(\d{5,})(?!\d)|(?<![\d,])(\d{5,})(\s?(?:rupees|rupee|रुपये|रुपए|रुपया|/-))", re.I)


def speakable(text: str) -> str:
    """Clean a reply for TTS: no source lines, URLs or markdown; amounts with commas;
    other long numbers (helplines) spaced digit by digit."""
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or re.match(r"^(Source|स्रोत)\s*:", s):
            continue
        s = re.sub(r"\((?:Source|स्रोत)\s*:[^)]*\)", "", s)
        s = re.sub(r"https?://\S+", "", s)
        s = re.sub(r"[*_`#>|\[\]]", "", s)
        s = re.sub(r"^\s*[-•]\s*", "", s)
        lines.append(s)
    t = "\n".join(lines)

    def amt(m):
        if m.group(2):
            return f"{m.group(1)} {_indian_commas(m.group(2))}"
        return f"{_indian_commas(m.group(3))}{m.group(4)}"

    t = _AMOUNT.sub(amt, t)
    t = re.sub(r"(?<![\d,])(\d{5,})(?![\d,])", lambda m: " ".join(m.group(1)), t)
    return re.sub(r"[ \t]+", " ", t).strip()


def chunk_text(text: str, limit: int) -> list[str]:
    """Split at sentence ends (. ? ! ।) or newlines into pieces of at most `limit` chars."""
    parts = [p.strip() for p in re.split(r"(?<=[.?!।])\s+|\n+", text) if p.strip()]
    out, cur = [], ""
    for p in parts:
        while len(p) > limit:          # a single over-long sentence: hard split at a space
            cut = p.rfind(" ", 0, limit)
            cut = cut if cut > limit // 2 else limit
            if cur:
                out.append(cur)
                cur = ""
            out.append(p[:cut].strip())
            p = p[cut:].strip()
        if cur and len(cur) + 1 + len(p) > limit:
            out.append(cur)
            cur = p
        else:
            cur = f"{cur} {p}".strip()
    if cur:
        out.append(cur)
    return out


def _norm_lang(code: str | None) -> str | None:
    if not code:
        return None
    c = str(code).strip()
    if c.lower() in ("unknown", "none", "null"):
        return None
    if len(c) == 2:
        c = f"{c.lower()}-IN"
    return c


# ---------------------------------------------------------------- Gemini (free tier)
def _gemini_call(entry: dict, payload: dict, est_tokens: int) -> dict:
    e = {"provider": "gemini", **entry}
    name = llm._resolve_gemini_name(e["model"])
    try:
        code, data = llm._send(e, f"{llm.GEMINI_BASE}/models/{name}:generateContent",
                               {"x-goog-api-key": llm._key("GEMINI_API_KEY")}, payload, est_tokens)
    except llm._Skip as s:
        if s.cooldown_s:
            llm._cool[llm._mkey(e)] = llm.time.time() + s.cooldown_s
        raise VoiceError(s.reason)
    except llm.LLMError as ex:
        raise VoiceError(str(ex))
    if code != 200:
        raise VoiceError(f"HTTP {code}: {str(data)[:160]}")
    return data


def _parts(data: dict) -> list[dict]:
    try:
        return data["candidates"][0]["content"]["parts"] or []
    except (KeyError, IndexError, TypeError):
        reason = (data.get("promptFeedback") or {}).get("blockReason") if isinstance(data, dict) else None
        raise VoiceError(f"empty or blocked response{f' ({reason})' if reason else ''}")


_STT_PROMPT = ("Transcribe this audio exactly as spoken. The speaker is in India and may use Hindi, English or "
               "Hinglish. Write Hindi words in Devanagari and English words in Latin script. Do not translate, "
               "summarise or answer the question. "
               'Return ONLY JSON: {"transcript": "...", "language_code": "hi-IN" or "en-IN" or another BCP-47 code}')


def _mime(audio: bytes) -> str:
    if audio[:4] == b"RIFF":
        return "audio/wav"
    if audio[:3] == b"ID3" or audio[:2] in (b"\xff\xfb", b"\xff\xf3"):
        return "audio/mp3"
    if audio[:4] == b"OggS":
        return "audio/ogg"
    if audio[4:8] == b"ftyp":
        return "audio/mp4"
    if audio[:4] == b"\x1aE\xdf\xa3":
        return "audio/webm"
    return "audio/wav"


def _stt_gemini(entry: dict, audio: bytes, lang_hint: str | None) -> tuple[str, str | None, int]:
    payload = {"contents": [{"role": "user", "parts": [
        {"inline_data": {"mime_type": _mime(audio), "data": base64.b64encode(audio).decode()}},
        {"text": _STT_PROMPT}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    secs = wav_seconds(audio) or 60
    data = _gemini_call(entry, payload, int(secs * 32) + 300)   # ~32 audio tokens per second
    text = "".join(p.get("text", "") for p in _parts(data) if not p.get("thought")).strip()
    if not text:
        raise VoiceError("empty transcription")
    try:
        j = llm.parse_json(text)
        return str(j.get("transcript", "")).strip(), _norm_lang(j.get("language_code")) or lang_hint, 1
    except (ValueError, AttributeError):
        return text, lang_hint, 1


def _tts_gemini(entry: dict, text: str, lang: str) -> bytes:
    payload = {"contents": [{"parts": [{"text": text}]}],
               "generationConfig": {"responseModalities": ["AUDIO"],
                                    "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {
                                        "voiceName": entry.get("voice", "Kore")}}}}}
    data = _gemini_call(entry, payload, int(len(text) / 2.5) + 50)
    for p in _parts(data):
        inline = p.get("inlineData") or p.get("inline_data")
        if inline and inline.get("data"):
            mime = inline.get("mimeType") or inline.get("mime_type") or ""
            raw = base64.b64decode(inline["data"])
            if raw[:4] == b"RIFF":
                return raw
            m = re.search(r"rate=(\d+)", mime)
            return pcm_to_wav(raw, int(m.group(1)) if m else 24000)
    raise VoiceError("no audio in Gemini TTS response")


# ---------------------------------------------------------------- Sarvam (paid credits)
def _sarvam_post(path: str, **kw) -> requests.Response:
    last = None
    for _ in range(2):
        try:
            r = requests.post(f"{SARVAM}{path}", headers={"api-subscription-key": _sarvam_key()},
                              timeout=90, **kw)
        except requests.RequestException as ex:
            last = VoiceError(f"network error ({type(ex).__name__})")
            llm.time.sleep(2)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            last = VoiceError(f"HTTP {r.status_code}")
            llm.time.sleep(3)
            continue
        if r.status_code in (401, 403):
            raise VoiceError(f"Sarvam HTTP {r.status_code}: key rejected")
        return r
    raise last or VoiceError("request failed")


def _stt_sarvam(entry: dict, audio: bytes, lang_hint: str | None) -> tuple[str, str | None, int]:
    pieces = split_wav(audio, _vcfg()["max_piece_s"])
    texts, lang = [], None
    for p in pieces:
        data = {"model": entry["model"], "language_code": lang_hint if lang_hint in SUPPORTED else "unknown"}
        if entry["model"].startswith("saaras:v3"):
            data["mode"] = "transcribe"
        r = _sarvam_post("/speech-to-text", files={"file": ("audio.wav", p, _mime(p))}, data=data)
        if r.status_code != 200:
            raise VoiceError(f"HTTP {r.status_code}: {r.text[:160]}")
        j = r.json()
        texts.append((j.get("transcript") or "").strip())
        lang = lang or _norm_lang(j.get("language_code"))
    return " ".join(t for t in texts if t).strip(), lang or lang_hint, len(pieces)


def _tts_sarvam(entry: dict, text: str, lang: str) -> bytes:
    speaker = entry.get("speaker") or _vcfg()["sarvam_speaker"]
    for field in ("language_code", "target_language_code"):
        body = {"text": text, field: lang, "model": entry["model"]}
        if speaker:
            body["speaker"] = speaker
        r = _sarvam_post("/text-to-speech", json=body)
        if r.status_code in (400, 422) and field == "language_code" and \
                re.search(r"language_code|field required|extra", r.text, re.I):
            continue                                   # older API spelling
        if r.status_code != 200:
            raise VoiceError(f"HTTP {r.status_code}: {r.text[:160]}")
        audios = r.json().get("audios") or []
        if not audios:
            raise VoiceError("no audio in TTS response")
        return join_wavs([base64.b64decode(a) for a in audios])
    raise VoiceError("TTS request rejected with both language field names")


_STT = {"gemini": _stt_gemini, "sarvam": _stt_sarvam}
_TTS = {"gemini": _tts_gemini, "sarvam": _tts_sarvam}


# ---------------------------------------------------------------- public API
def _ordered(chain: list[dict], prefer: str | None, fallback: bool = True) -> list[dict]:
    """The user's choice in Settings ("google" or "sarvam") goes first. With fallback off, ONLY that provider
    is used (no silent switch to a paid one); with it on, the other provider is tried if the chosen one fails."""
    want = {"google": "gemini", "gemini": "gemini", "sarvam": "sarvam"}.get((prefer or "").lower())
    if not want:
        return chain
    mine = [e for e in chain if e.get("provider", "gemini") == want]
    return mine + ([e for e in chain if e.get("provider", "gemini") != want] if fallback else [])


def stt(audio: bytes, lang_hint: str | None = None, prefer: str | None = None, fallback: bool = True) -> dict:
    """Transcribe a recording. Raises VoiceError only if every model in the chain fails."""
    if not audio:
        raise VoiceError("empty recording")
    errors: list[str] = []
    for e in _ordered(_vcfg()["stt_chain"], prefer, fallback):
        prov = e.get("provider", "gemini")
        fn = _STT.get(prov)
        tag = f"{prov}:{e['model']}"
        if fn is None:
            errors.append(f"{tag}: unknown provider")
            continue
        try:
            text, lang, pieces = fn(e, audio, lang_hint)
            if not text:
                raise VoiceError("empty transcript (silence or unclear audio)")
            return {"text": text, "language": lang or lang_hint, "provider": prov, "model": e["model"],
                    "pieces": pieces, "errors": errors}
        except (VoiceError, ValueError, KeyError) as ex:
            errors.append(f"{tag}: {ex}")
    raise VoiceError("could not transcribe: " + "; ".join(errors[-4:]))


def tts(text: str, lang: str, prefer: str | None = None, fallback: bool = True) -> dict:
    """Speak a reply. Raises VoiceError if every model in the chain fails."""
    cfg = _vcfg()
    lang = lang if lang in SUPPORTED else "en-IN"
    clean = speakable(text)
    truncated = len(clean) > cfg["tts_max_chars"]
    if truncated:
        cut = max(clean.rfind(".", 0, cfg["tts_max_chars"]), clean.rfind("।", 0, cfg["tts_max_chars"]))
        clean = clean[:cut + 1 if cut > 200 else cfg["tts_max_chars"]]
    if not clean:
        raise VoiceError("nothing to speak")
    errors: list[str] = []
    for e in _ordered(cfg["tts_chain"], prefer, fallback):
        prov = e.get("provider", "gemini")
        fn = _TTS.get(prov)
        tag = f"{prov}:{e['model']}"
        if fn is None:
            errors.append(f"{tag}: unknown provider")
            continue
        limit = min(cfg["tts_chunk_chars"], 1450 if e["model"].startswith("bulbul:v2") else 2400)
        try:
            pieces = [fn(e, c, lang) for c in chunk_text(clean, limit)]
            return {"audio": join_wavs(pieces), "provider": prov, "model": e["model"],
                    "chars": len(clean), "truncated": truncated, "errors": errors}
        except (VoiceError, ValueError, KeyError) as ex:
            errors.append(f"{tag}: {ex}")
    raise VoiceError("TTS failed: " + "; ".join(errors[-4:]))
