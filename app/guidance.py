"""General guidance: the answer when Haq has no verified passage to quote.

Before this layer, every question outside the three deep topics (and every in-scope question the corpus
could not match) got the same fixed text: "I don't cover this, call legal aid". That is safe but useless
for the most common case: a basic question that any lawyer, and most adults, could answer in two lines.

Now the model answers like a careful helper, and the reply is LABELLED as general information that was
not checked against a law text. What keeps it honest is code, not the prompt:
  - every sentence that would need a source is removed: section / article / rule numbers, Act years,
    case names and citations, any number the user or an official office did not give, any website or
    email that is not an official office's, and promises of an outcome;
  - a second model (the judge chain) removes sentences it thinks are wrong, misleading or too specific;
  - requests to commit or hide a crime get a refusal, never steps.
Verified answers (the three deep topics) are unchanged: they still quote and cite the law.
"""
import json
import logging
import re

from . import llm
from .config import load_config, read_prompt

log = logging.getLogger("ai_lawyer.guidance")

SECTION = re.compile(r"\b(?:sections?|sec\.|s\.|articles?|art\.|rules?|order|clause|schedule)\s*\d"
                     r"|(?:धारा|अनुच्छेद|नियम)\s*\d", re.I)
ACT_YEAR = re.compile(r"\b(?:act|code|rules|sanhita|अधिनियम|संहिता)\b[^.\n]{0,40}?\b(?:18|19|20)\d{2}\b"
                      r"|\b(?:18|19|20)\d{2}\b", re.I)
CASE = re.compile(r"\b[A-Z][\w.&]*\s+(?:v\.|vs\.?|versus)\s+[A-Z]|\bAIR\b|\bSCC\b|\bSCR\b", re.I)
SHORT_LAW = re.compile(r"\b(?:IPC|CrPC|BNS|BNSS|BSA)\b\s*\d")
PROMISE = re.compile(r"guarantee|definitely (?:win|get)|will surely|100 ?%|गारंटी|ज़रूर जीत|पक्का", re.I)
DIGITS = re.compile(r"\d[\d,]*")
DOMAIN = re.compile(r"\b((?:[a-z0-9-]+\.)+(?:gov\.in|nic\.in|org\.in|co\.in|ac\.in|in|com|org|net|gov))\b", re.I)
SENT = re.compile(r"(?<=[.!?।])\s+")
EMERGENCY = {"112"}   # India's single emergency number; every other number must come from the user or an office


def _numbers(text: str) -> set[str]:
    return {d.replace(",", "") for d in DIGITS.findall(text or "")}


def _domains(text: str) -> set[str]:
    return {d.lower().removeprefix("www.") for d in DOMAIN.findall(text or "")}


def _bad(sentence: str, nums: set[str], domains: set[str]) -> str | None:
    """Why this sentence cannot be shown without a source (None = fine)."""
    if SECTION.search(sentence) or SHORT_LAW.search(sentence):
        return "section number"
    if CASE.search(sentence):
        return "case citation"
    if ACT_YEAR.search(sentence):
        y = re.findall(r"\b(?:18|19|20)\d{2}\b", sentence)
        if any(v not in nums for v in y):
            return "year or Act year"
    if PROMISE.search(sentence):
        return "promise of an outcome"
    for n in _numbers(sentence):
        if n not in nums:
            return f"number {n}"
    for d in _domains(sentence):
        if not any(d == k or k.endswith("." + d) or d.endswith("." + k) for k in domains):
            return f"website {d}"
    return None


def clean(text: str, allowed_text: str) -> tuple[str, list[dict]]:
    """Drop every sentence that would need a source. Keeps line structure (bullets)."""
    nums = _numbers(allowed_text) | EMERGENCY
    domains = _domains(allowed_text)
    kept_lines, removed = [], []
    for line in (text or "").splitlines():
        if not line.strip():
            kept_lines.append("")
            continue
        bullet = re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", line)
        prefix = bullet.group(0) if bullet else ""
        body = line[len(prefix):]
        if CASE.search(body):   # "X v. Y" would be split at "v." by the sentence splitter: judge the whole line
            removed.append({"sentence": body[:160], "why": "case citation"})
            continue
        keep = []
        for s in SENT.split(body):
            why = _bad(s, nums, domains)
            if why:
                removed.append({"sentence": s[:160], "why": why})
            elif s.strip():
                keep.append(s.strip())
        if keep:
            kept_lines.append(("- " if prefix else "") + " ".join(keep))
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(kept_lines)).strip()
    return out, removed


def _judge(text: str) -> tuple[list[int], str]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    numbered = "\n".join(f"[{i}] {ln}" for i, ln in enumerate(lines))
    msgs = [{"role": "system", "content": read_prompt("guidance_judge.md")}, {"role": "user", "content": numbered}]
    try:
        d = llm.parse_json(llm.generate(msgs, role="judge", json_schema={"type": "object"}))
        bad = [int(x) for x in (d.get("remove") or []) if str(x).isdigit() and int(x) < len(lines)]
        return bad, "ok"
    except (llm.LLMError, ValueError, AttributeError, TypeError) as e:
        log.warning("guidance judge unavailable: %s", e)
        return [], f"unavailable: {e}"


def answer(user_text: str, recent: str, lang: str, kind: str, offices: list[dict], case_text: str = "") -> dict | None:
    """kind: out_of_scope | danger | unverified. Returns {"type", "text", "removed", "judge"} or None
    (None = fall back to the fixed safe response)."""
    if llm.is_mock() or not load_config().get("guidance", {}).get("enabled", True):
        return None
    office_txt = "\n".join(f"- {c['doc_title']}: {c['text'][:600]} (source: {c.get('source_url', '')})" for c in offices) or "(none)"
    lang_name = "Hindi in Devanagari script" if lang.lower().startswith("hi") else "English"
    user = (f"REPLY LANGUAGE: {lang} ({lang_name})\nSITUATION: {kind}\n"
            f"OFFICIAL OFFICES YOU MAY NAME (use their numbers and websites exactly, nothing else):\n{office_txt}\n"
            f"RECENT CONVERSATION (context only):\n{recent or '(none)'}\n"
            f"USER MESSAGE: {user_text}")
    msgs = [{"role": "system", "content": read_prompt("guidance.md")}, {"role": "user", "content": user}]
    try:
        d = llm.parse_json(llm.generate(msgs, role="main", json_schema={"type": "object"}))
    except (llm.LLMError, ValueError) as e:
        log.warning("guidance unavailable: %s", e)
        return None
    typ = str(d.get("type") or "guidance")
    if typ not in ("chat", "guidance", "refuse_harm"):
        typ = "guidance"
    allowed = "\n".join([user_text, recent or "", case_text, office_txt])
    text, removed = clean(str(d.get("text") or ""), allowed)
    note = "skipped"
    if typ == "guidance" and text and load_config().get("guidance", {}).get("judge", True):
        bad, note = _judge(text)
        if bad:
            lines = [ln for ln in text.splitlines() if ln.strip()]
            removed += [{"sentence": lines[i][:160], "why": "judge"} for i in bad]
            text = "\n".join(ln for i, ln in enumerate(lines) if i not in set(bad))
    if len(re.sub(r"\W", "", text)) < 20:
        return None
    return {"type": typ, "text": text, "removed": removed, "judge": note}
