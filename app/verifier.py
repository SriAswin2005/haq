"""Anti-hallucination verifier (Architecture Section 8, points 5 and 6).

Deterministic checks (`check`) + optional LLM faithfulness judge (`judge`).
All regex lists live in this one place (PATTERNS) so they are easy to extend.
"""
import json
import logging
import re

from . import llm
from .config import load_config, read_prompt

log = logging.getLogger("ai_lawyer.verifier")

# ---- patterns: (kind, regex). The regex's group(0) is what must be present in the retrieved material.
PATTERNS = {
    "section": re.compile(r"(?:\b(?:Section|Sections|Sec\.?)\s*|\bs\.\s*|धारा\s*)(\d+[A-Za-z]?)", re.I),
    "article": re.compile(r"\bArticle\s+(\d+[A-Za-z]?)", re.I),
    "rule": re.compile(r"\bRules?\s+(\d+[A-Za-z]?)", re.I),
    "order": re.compile(r"\bOrder\s+([IVXLC]+|\d+)\b"),
    "act": re.compile(r"\bAct,?\s+(?:of\s+)?((?:18|19|20)\d{2})\b"),
    "case_v": re.compile(r"\b[A-Z][\w.&]*\s+(?:v\.|vs\.?|versus)\s+[A-Z][\w.&]*"),
    "case_cite": re.compile(r"\bAIR\b|\bSCC\b|\bSCR\b|\bCPJ\b|\(\d{4}\)\s*\d+\s*(?:SCC|SCR|CPJ)"),
}
WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
            "ten": 10, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "forty-five": 45,
            "sixty": 60, "ninety": 90, "hundred": 100}
UNIT = r"(?:days?|months?|years?|weeks?|hours?|rupees?|rs\.?|inr|lakhs?|crores?|per\s?cent|percent|%|₹)"
NUM_RE = re.compile(r"(?:₹|rs\.?\s*)?(\d[\d,]*(?:\.\d+)?)(?:\s*" + UNIT + r")?", re.I)
WORDNUM_RE = re.compile(r"\b(" + "|".join(sorted(WORD_NUM, key=len, reverse=True)) + r")[\s-]+" + UNIT, re.I)
NOT_CURRENT = re.compile(r"no longer|repealed|replaced|not (?:in force|current)|old law|पुराना|निरस्त", re.I)


def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\b(?:sections?|sec\.?)\s*(\d+)", r"section \1", s)
    s = re.sub(r"\bs\.\s*(\d+)", r"section \1", s)
    s = re.sub(r"धारा\s*(\d+)", r"section \1", s)
    s = re.sub(r"\brules\s+(\d+)", r"rule \1", s)
    s = re.sub(r"act,\s*", "act ", s)
    return re.sub(r"\s+", " ", s)


def _meta_text(c: dict) -> str:
    unit = str(c.get("unit", "")).lower()
    n = c.get("unit_number", "")
    bits = [c.get("doc_title", ""), c.get("heading", ""), f"{unit} {n}", c.get("effective_from") or ""]
    return " ".join(str(b) for b in bits)


def _haystack(chunks: list[dict]) -> str:
    return _norm(" \n ".join(c.get("text", "") + " " + _meta_text(c) for c in chunks))


def _nums_in(text: str) -> set[str]:
    out = set()
    for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", text):
        out.add(m.group(0).replace(",", "").rstrip("."))
    for m in WORDNUM_RE.finditer(text):
        out.add(str(WORD_NUM[m.group(1).lower()]))
    return out


def _case_nums(case_file: dict) -> set[str]:
    return _nums_in(json.dumps(case_file, ensure_ascii=False))


def scan_patterns(text: str, chunks: list[dict]) -> list[str]:
    """Flag statute/case patterns in `text` that are absent from the retrieved chunks' text or metadata."""
    hay = _haystack(chunks)
    has_judgment = any(c.get("doc_type") == "judgment" for c in chunks)
    issues = []
    for kind, rx in PATTERNS.items():
        for m in rx.finditer(text):
            frag = _norm(m.group(0)).strip()
            if kind in ("section", "article", "rule", "order"):
                num = m.group(1).lower()
                label = {"section": "section", "article": "article", "rule": "rule", "order": "order"}[kind]
                ok = f"{label} {num}" in hay
            elif kind == "act":
                ok = _norm(m.group(0)) in hay or f"act {m.group(1)}" in hay
            else:  # case patterns
                ok = has_judgment and frag in hay
            if not ok:
                issues.append(f"unsupported {kind} reference '{m.group(0).strip()}' not in retrieved sources")
    return list(dict.fromkeys(issues))


def _must_verify(text: str):
    """Yield numbers that need support: have a unit, are >=3 digits, or are decimals/percentages."""
    for m in NUM_RE.finditer(text):
        raw = m.group(0)
        n = m.group(1).replace(",", "").rstrip(".")
        has_unit = bool(re.search(UNIT, raw, re.I)) or raw.strip().startswith(("₹",)) or raw.lower().startswith("rs")
        if has_unit or len(n.replace(".", "")) >= 3 or "." in n:
            yield n, raw.strip()
    for m in WORDNUM_RE.finditer(text):
        yield str(WORD_NUM[m.group(1).lower()]), m.group(0)


# Scripts that never belong in an English/Hindi answer: a model glitch (seen in round 4: Hindi "क्леम" with
# Cyrillic letters). Arabic script is left out because Urdu replies are legitimate.
STRAY_SCRIPT = re.compile(r"[\u0370-\u03FF\u0400-\u04FF\u0E00-\u0E7F\u3040-\u30FF\u3400-\u9FFF\uAC00-\uD7AF]")


# Websites and email domains must be copied exactly from a source: round 4 showed "airseva.gov.in" for the
# source's "airsewa.gov.in", which sends a user to a wrong (possibly fake) site.
DOMAIN = re.compile(r"\b((?:[a-z0-9-]+\.)+(?:gov\.in|nic\.in|org\.in|co\.in|ac\.in|in|com|org|net|gov))\b")


def _domains(text: str) -> set[str]:
    return {d[4:] if d.startswith("www.") else d for d in DOMAIN.findall((text or "").lower())}


def _domain_ok(d: str, known: set[str]) -> bool:
    return any(d == k or k.endswith("." + d) or d.endswith("." + k) for k in known)


def check(answer: dict, retrieved: list[dict], case_file: dict) -> list[str]:
    """Deterministic checks. Returns a list of issue strings (empty = pass).
    answer: {"blocks":[{"text","type","cites"}], ...}; retrieved: chunk dicts for this turn."""
    issues = []
    by_id = {c["id"]: c for c in retrieved}
    blocks = answer.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        return ["answer has no blocks"]
    cf_nums = _case_nums(case_file)
    known_domains = _domains(json.dumps(case_file, ensure_ascii=False))
    for c in retrieved:
        known_domains |= _domains(c.get("text", "")) | _domains(c.get("source_url", ""))
    all_text_nums = set()
    for c in retrieved:
        all_text_nums |= _nums_in(c.get("text", "")) | _nums_in(_meta_text(c))
    for i, b in enumerate(blocks):
        if not isinstance(b, dict) or not isinstance(b.get("text"), str):
            issues.append(f"block {i}: malformed")
            continue
        typ, text, cites = b.get("type"), b["text"], b.get("cites") or []
        if STRAY_SCRIPT.search(text):
            issues.append(f"block {i}: garbled text (characters from an unrelated script)")
        bad_sites = sorted(d for d in _domains(text) if not _domain_ok(d, known_domains))
        if bad_sites:
            issues.append(f"block {i}: website or email {bad_sites} not found in the sources")
        if typ not in ("legal", "practical", "question"):
            issues.append(f"block {i}: bad type {typ!r}")
            continue
        bad = [x for x in cites if x not in by_id]
        if bad:
            issues.append(f"block {i}: cites ids not in this turn's sources: {bad}")
        if typ == "legal":
            if not cites:
                issues.append(f"block {i}: legal block without a citation")
            cited = [by_id[x] for x in cites if x in by_id]
            stale = [c["id"] for c in cited if c.get("status") != "in_force"]
            if stale and not NOT_CURRENT.search(text):
                issues.append(f"block {i}: cites non-current law {stale} without saying it is not current")
            support = set(cf_nums)
            for c in cited:
                support |= _nums_in(c.get("text", "")) | _nums_in(_meta_text(c))
        elif typ == "practical":
            support = set(cf_nums) | all_text_nums
            if any(PATTERNS[k].search(text) for k in ("section", "article", "rule", "act", "case_v", "case_cite")):
                # a statement of law labelled "practical" would skip the judge (production review, 7 Nov)
                issues.append(f"block {i}: legal reference in a practical block (must be a cited legal block)")
        else:
            support = None
        if support is not None:
            for n, raw in _must_verify(text):
                if n not in support:
                    issues.append(f"block {i}: number '{raw}' not found in cited source or user's facts")
        issues.extend(f"block {i}: {x}" for x in scan_patterns(text, retrieved))
    return list(dict.fromkeys(issues))


def judge(answer: dict, retrieved: list[dict]) -> tuple[list[str], str]:
    """LLM faithfulness judge. Returns (issues, note). If the judge is unavailable the code checks stand
    and the note says so (never silently)."""
    by_id = {c["id"]: c for c in retrieved}
    parts = []
    for i, b in enumerate(answer.get("blocks", [])):
        if b.get("type") == "legal":
            src = "\n".join(f"  [{x}] {by_id[x]['text']}" for x in b.get("cites", []) if x in by_id)
            parts.append(f"[BLOCK {i}] CLAIM: {b['text']}\nCITED SOURCES:\n{src}")
    if not parts:
        return [], "no legal blocks"
    msgs = [{"role": "system", "content": read_prompt("judge.md")},
            {"role": "user", "content": "\n\n".join(parts)}]
    try:
        raw = llm.generate(msgs, role="judge", json_schema={"type": "object"})
        d = llm.parse_json(raw)
        issues, seen = [], set()
        for v in d.get("verdicts", []) if isinstance(d.get("verdicts"), list) else []:
            if not isinstance(v, dict):
                continue
            try:
                seen.add(int(v.get("block")))
            except (TypeError, ValueError):
                pass
            if not v.get("supported", False):
                issues.append(f"block {v.get('block')}: claim not supported by its cited source "
                              f"({str(v.get('reason', ''))[:120]})")
        # An empty or partial verdict list is a failure to check, not a pass (production review, 7 Nov).
        for i, b in enumerate(answer.get("blocks", [])):
            if b.get("type") == "legal" and i not in seen:
                issues.append(f"block {i}: the judge returned no verdict for this claim")
        return issues, "ok"
    except (llm.LLMError, ValueError, AttributeError) as e:
        log.warning("judge unavailable: %s", e)
        if load_config().get("verifier", {}).get("require_judge", True):
            return [f"block {i}: not checked (judge unavailable)" for i, b in enumerate(answer.get("blocks", []))
                    if b.get("type") == "legal"], f"judge_unavailable: {e}"
        return [], f"judge_unavailable: {e}"


def verify(answer: dict, retrieved: list[dict], case_file: dict) -> tuple[list[str], dict]:
    """Full verification: code checks, then (if enabled and code checks passed) the LLM judge."""
    issues = check(answer, retrieved, case_file)
    info = {"judge": "skipped"}
    if not issues and load_config().get("verifier", {}).get("llm_judge", True):
        j_issues, note = judge(answer, retrieved)
        issues.extend(j_issues)
        info["judge"] = note
    return issues, info
