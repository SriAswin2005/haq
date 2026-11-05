"""Corpus loading, embedding index (cached), filtered cosine search, confidence gate."""
import hashlib
import json
import logging
from pathlib import Path

import numpy as np

from . import llm
from .config import load_config, resolve, is_mock

log = logging.getLogger("ai_lawyer.retrieval")

REQUIRED = ["id", "category", "doc_title", "doc_type", "jurisdiction", "unit", "unit_number", "text",
            "status", "source_url", "source_type", "fetched_on", "verified"]
CATS = {"consumer", "wages", "tenancy", "common"}
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
    return f"{c['doc_title']} {c.get('unit','')} {c.get('unit_number','')}. {c.get('heading','')}. {c['text']}"


def _cache_file() -> Path:
    d = resolve("data/index")
    d.mkdir(parents=True, exist_ok=True)
    m = load_config()["embeddings"]["model"] if not is_mock() else "mock-hash"
    return d / f"embeddings_{m.replace('/', '_')}.json"


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
    if todo:
        vecs = llm.embed([texts[i] for i in todo], task="document")
        for i, v in zip(todo, vecs):
            cache[i] = {"h": hashes[i], "v": [round(float(x), 6) for x in v]}
        try:
            cf.write_text(json.dumps({k: cache[k] for k in texts}), encoding="utf-8")
        except OSError as e:
            log.warning("could not write embedding cache: %s", e)
    mat = np.asarray([cache[c["id"]]["v"] for c in chunks], dtype=np.float32) if chunks else np.zeros((0, 1))
    idx = {"chunks": chunks, "matrix": mat, "problems": problems, "path": path or load_config()["corpus"]["path"],
           "has_sample": any(c["id"].startswith("SAMPLE-") for c in chunks), "embedded_now": len(todo)}
    _state["index"] = idx
    return idx


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


def search(query_en: str, categories: list[str], jurisdictions: list[str], k: int | None = None,
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
    cats, juris = set(categories), set(jurisdictions)
    base = np.array([c["category"] in cats and c["jurisdiction"] in juris for c in idx["chunks"]])
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
    old = _search(q, idx, base & ~live, 2)
    return {"hits": hits, "old_law": old, "top_score": hits[0]["score"] if hits else 0.0}


def passes_gate(top_score: float) -> bool:
    """Confidence gate: weak retrieval -> no answer."""
    r = load_config()["retrieval"]
    # The threshold is calibrated for the real embedding model. Mock (hash) embeddings give meaningless
    # scores, so mock mode uses its own floor (default 0) and offline tests still exercise the answer path.
    floor = float(r.get("mock_min_score", 0.0)) if llm.is_mock() else float(r["min_score"])
    return top_score > 0 and top_score >= floor
