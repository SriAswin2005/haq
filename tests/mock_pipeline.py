"""Tests-only wiring fixture, used ONLY when --mock and app/pipeline.py is absent.

This is not the application and cannot demonstrate retrieval or legal quality.
It never reads cases/expectations, emits no legal rules, and makes no API calls.
"""
from dataclasses import dataclass, field
import re
import uuid


@dataclass
class Session:
    id: str
    lang: str = "en-IN"
    mode: str = "advice"
    case_file: dict = field(default_factory=dict)
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


def new_session(lang_hint=None):
    return Session(id=str(uuid.uuid4()), lang=lang_hint or "en-IN")


def handle_turn(session, user_text, input_mode="text", lang_hint=None):
    session.lang = lang_hint or session.lang
    combined = " ".join(h["text"] for h in session.history if h["role"] == "user") + " " + user_text
    text = combined.lower()
    if re.search(r"bail|custody|divorce|ownership|inherited|tax notice|cheque|कस्टडी|तलाक|ipc", text):
        category = "out_of_scope"
    elif re.search(r"salary|wages|employer|तनख्वाह", text):
        category = "wages"
    elif re.search(r"deposit|landlord|tenant|मकान|किराये", text):
        category = "tenancy"
    elif re.search(r"refund|bought|seller|shop|repair|charger|मिक्सर", text):
        category = "consumer"
    else:
        category = "unclear"
    hindi = session.lang.startswith("hi")
    reply = ("[MOCK: केवल परीक्षण] मुझे इस हिस्से की सत्यापित जानकारी नहीं है। दस्तावेज और तारीखें संभालें। वकील या कानूनी सहायता से बात करें।"
             if hindi else "[MOCK: harness fixture only] I have no verified information to answer this part. Keep documents and dates. Speak with a lawyer or legal aid.")
    draft = None
    action = "escalate" if category == "out_of_scope" else "refuse_unverified"
    if session.mode == "draft" and category != "out_of_scope":
        draft = ("[MOCK: harness fixture only]\nFrom: [● name and address]\nTo: [● recipient and address]\n"
                 "Please review the outstanding payment for [● confirmed facts and date]. Confirm any conflicting dates.\n"
                 "Check every detail before sending. For high-value or complex matters, have a lawyer review it.")
        action = "draft"
        reply += " Confirm the missing facts in the draft."
    result = TurnResult(reply, session.lang, category, action, [], [], True, ["mock_no_sources"],
                        {"status": "pass", "issues": []}, draft,
                        {"models": {"main": "tests-only-no-model"}, "llm_calls": 0,
                         "fixture_only": True, "input_mode_received": input_mode})
    session.history.extend([{"role": "user", "text": user_text}, {"role": "assistant", "text": reply}])
    return result
