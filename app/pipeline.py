"""handle_turn(): the ONLY entry point tests and the UI use (Architecture Sections 6, 7, 8, 10)."""
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field

from . import drafts, guards, llm, retrieval, router, verifier
from .config import ROOT, load_config, read_prompt, resolve

log = logging.getLogger("ai_lawyer.pipeline")
_MSG = json.loads((ROOT / "app" / "templates" / "messages.json").read_text(encoding="utf-8"))

DISCLAIMER_KEYS = ("disclaimer",)


@dataclass
class Session:
    id: str
    lang: str
    mode: str
    case_file: dict
    history: list = field(default_factory=list)


@dataclass
class TurnResult:
    reply_text: str
    reply_lang: str
    category: str
    action: str
    citations: list
    retrieved: list
    needs_lawyer: bool
    escalation_reasons: list
    verifier: dict
    draft_text: str | None
    trace: dict


def new_session(lang_hint: str | None = None) -> Session:
    return Session(id=uuid.uuid4().hex[:12], lang=lang_hint or "en-IN", mode="advice", case_file={}, history=[])


def _m(lang: str) -> dict:
    return _MSG["hi"] if lang.lower().startswith("hi") else _MSG["en"]


def _reason_text(reasons: list[str], m: dict) -> str:
    labels, out = m["reason_labels"], []
    for r in reasons:
        if r.startswith("llm:") and not router.HARD_LLM.search(r):
            key = "llm_soft"
        else:
            key = "keyword" if r.startswith(("keyword:", "llm:")) else r
        t = labels.get(key)
        if t and t not in out:
            out.append(t)
    return "; ".join(out)


def _facts_line(case_file: dict, m: dict) -> str:
    keys = [k for k in case_file if case_file[k] not in (None, "", [], {}) and k not in ("minor_stated", "category")]
    if not keys:
        return m["no_facts"]
    return "; ".join(f"{k.replace('_', ' ')}: {case_file[k]}" for k in keys)


_PHONE = re.compile(r"(?<![\d-])(1800[-\s]?\d{2,3}[-\s]?\d{4}|0\d{3}[-\s]?\d{6,7}|1\d{2,4})(?![\d-])")
_last_aid: dict = {}  # chunk id -> aid-search score, so citations can be listed in `retrieved`


def _helpline_numbers(chunk: dict) -> list[str]:
    """Phone numbers copied verbatim from a helpline chunk (years like 1987 are skipped
    unless the chunk itself is that number, e.g. NCH 1915)."""
    out = []
    for n in _PHONE.findall(chunk.get("text", "")):
        n = n.strip()
        if re.fullmatch(r"(19|20)\d{2}", n) and n != str(chunk.get("unit_number")):
            continue
        if n not in out:
            out.append(n)
    return out[:3]


def _aid_lines(lang: str, state: str | None) -> tuple[str, list[str], list[dict]]:
    """Verified legal-aid pointer from corpus `helpline`/`common` chunks only."""
    m = _m(lang)
    try:
        res = retrieval.search("free legal aid helpline legal services authority", ["common"],
                               ["central"] + ([state] if state else []), 4)
    except Exception as e:  # never crash on retrieval problems
        log.warning("aid retrieval failed: %s", e)
        return m["aid_missing"], [], []
    hits = [h for h in res["hits"] if h["chunk"].get("doc_type") == "helpline"
            and h["chunk"].get("status") == "in_force"][:2]
    if not hits or not retrieval.passes_gate(res["top_score"]):
        return m["aid_missing"], [], [{"id": h["id"], "score": h["score"]} for h in res["hits"]]
    lines = [m["aid_pointer"]]
    for h in hits:
        c = h["chunk"]
        nums = _helpline_numbers(c)
        body = " / ".join(nums) if nums else c["text"][:240]
        lines.append(f"- {c['doc_title']}: {body} ({m['source_label']}: {c['source_url']})")
        _last_aid[h["id"]] = h["score"]
    return "\n".join(lines), [h["id"] for h in hits], [{"id": h["id"], "score": h["score"]} for h in res["hits"]]


def safe_response(lang: str, case_file: dict, state: str | None, reasons: list[str], escalate: bool,
                  error: bool = False) -> tuple[str, list[str], list[dict]]:
    """SAFE RESPONSE (Section 10): understood / no verified info / what to do now / verified aid pointer."""
    m = _m(lang)
    aid, cites, ret = _aid_lines(lang, state)
    parts = [f"{m['understood']} {_facts_line(case_file, m)}"]
    if error:
        parts.append(m["service_error"])
    elif escalate:
        parts.append(m["escalate_intro"])
        rt = _reason_text(reasons, m)
        if rt:
            parts.append(m["escalate_reason"] + rt)
    else:
        parts.append(m["no_verified"])
    parts += [m["can_do_now"], aid]
    parts.append(m["disclaimer"])
    return "\n\n".join(parts), cites, ret


def _mentions_law(chunk: dict, texts: list[str]) -> bool:
    """Did the user refer to this (old) law? By its year, or by its first two distinctive title words."""
    t = " ".join(texts).lower()
    title = chunk.get("doc_title", "").lower()
    if any(y in t for y in re.findall(r"\b(?:18|19|20)\d{2}\b", title)):
        return True
    core = re.sub(r"\(.*?\)|\b(?:18|19|20)\d{2}\b", " ", title)
    stop = {"the", "of", "and", "act", "uttar", "pradesh", "up", "india", "indian", "regulation", "a"}
    words = [w for w in re.findall(r"[a-z]+", core) if w not in stop]
    return len(words) >= 2 and all(w in t for w in words[:2])


def _source_line(c: dict, m: dict) -> str:
    return f"{m['source_label']}: {c['doc_title']}, {c['unit']} {c['unit_number']}"


def _answer_prompt(lang, chunks, case_file, missing, user_text, issues=None) -> list[dict]:
    chunk_txt = "\n".join(
        f"[CHUNK id={c['id']}]\nDOC: {c['doc_title']} | {c['unit']} {c['unit_number']} | {c.get('heading','')} | "
        f"status={c['status']} | doc_type={c['doc_type']}\nTEXT: {c['text']}" for c in chunks)
    user = (f"REPLY LANGUAGE: {lang}\nCASE FILE: {json.dumps(case_file, ensure_ascii=False)}\n"
            f"MISSING FACTS: {missing}\n=== SOURCE CHUNKS ===\n{chunk_txt}\n=== END CHUNKS ===\n"
            f"USER MESSAGE: {user_text}\n=== END ===")
    if issues:
        user += ("\n\nVERIFIER ISSUES in your previous answer. Fix all of them: remove or rewrite the unsupported "
                 "statements, cite only ids shown above:\n- " + "\n- ".join(issues))
    return [{"role": "system", "content": read_prompt("answer.md")}, {"role": "user", "content": user}]


def _answer_script_ok(answer: dict, lang: str) -> bool:
    text = " ".join(b.get("text", "") for b in answer.get("blocks", []) if isinstance(b, dict))
    return guards.script_ok(text, lang)


def _valid_answer(d) -> bool:
    return isinstance(d, dict) and isinstance(d.get("blocks"), list)


def _generate_answer(msgs) -> dict | None:
    for _ in range(2):  # retry once on malformed output
        try:
            d = llm.parse_json(llm.generate(msgs, role="main", json_schema={"type": "object"}))
            if _valid_answer(d):
                return d
        except (llm.LLMError, ValueError) as e:
            log.warning("answer generation failed: %s", e)
    return None


def _trace_write(trace: dict) -> None:
    try:
        p = resolve("outputs/live_trace.jsonl")
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace, ensure_ascii=False, default=str) + "\n")
    except OSError as e:
        log.warning("trace write failed: %s", e)


def handle_turn(session: Session, user_text: str, input_mode: str = "text",
                lang_hint: str | None = None) -> TurnResult:
    t0 = time.time()
    llm.reset_stats()
    cfg = load_config()
    trace: dict = {"session": session.id, "input_mode": input_mode, "user_text": user_text, "mode": session.mode}
    try:
        res = _handle(session, user_text, lang_hint, cfg, trace)
    except Exception as e:  # last-resort: never crash, degrade honestly
        log.exception("unhandled error in handle_turn")
        trace["fatal_error"] = f"{type(e).__name__}: {e}"
        lang = lang_hint or session.lang
        text, cites, ret = safe_response(lang, session.case_file, session.case_file.get("state"), [], False, error=True)
        res = TurnResult(text, lang, "unclear", "refuse_unverified", cites, ret, True, ["internal_error"],
                         {"status": "failed", "issues": ["internal error"]}, None, trace)
    trace.update({"timings_s": round(time.time() - t0, 3), "llm": llm.snapshot_stats(),
                  "action": res.action, "category": res.category, "retrieved": res.retrieved,
                  "citations": res.citations, "verifier": res.verifier,
                  "escalation_reasons": res.escalation_reasons,
                  "models": cfg.get("models"), "mock": llm.is_mock()})
    res = _case_law_line(res, user_text, trace)
    have = {r["id"] for r in res.retrieved}
    extra = [{"id": c, "score": _last_aid.get(c, 0.0), "via": "aid_search"} for c in res.citations if c not in have]
    if extra:  # e.g. legal-aid helplines found by the separate aid search
        res.retrieved = list(res.retrieved) + extra
        trace["retrieved"] = res.retrieved
    res.trace = trace
    session.history.append({"role": "user", "text": user_text})
    session.history.append({"role": "assistant", "text": res.reply_text})
    _trace_write(trace)
    return res


def _case_law_line(res: TurnResult, user_text: str, trace: dict) -> TurnResult:
    """Deterministic: if the user asks for cases/judgments and no judgment chunk was retrieved, say so."""
    if not guards.case_law_request(user_text):
        return res
    try:
        by_id = {c["id"]: c for c in retrieval.get_index()["chunks"]}
    except Exception:
        by_id = {}
    ids = [r["id"] for r in res.retrieved] + list(res.citations)
    if any(by_id.get(i, {}).get("doc_type") == "judgment" for i in ids):
        return res
    m = _m(res.reply_lang)
    line = m["no_case_law"]
    if line not in res.reply_text:
        disc = m["disclaimer"]
        if res.reply_text.rstrip().endswith(disc):
            head = res.reply_text.rstrip()[: -len(disc)].rstrip()
            res.reply_text = f"{head}\n\n{line}\n\n{disc}"
        else:
            res.reply_text = f"{res.reply_text.rstrip()}\n\n{line}"
    res.needs_lawyer = True
    trace["case_law_request"] = True
    return res


def _handle(session, user_text, lang_hint, cfg, trace) -> TurnResult:
    # ---- route
    rj, info = router.route(session.case_file, session.history, user_text)
    trace["router"] = rj
    trace["router_info"] = {k: v for k, v in info.items() if k != "raw"}
    if info.get("error") and rj["category"] == "unclear":  # model unreachable: say so, do not pretend to clarify
        lang0 = lang_hint or session.lang
        text, cites, ret = safe_response(lang0, session.case_file, session.case_file.get("state"), [], False, error=True)
        return TurnResult(text, lang0, "unclear", "refuse_unverified", cites, ret, True, ["service_error"],
                          {"status": "failed", "issues": [f"router failed: {info['error']}"]}, None, trace)
    lang = lang_hint or rj.get("language") or session.lang
    session.lang = lang
    m = _m(lang)
    cf = session.case_file
    for k, v in (rj.get("case_file_update") or {}).items():
        if k == "months_since_event":  # never trust LLM date arithmetic; recomputed in code below
            continue
        if v not in (None, "", [], {}):
            cf[k] = v
    cf.pop("months_since_event", None)
    ed = guards.parse_event_date(cf.get("event_date")) if cf.get("event_date") else None
    if ed is None:
        ed = guards.relative_event_date(user_text)  # "2 months ago", "3 साल पहले": also code, not LLM
    if ed:
        cf["event_date"] = ed
        cf["months_since_event"] = guards.months_since(ed)
    elif cf.get("event_date"):
        trace["event_date_unparsed"] = cf.pop("event_date")
    if rj.get("state_or_city"):
        cf["state"] = rj["state_or_city"]
    cat = rj["category"]
    if cat in ("unclear",) and session.case_file.get("category"):
        cat = session.case_file["category"]  # keep the topic across turns when the follow-up is short
        rj["category"] = cat
    elif cat in ("consumer", "wages", "tenancy"):
        cf["category"] = cat
    state = cf.get("state")
    covered = [s.upper() for s in cfg.get("covered_states", [])]
    state_code = state.upper() if state and state.upper() in covered else None
    esc = router.escalation(user_text, rj, cf)
    reasons = esc["reasons"]
    if "minor_age" in reasons:
        cf["minor_stated"] = True

    # ---- mode: practice (P2, not built)
    if session.mode == "practice":
        return TurnResult(m["practice_unavailable"], lang, cat, "practice", [], [], False, [],
                          {"status": "pass", "issues": []}, None, trace)

    # ---- hard escalation / out of scope -> SAFE RESPONSE
    if esc["hard"]:
        text, cites, ret = safe_response(lang, cf, state_code, reasons, escalate=True)
        return TurnResult(text, lang, cat, "escalate", cites, ret, True, reasons,
                          {"status": "pass", "issues": []}, None, trace)

    # ---- unclear -> clarify (no retrieval, no legal statement)
    if cat == "unclear":
        text = f"{m['understood']} {_facts_line(cf, m)}\n\n{m['clarify_category']}\n\n{m['disclaimer']}"
        return TurnResult(text, lang, cat, "clarify", [], [], False, reasons, {"status": "pass", "issues": []},
                          None, trace)

    # ---- retrieval
    juris = ["central"] + ([state_code] if state_code else [])
    query = rj.get("english_retrieval_query") or user_text
    rcfg = cfg["retrieval"]
    sr = retrieval.search(query, [cat, "common"], juris,
                          extra_queries=(rcfg.get("forum_queries") or {}).get(cat), extra_k=int(rcfg.get("forum_extra", 2)))
    retrieved = [{"id": h["id"], "score": h["score"]} for h in sr["hits"]]
    trace["retrieval"] = {"query": query, "jurisdictions": juris, "top_score": sr["top_score"],
                          "min_score": cfg["retrieval"]["min_score"],
                          "old_law": [{"id": o["id"], "score": o["score"]} for o in sr["old_law"]]}

    # ---- draft mode: deposit notice (tenancy), salary demand notice (wages), grievance email (consumer)
    if session.mode == "draft":
        if cat not in drafts.DRAFTS:
            return TurnResult(m["draft_only_deposit"] + "\n\n" + m["disclaimer"], lang, cat, "clarify", [], retrieved,
                              False, reasons, {"status": "pass", "issues": []}, None, trace)
        d = drafts.make_draft(cat, cf, state_code)
        trace["draft"] = {"kind": d["kind"], "file_name": d["file_name"], "missing": d["missing"],
                          "scan_issues": d["scan_issues"]}
        if d["scan_issues"]:
            text, cites, ret = safe_response(lang, cf, state_code, reasons, False)
            return TurnResult(text, lang, cat, "refuse_unverified", cites, retrieved, True, reasons,
                              {"status": "failed", "issues": d["scan_issues"]}, None, trace)
        reply = f"{m.get('draft_intro_' + cat, m['draft_intro'])}\n\n{d['text']}\n\n{m['draft_footer']}"
        return TurnResult(reply, lang, cat, "draft", d["citations"], d["retrieved"] or retrieved, bool(reasons),
                          reasons, {"status": "pass", "issues": []}, d["text"] + "\n\n" + m["draft_footer"], trace)

    # ---- confidence gate
    if not retrieval.passes_gate(sr["top_score"]):
        if "state_unknown" in reasons:  # ask for the state instead of refusing outright
            text = f"{m['understood']} {_facts_line(cf, m)}\n\n{m['ask_state']}\n\n{m['disclaimer']}"
            return TurnResult(text, lang, cat, "clarify", [], retrieved, False, reasons,
                              {"status": "pass", "issues": ["confidence gate: state unknown"]}, None, trace)
        text, cites, ret = safe_response(lang, cf, state_code, reasons, False)
        return TurnResult(text, lang, cat, "refuse_unverified", cites, retrieved, True, reasons,
                          {"status": "pass", "issues": ["confidence gate: no verified information"]}, None, trace)

    chunks = [h["chunk"] for h in sr["hits"]]
    missing = rj.get("missing_facts", [])
    # ---- generate -> verify -> regenerate once -> SAFE RESPONSE
    max_regen = int(cfg["verifier"].get("max_regenerations", 1))
    issues_hist, answer, status, issues = [], None, "failed", []
    prior = None
    for attempt in range(max_regen + 1):
        msgs = _answer_prompt(lang, chunks, cf, missing, user_text, prior)
        answer = _generate_answer(msgs)
        if answer is not None and not _answer_script_ok(answer, lang):  # Hindi user got a non-Hindi body: retry once
            retry = msgs[:-1] + [{"role": "user", "content": msgs[-1]["content"] + "\n\n" + read_prompt(
                "language_retry.md").format(lang=lang, language_name="Hindi" if lang.lower().startswith("hi") else lang)}]
            a2 = _generate_answer(retry)
            trace["language_retry"] = True
            if a2 is not None and _answer_script_ok(a2, lang):
                answer = a2
            else:
                trace["language_warning"] = f"reply body not in the script of {lang} after one retry"
        if answer is None:
            issues = ["model returned no usable answer"]
        else:
            if sum(1 for b in answer["blocks"] if isinstance(b, dict) and b.get("type") == "question") > 2:
                qs = 0
                keep = []
                for b in answer["blocks"]:
                    if isinstance(b, dict) and b.get("type") == "question":
                        qs += 1
                        if qs > 2:
                            continue
                    keep.append(b)
                answer["blocks"] = keep
            issues, vinfo = verifier.verify(answer, chunks, cf)
            trace["judge"] = vinfo.get("judge")
        issues_hist.append(list(issues))
        if not issues:
            status = "pass" if attempt == 0 else "fixed"
            break
        prior = issues
    trace["verifier_history"] = issues_hist
    if status == "failed":
        text, cites, ret = safe_response(lang, cf, state_code, reasons, False)
        return TurnResult(text, lang, cat, "refuse_unverified", cites, retrieved, True, reasons,
                          {"status": "failed", "issues": issues}, None, trace)

    # ---- render
    by_id = {c["id"]: c for c in chunks}
    paras, cited = [], []
    cf_nums = set(re.findall(r"\d{3,}", json.dumps(cf, ensure_ascii=False).replace(",", "")))
    for b in answer["blocks"]:
        paras.append(b["text"].strip())
        if b["type"] == "legal":
            for cid in b.get("cites", []):
                if cid not in cited:
                    cited.append(cid)
        # numbers (helplines, amounts, days) in ANY block: show the chunk they came from as a source
        for num in re.findall(r"\d[\d\-]{2,}\d", b["text"]):
            plain = num.replace("-", "")
            if plain in cf_nums:
                continue
            src = next((c for c in chunks if plain in c.get("text", "").replace("-", "").replace(" ", "")), None)
            if src and src["id"] not in cited:
                cited.append(src["id"])
    body = "\n\n".join(paras)
    if cited:
        body += "\n\n" + "\n".join(_source_line(by_id[c], m) for c in cited)
    old_note_chunks = []  # chunks behind our own "no longer in force" note; the final scan must see them
    said = [user_text] + [h["text"] for h in session.history if h.get("role") == "user"]
    for o in sr["old_law"][:2]:
        if o["chunk"]["status"] in ("repealed", "superseded") and _mentions_law(o["chunk"], said) \
                and o["chunk"]["doc_title"] not in [c["doc_title"] for c in old_note_chunks]:
            body += "\n\n" + m["old_law"].format(title=o["chunk"]["doc_title"])
            old_note_chunks.append(o["chunk"])
            retrieved.append({"id": o["id"], "score": o["score"], "old_law": True})
    if answer.get("gaps"):
        body += "\n\n" + m["gaps"] + "\n- " + "\n- ".join(str(g) for g in answer["gaps"][:4])
    needs_lawyer = bool(answer.get("needs_lawyer")) or bool(reasons)
    for r in reasons:
        if r in ("state_unknown", "state_not_covered"):
            body += "\n\n" + m[r]
    if reasons:
        rt = _reason_text(reasons, m)
        body += "\n\n" + m["see_lawyer"] + (f" ({rt})" if rt else "")
        aid, aid_ids, _ = _aid_lines(lang, state_code)
        body += "\n\n" + aid
        for a in aid_ids:
            if a not in cited:
                cited.append(a)
    body += "\n\n" + m["disclaimer"]
    # final-text scan: nothing invented may have crept into the rendered reply
    final_chunks = chunks + old_note_chunks + [c for c in (retrieval.get_index()["chunks"]) if c["id"] in cited]
    final_issues = verifier.scan_patterns(body, final_chunks)
    if final_issues:
        trace["final_scan_issues"] = final_issues
        text, cites, ret = safe_response(lang, cf, state_code, reasons, False)
        return TurnResult(text, lang, cat, "refuse_unverified", cites, retrieved, True, reasons,
                          {"status": "failed", "issues": final_issues}, None, trace)
    has_legal = any(b["type"] == "legal" for b in answer["blocks"])
    action = "answer" if has_legal else "clarify"
    return TurnResult(body, lang, cat, action, cited, retrieved, needs_lawyer, reasons,
                      {"status": status, "issues": []}, None, trace)
