"""Corpus loading, embedding index (cached), filtered cosine search, confidence gate."""
import hashlib
import json
import logging
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np

from . import llm
from .config import load_config, resolve, is_mock

log = logging.getLogger("ai_lawyer.retrieval")

REQUIRED = ["id", "category", "doc_title", "doc_type", "jurisdiction", "unit", "unit_number", "text",
            "status", "source_url", "source_type", "fetched_on", "verified"]
CATS = {"consumer", "wages", "tenancy", "common", "rights", "criminal", "family", "civic", "money", "property"}
STATUSES = {"in_force", "repealed", "superseded", "not_yet_in_force", "model_only", "unclear"}
DOC_TYPES = {"statute", "rule", "govt_guidance", "portal_procedure", "helpline", "judgment"}

_state: dict = {}


def validate_chunk(c: dict) -> str | None:
    """Return an error string, or None if the chunk matches the Section 5 contract."""
    if not isinstance(c, dict):
        return "not an object"
    for k in REQUIRED:
        if k not in c or c[k] in (None, ""):
            if k in ("unit_number",) and c.get(k) is not None:
                continue
            return f"missing field {k}"
    if c["category"] not in CATS:
        return f"bad category {c['category']}"
    if c["status"] not in STATUSES:
        return f"bad status {c['status']}"
    if c["doc_type"] not in DOC_TYPES:
        return f"bad doc_type {c['doc_type']}"
    if c["source_type"] == "secondary" and not c.get("human_check_required"):
        return "secondary source without human_check_required"
    return None


def load_corpus(path: str | None = None) -> tuple[list[dict], list[str]]:
    """Load all *.jsonl under the corpus path. Bad lines are skipped and logged, never fatal."""
    base = resolve(path or load_config()["corpus"]["path"])
    files = sorted(base.glob("*.jsonl")) if base.is_dir() else [base]
    chunks, problems, seen = [], [], set()
    for f in files:
        with open(f, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    c = json.loads(line)
                except json.JSONDecodeError as e:
                    problems.append(f"{f.name}:{n} invalid JSON ({e.msg})")
                    continue
                err = validate_chunk(c)
                if err is None and c["id"] in seen:
                    err = "duplicate id"
                if err:
                    problems.append(f"{f.name}:{n} skipped: {err}")
                    continue
                seen.add(c["id"])
                chunks.append(c)
    for p in problems:
        log.warning("CORPUS: %s", p)
    return chunks, problems


def _embed_text(c: dict) -> str:
    title = f"{c['doc_title']} {c.get('unit','')} {c.get('unit_number','')}. {c.get('heading','')}".strip()
    if not is_mock() and str(load_config()["embeddings"]["model"]).startswith("gemini-embedding-2"):
        return f"title: {title} | text: {c['text']}"      # Embedding 2's document format (no taskType field)
    return f"{title}. {c['text']}"


def _cache_file() -> Path:
    d = resolve("data/index")
    d.mkdir(parents=True, exist_ok=True)
    ec = load_config()["embeddings"]
    m = ec["model"] if not is_mock() else "mock-hash"
    dims = f"_{ec['dims']}" if ec.get("dims") and not is_mock() else ""
    return d / f"embeddings_{m.replace('/', '_')}{dims}.json"


def build_index(path: str | None = None, force: bool = False) -> dict:
    """Embed chunks; cache by chunk id + hash of text so only changed chunks are re-embedded."""
    chunks, problems = load_corpus(path)
    cf = _cache_file()
    cache = {}
    if cf.exists() and not force:
        try:
            cache = json.loads(cf.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
    texts = {c["id"]: _embed_text(c) for c in chunks}
    hashes = {i: hashlib.sha256(t.encode("utf-8")).hexdigest() for i, t in texts.items()}
    todo = [i for i in texts if cache.get(i, {}).get("h") != hashes[i]]
    for start in range(0, len(todo), 100):   # save after every 100, so a quota stop loses little
        part = todo[start:start + 100]
        vecs = llm.embed([texts[i] for i in part], task="document")
        for i, v in zip(part, vecs):
            cache[i] = {"h": hashes[i], "v": [round(float(x), 6) for x in v]}
        try:
            cf.write_text(json.dumps({k: cache[k] for k in texts if k in cache}), encoding="utf-8")
        except OSError as e:
            log.warning("could not write embedding cache: %s", e)
    mat = np.asarray([cache[c["id"]]["v"] for c in chunks], dtype=np.float32) if chunks else np.zeros((0, 1))
    if len(mat):   # shortened (e.g. 768-dim) Gemini vectors are not unit length: normalise for cosine
        mat = mat / np.maximum(np.linalg.norm(mat, axis=1, keepdims=True), 1e-9)
    idx = {"chunks": chunks, "matrix": mat, "problems": problems, "path": path or load_config()["corpus"]["path"],
           "has_sample": any(c["id"].startswith("SAMPLE-") for c in chunks), "embedded_now": len(todo),
           "bm25": _bm25_index([_embed_text(c) for c in chunks])}
    _state["index"] = idx
    return idx


# ---------------------------------------------------------------- keyword search (BM25)
# Meaning-based vectors miss exact references ("section 138", "RTI", "498A"); keywords catch them.
_TOK = re.compile(r"[a-z0-9]+")
_STOP = set("a an the of to in on for and or is are be by with as at from that this it its any such which shall may "
            "under section act sub said other than not no where who whom whose has have been".split())


def _toks(text: str) -> list[str]:
    return [t for t in _TOK.findall(text.lower()) if t not in _STOP and len(t) > 1]


def _bm25_index(docs: list[str]) -> dict:
    toks = [_toks(d) for d in docs]
    df = Counter(t for d in toks for t in set(d))
    n = max(len(toks), 1)
    return {"tf": [Counter(d) for d in toks], "len": [len(d) for d in toks],
            "avg": (sum(len(d) for d in toks) / n) if toks else 1.0,
            "idf": {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}}


def _bm25(idx: dict, query: str, mask, k: int, k1: float = 1.4, b: float = 0.75) -> list[dict]:
    bm = idx.get("bm25")
    q = _toks(query)
    if not bm or not q:
        return []
    scores = []
    for i, tf in enumerate(bm["tf"]):
        if not mask[i]:
            continue
        s = 0.0
        for t in q:
            f = tf.get(t)
            if f:
                s += bm["idf"].get(t, 0) * f * (k1 + 1) / (f + k1 * (1 - b + b * bm["len"][i] / bm["avg"]))
        if s > 0:
            scores.append((s, i))
    scores.sort(reverse=True)
    return [{"id": idx["chunks"][i]["id"], "score": float(s), "chunk": idx["chunks"][i], "row": i} for s, i in scores[:k]]


def get_index() -> dict:
    cur = _state.get("index")
    want = load_config()["corpus"]["path"]
    if cur is None or cur["path"] != want or _state.get("mock") != is_mock():
        _state["mock"] = is_mock()
        build_index()
    return _state["index"]


def _search(q_vec, idx, mask, k):
    if not mask.any():
        return []
    sims = idx["matrix"] @ q_vec
    order = [i for i in np.argsort(-sims) if mask[i]][:k]
    return [{"id": idx["chunks"][i]["id"], "score": float(sims[i]), "chunk": idx["chunks"][i]} for i in order]


def search(query_en: str, categories: list[str] | None, jurisdictions: list[str], k: int | None = None,
           extra_queries: list[str] | None = None, extra_k: int = 2) -> dict:
    """Returns {"hits": [...in-force/usable...], "old_law": [...repealed/superseded...], "top_score": float}.
    hits exclude repealed/superseded; those are searched separately for old-law detection only.
    extra_queries (e.g. the category's "where to complain" query) add up to extra_k new hits each,
    after the main hits, with the same category/jurisdiction/status filters. top_score (the
    confidence gate) still comes from the user's own query only."""
    idx = get_index()
    k = k or load_config()["retrieval"]["top_k"]
    if not idx["chunks"]:
        return {"hits": [], "old_law": [], "top_score": 0.0}
    q = llm.embed([query_en], task="query")[0]
    cats, juris = (set(categories) if categories else None), set(jurisdictions)   # None = every topic
    base = np.array([(cats is None or c["category"] in cats) and c["jurisdiction"] in juris for c in idx["chunks"]])
    live = np.array([c["status"] not in ("repealed", "superseded") for c in idx["chunks"]])
    hits = _search(q, idx, base & live, k)
    seen = {h["id"] for h in hits}
    for xq in extra_queries or []:
        xv = llm.embed([xq], task="query")[0]
        added = 0
        for h in _search(xv, idx, base & live, k + extra_k):
            if h["id"] not in seen and added < extra_k:
                h = dict(h, via="forum_query")
                hits.append(h)
                seen.add(h["id"])
                added += 1
    # keyword matches the vectors missed (exact Act names, section numbers): added after the main hits
    kw_k = int(load_config()["retrieval"].get("keyword_extra", 2))
    added = 0
    for h in _bm25(idx, query_en, base & live, kw_k + len(hits)):
        if added >= kw_k:
            break
        if h["id"] not in seen:
            hits.append({"id": h["id"], "score": float(idx["matrix"][h["row"]] @ q),
                         "chunk": h["chunk"], "via": "keyword"})
            seen.add(h["id"])
            added += 1
    old = _search(q, idx, base & ~live, 2)
    return {"hits": hits, "old_law": old, "top_score": max((h["score"] for h in hits if h.get("via") is None), default=0.0)}


def passes_gate(top_score: float) -> bool:
    """Confidence gate: weak retrieval -> no answer."""
    r = load_config()["retrieval"]
    # The threshold is calibrated for the real embedding model. Mock (hash) embeddings give meaningless
    # scores, so mock mode uses its own floor (default 0) and offline tests still exercise the answer path.
    # Each embedding model has its own score scale, so the floor is set per model (min_score_by_model).
    model = load_config()["embeddings"].get("model", "")
    floor = float(r.get("mock_min_score", 0.0)) if llm.is_mock() else \
        float((r.get("min_score_by_model") or {}).get(model, r["min_score"]))
    return top_score > 0 and top_score >= floor
