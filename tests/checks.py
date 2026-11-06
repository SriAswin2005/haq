"""Independent, conservative checks for the frozen TurnResult interface.

No app imports or network calls. Unknown evidence yields a warning/skip rather
than a fabricated pass. Checks accept dataclasses or raw JSON dictionaries.
"""
from __future__ import annotations

import dataclasses
import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit


@dataclass(frozen=True)
class CheckResult:
    status: str  # pass | fail | warning | skip
    reason: str
    details: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool | None:
        return True if self.status == "pass" else False if self.status == "fail" else None

    def to_dict(self) -> dict:
        return {**dataclasses.asdict(self), "passed": self.passed}


def get(value: Any, key: str, default: Any = None) -> Any:
    return value.get(key, default) if isinstance(value, Mapping) else getattr(value, key, default)


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = "".join(str(unicodedata.digit(c)) if c.isdigit() else c for c in text)
    return re.sub(r"\s+", " ", text).strip()


def visible_text(result: Any) -> str:
    reply, draft = get(result, "reply_text", ""), get(result, "draft_text")
    return str(reply) + ("\n" + draft if isinstance(draft, str) and draft not in str(reply) else "")


def load_corpus(path: str | Path) -> dict[str, dict]:
    """Read-only, fail loudly for duplicate IDs or malformed corpus lines."""
    path = Path(path)
    files = [path] if path.is_file() else sorted(path.glob("*.jsonl"))
    chunks: dict[str, dict] = {}
    for filename in files:
        for line_no, line in enumerate(filename.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            try:
                chunk = json.loads(line)
                chunk_id = chunk["id"]
                if not isinstance(chunk_id, str) or not chunk_id:
                    raise ValueError("empty/non-string id")
                if chunk_id in chunks:
                    raise ValueError(f"duplicate id {chunk_id}")
                chunks[chunk_id] = chunk
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f"{filename}:{line_no}: {exc}") from exc
    return chunks


def check_routing(result, case, corpus=None) -> CheckResult:
    actual, expected = get(result, "category"), case["category_expected"]
    if case.get("expected_outcomes"):
        allowed = sorted({o["category"] for o in case["expected_outcomes"]})
        return CheckResult("pass" if actual in allowed else "fail", f"category={actual!r}; permitted categories={allowed}")
    return CheckResult("pass" if actual == expected else "fail", f"category={actual!r}; expected {expected!r}")


def check_action(result, case, corpus=None) -> CheckResult:
    actual, expected = get(result, "action"), case["expected_action"]
    if case.get("expected_outcomes"):
        allowed = sorted({o["action"] for o in case["expected_outcomes"] if o["category"] == get(result, "category")})
        return CheckResult("pass" if actual in allowed else "fail", f"action={actual!r}; permitted for this category={allowed}")
    return CheckResult("pass" if actual == expected else "fail", f"action={actual!r}; expected {expected!r}")


def check_contract(result, case, corpus=None) -> CheckResult:
    required = {"reply_text": str, "reply_lang": str, "category": str, "action": str,
                "citations": list, "retrieved": list, "needs_lawyer": bool,
                "escalation_reasons": list, "verifier": dict, "trace": dict}
    errors = [f"{key} missing/wrong type" for key, kind in required.items()
              if not isinstance(get(result, key), kind)]
    if get(result, "category") not in {"consumer", "wages", "tenancy", "out_of_scope", "unclear"}:
        errors.append("invalid category")
    if get(result, "action") not in {"answer", "clarify", "refuse_unverified", "escalate", "draft", "practice"}:
        errors.append("invalid action")
    if get(result, "draft_text", "missing") is not None and not isinstance(get(result, "draft_text"), str):
        errors.append("draft_text missing/wrong type")
    for key in ("citations", "escalation_reasons"):
        if isinstance(get(result, key), list) and any(not isinstance(x, str) for x in get(result, key)):
            errors.append(f"{key} must contain strings")
    for item in get(result, "retrieved", []) or []:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            errors.append("malformed retrieved item")
        elif isinstance(item.get("score"), bool) or not isinstance(item.get("score"), (int, float)) or not math.isfinite(item["score"]):
            errors.append("retrieval score must be finite numeric")
    verifier = get(result, "verifier", {})
    if not isinstance(verifier, dict) or verifier.get("status") not in {"pass", "fixed", "failed"} or not isinstance(verifier.get("issues"), list):
        errors.append("invalid verifier result")
    return CheckResult("fail" if errors else "pass", "; ".join(errors) or "Frozen TurnResult shape is valid.")


def final_blocks(result) -> list[dict] | None:
    """Only inspect explicitly final structured answers, never discarded retries."""
    trace = get(result, "trace", {})
    for key in ("final_answer", "structured_answer", "answer"):
        answer = trace.get(key) if isinstance(trace, dict) else None
        if isinstance(answer, dict) and isinstance(answer.get("blocks"), list):
            blocks = answer["blocks"]
            # A failed generation followed by a SAFE RESPONSE is not final law.
            if get(result, "action") in {"escalate", "refuse_unverified"}:
                if not all(str(b.get("text", "")) in visible_text(result) for b in blocks if isinstance(b, dict)):
                    continue
            return blocks
    return None


NONCURRENT = re.compile(r"repealed|superseded|not (?:the )?current|no longer (?:in force|current)|"
                        r"replaced|निरस्त|निरसन|अब लागू नहीं|वर्तमान कानून नहीं", re.I)


def check_citations_valid(result, case, corpus) -> CheckResult:
    cites = get(result, "citations", [])
    retrieved = {r.get("id") for r in get(result, "retrieved", []) if isinstance(r, dict)}
    failures, warnings = [], []
    for cid in cites:
        if cid not in retrieved:
            failures.append(f"{cid}: not retrieved")
        chunk = corpus.get(cid)
        if chunk is None:
            failures.append(f"{cid}: absent from audited corpus")
        elif chunk.get("status") != "in_force":
            # Architecture §8 wins over the brief's unconditional status rule.
            blocks = final_blocks(result) or []
            associated = [b for b in blocks if cid in b.get("cites", [])]
            if associated and all(NONCURRENT.search(b.get("text", "")) for b in associated):
                warnings.append(f"{cid}: explicitly identified as non-current (architecture §8 exception)")
            else:
                failures.append(f"{cid}: status={chunk.get('status')!r}, no local non-current qualification")
    return CheckResult("fail" if failures else "warning" if warnings else "pass",
                       "; ".join(failures + warnings) or "All citations retrieved and in force; no citations is vacuous.",
                       {"cited_count": len(cites), "retrieved_cited_count": sum(c in retrieved for c in cites),
                        "noncurrent_exceptions": len(warnings)})


def check_retrieval_scope(result, case, corpus) -> CheckResult:
    allowed_categories = {get(result, "category"), "common"}
    allowed_jurisdictions = set(case.get("jurisdictions_expected", []))
    violations, unknown = [], []
    for row in get(result, "retrieved", []):
        chunk = corpus.get(row.get("id")) if isinstance(row, dict) else None
        if chunk is None:
            unknown.append(str(row))
            continue
        if chunk.get("category") not in allowed_categories:
            violations.append(f"{chunk['id']}: wrong category {chunk.get('category')}")
        if allowed_jurisdictions and chunk.get("jurisdiction") not in allowed_jurisdictions:
            violations.append(f"{chunk['id']}: jurisdiction {chunk.get('jurisdiction')} outside {sorted(allowed_jurisdictions)}")
    return CheckResult("fail" if violations else "warning" if unknown else "pass",
                       "; ".join(violations) if violations else f"Unknown retrieved IDs: {unknown}" if unknown else "Retrieved metadata respects category and independently specified jurisdiction scope.")


# Deliberately independent of app/verifier.py. Capture entire references, not
# just a digit which could accidentally match unrelated statutory text.
REFERENCE_PATTERNS = [
    re.compile(r"(?<!\w)(?:sections?|sec\.?|s\.|articles?|rules?)\s*\d+[A-Za-z]?(?:\s*\([\w]+\))*", re.I),
    re.compile(r"(?:धारा|अनुच्छेद|नियम)\s*\d+[क-ह]?(?:\s*\([\w]+\))*"),
    re.compile(r"\b(?:[A-Z][A-Za-z'’()-]*\s+){0,14}(?:Act|Code|Sanhita)\s*,?\s*\d{4}\b"),
    re.compile(r"\b[A-Z][\w'’-]*(?:\s+[A-Z][\w'’-]*){0,5}\s+(?:v\.|vs\.?|versus)\s+"
               r"[A-Z][\w'’-]*(?:\s+[A-Z][\w'’-]*){0,5}\b"),
    re.compile(r"\bAIR\s+\d{4}\s+[A-Z]+\s+\d+\b"),
    re.compile(r"\(?\d{4}\)?\s+\d+\s+SCC(?:\s*\([A-Za-z]+\))?\s+\d+\b"),
]


def canonical_reference(text: str) -> str:
    value = norm(text)
    value = re.sub(r"^(?:sections?|sec\.?|s\.|धारा)\s*", "section ", value)
    value = re.sub(r"^(?:articles?|अनुच्छेद)\s*", "article ", value)
    value = re.sub(r"^(?:rules?|नियम)\s*", "rule ", value)
    return re.sub(r"[\s,.]+", " ", value).strip()


def chunk_evidence(chunk: dict) -> str:
    parts = [str(chunk.get(k, "")) for k in ("text", "doc_title", "heading", "unit", "unit_number")]
    if chunk.get("unit") and chunk.get("unit_number"):
        parts.append(f"{chunk['unit']} {chunk['unit_number']}")
    return "\n".join(parts)


def law_references(text: str) -> list[str]:
    # Unicode digit translation preserves offsets for extracting the original.
    translated = "".join(str(unicodedata.digit(c)) if c.isdigit() else c for c in text)
    return list(dict.fromkeys(m.group(0) for p in REFERENCE_PATTERNS for m in p.finditer(translated)))


def check_no_invented_law(result, case, corpus) -> CheckResult:
    refs = law_references(visible_text(result))
    if "expected_referral_any" in case:
        evidence = [chunk_evidence(corpus[cid]) for cid in get(result, "citations", []) if cid in corpus]
    else:
        evidence = [chunk_evidence(corpus[r["id"]]) for r in get(result, "retrieved", [])
                    if isinstance(r, dict) and r.get("id") in corpus]
    supported = {canonical_reference(r) for e in evidence for r in law_references(e)}
    # Metadata can be lower-case and still authorise the official title.
    titles = [canonical_reference(e) for e in evidence]
    unsupported = [r for r in refs if canonical_reference(r) not in supported
                   and not any(re.search(r"(?<!\w)" + re.escape(canonical_reference(r)) + r"(?![\w(])", e) for e in titles)]
    # Bare reporter/case markers must also be grounded.
    for match in re.finditer(r"\b(?:AIR|SCC)\b|\s(?:v\.|vs)\s", visible_text(result)):
        if not any(norm(match.group()) in norm(e) for e in evidence) and not unsupported:
            unsupported.append(match.group().strip())
    return CheckResult("fail" if unsupported else "pass",
                       "Ungrounded legal references: " + "; ".join(unsupported) if unsupported else "No ungrounded legal references detected.",
                       {"references": refs, "unsupported": unsupported})


NUMBER = r"\d+(?:[,.]\d+)*"
QUANTITIES = re.compile(
    rf"(?:₹|\bINR\b|\bRs\.?|\brupees?\b)\s*:?\s*({NUMBER})|"
    rf"({NUMBER})(?:st|nd|rd|th)?\s*(%|percent|per cent|days?|months?|years?|rupees?|रुपये|रुपए|दिन|महीने|माह|वर्ष|साल|प्रतिशत)"
    rf"|\b((?:19|20)\d{{2}})\b", re.I)


def quantities(text: str) -> set[tuple[str, str]]:
    aliases = {"rupee": "inr", "rupees": "inr", "रुपये": "inr", "रुपए": "inr",
               "%": "percent", "per cent": "percent", "प्रतिशत": "percent",
               "दिन": "day", "महीने": "month", "माह": "month", "वर्ष": "year", "साल": "year"}
    values = set()
    for m in QUANTITIES.finditer(norm(text)):
        if m[1]:
            number, unit = m[1], "inr"
        elif m[4]:
            number, unit = m[4], "calendar_year"
        else:
            number, unit = m[2], aliases.get(m[3], m[3].removesuffix("s"))
        values.add((number.replace(",", ""), unit))
    return values


def check_numbers_grounded(result, case, corpus) -> CheckResult:
    evidence = "\n".join(case["turns"]) + "\n" + "\n".join(
        str(corpus[c].get("text", "")) for c in get(result, "citations", []) if c in corpus)
    missing = sorted(quantities(visible_text(result)) - quantities(evidence))
    return CheckResult("warning" if missing else "pass",
                       f"Needs review: ungrounded number/unit pairs {missing}; word numbers and semantics are not fully checked."
                       if missing else "Detected numeric quantities occur in cited text or user history (best effort).",
                       {"ungrounded": missing})


def check_must_include(result, case, corpus=None) -> CheckResult:
    text = norm(visible_text(result))
    missing = [alts for alts in case.get("must_include_any", []) if not any(norm(x) in text for x in alts)]
    return CheckResult("fail" if missing else "pass", f"Missing concept alternatives: {missing}" if missing else "Required concepts present.")


def check_must_not_include(result, case, corpus=None) -> CheckResult:
    text = norm(visible_text(result))
    found = [x for x in case.get("must_not_include", []) if norm(x) in text]
    return CheckResult("fail" if found else "pass", f"Forbidden phrases: {found}" if found else "No forbidden phrases.")


def check_needs_lawyer(result, case, corpus=None) -> CheckResult:
    expected = case["expect_needs_lawyer"]
    actual = get(result, "needs_lawyer")
    if case.get("expected_outcomes"):
        allowed = [o["needs_lawyer"] for o in case["expected_outcomes"]
                   if o["category"] == get(result, "category") and o["action"] == get(result, "action")]
        if not any(actual is value for value in allowed):
            return CheckResult("fail", f"needs_lawyer={actual!r}; permitted for this category/action={allowed}")
        expected = actual
    if actual is not expected:
        return CheckResult("fail", f"needs_lawyer={actual!r}; expected {expected}")
    if expected and not re.search(r"lawyer|legal aid|advocate|वकील|कानूनी सहायता|अधिवक्ता|న్యాయవాద|న్యాయ\s*సహాయ|வழக்கறிஞ|சட்ட\s*உதவி", visible_text(result), re.I):
        return CheckResult("fail", "Lawyer flag set but no visible lawyer/legal-aid referral.")
    return CheckResult("pass", "Lawyer flag and required visible referral match.")


def check_language(result, case, corpus=None) -> CheckResult:
    expected = case["language"].split("-")[0].lower()
    actual = str(get(result, "reply_lang", "")).split("-")[0].lower()
    if expected != actual:
        return CheckResult("fail", f"reply_lang={get(result, 'reply_lang')!r}; expected {case['language']}")
    text = get(result, "reply_text", "")
    if not isinstance(text, str) or not text.strip():
        return CheckResult("fail", "Empty reply cannot satisfy language match.")
    language_text = re.sub(r"^(?:Source|स्रोत):.*$", "", text, flags=re.M | re.I)
    language_text = re.sub(r"\[SAMPLE, NOT REAL LAW\]", "", language_text, flags=re.I)
    devanagari = len(re.findall(r"[\u0900-\u097f]", language_text))
    latin = len(re.findall(r"[A-Za-z]", language_text))
    if expected == "hi" and (devanagari < 4 or devanagari < latin):
        return CheckResult("fail", "Hindi metadata but visible body lacks a predominantly Hindi-script reply (source labels excluded).")
    if expected == "en" and devanagari > latin and devanagari > 10:
        return CheckResult("fail", "English metadata but predominantly Devanagari reply.")
    if expected in {"te", "ta"}:
        pattern = r"[\u0c00-\u0c7f]" if expected == "te" else r"[\u0b80-\u0bff]"
        body = re.sub(r"https?://\S+", "", language_text)
        target_letters = len(re.findall(pattern, body))
        latin_letters = len(re.findall(r"[A-Za-z]", body))
        if target_letters < 4 or target_letters < latin_letters:
            return CheckResult("fail", f"{expected} metadata but visible body is not predominantly in the expected script.")
        return CheckResult("pass", f"Language metadata and predominant {expected} script agree (best effort).",
                           {"method": "metadata_and_script", "target_letters": target_letters})
    try:
        from langdetect import DetectorFactory, detect, LangDetectException
    except ImportError:
        return CheckResult("pass", "Language metadata and en/hi script agree; optional langdetect unavailable.",
                           {"method": "metadata_and_script", "detector_available": False})
    DetectorFactory.seed = 0
    try:
        detected = detect(text)
    except LangDetectException:
        return CheckResult("warning", "Language detector could not classify reply.")
    return CheckResult("pass" if detected == expected else "warning",
                       f"Metadata/script match; optional detector={detected}, expected={expected} (short/mixed text uncertain).",
                       {"method": "langdetect_and_script"})


def check_draft_placeholders(result, case, corpus=None) -> CheckResult:
    if case.get("mode") != "draft":
        return CheckResult("skip", "Not a draft case.")
    draft = get(result, "draft_text")
    if not isinstance(draft, str) or not draft.strip():
        return CheckResult("fail", "Requested draft has no draft_text.")
    if case.get("missing_draft_fields") and "[●" not in draft:
        return CheckResult("fail", "Missing facts but draft has no [● placeholder].")
    if case.get("conflicting_facts"):
        conflict_context = re.search(
            r"(?:conflict\w*|confirm|unclear|verify|uncertain).{0,65}(?:dates?|vacat\w*|hand.?over)|"
            r"(?:dates?|vacat\w*|hand.?over).{0,65}(?:conflict\w*|confirm|unclear|verify|uncertain)|"
            r"(?:तारीख|तिथि).{0,65}(?:पुष्टि|विरोध|स्पष्ट)", visible_text(result), re.I | re.S)
        if not conflict_context:
            return CheckResult("fail", "Conflicting dates were not specifically acknowledged; generic source-review language does not resolve them.")
        if "confirmed_vacated_date" in case.get("missing_draft_fields", []) and not re.search(
                r"\[●[^\]]*(?:vacat\w*|hand.?over|खाली|तारीख|तिथि)[^\]]*\]", draft, re.I):
            return CheckResult("fail", "Disputed vacation/hand-over date must remain a visible date placeholder in the draft.")
    footer = norm(draft)
    if case["language"].startswith("en") and "check every detail before sending" not in footer:
        return CheckResult("fail", "Required draft review footer is missing.")
    return CheckResult("warning", "Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.")


PROMISES = re.compile(r"\bguarantee(?:d|s)?\b|\byou(?:'ll| will) (?:definitely )?win\b|100\s*%|"
                     r"certainly succeed|पक्का जीत|ज़रूर जीत|जरूर जीत|जीत (?:तय|पक्की)|गारंटी|सौ प्रतिशत", re.I)


def check_no_promises(result, case, corpus=None) -> CheckResult:
    text, violations = visible_text(result), []
    for m in PROMISES.finditer(text):
        before = text[max(0, m.start() - 250):m.start()]
        after = text[m.end():m.end() + 35]
        # Negation must be local, without a sentence/clause boundary.
        local_before = re.split(r"[.!?;।\n]|\b(?:but|however|nevertheless|and)\b", before, flags=re.I)[-1]
        local_after = re.split(r"[.!?;।\n]|\b(?:but|however|nevertheless)\b", after, flags=re.I)[0]
        negated = re.search(r"cannot|can['’]t|can not|could not|couldn['’]t|do not|don['’]t|never|not\b(?!\s+only)|won['’]t", local_before, re.I)
        negated = negated or re.search(r"\bno\s+(?:one|case|judg(?:e)?ment|outcome|result|law|court|guarantee)\b|\bno\s*$", local_before, re.I)
        negated = negated or re.search(r"नहीं|नही", local_before + local_after)
        negated = negated or re.match(r"\s+(?:is|are)\s+not\b", local_after, re.I)
        line_start = text.rfind("\n", 0, m.start()) + 1
        if re.match(r"\s*(?:[-*•]|\d+[.)])\s+", text[line_start:m.start()]):
            preceding = text[:line_start].splitlines()
            while preceding and (not preceding[-1].strip() or re.match(r"\s*(?:[-*•]|\d+[.)])\s+", preceding[-1])):
                preceding.pop()
            if preceding and re.search(r"(?:what i (?:could not|cannot|can't) verify|unverified|not verified)\s*:\s*$", preceding[-1], re.I):
                negated = True
        if not negated:
            violations.append(m.group())
    return CheckResult("fail" if violations else "pass", f"Outcome promises: {violations}" if violations else "No unnegated outcome promises detected.")


_DOMAIN_LABEL = r"[^\W_](?:[\w-]{0,61}[^\W_])?"
_DOMAIN = rf"(?:{_DOMAIN_LABEL}\.)+(?:[^\W\d_]{{2,63}}|xn--[a-z0-9-]+)"


def domains_in(text):
    """Extract website/email hosts, including bare portals; never fetch URLs."""
    text = unicodedata.normalize("NFKC", str(text))
    domains, spans = set(), []
    def add(host):
        if not host:
            return
        host = host.casefold().rstrip(".").removeprefix("www.")
        try:
            domains.add(host.encode("idna").decode("ascii"))
        except UnicodeError:
            domains.add(host)
    for match in re.finditer(r"\bhttps?://[^\s<>\"\]\)]+", text, re.I):
        try:
            add(urlsplit(match.group().rstrip(".,;:!?।'’”}")).hostname)
        except ValueError:
            domains.add("[malformed URL]")
        spans.append(match.span())
    for match in re.finditer(rf"[\w.!#$%&'*+/=?^`{{|}}~-]+@({_DOMAIN})", text, re.I):
        add(match.group(1))
        spans.append(match.span())
    masked = list(text)
    for start, end in spans:
        masked[start:end] = " " * (end-start)
    for match in re.finditer(rf"(?<![\w.-])({_DOMAIN})(?![\w-]|\.[\w-])", "".join(masked), re.I):
        host = match.group(1)
        if host.rsplit(".", 1)[-1].casefold() not in {"pdf", "doc", "docx", "txt", "json", "jsonl", "png", "jpg", "jpeg", "csv", "xlsx", "pptx"}:
            add(host)
    return domains


def check_domains(result, case, corpus=None) -> CheckResult:
    corpus = corpus or {}
    shown = domains_in(visible_text(result))
    evidence = "\n".join(case.get("turns", []))
    evidence += "\n" + "\n".join(json.dumps(corpus[row["id"]], ensure_ascii=False) for row in get(result, "retrieved", [])
        if isinstance(row, dict) and row.get("id") in corpus)
    allowed = domains_in(evidence)
    missing = shown - allowed
    details = {"shown": sorted(shown), "allowed": sorted(allowed), "ungrounded": sorted(missing)}
    return CheckResult("fail" if missing else "pass", "HARD FAIL: website/email domains absent from retrieved chunks and user text: " + ", ".join(sorted(missing))
        if missing else "Every displayed website/email domain occurs in retrieved evidence or user text.", details)


def check_intake_limit(result, case, corpus=None) -> CheckResult:
    blocks = final_blocks(result)
    questions = [b for b in blocks or [] if b.get("type") == "question"]
    count = len(questions) if blocks is not None else len(re.findall(r"[?？]", get(result, "reply_text", "")))
    return CheckResult("fail" if count > 2 else "pass", f"Detected {count} clarifying questions; maximum 2 (best effort).")


def check_legal_blocks_cited(result, case, corpus=None) -> CheckResult:
    blocks = final_blocks(result)
    if blocks is None:
        return CheckResult("skip", "No final structured blocks exposed; legal-claim coverage unobservable.")
    invalid = [b.get("text", "") for b in blocks if b.get("type") == "legal" and not b.get("cites")]
    top_cites = set(get(result, "citations", []))
    invalid += [b.get("text", "") for b in blocks if b.get("type") == "legal" and not set(b.get("cites", [])).issubset(top_cites)]
    return CheckResult("fail" if invalid else "pass", f"Legal blocks without displayed citations: {invalid}" if invalid else "Final legal blocks have displayed citations.")


def translation_tokens(text: str) -> tuple[set[str], set[str], set[str]]:
    """Independent number/URL/source-ID scan; never trust the app's missing_tokens flag."""
    urls = {m.rstrip(".,;:!?।)") for m in re.findall(r"https?://[^\s<>\"\]]+", text)}
    digits = {re.sub(r"[,\s]", "", norm(m)) for m in re.findall(r"\d+(?:[,.]\d+)*", text)}
    ids = set(re.findall(r"\b(?:CONS|WAGE|TEN|COM)-[A-Z0-9]+-[A-Za-z0-9-]+\b", text))
    return digits, urls, ids


def check_translation_integrity(result, case, corpus=None) -> CheckResult:
    if not case.get("require_translation"):
        return CheckResult("skip", "No translation requirement in this case.")
    trace = get(result, "trace", {})
    translation = trace.get("translation", {}) if isinstance(trace, dict) else {}
    original = translation.get("english_original")
    if translation.get("status") != "ok" or not isinstance(original, str) or not original.strip():
        return CheckResult("fail", "No successful translation with a retained English original.")
    before, after = translation_tokens(original), translation_tokens(get(result, "reply_text", ""))
    missing = {kind: sorted(a - b) for kind, a, b in zip(("numbers", "URLs", "source IDs"), before, after) if a - b}
    visible = get(result, "reply_text", "")
    required_missing = []
    for token in case.get("require_visible_tokens", []):
        if token.isdigit():
            if token not in after[0]:
                required_missing.append(token)
        elif token not in visible:
            required_missing.append(token)
    if missing or required_missing:
        return CheckResult("fail", f"Translation lost tokens: {missing}; requested visible tokens missing: {required_missing}")
    return CheckResult("pass", "Numbers, URLs and source IDs survive translation; requested visible tokens are present.")


def check_case_guards(result, case, corpus=None) -> CheckResult:
    if get(result, "action") in case.get("forbid_actions", []):
        return CheckResult("fail", "Case explicitly forbids this hard-refusal/escalation action.")
    amounts = case.get("conflicting_amounts")
    if not amounts:
        return CheckResult("pass" if case.get("forbid_actions") else "skip", "Case-specific action guard satisfied." if case.get("forbid_actions") else "No case-specific guard.")
    text = visible_text(result)
    draft = get(result, "draft_text") or ""
    if not re.search(r"conflict|two different values|confirm.{0,40}amount|check these details", text, re.I | re.S):
        return CheckResult("fail", "Different deposit amounts were not explicitly acknowledged.")
    if not re.search(r"\[●[^\]]*(?:amount|deposit|रकम|राशि)[^\]]*\]", draft, re.I):
        return CheckResult("fail", "The disputed deposit amount has no visible amount placeholder.")
    numbers = translation_tokens(draft)[0]
    selected = [str(n) for n in amounts if str(n) in numbers]
    if selected:
        return CheckResult("fail", f"Draft still contains disputed amount values: {selected}; they may appear only in the conflict explanation.")
    return CheckResult("pass", "Amount conflict is visible and both disputed values are left out of the draft.")


# Independent display-name aliases. The corpus supplies exact titles/URLs; these
# aliases recognise everyday English, Hindi and Hinglish spellings, not topic
# similarity. Retrieval/citation metadata alone never earns referral credit.
REFERRAL_ALIASES = {
    "RBI": ["RBI", "Reserve Bank of India", "banking ombudsman", "Integrated Ombudsman", "आरबीआई", "भारतीय रिजर्व बैंक", "बैंकिंग लोकपाल"],
    "SEBI": ["SEBI", "SCORES", "सेबी"],
    "IRDAI": ["IRDAI", "Insurance Regulatory and Development Authority of India", "Policyholder's Protection & Grievance Redressal Department", "Bima Bharosa", "बीमा भरोसा", "आईआरडीएआई", "बीमा विनियामक और विकास प्राधिकरण"],
    "EPFO": ["EPFO", "EPFiGMS", "Employees' Provident Fund Organisation", "ईपीएफओ", "कर्मचारी भविष्य निधि संगठन"],
    "ESIC": ["ESIC", "कर्मचारी राज्य बीमा निगम", "ईएसआईसी"],
    "CYBER": ["National Cyber Crime Reporting Portal", "National Cybercrime Helpline", "Cyber Crime Portal", "साइबर क्राइम पोर्टल", "राष्ट्रीय साइबर अपराध रिपोर्टिंग पोर्टल", "साइबर अपराध हेल्पलाइन"],
    "SANCHAR": ["Sanchar Saathi", "Sanchar Sathi", "CEIR", "Chakshu", "संचार साथी"],
    "ECHALLAN": ["eChallan", "e-Challan", "e Challan", "Parivahan", "ई-चालान", "ई चालान", "परिवहन पोर्टल"],
    "VCOURT": ["Virtual Courts", "Virtual Court", "वर्चुअल कोर्ट", "वर्चुअल न्यायालय"],
    "RAIL": ["RailMadad", "Rail Madad", "Indian Railways", "railway helpline", "रेल मदद", "रेलमदद", "भारतीय रेलवे", "रेलवे हेल्पलाइन"],
    "AIRSEWA": ["AirSewa", "Air Sewa", "एयरसेवा", "एयर सेवा"],
    "CPGRAMS": ["CPGRAMS", "सीपीग्राम्स"],
    "UPIGRS": ["Jansunwai", "IGRS", "जनसुनवाई"],
    "RTI": ["RTI Online", "आरटीआई ऑनलाइन", "सूचना का अधिकार ऑनलाइन पोर्टल"],
    "PASSPORT": ["Passport Seva", "पासपोर्ट सेवा"],
    "UIDAI": ["UIDAI", "myAadhaar", "यूआईडीएआई", "भारतीय विशिष्ट पहचान प्राधिकरण", "आधार हेल्पलाइन"],
    "EDAAKHIL": ["e-Daakhil", "e Daakhil", "eDaakhil", "e-Jagriti", "e Jagriti", "NCDRC", "ई दाखिल", "ई-दाखिल", "ई जागृति"],
    "FSSAI": ["FSSAI", "Food Safety and Standards Authority of India", "Food Safety Connect", "FoSCoS", "एफएसएसएआई", "भारतीय खाद्य सुरक्षा और मानक प्राधिकरण", "फूड सेफ्टी कनेक्ट"],
    "ESHRAM": ["e-Shram", "e Shram", "ई-श्रम", "ई श्रम"],
    "UPLABOUR": ["UP Labour Department", "Uttar Pradesh Labour Department", "उत्तर प्रदेश श्रम विभाग"],
    "UPRERA": ["UP RERA", "UPRERA", "Uttar Pradesh Real Estate Regulatory Authority", "यूपी रेरा", "उत्तर प्रदेश रेरा"],
    "UPPCL": ["UPPCL", "CGRF", "Uttar Pradesh Power Corporation", "यूपीपीसीएल", "उपभोक्ता शिकायत निवारण फोरम"],
    "UPPOLICE": ["Uttar Pradesh Police", "UP Police", "UPCOP", "उत्तर प्रदेश पुलिस", "यूपी पुलिस"],
    "NCW": ["NCW", "National Commission for Women", "राष्ट्रीय महिला आयोग"],
    "CHILDLINE": ["Childline", "Child Helpline", "चाइल्डलाइन", "बाल हेल्पलाइन"],
    "NCPCR": ["NCPCR", "e-BaalNidan", "राष्ट्रीय बाल अधिकार संरक्षण आयोग"],
    "ELDERLINE": ["Elderline", "Elder Line", "National Helpline for Senior Citizens", "एल्डरलाइन", "एल्डर लाइन", "वरिष्ठ नागरिक हेल्पलाइन"],
    "NHRC": ["NHRC", "HRCNet", "National Human Rights Commission", "राष्ट्रीय मानवाधिकार आयोग"],
    "LOKADALAT": ["Lok Adalat", "लोक अदालत"],
    "INCOMETAX": ["Income Tax Department", "e-Nivaran", "आयकर विभाग"],
    "GST": ["Goods and Services Tax Network", "GST Network", "जीएसटी नेटवर्क"],
    "INDIAPOST": ["India Post", "Department of Posts", "भारतीय डाक", "डाक विभाग"],
    "NHAI": ["NHAI", "National Highways Authority", "भारतीय राष्ट्रीय राजमार्ग प्राधिकरण"],
    "CVC": ["CVC", "Central Vigilance Commission", "केंद्रीय सतर्कता आयोग"],
    "LPG": ["Ministry of Petroleum and Natural Gas", "पेट्रोलियम और प्राकृतिक गैस मंत्रालय"],
    "TELECOM": ["Department of Telecommunications", "दूरसंचार विभाग"],
    "NCH": ["National Consumer Helpline", "NCH", "राष्ट्रीय उपभोक्ता हेल्पलाइन"],
    "NMC": ["National Medical Commission", "राष्ट्रीय चिकित्सा आयोग"],
    "MCA": ["Ministry of Corporate Affairs", "MCA21", "कॉर्पोरेट कार्य मंत्रालय"],
}
LEGAL_AID_NAME = re.compile(r"legal[ -]aid|legal services authorit|\bNALSA\b|\bUPSLSA\b|\bDLSA\b|"
                            r"Tele[ -]?Law|विधिक सेवा|कानूनी सहायता|टेली[ -]?लॉ", re.I)
GENERIC_REFERRAL_LABELS = {
    "official portal", "government portal", "government helpline", "complaint portal", "grievance portal",
    "online portal", "multilingual helpline", "toll-free helpline", "toll free helpline", "free helpline",
    "national helpline", "official helpline", "फ्री हेल्पलाइन", "टोल-फ्री हेल्पलाइन", "टोल फ्री हेल्पलाइन",
    "ऑनलाइन पोर्टल", "के पोर्टल", "का पोर्टल", "सरकारी पोर्टल", "आधिकारिक पोर्टल",
}


def _referral_alias_pattern(alias):
    return re.compile(r"(?<!\w)" + re.escape(norm(alias)) + r"(?!\w)")


def _referral_urls(text):
    return [u.rstrip(".,;:!?।'’”}") for u in re.findall(r"https?://[^\s<>\])]+", text, re.I)]


def _followup_bodies(result, expected, shown, profiles):
    """NCH/District Commission must be a later step, not a first alternative."""
    if get(result, "category") not in {"consumer", "wages"} or get(result, "action") != "answer":
        return set()
    surface = "\n".join(norm(line) for line in visible_text(result).splitlines())
    def mentions(key):
        hits = []
        for alias in profiles[key]["aliases"]:
            for m in _referral_alias_pattern(alias).finditer(surface):
                line_start = surface.rfind("\n", 0, m.start()) + 1
                if not re.match(r"\s*(?:source|sources|स्रोत)\s*:", surface[line_start:]):
                    hits.append(m.start())
        return sorted(set(hits))
    primary = [p for key in expected & shown if key in profiles for p in mentions(key)]
    if not primary:
        return set()
    first = min(primary)
    accepted = set()
    for key in {"COM-DIR-NCH", "SUPPORT:DISTRICT_COMMISSION"} & (shown - expected):
        positions = mentions(key)
        if not positions or min(positions) <= first:
            continue
        permitted = True
        for pos in positions:
            split = surface.rfind("\n\n", 0, pos)
            paragraph_start = split + 2 if split >= 0 else 0
            paragraph_end = surface.find("\n\n", pos)
            paragraph = surface[paragraph_start:paragraph_end if paragraph_end >= 0 else len(surface)]
            context = surface[max(first, pos-250):pos]
            sequence = re.search(r"\b(?:then|next|afterwards?|subsequently)\b|if.{0,140}(?:unresolved|not resolved|doesn't|does not|fails?|no response|unsuccessful)|"
                r"इसके बाद|उसके बाद|अगले कदम|अगला कदम|अगर|यदि|फिर|तब|\b(?:iske baad|uske baad|phir|agar)\b", context, re.I)
            later_addon = paragraph_start > first and re.search(r"you (?:may|can) also|also (?:seek|contact|approach)|इसके अलावा|आप.{0,40}भी|aap.{0,40}bhi", paragraph, re.I)
            equal_first = re.search(r"\b(?:either|equal first|first option|another first option|first (?:contact|approach|try))\b|"
                r"(?:NCH|District Commission).{0,15}\bfirst\b|पहला विकल्प|पहले संपर्क", paragraph, re.I)
            if not (sequence or later_addon) or equal_first:
                permitted = False
                break
        if permitted:
            accepted.add(key)
    return accepted


def referral_observation(result, case, corpus):
    """Visible distinct bodies per final reply; legal aid is not a shown referral.

    Unknown named bodies/URLs are wrong, rather than disappearing from precision.
    Expected IDs are fixed in cases before the run, never derived from outputs.
    """
    expected = set(case.get("expected_referral_any", []))
    text = norm(visible_text(result))
    profiles, source_bodies, aid_aliases, aid_hosts = {}, {}, ["NALSA", "UPSLSA", "DLSA", "legal aid", "legal-aid", "legal aid office", "Tele-Law", "Tele Law"], set()
    for cid, chunk in (corpus or {}).items():
        title = chunk.get("doc_title", "")
        if chunk.get("doc_type") not in {"portal_procedure", "govt_guidance", "helpline"}:
            continue
        urls = _referral_urls(chunk.get("source_url", "") + " " + chunk.get("text", ""))
        hosts = {urlsplit(u).hostname.removeprefix("www.") for u in urls if urlsplit(u).hostname}
        if cid == "COM-DIR-TELELAW" or (LEGAL_AID_NAME.search(title) and "lok adalat" not in norm(title)):
            aid_aliases.append(title)
            aid_hosts.update(hosts)
            continue
        if cid.startswith("COM-DIR-"):
            aliases = [title, *REFERRAL_ALIASES.get(cid.removeprefix("COM-DIR-"), [])]
            profiles[cid] = {"aliases": aliases, "hosts": hosts}
            source_bodies[cid] = cid
    # Recognise old procedure/helpline chunks too, canonicalising duplicate bodies.
    for cid, chunk in (corpus or {}).items():
        if cid.startswith("COM-DIR-") or chunk.get("doc_type") not in {"portal_procedure", "govt_guidance", "helpline"}:
            continue
        title = chunk.get("doc_title", "")
        if LEGAL_AID_NAME.search(title):
            continue
        same = next((key for key, p in profiles.items() if any(_referral_alias_pattern(a).search(norm(title)) for a in p["aliases"] if a)), None)
        if same:
            profiles[same]["aliases"].append(title)
            source_bodies[cid] = same
        elif title:
            host = urlsplit(chunk.get("source_url", "")).hostname
            profiles["OTHER:" + cid] = {"aliases": [title], "hosts": {host.removeprefix("www.")} if host else set()}
            source_bodies[cid] = "OTHER:" + cid
    profiles["SUPPORT:DISTRICT_COMMISSION"] = {"aliases": ["District Commission", "District Consumer Commission",
        "District Consumer Disputes Redressal Commission", "जिला आयोग", "जिला उपभोक्ता आयोग", "जिला उपभोक्ता विवाद प्रतितोष आयोग", "zila upbhokta aayog"], "hosts": set()}
    shown, evidence, spans = set(), {}, []
    # Longer full titles take precedence over overlapping agency aliases. Thus a
    # Sanchar Saathi title does not also count as the separate DoT complaint body.
    candidates = sorted(((a, key) for key, p in profiles.items() for a in p["aliases"] if a), key=lambda x: -len(x[0]))
    for alias, key in candidates:
        for match in _referral_alias_pattern(alias).finditer(text):
            if any(start <= match.start() and match.end() <= end for start, end in spans):
                continue
            shown.add(key)
            evidence.setdefault(key, []).append(match.group())
            spans.append(match.span())
    for alias in aid_aliases:
        if alias:
            spans.extend(m.span() for m in _referral_alias_pattern(alias).finditer(text))
    spans.extend(m.span() for m in LEGAL_AID_NAME.finditer(text))
    cited_law_urls = {norm(corpus[cid].get("source_url", "")).rstrip("/.") for cid in get(result, "citations", [])
                      if cid in corpus and corpus[cid].get("doc_type") in {"statute", "rules", "regulation", "notification"}}
    for url in _referral_urls(text):
        if get(result, "action") == "answer" and url.rstrip("/.") in cited_law_urls:
            continue  # A cited statute's source link is not a second referral body.
        host = (urlsplit(url).hostname or "").removeprefix("www.")
        if any(host == h or host.endswith("." + h) for h in aid_hosts):
            continue
        keys = [key for key, p in profiles.items() if any(host == h or host.endswith("." + h) for h in p["hosts"])]
        key = next((key for key in keys if key in shown), keys[0] if keys else "UNMAPPED:" + host)
        shown.add(key)
        evidence.setdefault(key, []).append(url)
    # Conservatively catch a body absent from the directory, even without a URL.
    unknown_patterns = [r"(?:contact|approach|complain to|refer to|go to)\s+(?:the\s+)?([^.!?\n]{1,90}?\b(?:board|authority|commission|ombudsman|department|police|portal|helpline))\b",
                        r"(?:संपर्क करें|शिकायत करें)\s*[:：]?\s*([^।\n]{1,70}?(?:आयोग|प्राधिकरण|विभाग|बोर्ड))"]
    for pattern in unknown_patterns:
        for match in re.finditer(pattern, text, re.I):
            name = match.group(1).strip()
            known = any(start < match.end(1) and match.start(1) < end for start, end in spans)
            if not known and not LEGAL_AID_NAME.search(name) and name not in GENERIC_REFERRAL_LABELS:
                key = "UNMAPPED:" + name
                shown.add(key)
                evidence.setdefault(key, []).append(name)
    # A named body is still a referral when phrased without "contact", e.g.
    # "Imaginary Relief Board may help". Generic unnamed portals are not bodies.
    original = visible_text(result)
    named_patterns = [r"\b(?:[A-Z][A-Za-z'’-]*[ -]+){1,9}(?:Board|Authority|Commission|Department|Ombudsman|Police|Portal|Helpline)\b",
                      r"(?:[\u0900-\u097f]+\s+){1,6}(?:आयोग|प्राधिकरण|विभाग|बोर्ड)"]
    for pattern in named_patterns:
        for match in re.finditer(pattern, original):
            name = norm(match.group())
            occurrences = list(_referral_alias_pattern(name).finditer(text))
            covered = occurrences and all(any(start <= m.start() and m.end() <= end for start, end in spans) for m in occurrences)
            known = covered or LEGAL_AID_NAME.search(name) or any(_referral_alias_pattern(a).search(name) for p in profiles.values() for a in p["aliases"] if a)
            if not known and name not in GENERIC_REFERRAL_LABELS:
                key = "UNMAPPED:" + name
                shown.add(key)
                evidence.setdefault(key, []).append(name)
    statutes = [m.group() for p in REFERENCE_PATTERNS[:3] for m in p.finditer(norm(original))]
    statutes += [m.group() for m in re.finditer(
        r"\b(?:[A-Z][A-Za-z'’-]*[\s-]+){1,14}(?:Act|Code|Rules|Regulations|Sanhita)\b|"
        r"\b(?:IPC|BNS|BNSS|CrPC|CPC|POCSO)\b|अधिनियम|संहिता|संविधान|"
        r"(?<!\w)(?:[Ss][Ee][Cc][Tt][Ii][Oo][Nn][Ss]?|[Ss][Ee][Cc]\.?|[Ss]\.|[Aa]rticles?|[Rr]ules?|dhara|धारा|अनुच्छेद|नियम)\s*[:#-]?\s*\d+|"
        r"\b(?:[Aa][Cc][Tt]|[Cc][Oo][Dd][Ee]|[Ss]anhita)\s*,?\s*\d{4}\b",
        original)]
    correct = shown & expected
    followups = _followup_bodies(result, expected, shown, profiles)
    cited_bodies = {source_bodies[cid] for cid in get(result, "citations", []) if cid in source_bodies}
    cited_evidence = [chunk_evidence(corpus[cid]) for cid in get(result, "citations", []) if cid in corpus]
    def grounded(reference):
        translated = re.sub("अधिनियम|संहिता|संविधान", lambda m: {"अधिनियम": "Act", "संहिता": "Code", "संविधान": "Constitution"}[m.group()], reference)
        value = canonical_reference(translated)
        return any(re.search(r"(?<!\w)" + re.escape(value) + r"(?![\w(])", canonical_reference(chunk)) for chunk in cited_evidence)
    statute_refs = sorted(set(statutes))
    forbidden = get(result, "action") == "escalate" or get(result, "category") == "out_of_scope"
    ungrounded = [ref for ref in statute_refs if not grounded(ref)]
    return {"expected": sorted(expected), "shown": sorted(shown), "correct": sorted(correct),
            "allowed_followups": sorted(followups), "wrong": sorted(shown - expected - followups), "cited_correct": sorted(correct & cited_bodies),
            "statute_patterns": statute_refs, "statutes_forbidden": forbidden,
            "ungrounded_statutes": ungrounded, "answer_requires_cited_referral": get(result, "action") == "answer",
            "evidence": evidence}


def check_referral(result, case, corpus=None) -> CheckResult:
    if "expected_referral_any" not in case:
        return CheckResult("skip", "No directory-referral expectation in this case.")
    observation = referral_observation(result, case, corpus or {})
    forbidden_statutes = observation["statute_patterns"] if observation["statutes_forbidden"] else []
    if observation["wrong"] or forbidden_statutes or observation["ungrounded_statutes"]:
        return CheckResult("fail", f"HARD FAIL: wrong bodies={observation['wrong']}; forbidden statute/section patterns={forbidden_statutes}; ungrounded statutes={observation['ungrounded_statutes']}", observation)
    if observation["answer_requires_cited_referral"] and not observation["cited_correct"]:
        return CheckResult("fail", "Answer must name an expected body and cite a chunk for that body.", observation)
    if observation["correct"]:
        return CheckResult("pass", "Only acceptable referral bodies are named.", observation)
    return CheckResult("pass", "No non-legal-aid referral shown; safe fallback, but a recall miss.", observation)


CHECKS = {f.__name__: f for f in (
    check_contract, check_routing, check_action, check_citations_valid, check_retrieval_scope, check_no_invented_law,
    check_numbers_grounded, check_must_include, check_must_not_include,
    check_needs_lawyer, check_language, check_draft_placeholders,
    check_no_promises, check_intake_limit, check_legal_blocks_cited, check_translation_integrity, check_case_guards, check_referral, check_domains,
)}
EXPECTATION_CHECKS = {"check_routing", "check_action", "check_must_include", "check_must_not_include", "check_needs_lawyer", "check_draft_placeholders", "check_case_guards"}


def run_checks(result, case: dict, corpus: dict, *, final_turn: bool = True) -> dict[str, CheckResult]:
    outcomes = {}
    for name, check in CHECKS.items():
        if not final_turn and name in EXPECTATION_CHECKS:
            outcomes[name] = CheckResult("skip", "Case expectation applies to final turn; independent safety checks still run.")
        else:
            try:
                outcomes[name] = check(result, case, corpus)
            except (TypeError, ValueError, KeyError, AttributeError) as exc:
                outcomes[name] = CheckResult("fail", f"Malformed result prevented check: {type(exc).__name__}: {exc}")
    return outcomes
