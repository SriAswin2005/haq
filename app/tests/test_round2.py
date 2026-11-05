"""Unit tests for the Round-2 code gaps. Keyless: run with
    python -m unittest discover -s app/tests -t .
(Mock model + hash embeddings; AI_LAWYER_TODAY pins the date for the limitation arithmetic.)"""
import os
import unittest
from datetime import date
from unittest import mock

os.environ["AI_LAWYER_MOCK"] = "1"
os.environ["AI_LAWYER_TODAY"] = "2026-11-05"

from app import guards, pipeline, router  # noqa: E402

LANDLORD = "my landlord in Lucknow kept my deposit of Rs 20000"


def turn(text, lang=None, session=None):
    s = session or pipeline.new_session()
    return pipeline.handle_turn(s, text, lang_hint=lang), s


class MinorDetection(unittest.TestCase):
    def test_flags(self):
        for t in ["I am 16 and my landlord kept my deposit", "I'm 17", "I am 16 years old", "she is a 15-year-old",
                  "my age is 14", "mera umar 16 hai", "umar 16", "main 16 saal ka hoon", "मैं 16 साल का हूँ",
                  "मैं १६ साल की हूं", "मेरी उम्र 15 है"]:
            self.assertEqual(guards.minor_flags(t), ["minor_age"], t)

    def test_no_false_flags(self):
        for t in ["I am 25 years old", "I am 3 months late on rent", "I am 5 days away", "my deposit is 16000 rupees",
                  "I worked 3 years there", "5 साल का किराया बाकी है", "मैं 30 साल का हूँ", "I am 18", "umar 45"]:
            self.assertEqual(guards.minor_flags(t), [], t)

    def test_pipeline_hard_escalation_and_persists(self):
        r, s = turn("I am 16 and my landlord in Lucknow kept my deposit of Rs 20000")
        self.assertEqual(r.action, "escalate")
        self.assertIn("minor_age", r.escalation_reasons)
        self.assertTrue(r.needs_lawyer)
        r2, _ = turn("he still has not paid", session=s)  # no age restated: still escalates
        self.assertEqual(r2.action, "escalate")
        self.assertNotIn("minor stated", r2.reply_text)


class CriminalKeywords(unittest.TestCase):
    def test_keywords(self):
        for t in ["I will send him to jail", "he is guilty under IPC", "BNS section", "this is a 420 case",
                  "cheating case against landlord", "fraud case", "I will file a police case", "main case karunga",
                  "उसे जेल भेजूंगा", "यह धोखाधड़ी है", "मैं केस करूंगा"]:
            self.assertTrue(router.keyword_flags(t), t)

    def test_no_false_flags(self):
        for t in ["Rs 4200 deposit", "my first order", "deposit not returned"]:
            self.assertEqual(router.keyword_flags(t), [], t)

    def test_pipeline_escalates(self):
        r, _ = turn("landlord in Lucknow kept my deposit, I want him in jail")
        self.assertEqual(r.action, "escalate")


class LimitationInCode(unittest.TestCase):
    def test_months_since(self):
        t = date(2026, 11, 5)
        self.assertEqual(guards.months_since("2026-09-05", t), 2.0)
        self.assertEqual(guards.months_since("2023-03", t), 44.1)  # 44 months + 4 days
        self.assertEqual(round(guards.months_since("2024-11", t)), 24)
        self.assertEqual(guards.months_since("March 2024", t), guards.months_since("2024-03", t))
        self.assertIsNone(guards.months_since("not a date", t))
        self.assertEqual(guards.months_since("2030-01-01", t), 0.0)

    def test_relative(self):
        t = date(2026, 11, 5)
        self.assertEqual(guards.relative_event_date("I left 2 months ago", t), "2026-09-05")
        self.assertEqual(guards.relative_event_date("3 साल पहले", t), "2023-11-05")
        self.assertEqual(guards.relative_event_date("6 mahine pehle", t), "2026-05-05")
        self.assertIsNone(guards.relative_event_date("no dates here", t))

    def test_llm_months_ignored_and_code_computes(self):
        fake = ({"category": "tenancy", "language": "en-IN", "state_or_city": "UP",
                 "case_file_update": {"event_date": "2023-03", "months_since_event": 1, "amount_inr": 20000},
                 "missing_facts": [], "escalation_flags": [],
                 "english_retrieval_query": "security deposit"}, {"attempts": 1, "error": None})
        with mock.patch("app.router.route", return_value=fake):
            r, s = turn(LANDLORD)
        self.assertGreater(s.case_file["months_since_event"], 40)  # not the LLM's 1
        self.assertIn("limitation_risk", r.escalation_reasons)
        self.assertTrue(r.needs_lawyer)

    def test_recent_event_no_flag(self):
        r, s = turn("I vacated my flat in Lucknow 2 months ago, landlord not returning 30000 deposit")
        self.assertEqual(s.case_file["months_since_event"], 2.0)
        self.assertNotIn("limitation_risk", r.escalation_reasons)

    def test_month_year_pipeline(self):
        r, s = turn("I left the flat in Lucknow in March 2023, landlord keeps my Rs 20000 deposit")
        self.assertGreater(s.case_file["months_since_event"], 30)
        self.assertIn("limitation_risk", r.escalation_reasons)


class CaseLaw(unittest.TestCase):
    def test_detect(self):
        for t in ["give me a Supreme Court judgment", "any precedent?", "case law on deposits", "similar cases",
                  "इस पर कोई फैसला बताओ", "सुप्रीम कोर्ट का फैसला", "koi faisla hai?"]:
            self.assertTrue(guards.case_law_request(t), t)
        for t in ["my landlord kept my deposit", "I want to file a case", "मेरा केस क्या होगा"]:
            self.assertFalse(guards.case_law_request(t), t)

    def test_reply_has_line_en(self):
        r, _ = turn(LANDLORD + ". Please quote a Supreme Court judgment on this.")
        self.assertIn("I can't cite court cases; I don't have verified judgments.", r.reply_text)
        self.assertTrue(r.needs_lawyer)

    def test_reply_has_line_hi_and_on_refusal_paths(self):
        line = pipeline._m("hi-IN")["no_case_law"]
        r, _ = turn("मेरे मकान मालिक ने लखनऊ में डिपॉज़िट नहीं लौटाया, इस पर कोई फैसला बताइए", lang="hi-IN")
        self.assertIn(line, r.reply_text)
        r2, _ = turn("police case: any judgment?")  # escalation path also carries the line
        self.assertIn("I can't cite court cases", r2.reply_text)

    def test_no_line_when_not_asked(self):
        r, _ = turn(LANDLORD)
        self.assertNotIn("can't cite court cases", r.reply_text)


class HindiBody(unittest.TestCase):
    def test_script_check(self):
        self.assertTrue(guards.script_ok("मकान मालिक को जमा राशि लौटानी होगी, यह नियम में लिखा है।", "hi-IN"))
        self.assertFalse(guards.script_ok("The landlord must return the deposit within the time in the law.", "hi-IN"))
        self.assertTrue(guards.script_ok("The landlord must return the deposit within the time.", "en-IN"))

    def test_retry_once_when_body_is_english(self):
        calls = []
        english = {"blocks": [{"text": "The landlord must return the deposit within 30 days of leaving.",
                               "type": "legal", "cites": ["__ID__"]}], "needs_lawyer": False, "gaps": []}
        real = pipeline._generate_answer

        def fake(msgs):
            calls.append(msgs[-1]["content"])
            a = real(msgs)
            if "LANGUAGE ISSUE" not in msgs[-1]["content"]:
                return {"blocks": [dict(b, text="The landlord must return the deposit.") if b["type"] == "legal" else b
                                   for b in a["blocks"]], "needs_lawyer": False, "gaps": []}
            return {"blocks": [dict(b, text="मकान मालिक को जमा राशि लौटानी होगी, यह स्रोत में लिखा है।") if b["type"] == "legal" else b
                               for b in a["blocks"]], "needs_lawyer": False, "gaps": []}

        with mock.patch("app.pipeline._generate_answer", side_effect=fake), \
                mock.patch("app.verifier.verify", return_value=([], {"judge": "mock"})):
            r, _ = turn("मेरे मकान मालिक ने लखनऊ में डिपॉज़िट नहीं लौटाया", lang="hi-IN")
        self.assertEqual(len(calls), 2)
        self.assertIn("LANGUAGE ISSUE", calls[1])
        self.assertTrue(r.trace.get("language_retry"))
        self.assertNotIn("language_warning", r.trace)
        self.assertIn("मकान मालिक को जमा राशि", r.reply_text)


class SourceNotes(unittest.TestCase):
    def test_notes(self):
        sec = {"source_type": "secondary", "status_note": "REVIEW 2026-11-05: summary, not verbatim"}
        n = guards.source_notes(sec)
        self.assertIn("source type: secondary", n)
        self.assertIn(sec["status_note"], n)
        self.assertIn("(unverified source – check before relying on it)", n)
        off = guards.source_notes({"source_type": "official", "status_note": ""})
        self.assertEqual(off, ["source type: official"])


if __name__ == "__main__":
    unittest.main()
