"""Live legal answers from Google Search, used when the law library has no passage for the question.

The model answers with Google Search grounding (Gemini's google_search tool). Google returns, with the
answer, which web pages it used and which parts of the answer each page supports (groundingSupports).
Code then keeps ONLY the sentences that Google ties to at least one acceptable source, numbers each with
its sources, and drops the rest. So every legal statement a user sees from this path has a page behind it
that they can open, and sources such as social media or forums never count as support.
"""
import logging
import re
import time
import unicodedata

from . import llm
from .config import load_config, read_prompt

log = logging.getLogger("ai_lawyer.websearch")
_off_until = 0.0   # web search is skipped until this time after Google refuses it

# Pages that never count as support for a legal statement.
BLOCKED = re.compile(r"(^|\.)(quora|reddit|facebook|instagram|youtube|x|twitter|linkedin|medium|blogspot|"
                     r"wordpress|pinterest|tiktok|sharechat|answers|brainly)\.", re.I)
OFFICIAL = re.compile(r"(\.gov\.in|\.nic\.in|\.gov|sci\.gov\.in|indiacode|ecourts|\.courts?\.)", re.I)
SENT = re.compile(r"(?<=[.!?।])\s+")


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", t or "")
    t = re.sub(r"[*_`#>\[\]]", "", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def _domain(title: str, uri: str) -> str:
    t = (title or "").strip().lower()
    if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", t):
        return t.removeprefix("www.")
    m = re.match(r"https?://([^/]+)", uri or "")
    return (m.group(1) if m else t or "web").removeprefix("www.")


def _supported(sentence: str, supports: list[tuple[str, list[int]]]) -> list[int]:
    """Indices of grounding chunks that support this sentence (matched by the supported text segment)."""
    s = _norm(sentence)
    if len(s) < 12:
        return []
    out: list[int] = []
    for seg, idx in supports:
        if not seg or len(seg) < 12:
            continue
        if seg in s or s in seg or (len(seg) > 40 and seg[:40] in s):
            out += [i for i in idx if i not in out]
    return out


def _is_heading(line: str) -> bool:
    t = line.strip().strip("*#").strip()
    return 0 < len(t) <= 60 and t.endswith(":") and not re.search(r"\d", t)


def answer(question: str, user_text: str, lang: str, country: str | None, state: str | None,
           recent: str = "") -> dict | None:
    """Returns {"text", "sources": [{"n", "domain", "uri", "official"}], "queries", "dropped", "search_html"}
    or None if search is off, unavailable, or too little of the answer is supported."""
    cfg = load_config().get("web_search", {})
    global _off_until
    if llm.is_mock() or not cfg.get("enabled", True) or time.time() < _off_until:
        return None
    lang_name = "Hindi in Devanagari script" if lang.lower().startswith("hi") else "English"
    place = "India" if (country or "IN") == "IN" else f"the country with code {country} (and say whether Indian law applies)"
    user = (f"REPLY LANGUAGE: {lang_name}\nPLACE: {place}{f', state {state}' if state else ''}\n"
            f"RECENT CONVERSATION (context only):\n{recent or '(none)'}\n"
            f"QUESTION: {question or user_text}\nTHE PERSON'S OWN WORDS: {user_text}")
    msgs = [{"role": "system", "content": read_prompt("web_answer.md")}, {"role": "user", "content": user}]
    try:
        text, meta = llm.generate_grounded(msgs, role="search")
    except llm.LLMError as e:
        log.warning("web search unavailable: %s", e)
        if "429" in str(e):   # Google is refusing search for this key: don't spend ~60 s per turn retrying
            _off_until = time.time() + 600
        return None
    chunks = meta.get("groundingChunks") or []
    sources_all = []
    for c in chunks:
        w = c.get("web") or {}
        dom = _domain(w.get("title", ""), w.get("uri", ""))
        sources_all.append({"domain": dom, "uri": w.get("uri", ""), "official": bool(OFFICIAL.search(dom)),
                            "blocked": bool(BLOCKED.search(dom + "."))})
    supports = []
    for sp in meta.get("groundingSupports") or []:
        seg = _norm((sp.get("segment") or {}).get("text", ""))
        idx = [i for i in (sp.get("groundingChunkIndices") or []) if isinstance(i, int) and i < len(sources_all)
               and not sources_all[i]["blocked"]]
        if seg and idx:
            supports.append((seg, idx))
    used: dict[int, int] = {}          # grounding chunk index -> number shown to the user
    out_lines, dropped, kept_claims = [], [], 0
    for line in (text or "").splitlines():
        if not line.strip():
            out_lines.append("")
            continue
        if _is_heading(line):
            out_lines.append("\x00" + line.strip().strip("*#").strip())   # marked as a heading
            continue
        bullet = re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", line)
        body = line[bullet.end():] if bullet else line
        keep = []
        for s in SENT.split(body):
            idx = _supported(s, supports)
            if idx:
                for i in idx:
                    used.setdefault(i, len(used) + 1)
                keep.append(s.strip().replace("**", "") + " " + "".join(f"[{used[i]}]" for i in idx[:3]))
                kept_claims += 1
            elif s.strip():
                dropped.append(s.strip()[:200])
        if keep:
            out_lines.append(("- " if bullet else "") + " ".join(keep))
    # drop headings left with nothing under them
    cleaned: list[str] = []
    for i, ln in enumerate(out_lines):
        if ln.startswith("\x00"):
            nxt = next((x for x in out_lines[i + 1:] if x.strip()), "")
            if not nxt or nxt.startswith("\x00"):
                continue
            ln = ln[1:]
        cleaned.append(ln)
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip()
    if kept_claims < int(cfg.get("min_supported_sentences", 2)):
        log.info("web answer dropped: only %d supported sentences", kept_claims)
        return None
    srcs = [dict(sources_all[i], n=n) for i, n in sorted(used.items(), key=lambda x: x[1])]
    entry = (meta.get("searchEntryPoint") or {}).get("renderedContent") or ""
    return {"text": body, "sources": srcs, "queries": meta.get("webSearchQueries") or [],
            "dropped": dropped[:10], "search_html": entry}
