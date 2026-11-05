"""Mock LLM + hash embeddings. Deterministic, no keys. Clearly NOT real model behaviour.

Env switches for tests:
  AI_LAWYER_MOCK_FAKECITE=1       first answer attempt cites a fake id / invented section; regeneration is clean
  AI_LAWYER_MOCK_FAKECITE=always  every attempt is bad (forces SAFE RESPONSE)
"""
import hashlib
import json
import os
import re

import numpy as np

DIM = 512
_STOP = set("a an the of to in on for and or is are was were be been my me i you your it this that with from by at as "
            "he she they we not no do did does have has had can may must if then so but about what how when who which "
            "will would should could shall any all than into out up down over under after before within".split())


def _tok(text: str) -> list[str]:
    toks = re.findall(r"\w+", text.lower())
    out = []
    for t in toks:
        if t in _STOP:
            continue
        if len(t) > 3 and t.endswith("s"):
            t = t[:-1]
        out.append(t)
    return out


def embed(texts: list[str]) -> np.ndarray:
    arr = np.zeros((len(texts), DIM), dtype=np.float32)
    for i, t in enumerate(texts):
        for tok in _tok(t):
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            arr[i, h % DIM] += 1.0
    n = np.linalg.norm(arr, axis=1, keepdims=True)
    return arr / np.maximum(n, 1e-9)


# ------------------------------------------------------------------ router
_CATS = {
    "tenancy": ["deposit", "landlord", "tenant", "rent ", "rental", "flat", "vacate", "lease", "डिपॉज़िट", "डिपॉजिट",
                "मकान", "किराया", "किराए", "मकान मालिक", "जमा राशि", "सिक्योरिटी"],
    "wages": ["salary", "wage", "wages", "employer", "boss", "unpaid", "not paid", "dues", "gratuity", "bonus", "job",
              "सैलरी", "वेतन", "तनख्वाह", "मजदूरी", "नौकरी", "मालिक ने"],
    "consumer": ["refund", "defective", "product", "order", "seller", "phone", "delivery", "warranty", "shop",
                 "online", "amazon", "flipkart", "laptop", "refrigerator", "रिफंड", "खराब", "सामान", "दुकान", "ऑर्डर"],
}
_OOS = ["divorce", "custody", "inherit", "will deed", "fir", "arrest", "bail", "cheque", "tax notice", "visa",
        "तलाक", "गिरफ्तार", "एफआईआर", "जमानत", "चेक"]
_QUERY = {
    "tenancy": "landlord must return security deposit after tenant vacates; remedy if deposit not returned",
    "wages": "employer unpaid wages salary payment time limit; complaint for unpaid wages",
    "consumer": "refund or replacement for defective goods or services; consumer complaint",
    "unclear": "legal information",
    "out_of_scope": "legal information",
}
_STATES = {"UP": ["uttar pradesh", " up ", "lucknow", "kanpur", "noida", "varanasi", "agra", "prayagraj", "ghaziabad",
                  "उत्तर प्रदेश", "लखनऊ", "कानपुर", "नोएडा"],
           "OTHER": ["delhi", "mumbai", "maharashtra", "bangalore", "bengaluru", "karnataka", "chennai", "kolkata",
                     "hyderabad", "gujarat", "rajasthan", "दिल्ली", "मुंबई"]}


def _user_message(messages) -> str:
    txt = messages[-1]["content"]
    m = re.search(r"USER MESSAGE:\s*(.*?)(?:\n=== |\Z)", txt, flags=re.S)
    return (m.group(1) if m else txt).strip()


def _router(messages) -> str:
    um = _user_message(messages)
    low = " " + um.lower() + " "
    lang = "hi-IN" if re.search(r"[ऀ-ॿ]", um) else "en-IN"
    cat = "unclear"
    if any(k in low for k in _OOS):
        cat = "out_of_scope"
    else:
        for c, kws in _CATS.items():
            if any(k in low for k in kws):
                cat = c
                break
    state = None
    for code, kws in _STATES.items():
        if any(k in low for k in kws):
            state = "UP" if code == "UP" else "other"
            break
    cf = {}
    m = re.search(r"(?:₹|rs\.?|inr|rupees)\s*([\d,]+)|([\d,]{3,})\s*(?:rupees|rs|₹|रुपये|रुपए)", low)
    if m:
        cf["amount_inr"] = int((m.group(1) or m.group(2)).replace(",", "") or 0)
    if state:
        cf["state"] = state
    missing = []
    if cat in ("tenancy", "wages") and not state:
        missing.append("state or city")
    if "amount_inr" not in cf and cat in ("tenancy", "wages", "consumer"):
        missing.append("amount involved")
    return json.dumps({
        "category": cat, "language": lang, "state_or_city": state,
        "case_file_update": cf, "missing_facts": missing[:2], "escalation_flags": [],
        "english_retrieval_query": _QUERY[cat] + (" " + um if lang == "en-IN" else ""),
    }, ensure_ascii=False)


# ------------------------------------------------------------------ answer
def _chunks_from_prompt(text: str) -> list[tuple[str, str]]:
    out = []
    for m in re.finditer(r"\[CHUNK id=(\S+?)\]\n(.*?)(?=\n\[CHUNK id=|\n=== END CHUNKS|\Z)", text, flags=re.S):
        body = m.group(2)
        t = re.search(r"TEXT:\s*(.*)", body, flags=re.S)
        out.append((m.group(1), (t.group(1) if t else body).strip()))
    return out


def _answer(messages) -> str:
    full = "\n".join(m["content"] for m in messages)
    chunks = _chunks_from_prompt(full)
    regen = "VERIFIER ISSUES" in full
    mode = os.environ.get("AI_LAWYER_MOCK_FAKECITE", "")
    hi = "REPLY LANGUAGE: hi" in full
    blocks = []
    if hi:
        blocks.append({"text": "मैंने आपकी बात समझ ली है। (mock mode)", "type": "practical", "cites": []})
    for cid, text in chunks[:2]:
        blocks.append({"text": text, "type": "legal", "cites": [cid]})
    if mode == "always" or (mode == "1" and not regen):
        blocks.append({"text": "Section 420 of the Indian Penal Code, 1860 also applies and you will get 5 lakh.",
                       "type": "legal", "cites": ["FAKE-ID-999"]})
    blocks.append({"text": "Keep your receipts, messages and a written timeline of dates.", "type": "practical", "cites": []})
    mf = re.search(r"MISSING FACTS: (.*)", full)
    if mf and mf.group(1).strip() not in ("", "[]", "none"):
        blocks.append({"text": "Can you tell me " + mf.group(1).strip().strip("[]'\"").split("', '")[0] + "?",
                       "type": "question", "cites": []})
    if not chunks:
        return json.dumps({"blocks": [], "needs_lawyer": False, "gaps": ["no sources provided"]})
    return json.dumps({"blocks": blocks, "needs_lawyer": False, "gaps": []}, ensure_ascii=False)


def _judge(messages) -> str:
    full = messages[-1]["content"]
    verdicts = []
    for m in re.finditer(r"\[BLOCK (\d+)\](.*?)(?=\n\[BLOCK |\Z)", full, flags=re.S):
        verdicts.append({"block": int(m.group(1)), "supported": "FAKE" not in m.group(2),
                         "reason": "mock judge"})
    return json.dumps({"verdicts": verdicts})


def generate(messages, role, json_schema=None) -> str:
    sysmsg = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
    task = re.match(r"TASK:\s*(\w+)", sysmsg)
    task = task.group(1) if task else role
    if task == "router":
        return _router(messages)
    if task == "answer":
        return _answer(messages)
    if task == "judge":
        return _judge(messages)
    if task == "practice":
        return "[MOCK SIMULATION] I don't think I owe you anything. Show me proof."
    return "{}"
