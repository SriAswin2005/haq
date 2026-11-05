"""Provider-swappable LLM + embedding client with per-role model fallback chains.

generate(messages, role, json_schema=None, temperature=0) -> str
embed(texts, task) -> np.ndarray (n, d), L2-normalised

Each role in config.yaml `models:` (router, main, judge) is an ORDERED LIST of models
(a single dict still works). For every call the client walks the chain and uses the
first model that is
  * available to this key (unknown / not-found models are skipped),
  * inside its own budget: `rpm`, `tpm` (input tokens), `rpd` from config,
  * not cooling down after a rate-limit (429) answer.
On a 429, daily-quota error, 5xx, timeout, unknown model or empty/blocked answer it
records the reason in the trace and moves to the next model straight away. It waits
only when every model is briefly busy, and gives up (LLMError -> the pipeline's
honest service-error message) only when the whole chain is exhausted.

Daily request counts persist in data/index/quota_state.json, so the UI, the CLI and
the eval harness share one budget. Gemini daily quotas reset at midnight Pacific.

Gemma models on the Gemini API reject system instructions and JSON mode, so for any
model whose name starts with "gemma" the system prompt is folded into the first user
turn and JSON is requested in words (callers parse tolerantly). Any model that
answers 400 to those features is remembered and retried once without them.

Embeddings deliberately have NO cross-model fallback: vectors from two embedding
models are not comparable, so a silent switch would corrupt retrieval. They are
paced to `embeddings.rpm` and retried with backoff instead.

Mock mode (config mock: true or AI_LAWYER_MOCK=1) uses app/llm_mock.py, no network.
"""
import json
import os
import re
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone

import numpy as np
import requests

from .config import load_config, is_mock, resolve

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


class LLMError(Exception):
    pass


class _Skip(Exception):
    """This model cannot serve the call right now; try the next one in the chain."""

    def __init__(self, reason: str, cooldown_s: float = 0.0):
        super().__init__(reason)
        self.reason = reason
        self.cooldown_s = cooldown_s


_lock = threading.RLock()
stats = {"calls": 0, "retries": 0, "latency_s": 0.0, "models": [], "fallbacks": []}

_state: dict = {}            # persisted: {"day", "count": {key: n}, "exhausted": {key: reason}}
_cool: dict = {}             # key -> unix time until which the model is skipped (429 per-minute)
_last: dict = {}             # key -> unix time of the last request sent
_tok: dict = {}              # key -> deque[(ts, input_tokens)] for the TPM window
_unavailable: dict = {}      # key -> reason (process lifetime: not found / not allowed)
_learned: dict = {}          # key -> {"no_system": bool, "no_json": bool}
_fail_streak: dict = {}      # key -> consecutive 5xx/network failures (escalates the cooldown)
_BACKOFF = (20.0, 120.0, 600.0)


def _server_cooldown(k: str) -> float:
    n = _fail_streak[k] = _fail_streak.get(k, 0) + 1
    return _BACKOFF[min(n, len(_BACKOFF)) - 1]
_available_names: set | None = None
_last_global = 0.0


def reset_stats() -> None:
    stats.update({"calls": 0, "retries": 0, "latency_s": 0.0, "models": [], "fallbacks": []})


def snapshot_stats() -> dict:
    return {"calls": stats["calls"], "retries": stats["retries"],
            "latency_s": round(stats["latency_s"], 2), "models": list(stats["models"]),
            "fallbacks": list(stats["fallbacks"])}


def _llm_cfg() -> dict:
    return load_config().get("llm", {}) or {}


def _key(env_name: str) -> str:
    v = os.environ.get(env_name, "").strip()
    if not v:
        raise LLMError(f"missing environment variable {env_name}")
    return v


# ---------------------------------------------------------------- quota state
def _quota_day() -> str:
    # Gemini daily quotas reset at midnight Pacific. Fixed UTC-8 avoids needing tzdata on Windows.
    return (datetime.now(timezone.utc) - timedelta(hours=8)).strftime("%Y-%m-%d")


def _state_path():
    return resolve("data/index/quota_state.json")


def _sync(increment: str | None = None, exhaust: tuple[str, str] | None = None) -> None:
    """Merge the on-disk budget with ours (max of counts), optionally bump/mark, write back."""
    with _lock:
        day = _quota_day()
        p = _state_path()
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        if d.get("day") != day:
            d = {"day": day, "count": {}, "exhausted": {}}
        d.setdefault("count", {})
        d.setdefault("exhausted", {})
        if _state.get("day") == day:
            for k, v in _state.get("count", {}).items():
                d["count"][k] = max(int(v), int(d["count"].get(k, 0)))
            d["exhausted"].update(_state.get("exhausted", {}))
        if increment:
            d["count"][increment] = int(d["count"].get(increment, 0)) + 1
        if exhaust:
            d["exhausted"][exhaust[0]] = exhaust[1]
        _state.clear()
        _state.update(d)
        if increment or exhaust:
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                tmp = p.with_suffix(".tmp")
                tmp.write_text(json.dumps(d, indent=1), encoding="utf-8")
                os.replace(tmp, p)
            except OSError:
                pass  # budget tracking is best effort; never break a user turn over it


# ---------------------------------------------------------------- chain + model names
def _chain(role: str) -> list[dict]:
    models = load_config().get("models", {}) or {}
    ch = models.get(role) or models.get("main") or []
    if isinstance(ch, dict):
        ch = [ch]
    return [e for e in ch if isinstance(e, dict) and e.get("model")]


def _mkey(e: dict) -> str:
    return f"{e.get('provider', 'gemini')}:{e['model']}"


def list_gemini_models(force: bool = False) -> list[dict]:
    """Models this key can call for generateContent / embedContent. Cached for 12 h."""
    cache = resolve("data/index/available_models.json")
    if not force:
        try:
            d = json.loads(cache.read_text(encoding="utf-8"))
            if time.time() - d.get("fetched_at", 0) < 12 * 3600:
                return d["models"]
        except Exception:
            pass
    out, token = [], None
    for _ in range(10):
        params = {"pageSize": 1000}
        if token:
            params["pageToken"] = token
        r = requests.get(f"{GEMINI_BASE}/models", params=params,
                         headers={"x-goog-api-key": _key("GEMINI_API_KEY")}, timeout=30)
        if r.status_code != 200:
            raise LLMError(f"model list failed: HTTP {r.status_code}: {r.text[:200]}")
        d = r.json()
        for m in d.get("models", []):
            out.append({"name": m.get("name", "").removeprefix("models/"),
                        "display": m.get("displayName", ""),
                        "methods": m.get("supportedGenerationMethods", [])})
        token = d.get("nextPageToken")
        if not token:
            break
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"fetched_at": time.time(), "models": out}, indent=1), encoding="utf-8")
    except OSError:
        pass
    return out


def _resolve_gemini_name(model: str) -> str:
    """Use the configured id if the key can see it; otherwise the closest id that starts
    with it (e.g. 'gemini-x-flash-lite' -> 'gemini-x-flash-lite-preview'). If the list
    cannot be fetched, the configured id is used as-is."""
    global _available_names
    if _available_names is None:
        try:
            _available_names = {m["name"] for m in list_gemini_models()}
        except Exception:
            _available_names = set()
    if not _available_names or model in _available_names:
        return model
    cands = sorted((n for n in _available_names if n.startswith(model + "-")), key=len)
    return cands[0] if cands else model


def _estimate_tokens(system: str, turns: list[dict]) -> int:
    chars = len(system) + sum(len(m["content"]) for m in turns)
    return int(chars / 2.5) + 50   # conservative: Devanagari tokenises heavier than English


# ---------------------------------------------------------------- budget pre-check
def _precheck(e: dict, est_tokens: int) -> float:
    """Raise _Skip if the model cannot be used today; else return seconds to wait first."""
    k = _mkey(e)
    now = time.time()
    if k in _unavailable:
        raise _Skip(f"unavailable ({_unavailable[k]})")
    if k in _state.get("exhausted", {}):
        raise _Skip("daily quota exhausted")
    rpd = e.get("rpd")
    if rpd and int(_state.get("count", {}).get(k, 0)) >= int(rpd):
        raise _Skip(f"local daily budget of {rpd} used")
    tpm = e.get("tpm")
    if tpm and est_tokens > int(tpm):
        raise _Skip(f"prompt ~{est_tokens} tokens is over its TPM {tpm}")
    wait = 0.0
    if _cool.get(k, 0) > now:
        wait = max(wait, _cool[k] - now)
    rpm = e.get("rpm")
    if rpm:
        wait = max(wait, _last.get(k, 0) + 60.0 / float(rpm) * 1.05 - now)
    if tpm:
        dq = _tok.setdefault(k, deque())
        while dq and dq[0][0] < now - 60:
            dq.popleft()
        used = sum(t for _, t in dq)
        if dq and used + est_tokens > int(tpm):
            wait = max(wait, dq[0][0] + 60.5 - now)
    return max(wait, 0.0)


# ---------------------------------------------------------------- one HTTP request
def _retry_delay(text: str) -> float | None:
    m = re.search(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"', text)
    return float(m.group(1)) if m else None


def _send(e: dict, url: str, headers: dict, payload: dict, est_tokens: int,
          timeout: int = 90) -> tuple[int, dict | str]:
    """Send one request for model entry e. Returns (200, json) or (400, text);
    raises _Skip for anything that means 'try another model'."""
    global _last_global
    k = _mkey(e)
    gap = float(_llm_cfg().get("min_interval_s", 0) or 0)
    for attempt in range(2):          # second attempt only for 5xx / network errors
        with _lock:
            w = _last_global + gap - time.time()
            if w > 0:
                time.sleep(w)
            _last_global = time.time()
        _last[k] = time.time()
        t0 = time.time()
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except requests.RequestException as ex:
            stats["latency_s"] += time.time() - t0
            stats["retries"] += 1
            if attempt == 0:
                time.sleep(2)
                continue
            raise _Skip(f"network error ({type(ex).__name__})", cooldown_s=_server_cooldown(k))
        stats["latency_s"] += time.time() - t0
        stats["calls"] += 1
        code, text = r.status_code, r.text
        if code == 429:
            if re.search(r"per\s*day|PerDay|daily", text, re.I):
                _sync(exhaust=(k, "429 per-day quota"))
                raise _Skip("429 daily quota")
            raise _Skip("429 rate limit", cooldown_s=_retry_delay(text) or 30.0)
        _sync(increment=k)
        _tok.setdefault(k, deque()).append((time.time(), est_tokens))
        if code >= 500:
            stats["retries"] += 1
            if attempt == 0:
                time.sleep(2)
                continue
            raise _Skip(f"HTTP {code}", cooldown_s=_server_cooldown(k))
        if code in (401, 403, 404):
            _unavailable[k] = f"HTTP {code}"
            raise _Skip(f"HTTP {code}: {text[:160]}")
        if code == 400:
            return 400, text
        if code != 200:
            raise _Skip(f"HTTP {code}: {text[:160]}")
        _fail_streak.pop(k, None)
        try:
            return 200, r.json()
        except ValueError:
            raise _Skip("non-JSON response body")
    raise _Skip("unreachable")


# ---------------------------------------------------------------- providers
_JSON_ASK = "\n\nReturn ONLY one valid JSON object. No prose, no code fences."


def _gemini_generate(e: dict, system: str, turns: list[dict], want_json: bool,
                     temperature: float, est: int) -> str:
    k = _mkey(e)
    name = _resolve_gemini_name(e["model"])
    learned = _learned.setdefault(k, {})
    is_gemma = name.startswith("gemma")
    for _ in range(2):
        no_system = is_gemma or e.get("no_system_instruction") or learned.get("no_system")
        no_json = is_gemma or e.get("no_json_mode") or learned.get("no_json")
        contents = [{"role": "model" if m["role"] == "assistant" else "user",
                     "parts": [{"text": m["content"]}]} for m in turns]
        sys_text = system + (_JSON_ASK if want_json and no_json else "")
        if sys_text and no_system:
            if contents and contents[0]["role"] == "user":
                contents[0]["parts"][0]["text"] = f"{sys_text}\n\n---\n\n{contents[0]['parts'][0]['text']}"
            else:
                contents.insert(0, {"role": "user", "parts": [{"text": sys_text}]})
        gen = {"temperature": temperature}
        if want_json and not no_json:
            gen["responseMimeType"] = "application/json"
        gen.update(e.get("generation_config") or {})
        payload = {"contents": contents, "generationConfig": gen}
        if sys_text and not no_system:
            payload["systemInstruction"] = {"parts": [{"text": sys_text}]}
        code, data = _send(e, f"{GEMINI_BASE}/models/{name}:generateContent",
                           {"x-goog-api-key": _key("GEMINI_API_KEY")}, payload, est)
        if code == 400:
            t = str(data)
            if want_json and not no_json and re.search(r"json mode|response_?mime|responseMimeType", t, re.I):
                learned["no_json"] = True
                continue
            if sys_text and not no_system and re.search(r"instruction", t, re.I):
                learned["no_system"] = True
                continue
            if re.search(r"not found|not supported|unknown name|is not available", t, re.I):
                _unavailable[k] = "HTTP 400 model not usable"
            raise _Skip(f"HTTP 400: {t[:160]}")
        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        except (KeyError, IndexError, TypeError):
            reason = (data.get("promptFeedback") or {}).get("blockReason") if isinstance(data, dict) else None
            raise _Skip(f"empty or blocked response{f' ({reason})' if reason else ''}")
        if not text.strip():
            raise _Skip("empty response")
        um = data.get("usageMetadata") or {}
        if um.get("promptTokenCount") and _tok.get(k):
            _tok[k][-1] = (_tok[k][-1][0], int(um["promptTokenCount"]))
        return text
    raise _Skip("rejected request format twice")


def _openai_generate(e: dict, system: str, turns: list[dict], want_json: bool,
                     temperature: float, est: int) -> str:
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": m["role"], "content": m["content"]} for m in turns]
    payload = {"model": e["model"], "messages": msgs, "temperature": temperature}
    if want_json:
        payload["response_format"] = {"type": "json_object"}
    base = str(e.get("base_url", "")).rstrip("/")
    if not base:
        raise _Skip("openai_compatible entry has no base_url")
    code, data = _send(e, f"{base}/chat/completions",
                       {"Authorization": f"Bearer {_key(e.get('api_key_env', 'KUKU_API_KEY'))}"}, payload, est)
    if code == 400 and want_json:   # some servers lack response_format
        payload.pop("response_format", None)
        payload["messages"][0 if system else -1]["content"] += _JSON_ASK
        code, data = _send(e, f"{base}/chat/completions",
                           {"Authorization": f"Bearer {_key(e.get('api_key_env', 'KUKU_API_KEY'))}"}, payload, est)
    if code == 400:
        raise _Skip(f"HTTP 400: {str(data)[:160]}")
    try:
        text = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise _Skip("empty OpenAI-compatible response")
    if not text.strip():
        raise _Skip("empty response")
    return text


def _anthropic_generate(e: dict, system: str, turns: list[dict], want_json: bool,
                        temperature: float, est: int) -> str:
    payload = {"model": e["model"], "max_tokens": int(e.get("max_tokens", 4096)), "temperature": temperature,
               "messages": [{"role": m["role"], "content": m["content"]} for m in turns]}
    if system or want_json:
        payload["system"] = system + (_JSON_ASK if want_json else "")
    code, data = _send(e, "https://api.anthropic.com/v1/messages",
                       {"x-api-key": _key(e.get("api_key_env", "ANTHROPIC_API_KEY")),
                        "anthropic-version": "2023-06-01"}, payload, est)
    if code == 400:
        raise _Skip(f"HTTP 400: {str(data)[:160]}")
    try:
        text = "".join(b.get("text", "") for b in data["content"])
    except (KeyError, TypeError):
        raise _Skip("empty Anthropic response")
    if not text.strip():
        raise _Skip("empty response")
    return text


_PROVIDERS = {"gemini": _gemini_generate, "openai_compatible": _openai_generate,
              "anthropic": _anthropic_generate}


# ---------------------------------------------------------------- generate
def generate(messages: list[dict], role: str = "main", json_schema: dict | None = None,
             temperature: float = 0) -> str:
    """messages: [{"role": "system"|"user"|"assistant", "content": str}]. Returns text.
    If json_schema is given JSON is requested; callers still validate (parse_json)."""
    if is_mock():
        from . import llm_mock
        stats["calls"] += 1
        stats["models"].append(f"mock:{role}")
        return llm_mock.generate(messages, role, json_schema)

    chain = _chain(role)
    if not chain:
        raise LLMError(f"no models configured for role '{role}'")
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    turns = [m for m in messages if m["role"] != "system"]
    est = _estimate_tokens(system, turns)
    cfg = _llm_cfg()
    max_wait = float(cfg.get("max_wait_s", 8))
    wait_cap = float(cfg.get("max_total_wait_s", 75))
    reasons: list[str] = []
    waited = 0.0

    for _sweep in range(4):
        _sync()
        soonest = None
        for e in chain:
            k = _mkey(e)
            fn = _PROVIDERS.get(e.get("provider", "gemini"))
            try:
                if fn is None:
                    raise _Skip(f"unknown provider {e.get('provider')}")
                w = _precheck(e, est)
                if w > max_wait:
                    soonest = w if soonest is None else min(soonest, w)
                    raise _Skip(f"busy for ~{w:.0f}s")
                if w > 0:
                    time.sleep(w)
                text = fn(e, system, turns, json_schema is not None, temperature, est)
                stats["models"].append(f"{role}:{k}")
                return text
            except _Skip as s:
                if s.cooldown_s:
                    _cool[k] = time.time() + s.cooldown_s
                    soonest = s.cooldown_s if soonest is None else min(soonest, s.cooldown_s)
                reasons.append(f"{k}: {s.reason}")
                stats["fallbacks"].append({"role": role, "model": k, "reason": s.reason})
        if soonest is None or waited + soonest > wait_cap:
            break
        time.sleep(soonest + 0.5)
        waited += soonest + 0.5
    raise LLMError(f"all models failed for role '{role}': " + "; ".join(reasons[-8:]))


def parse_json(text: str):
    """Tolerant JSON parse (strips code fences, finds the outermost object). Raises ValueError."""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        s, e = t.find("{"), t.rfind("}")
        if s != -1 and e > s:
            return json.loads(t[s:e + 1])
        raise ValueError("no JSON object found")


# ---------------------------------------------------------------- embed
_emb_window: deque = deque()


def _embed_post(url: str, headers: dict, payload: dict, n_texts: int, rpm: int,
                tokens: int = 0, tpm: int = 0) -> dict:
    """Paced to `rpm` texts and `tpm` tokens per minute, retried with backoff.
    No model switching (see top)."""
    while True:
        now = time.time()
        while _emb_window and _emb_window[0][0] < now - 60:
            _emb_window.popleft()
        used_n = sum(n for _, n, _ in _emb_window)
        used_t = sum(t for _, _, t in _emb_window)
        over = used_n + n_texts > rpm or (tpm and used_t + tokens > tpm)
        if not (_emb_window and over):
            break
        time.sleep(max(0.5, _emb_window[0][0] + 60.5 - now))
    last = None
    for attempt in range(5):
        t0 = time.time()
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=90)
        except requests.RequestException as ex:
            last = type(ex).__name__
            stats["retries"] += 1
            time.sleep(min(2 ** attempt * 2, 30))
            continue
        stats["latency_s"] += time.time() - t0
        stats["calls"] += 1
        if r.status_code == 200:
            _emb_window.append((time.time(), n_texts, tokens))
            return r.json()
        last = f"HTTP {r.status_code}"
        if r.status_code == 429 and re.search(r"per\s*day|PerDay|daily", r.text, re.I):
            raise LLMError("embedding daily quota exhausted; retrieval cannot run until it resets")
        if r.status_code == 429 or r.status_code >= 500:
            stats["retries"] += 1
            time.sleep(_retry_delay(r.text) or min(2 ** attempt * 3, 45))
            continue
        raise LLMError(f"embedding {last}: {r.text[:200]}")
    raise LLMError(f"embedding failed after retries ({last})")


def embed(texts: list[str], task: str = "document") -> np.ndarray:
    """Returns L2-normalised vectors. task: 'document' | 'query'."""
    if not texts:
        return np.zeros((0, 1), dtype=np.float32)
    if is_mock():
        from . import llm_mock
        return llm_mock.embed(texts)
    ec = load_config()["embeddings"]
    provider, model = ec.get("provider", "gemini"), ec["model"]
    rpm = int(ec.get("rpm", 100))
    tpm = int(ec.get("tpm", 0) or 0)
    batch = max(1, min(int(ec.get("batch", 20)), rpm))
    out: list[list[float]] = []

    def _toks(chunk):
        return sum(int(len(t) / 2.5) + 5 for t in chunk)

    if tpm:  # shrink batches so a single batch never exceeds the per-minute token cap
        while batch > 1 and max(_toks(texts[i:i + batch]) for i in range(0, len(texts), batch)) > tpm:
            batch = max(1, batch // 2)
    if provider == "gemini":
        name = _resolve_gemini_name(model)
        url = f"{GEMINI_BASE}/models/{name}:batchEmbedContents"
        tt = "RETRIEVAL_QUERY" if task == "query" else "RETRIEVAL_DOCUMENT"
        for i in range(0, len(texts), batch):
            chunk = texts[i:i + batch]
            payload = {"requests": [{"model": f"models/{name}", "content": {"parts": [{"text": t}]},
                                     "taskType": tt} for t in chunk]}
            data = _embed_post(url, {"x-goog-api-key": _key("GEMINI_API_KEY")}, payload, len(chunk), rpm,
                               _toks(chunk), tpm)
            try:
                out.extend(e["values"] for e in data["embeddings"])
            except (KeyError, TypeError):
                raise LLMError("bad embedding response")
        stats["models"].append(f"embed:gemini:{name}")
    elif provider == "openai_compatible":
        base = ec["base_url"].rstrip("/")
        for i in range(0, len(texts), batch):
            chunk = texts[i:i + batch]
            data = _embed_post(f"{base}/embeddings",
                               {"Authorization": f"Bearer {_key(ec.get('api_key_env', 'KUKU_API_KEY'))}"},
                               {"model": model, "input": chunk}, len(chunk), rpm, _toks(chunk), tpm)
            out.extend(d["embedding"] for d in data["data"])
    else:
        raise LLMError(f"unknown embedding provider {provider}")
    arr = np.asarray(out, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    return arr / np.maximum(norms, 1e-9)
