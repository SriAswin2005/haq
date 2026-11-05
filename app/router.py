"""Router: one LLM call -> category, language, facts, flags, English retrieval query.
Plus deterministic escalation rules (config keywords + fact triggers), merged with the LLM's flags."""
import json
import logging
import re

from . import guards, llm
from .config import load_config, read_prompt

log = logging.getLogger("ai_lawyer.router")

VALID_CATS = {"consumer", "wages", "tenancy", "out_of_scope", "unclear"}


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
    return {"category": "unclear", "language": "en-IN", "state_or_city": None, "case_file_update": {},
            "missing_facts": [], "escalation_flags": [], "english_retrieval_query": ""}


def _validate(d) -> dict | None:
    if not isinstance(d, dict) or d.get("category") not in VALID_CATS:
        return None
    out = _fallback()
    out["category"] = d["category"]
    out["language"] = d.get("language") or "en-IN"
    s = d.get("state_or_city")
    out["state_or_city"] = s if isinstance(s, str) and s else None
    cfu = d.get("case_file_update")
    out["case_file_update"] = cfu if isinstance(cfu, dict) else {}
    for k in ("missing_facts", "escalation_flags"):
        v = d.get(k)
        out[k] = [str(x) for x in v][:2 if k == "missing_facts" else 10] if isinstance(v, list) else []
    q = d.get("english_retrieval_query")
    out["english_retrieval_query"] = q if isinstance(q, str) else ""
    return out


def route(case_file: dict, history: list[dict], user_text: str) -> tuple[dict, dict]:
    """Returns (router_json, info). info = {"attempts": n, "error": str|None}."""
    system = read_prompt("router.md")
    recent = "\n".join(f"{h['role']}: {h['text']}" for h in history[-6:]) or "(none)"
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
    """Deterministic + LLM escalation. Returns {"hard": [...], "soft": [...], "reasons": [...]}.
    hard  -> SAFE RESPONSE path (topic is outside scope / needs a lawyer now)
    soft  -> still answer from verified sources, but add lawyer/legal-aid message."""
    cfg = load_config()
    esc = cfg["escalation"]
    # LLM flags are hard only when they name a real hard trigger; anything else (e.g. "supreme_court",
    # "legal_precedent") becomes soft: still answer from verified sources, plus the lawyer pointer.
    llm_flags = [str(f) for f in router_json.get("escalation_flags", []) if f]
    hard_llm = [f"llm:{f}" for f in llm_flags if HARD_LLM.search(f)]
    soft_llm = [f"llm:{f}" for f in llm_flags if not HARD_LLM.search(f)]
    hard = keyword_flags(user_text) + hard_llm
    if case_file.get("minor_stated") and "minor_age" not in hard:
        hard.append("minor_age")  # a stated age under 18 stays in force for the whole session
    if router_json["category"] == "out_of_scope":
        hard.append("out_of_scope_topic")
    soft = list(soft_llm)
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
    if cat in ("tenancy", "wages"):
        if not state:
            soft.append("state_unknown")
        elif str(state).upper() not in covered:
            soft.append("state_not_covered")
    if cat == "unclear":
        soft.append("unclear")
    return {"hard": hard, "soft": soft, "reasons": hard + soft}
