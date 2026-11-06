"""Append the requested directory cases without changing the first 40 cases."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SPECS = [
    ("UPI fraud", "en-IN", "Someone posing as a delivery agent tricked me into approving a UPI request and Rs 4800 left my account today. I want to report this online financial fraud. Which official reporting service may help?", ["CYBER", "RBI"]),
    ("bank card charge", "hi-IN", "मेरे बैंक के कार्ड पर एक ही भुगतान दो बार कट गया। बैंक की शिकायत टीम को लिखने के बाद भी समाधान नहीं मिला। दुकानदार से रिफंड नहीं, बैंक की सेवा की शिकायत के लिए कौन सा आधिकारिक बाहरी मंच है?", ["RBI"]),
    ("insurance claim rejected", "en-IN", "Mera health insurance claim reject ho gaya. Insurance company ki grievance team bhi jawab nahi de rahi. Policyholder complaint ke liye kaunsa official insurance grievance portal dekhun?", ["IRDAI"]),
    ("PF withdrawal stuck", "en-IN", "My provident fund withdrawal has been pending for two months and the status never changes. Where can a PF member register an official service grievance? I only need the right office or portal.", ["EPFO"]),
    ("traffic challan", "hi-IN", "लखनऊ में मेरी गाड़ी के नाम ट्रैफिक चालान आया है। मैं उसका विवरण और भुगतान की स्थिति आधिकारिक जगह पर देखना चाहता हूं। किस पोर्टल पर जाऊं?", ["ECHALLAN", "VCOURT"]),
    ("train refund", "en-IN", "Meri train cancel hui thi, ticket ka refund ab tak nahi mila. Railway ki official passenger grievance service mein complaint kahan karun? Bas sahi service bata do.", ["RAIL"]),
    ("flight refund", "en-IN", "My airline cancelled my flight and has not returned the ticket payment despite repeated requests. Which official aviation grievance service may handle the refund complaint?", ["AIRSEWA"]),
    ("lost phone", "hi-IN", "लखनऊ में मेरा मोबाइल खो गया है। उसका मोबाइल नेटवर्क पर इस्तेमाल रोकना और खोने की रिपोर्ट करना चाहता हूं। किस आधिकारिक सेवा से मदद मिल सकती है?", ["SANCHAR", "UPPOLICE"]),
    ("RTI request", "en-IN", "Mujhe ek central government department se apni application ki file records maangni hain. Online information request bhejne ke liye kaunsa official portal hai? Kanoon ki explanation nahi chahiye.", ["RTI"]),
    ("Aadhaar update problem", "en-IN", "My Aadhaar address update has been stuck for weeks and the enrolment centre cannot explain it. Where is the official Aadhaar grievance channel?", ["UIDAI"]),
    ("electricity bill dispute", "hi-IN", "मैं उत्तर प्रदेश में बिजली उपभोक्ता हूं। इस महीने बिल अचानक बहुत अधिक आया है और मीटर रीडिंग गलत दिख रही है। बिजली कंपनी के आधिकारिक बिल शिकायत चैनल में कहां संपर्क करूं?", ["UPPCL"]),
    ("builder delay", "en-IN", "Noida UP mein builder promised possession se do saal late hai. Home buyers ke liye property regulator ka official complaint portal kaunsa hai? Mujhe abhi compensation ke legal rules nahi chahiye.", ["UPRERA"]),
    ("loan recovery harassment", "en-IN", "I live in Lucknow. A loan recovery agent from an NBFC repeatedly calls and sends abusive messages to my family. There is no immediate physical danger. Which official complaint body may handle this harassment?", ["RBI", "UPPOLICE"]),
    ("senior citizen neglected", "hi-IN", "मेरे पड़ोस के एक बुजुर्ग को परिवार खाना और देखभाल नहीं दे रहा। अभी कोई चिकित्सा आपात स्थिति नहीं है। वरिष्ठ नागरिक की उपेक्षा में सहायता देने वाली आधिकारिक हेल्पलाइन कौन सी है?", ["ELDERLINE"]),
    ("food adulteration complaint", "en-IN", "Packaged milk mein milawat ka shak hai aur batch details mere paas hain. Refund nahi, food safety complaint register karni hai. Kaunsa official food-safety complaint service dekhun?", ["FSSAI"]),
]
CONSUMER_SERVICE_NUMBERS = {42, 43, 46, 47, 51, 52, 55}


def build_cases():
    cases = []
    for number, (topic, language, text, bodies) in enumerate(SPECS, 41):
        ids = ["COM-DIR-" + body for body in bodies]
        cases.append({"id": f"T-{number:03d}", "group": "L_referrals", "tags": ["round4", "directory", topic],
            "category_expected": "out_of_scope", "language": language, "input_mode": "text", "turns": [text],
            "expected_action": "escalate", "expect_needs_lawyer": True, "expected_topics": [topic, "official referral"],
            "must_include_any": [], "must_not_include": [], "expected_chunk_ids": ids, "expected_referral_any": ids,
            "notes": "Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.",
            "expected_law_verified": False, "calibration_label": "exclude", "jurisdictions_expected": ["central", "UP"],
            "retrieval_expectation_kind": "safe_referral"})
        cases[-1]["notes"] = ("An answer must name and cite an expected body. Wrong bodies always hard fail. "
            "Statute/section patterns hard fail in escalate/out_of_scope replies; in an answer they must be grounded in cited chunks. "
            "Legal-aid-only escalation is a safe fallback and a recall miss. Targets remain agent-mapped, pending human confirmation.")
        if number in CONSUMER_SERVICE_NUMBERS:
            cases[-1].update(category_expected="consumer", expected_action="answer", expect_needs_lawyer=False,
                expected_outcomes=[{"category": "consumer", "action": "answer", "needs_lawyer": False},
                                   {"category": "out_of_scope", "action": "escalate", "needs_lawyer": True}])
        if number == 44:
            cases[-1].update(category_expected="wages", expected_action="answer", expect_needs_lawyer=False,
                expected_outcomes=[{"category": "wages", "action": "answer", "needs_lawyer": False},
                    {"category": "wages", "action": "answer", "needs_lawyer": True},
                    {"category": "out_of_scope", "action": "escalate", "needs_lawyer": True}])
    return cases


def main():
    path = ROOT / "tests/cases.jsonl"
    original = path.read_bytes()
    cases = [json.loads(line) for line in original.decode("utf-8-sig").splitlines() if line.strip()]
    additions = build_cases()
    if len(cases) == 55 and cases[40:] == additions:
        print("The 15 current round-four cases already exist.")
        return
    if [c["id"] for c in cases] != [f"T-{n:03d}" for n in range(1, 41)]:
        raise ValueError("Expected the unchanged 40-case catalogue before appending")
    from tests.checks import load_corpus
    corpus = load_corpus(ROOT / "data/corpus")
    if any(cid not in corpus for c in additions for cid in c["expected_referral_any"]):
        raise ValueError("A mapped directory ID is missing; no cases changed")
    text = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in additions).encode("utf-8")
    path.write_bytes(original + (b"" if original.endswith(b"\n") else b"\n") + text)
    assert path.read_bytes().startswith(original)
    print("Appended T-041..T-055; first 40 case bytes preserved.")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    main()
