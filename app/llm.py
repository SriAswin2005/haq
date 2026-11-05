"""Provider-swappable LLM + embedding client.

generate(messages, role, json_schema=None, temperature=0) -> str
embed(texts) -> np.ndarray (n, d), L2-normalised

Providers: gemini (default), openai_compatible, anthropic. Models come from config.yaml.
Mock mode (config mock: true or AI_LAWYER_MOCK=1) uses canned outputs and hash embeddings
so the whole pipeline runs with no keys. Mock lives in app/llm_mock.py, kept separate.
"""
import json
import os
import re
import threading
import time

import numpy as np
import requests

from .config import load_config, is_mock


class LLMError(Exception):
    pass


_lock = threading.Lock()
_last_call = 0.0
stats = {"calls": 0, "retries": 0, "latency_s": 0.0, "models": []}


def reset_stats() -> None:
    stats.update({"calls": 0, "retries": 0, "latency_s": 0.0, "models": []})


def snapshot_stats() -> dict:
    return {"calls": stats["calls"], "retries": stats["retries"],
            "latency_s": round(stats["latency_s"], 2), "models": list(stats["models"])}


def _throttle() -> None:
    global _last_call
    gap = float(load_config().get("llm", {}).get("min_interval_s", 0))
    with _lock:
        wait = gap - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()


def _post(url: str, headers: dict, payload: dict, timeout: int = 90) -> dict:
    """POST with min-interval throttle and exponential backoff on 429/5xx."""
    max_tries = int(load_config().get("llm", {}).get("max_retries", 3))
    last_err = None
    for attempt in range(max_tries):
        _throttle()
        t0 = time.time()
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            stats["latency_s"] += time.time() - t0
            stats["calls"] += 1
            if r.status_code == 429 or r.status_code >= 500:
                last_err = f"HTTP {r.status_code}"
                stats["retries"] += 1
                time.sleep(min(2 ** attempt * 2, 30))
                continue
            if r.status_code >= 400:
                # never include the key in the message (it is in headers, not url)
                raise LLMError(f"HTTP {r.status_code}: {r.text[:300]}")
            return r.json()
        except requests.RequestException as e:
            last_err = type(e).__name__
            stats["retries"] += 1
            time.sleep(min(2 ** attempt * 2, 30))
    raise LLMError(f"request failed after {max_tries} tries ({last_err})")


def _role_cfg(role: str) -> dict:
    cfg = load_config()["models"]
    return cfg.get(role) or cfg["main"]


def _key(env_name: str) -> str:
    v = os.environ.get(env_name, "")
    if not v:
        raise LLMError(f"missing environment variable {env_name}")
    return v


# ---------------------------------------------------------------- generate
def generate(messages: list[dict], role: str = "main", json_schema: dict | None = None,
             temperature: float = 0) -> str:
    """messages: [{"role": "system"|"user"|"assistant", "content": str}]. Returns text.
    If json_schema is given the provider is asked for JSON; callers still validate."""
    if is_mock():
        from . import llm_mock
        stats["calls"] += 1
        stats["models"].append(f"mock:{role}")
        return llm_mock.generate(messages, role, json_schema)
    rc = _role_cfg(role)
    provider, model = rc["provider"], rc["model"]
    stats["models"].append(f"{provider}:{model}")
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    turns = [m for m in messages if m["role"] != "system"]

    if provider == "gemini":
        contents = [{"role": "model" if m["role"] == "assistant" else "user",
                     "parts": [{"text": m["content"]}]} for m in turns]
        payload = {"contents": contents,
                   "generationConfig": {"temperature": temperature}}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        if json_schema is not None:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        data = _post(url, {"x-goog-api-key": _key("GEMINI_API_KEY")}, payload)
        try:
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError, TypeError):
            raise LLMError("empty or blocked Gemini response")

    if provider == "openai_compatible":
        msgs = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": m["role"], "content": m["content"]} for m in turns]
        payload = {"model": model, "messages": msgs, "temperature": temperature}
        if json_schema is not None:
            payload["response_format"] = {"type": "json_object"}
        base = rc["base_url"].rstrip("/")
        data = _post(f"{base}/chat/completions",
                     {"Authorization": f"Bearer {_key(rc.get('api_key_env', 'KUKU_API_KEY'))}"}, payload)
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise LLMError("empty OpenAI-compatible response")

    if provider == "anthropic":
        payload = {"model": model, "max_tokens": 4096, "temperature": temperature,
                   "messages": [{"role": m["role"], "content": m["content"]} for m in turns]}
        if system:
            payload["system"] = system
        data = _post("https://api.anthropic.com/v1/messages",
                     {"x-api-key": _key(rc.get("api_key_env", "ANTHROPIC_API_KEY")),
                      "anthropic-version": "2023-06-01"}, payload)
        try:
            return "".join(b.get("text", "") for b in data["content"])
        except (KeyError, TypeError):
            raise LLMError("empty Anthropic response")

    raise LLMError(f"unknown provider {provider}")


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
def embed(texts: list[str], task: str = "document") -> np.ndarray:
    """Returns L2-normalised vectors. task: 'document' | 'query'."""
    if not texts:
        return np.zeros((0, 1), dtype=np.float32)
    if is_mock():
        from . import llm_mock
        return llm_mock.embed(texts)
    ec = load_config()["embeddings"]
    provider, model = ec["provider"], ec["model"]
    out: list[list[float]] = []
    if provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"
        tt = "RETRIEVAL_QUERY" if task == "query" else "RETRIEVAL_DOCUMENT"
        for i in range(0, len(texts), 50):
            batch = texts[i:i + 50]
            payload = {"requests": [{"model": f"models/{model}", "content": {"parts": [{"text": t}]},
                                     "taskType": tt} for t in batch]}
            data = _post(url, {"x-goog-api-key": _key("GEMINI_API_KEY")}, payload)
            try:
                out.extend(e["values"] for e in data["embeddings"])
            except (KeyError, TypeError):
                raise LLMError("bad embedding response")
    elif provider == "openai_compatible":
        base = ec["base_url"].rstrip("/")
        for i in range(0, len(texts), 50):
            data = _post(f"{base}/embeddings",
                         {"Authorization": f"Bearer {_key(ec.get('api_key_env', 'KUKU_API_KEY'))}"},
                         {"model": model, "input": texts[i:i + 50]})
            out.extend(d["embedding"] for d in data["data"])
    else:
        raise LLMError(f"unknown embedding provider {provider}")
    arr = np.asarray(out, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    return arr / np.maximum(norms, 1e-9)
