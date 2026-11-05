"""Offline self-check of app/voice.py (no network, no keys, no credits used).

  python -m app.selfcheck_voice

Fakes Gemini and Sarvam answers and checks: Google models are tried first; Sarvam is used only
when every Google model fails; long recordings are split only for Sarvam; Gemini PCM is wrapped
into playable WAV; reply text is cleaned for speaking.
"""
import base64
import io
import json
import os
import tempfile
import wave
from pathlib import Path

import requests

from . import llm, voice


def _wav(seconds: float, rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(seconds * rate))
    return buf.getvalue()


class _R:
    def __init__(self, code, body):
        self.status_code = code
        self.text = body if isinstance(body, str) else json.dumps(body)
        self._b = body

    def json(self):
        return self._b if isinstance(self._b, dict) else json.loads(self._b)


def main() -> None:
    os.environ.setdefault("SARVAM_API_KEY", "selfcheck-not-real")
    os.environ.setdefault("GEMINI_API_KEY", "selfcheck-not-real")
    tmp = Path(tempfile.mkdtemp())
    llm._state_path = lambda: tmp / "quota_state.json"
    llm._available_names = set()
    llm.time.sleep = lambda s: None
    cfg = {"stt_chain": [{"provider": "gemini", "model": "g-transcribe"},
                         {"provider": "gemini", "model": "g-lite"},
                         {"provider": "sarvam", "model": "saaras:v3"}],
           "tts_chain": [{"provider": "gemini", "model": "g-tts", "voice": "Kore"},
                         {"provider": "sarvam", "model": "bulbul:v3"},
                         {"provider": "sarvam", "model": "bulbul:v2"}],
           "tts_chunk_chars": 1400, "tts_max_chars": 1800, "max_piece_s": 28, "sarvam_speaker": None}
    voice._vcfg = lambda: cfg
    sc = {"g_stt": "ok", "g_tts": "ok", "s_tts": "field"}
    calls = []
    pcm_1s = b"\x00\x00" * 24000

    def fake_post(url, headers=None, json=None, files=None, data=None, timeout=None):
        calls.append(url)
        if "generateContent" in url:
            model = url.split("/models/")[1].split(":")[0]
            if "responseModalities" in json.get("generationConfig", {}):           # Gemini TTS
                if sc["g_tts"] == "fail":
                    return _R(429, '{"error":{"message":"Quota exceeded: GenerateRequestsPerDayPerProjectPerModel"}}')
                return _R(200, {"candidates": [{"content": {"parts": [{"inlineData": {
                    "mimeType": "audio/L16;codec=pcm;rate=24000", "data": base64.b64encode(pcm_1s).decode()}}]}}]})
            assert "inline_data" in json["contents"][0]["parts"][0]                   # Gemini STT
            if sc["g_stt"] == "fail" or (sc["g_stt"] == "first_fails" and model == "g-transcribe"):
                return _R(404, '{"error":{"message":"model not found"}}')
            return _R(200, {"candidates": [{"content": {"parts": [
                {"text": '{"transcript": "मेरा डिपॉज़िट वापस नहीं मिला", "language_code": "hi-IN"}'}]}}]})
        if url.endswith("/speech-to-text"):
            return _R(200, {"request_id": "x", "transcript": "sarvam text", "language_code": "hi-IN"})
        if url.endswith("/text-to-speech"):
            if sc["s_tts"] == "field" and "language_code" in json:
                return _R(422, '{"error":"target_language_code: field required"}')
            if sc["s_tts"] == "v3down" and json["model"] == "bulbul:v3":
                return _R(500, "boom")
            return _R(200, {"request_id": "y", "audios": [base64.b64encode(_wav(1.5, 22050)).decode()]})
        return _R(404, "unknown")

    requests.post = fake_post
    checks = []

    def check(name, cond):
        checks.append((name, bool(cond)))

    s = voice.speakable("You may claim ₹30000 or 200000 rupees.\nCall 15100 (Source: https://nalsa.gov.in/contact-us/)\n"
                        "Source: UP Tenancy Act, 2021, section 11\n- keep receipts")
    check("amounts get Indian commas", "₹ 30,000" in s and "2,00,000 rupees" in s)
    check("helpline read digit by digit", "1 5 1 0 0" in s)
    check("source notes and URLs dropped", "Source" not in s and "http" not in s and "keep receipts" in s)
    ch = voice.chunk_text("यह एक वाक्य है। " * 400, 1400)
    check("chunks respect the char limit", len(ch) > 1 and all(len(c) <= 1400 for c in ch))
    pieces = voice.split_wav(_wav(70), 28)
    check("70 s recording splits into 3 (Sarvam only)", len(pieces) == 3)
    check("pieces rejoin to the same length", abs(voice.wav_seconds(voice.join_wavs(pieces)) - 70) < 0.01)

    calls.clear()
    r = voice.stt(_wav(70), "hi-IN")
    check("STT: Google first, whole recording in 1 call", r["provider"] == "gemini" and r["model"] == "g-transcribe"
          and r["pieces"] == 1 and len(calls) == 1)
    check("STT: Hindi transcript + language", "डिपॉज़िट" in r["text"] and r["language"] == "hi-IN")
    check("STT: Sarvam not called while Google works", not any(u.endswith("/speech-to-text") for u in calls))

    sc["g_stt"] = "first_fails"
    r = voice.stt(_wav(5))
    check("STT: transcribe model missing -> Flash-Lite", r["provider"] == "gemini" and r["model"] == "g-lite")

    sc["g_stt"] = "fail"
    llm._unavailable.clear()
    calls.clear()
    r = voice.stt(_wav(70), "hi-IN")
    check("STT: all Google fail -> Sarvam (paid backup)", r["provider"] == "sarvam" and r["pieces"] == 3)

    calls.clear()
    t = voice.tts("आपका डिपॉज़िट 30000 रुपये है। " * 3, "hi-IN")
    check("TTS: Google first, PCM wrapped as WAV", t["provider"] == "gemini" and
          abs(voice.wav_seconds(t["audio"]) - 1.0) < 0.01)
    check("TTS: Sarvam not called while Google works", not any(u.endswith("/text-to-speech") for u in calls))

    sc["g_tts"] = "fail"
    t = voice.tts("Your deposit must be refunded.", "en-IN")
    check("TTS: Google quota out -> Sarvam, field retry", t["provider"] == "sarvam" and t["model"] == "bulbul:v3")
    sc["s_tts"] = "v3down"
    t = voice.tts("Your deposit must be refunded.", "en-IN")
    check("TTS: bulbul:v3 down -> bulbul:v2", t["model"] == "bulbul:v2")
    t = voice.tts("Sentence one is here. " * 200, "en-IN")
    check("TTS: long reply truncated for speaking", t["truncated"] and t["chars"] <= 1800)

    width = max(len(n) for n, _ in checks)
    for n, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {n.ljust(width)}")
    failed = [n for n, ok in checks if not ok]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
