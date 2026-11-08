"""Router: one LLM call -> kind (chat / legal / harmful), topic, language, place, danger, facts, retrieval query.

Escalation no longer replaces an answer. A lawyer recommendation is one line under a useful answer, and
only immediate danger changes the reply (safety first, then the answer). See escalation()."""
import json
import logging
import re

from . import guards, llm
from .config import load_config, read_prompt

log = logging.getLogger("ai_lawyer.router")

INTENTS = {"explain_rights", "where_to_complain", "what_can_i_get", "documents_needed", "next_steps", "deadline",
           "draft_document", "follow_up", "other"}
QUESTION_INTENTS = INTENTS - {"draft_document", "other"}
VALID_CATS = {"consumer", "wages", "tenancy", "other_law", "unclear"}
KINDS = {"chat", "legal", "harmful"}
STATE_CODES = {"AP", "AR", "AS", "BR", "CG", "GA", "GJ", "HR", "HP", "JH", "KA", "KL", "MP", "MH", "MN", "ML", "MZ",
               "NL", "OR", "OD", "PB", "RJ", "SK", "TN", "TG", "TS", "TR", "UP", "UK", "UT", "WB", "DL", "JK", "LA",
               "CH", "PY", "AN", "DN", "DD", "LD"}


HARD_LLM = re.compile(r"arrest|police|fir\b|summons|notice_received|court_notice|legal_notice_received|bail|criminal|"
                      r"jail|violen|threat|harass|assault|lock|evict|divorce|custody|family|maintenance|domestic|"
                      r"property_(?:title|ownership|dispute)|inherit|minor|child", re.I)


def keyword_flags(text: str) -> list[str]:
    cfg = load_config()["escalation"]
    text = guards.norm(text)
    low = text.lower()
    flags = []
    for kw in cfg.get("keywords_en", []):
        if re.search(r"(?<!\w)" + re.escape(kw.lower()) + r"(?!\w)", low):
            flags.append(f"keyword:{kw}")
    for kw in cfg.get("keywords_hi", []):
        if guards.norm(kw) in text:
            flags.append(f"keyword:{kw}")
    flags += guards.minor_flags(text)
    return flags


def _fallback() -> dict:
    return {"kind": "legal", "category": "unclear", "topic": "", "language": "en-IN", "country": None,
            "state_or_city": None, "danger_now": False, "lawyer_note": "", "case_file_update": {},
            "missing_facts": [], "escalation_flags": [], "english_retrieval_query": "", "intent": [], "question": ""}


def _truthy(v) -> bool:
    return v in (True, "true", "True", 1, "yes")


def _validate(d) -> dict | None:
    if not isinstance(d, dict):
        return None
    cat = d.get("category")
    if cat == "out_of_scope":          # older prompt / model habit
        cat = "other_law"
    if cat not in VALID_CATS:
        return None
    out = _fallback()
    out["category"] = cat
    kind = str(d.get("kind") or "legal").lower()
    out["kind"] = kind if kind in KINDS else "legal"
    out["topic"] = str(d.get("topic") or "")[:120]
    out["language"] = d.get("language") or "en-IN"
    c = d.get("country")
    out["country"] = c.upper()[:2] if isinstance(c, str) and c.strip() else None
    s = d.get("state_or_city")
    s = s.strip().upper() if isinstance(s, str) else ""
    out["state_or_city"] = {"TS": "TG", "OD": "OR", "UT": "UK"}.get(s, s) if s in STATE_CODES else None
    out["danger_now"] = _truthy(d.get("danger_now"))
    ln = d.get("lawyer_note")
    out["lawyer_note"] = ln.strip()[:300] if isinstance(ln, str) else ""
    cfu = d.get("case_file_update")
    out["case_file_update"] = cfu if isinstance(cfu, dict) else {}
    for k in ("missing_facts", "escalation_flags"):
        v = d.get(k)
        out[k] = [str(x) for x in v][:2 if k == "missing_facts" else 10] if isinstance(v, list) else []
    q = d.get("english_retrieval_query")
    out["english_retrieval_query"] = q if isinstance(q, str) else ""
    it = d.get("intent")
    it = [it] if isinstance(it, str) else (it if isinstance(it, list) else [])
    out["intent"] = [str(x) for x in it if str(x) in INTENTS][:4]
    out["new_topic"] = d.get("new_topic") in (True, "true", "True", 1)
    sm = d.get("summary")
    out["summary"] = sm.strip()[:400] if isinstance(sm, str) else ""
    qq = d.get("question")
    out["question"] = qq.strip()[:600] if isinstance(qq, str) else ""
    return out


def _short(text: str, n: int = 500) -> str:
    """Earlier turns for context: long replies (drafts) are cut so the current message stays the focus."""
    t = " ".join(str(text).split())
    return t if len(t) <= n else t[:n] + " …"


def route(case_file: dict, history: list[dict], user_text: str) -> tuple[dict, dict]:
    """Returns (router_json, info). info = {"attempts": n, "error": str|None}."""
    system = read_prompt("router.md")
    recent = "\n".join(f"{h['role']}: {_short(h['text'])}" for h in history[-6:]) or "(none)"
    user = (f"TODAY: {guards.today().isoformat()}\nCASE FILE SO FAR: {json.dumps(case_file, ensure_ascii=False)}\n"
            f"RECENT CONVERSATION:\n{recent}\n\nUSER MESSAGE: {user_text}\n=== END ===")
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    err = None
    for attempt in (1, 2):  # retry once, then fall back to unclear
        try:
            raw = llm.generate(msgs, role="router", json_schema={"type": "object"})
            d = _validate(llm.parse_json(raw))
            if d:
                return d, {"attempts": attempt, "error": None, "raw": raw}
            err = "invalid router JSON"
        except (llm.LLMError, ValueError) as e:
            err = str(e)
            log.warning("router attempt %d failed: %s", attempt, err)
    return _fallback(), {"attempts": 2, "error": err, "raw": None}


def escalation(user_text: str, router_json: dict, case_file: dict) -> dict:
    """Returns {"hard": [], "soft": [...], "reasons": [...], "danger": bool}.
    Nothing here blocks an answer any more (the old keyword list sent every question that mentioned the
    police, harassment or family to "see a lawyer" with no information). soft reasons add one lawyer /
    legal-aid line under the answer; danger puts a safety line first."""
    cfg = load_config()
    esc = cfg["escalation"]
    soft = []
    if router_json.get("lawyer_note"):
        soft.append("lawyer_note")
    minor = guards.minor_flags(guards.norm(user_text))
    if minor or case_file.get("minor_stated"):
        soft.append("minor_age")   # a stated age under 18 stays in force for the whole session
    amt = case_file.get("amount_inr")
    try:
        if amt is not None and float(amt) > float(esc["high_amount_inr"]):
            soft.append("high_amount")
    except (TypeError, ValueError):
        pass
    try:
        m = case_file.get("months_since_event")
        if m is not None and float(m) > float(esc["limitation_warn_months"]):
            soft.append("limitation_risk")
    except (TypeError, ValueError):
        pass
    cat = router_json["category"]
    state = case_file.get("state") or router_json.get("state_or_city")
    covered = [s.upper() for s in cfg.get("covered_states", [])]
    try:   # a state counts as covered for a topic once the library holds that state's own law for it
        from . import retrieval
        covered += [c["jurisdiction"].upper() for c in retrieval.get_index()["chunks"]
                    if c.get("category") == cat and c.get("jurisdiction") not in (None, "central")]
    except Exception:  # noqa: BLE001 (never block routing on the index)
        pass
    if cat == "tenancy":   # wage law is central (Code on Wages), so no state note there
        if not state:
            soft.append("state_unknown")
        elif str(state).upper() not in covered:
            soft.append("state_not_covered")
    if cat == "unclear":
        soft.append("unclear")
    danger = bool(router_json.get("danger_now"))
    return {"hard": [], "soft": soft, "reasons": soft, "danger": danger}
