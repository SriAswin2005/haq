"""Topic switches start a fresh case file; any legal topic gets an answer; only real danger puts safety first."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import pipeline  # noqa: E402


def _route(cat, upd, flags=(), new_topic=False, q="", danger=False, lawyer=""):
    return lambda cf, hist, text: ({"kind": "legal", "category": cat, "language": "en-IN", "state_or_city": "UP",
                                    "danger_now": danger, "lawyer_note": lawyer,
                                    "case_file_update": upd, "missing_facts": [], "escalation_flags": list(flags),
                                    "english_retrieval_query": text, "intent": ["explain_rights"],
                                    "question": q, "new_topic": new_topic}, {"attempts": 1, "error": None})


class TopicAndScope(unittest.TestCase):
    def setUp(self):
        self._route = pipeline.router.route

    def tearDown(self):
        pipeline.router.route = self._route

    def test_other_legal_topic_is_answered_as_its_own_case(self):
        s = pipeline.new_session("en-IN")
        pipeline.router.route = _route("consumer", {"counterparty_name": "Jio", "resolution_wanted": "refund"})
        pipeline.handle_turn(s, "jio refund delayed", lang_hint="en-IN")
        pipeline.router.route = _route("other_law", {"what_happened": "police seized bike over unpaid challan"},
                                       new_topic=True)
        r = pipeline.handle_turn(s, "police seized my bike for a challan, what do I do", lang_hint="en-IN")
        self.assertNotEqual(r.action, "escalate", "a police question is answered, not referred away")
        self.assertNotIn("Jio", r.reply_text, "old case facts must not leak into a different topic")
        self.assertNotIn("don't cover this topic", r.reply_text)
        self.assertEqual(s.case_file["previous_cases"][-1].get("counterparty_name"), "Jio", "the consumer case is kept")

    def test_real_danger_puts_safety_first_and_still_answers(self):
        s = pipeline.new_session("en-IN")
        pipeline.router.route = _route("other_law", {"what_happened": "husband beats me every night"}, danger=True,
                                       lawyer="A lawyer can help you get a protection order quickly.")
        r = pipeline.handle_turn(s, "my husband beats me every night", lang_hint="en-IN")
        self.assertTrue(r.reply_text.startswith("If you or anyone is in danger right now, call 112"))
        self.assertIn("protection order", r.reply_text)
        self.assertTrue(r.needs_lawyer)

    def test_switch_between_covered_topics_archives_old_case(self):
        s = pipeline.new_session("en-IN")
        pipeline.router.route = _route("consumer", {"counterparty_name": "Jio", "amount_inr": 399})
        pipeline.handle_turn(s, "jio refund 399", lang_hint="en-IN")
        pipeline.router.route = _route("tenancy", {"amount_inr": 20000, "counterparty_type": "landlord"})
        r = pipeline.handle_turn(s, "different problem: landlord kept my 20000 deposit", lang_hint="en-IN")
        self.assertEqual(r.trace["topic_switch"], {"from": "consumer", "to": "tenancy", "restored": False})
        self.assertEqual(s.case_file["amount_inr"], 20000)
        self.assertNotIn("conflicts", s.case_file, "a new case is not a conflict with the old one")
        self.assertEqual(s.case_file["previous_cases"][-1]["counterparty_name"], "Jio")


if __name__ == "__main__":
    unittest.main()
