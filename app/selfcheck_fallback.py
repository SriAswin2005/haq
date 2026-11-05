"""Offline self-check of the model fallback logic (no network, no keys, no quota).

  python -m app.selfcheck_fallback

Fakes Gemini HTTP answers (per-minute 429, per-day 429, 400 JSON-mode rejection, 5xx)
and checks the client switches models correctly, folds prompts for Gemma, persists the
daily budget and fails honestly when the whole chain is exhausted.
"""
import json
import os
import tempfile
from pathlib import Path

from . import llm


class _Resp:
    def __init__(self, code, body):
        self.status_code = code
        self._body = body
        self.text = body if isinstance(body, str) else json.dumps(body)

    def json(self):
        return self._body if isinstance(self._body, dict) else json.loads(self._body)


def _ok(text):
    return _Resp(200, {"candidates": [{"content": {"parts": [{"text": text}]}}],
                       "usageMetadata": {"promptTokenCount": 42}})


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    os.environ.setdefault("GEMINI_API_KEY", "selfcheck-not-a-real-key")
    cfg = {
        "models": {
            "main": [
                {"provider": "gemini", "model": "m-minute", "rpm": 15, "rpd": 500},
                {"provider": "gemini", "model": "m-day", "rpm": 15, "rpd": 500},
                {"provider": "gemini", "model": "gemma-test", "rpm": 30, "tpm": 16000, "rpd": 14400},
            ],
            "router": [{"provider": "gemini", "model": "m-nojson", "rpm": 15}],
            "judge": [{"provider": "gemini", "model": "m-5xx"}, {"provider": "gemini", "model": "m-tiny", "rpd": 1}],
        },
        "llm": {"max_wait_s": 1, "max_total_wait_s": 30, "min_interval_s": 0},
        "embeddings": {"provider": "gemini", "model": "e"},
    }
    llm.load_config = lambda *a, **k: cfg
    llm.is_mock = lambda: False
    llm._state_path = lambda: tmp / "quota_state.json"
    llm._available_names = set()
    clock = [1_000_000.0]                    # fake clock: sleeps advance it, so the check is instant

    def _sleep(s):
        clock[0] += max(0.0, s)

    llm.time.time = lambda: clock[0]
    llm.time.sleep = _sleep
    sent = []

    def fake_post(url, headers=None, json=None, timeout=None):
        model = url.split("/models/")[1].split(":")[0]
        sent.append((model, json))
        if model == "m-minute":
            return _Resp(429, '{"error":{"message":"Quota exceeded: GenerateRequestsPerMinutePerProjectPerModel",'
                              '"details":[{"retryDelay":"23s"}]}}')
        if model == "m-day":
            return _Resp(429, '{"error":{"message":"Quota exceeded: GenerateRequestsPerDayPerProjectPerModel-FreeTier"}}')
        if model == "m-nojson":
            if "responseMimeType" in json["generationConfig"]:
                return _Resp(400, '{"error":{"message":"JSON mode is not enabled for this model"}}')
            return _ok('{"category": "tenancy"}')
        if model == "m-5xx":
            return _Resp(503, "overloaded")
        return _ok('{"answer": "from ' + model + '"}')

    llm.requests.post = fake_post
    checks = []

    def check(name, cond):
        checks.append((name, bool(cond)))

    # 1. per-minute 429 -> next; per-day 429 -> next; Gemma serves
    llm.reset_stats()
    out = llm.generate([{"role": "system", "content": "SYS"}, {"role": "user", "content": "hi"}],
                       role="main", json_schema={"type": "object"})
    check("main falls through to Gemma", "gemma-test" in out)
    g = [p for m, p in sent if m == "gemma-test"][-1]
    check("Gemma: no systemInstruction", "systemInstruction" not in g)
    check("Gemma: no JSON mode", "responseMimeType" not in g["generationConfig"])
    check("Gemma: system folded into user turn", g["contents"][0]["parts"][0]["text"].startswith("SYS"))
    reasons = [f["reason"] for f in llm.snapshot_stats()["fallbacks"]]
    check("trace records 429 rate limit", any("429 rate limit" in r for r in reasons))
    check("trace records daily quota", any("daily quota" in r for r in reasons))
    check("cooldown taken from retryDelay", llm._cool.get("gemini:m-minute", 0) > llm.time.time() + 20)

    # 2. daily-exhausted model is not even called on the next turn
    n_day = sum(1 for m, _ in sent if m == "m-day")
    llm.generate([{"role": "user", "content": "again"}], role="main")
    check("exhausted model skipped without a request", sum(1 for m, _ in sent if m == "m-day") == n_day)
    st = json.loads((tmp / "quota_state.json").read_text())
    check("daily state persisted to disk", "gemini:m-day" in st["exhausted"] and st["count"].get("gemini:gemma-test", 0) >= 2)

    # 3. model that rejects JSON mode is retried once without it, and remembered
    out = llm.generate([{"role": "user", "content": "route"}], role="router", json_schema={"type": "object"})
    check("400 JSON-mode -> retried without it", "tenancy" in out)
    before = sum(1 for m, _ in sent if m == "m-nojson")
    llm.generate([{"role": "user", "content": "route2"}], role="router", json_schema={"type": "object"})
    check("learned: no second 400 next time", sum(1 for m, _ in sent if m == "m-nojson") == before + 1)

    # 4. 5xx twice -> next model; local rpd budget respected; then honest failure
    out = llm.generate([{"role": "user", "content": "judge"}], role="judge")
    check("5xx -> next model", "m-tiny" in out)
    try:
        llm._cool.clear()
        llm.generate([{"role": "user", "content": "judge again"}], role="judge")
        check("whole chain exhausted raises LLMError", False)
    except llm.LLMError as ex:
        check("whole chain exhausted raises LLMError", "all models failed" in str(ex))

    width = max(len(n) for n, _ in checks)
    for n, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {n.ljust(width)}")
    failed = [n for n, ok in checks if not ok]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
