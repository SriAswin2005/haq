"""Topic switches start a fresh case file; out-of-scope topics are not presented as an emergency."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import pipeline  # noqa: E402


def _route(cat, upd, flags=(), new_topic=False, q=""):
    return lambda cf, hist, text: ({"category": cat, "language": "en-IN", "state_or_city": "UP",
                                    "case_file_update": upd, "missing_facts": [], "escalation_flags": list(flags),
                                    "english_retrieval_query": text, "intent": ["explain_rights"],
                                    "question": q, "new_topic": new_topic}, {"attempts": 1, "error": None})


class TopicAndScope(unittest.TestCase):
    def setUp(self):
        self._route = pipeline.router.route

    def tearDown(self):
        pipeline.router.route = self._route

    def test_switch_to_out_of_scope_does_not_mix_old_case(self):
        s = pipeline.new_session("en-IN")
        pipeline.router.route = _route("consumer", {"counterparty_name": "Jio", "resolution_wanted": "refund"})
        pipeline.handle_turn(s, "jio refund delayed", lang_hint="en-IN")
        pipeline.router.route = _route("out_of_scope", {"what_happened": "police seized bike over unpaid challan"},
                                       flags=["police_misconduct"], new_topic=True)
        r = pipeline.handle_turn(s, "police seized my bike for a challan, what do I do", lang_hint="en-IN")
        self.assertEqual(r.action, "escalate")
        self.assertNotIn("Jio", r.reply_text, "old case facts must not leak into a different topic")
        self.assertEqual(r.trace["escalation_level"], "out_of_scope")
        self.assertNotIn("needs a real lawyer", r.reply_text)
        self.assertIn("don't cover this topic", r.reply_text)
        self.assertEqual(s.case_file.get("counterparty_name"), "Jio", "the consumer case is kept for later")

    def test_real_danger_still_says_lawyer(self):
        s = pipeline.new_session("en-IN")
        pipeline.router.route = _route("out_of_scope", {"what_happened": "arrested after a fight"}, flags=["arrest"])
        r = pipeline.handle_turn(s, "police arrested my brother last night", lang_hint="en-IN")
        self.assertEqual(r.trace["escalation_level"], "danger")
        self.assertIn("real lawyer", r.reply_text)

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
