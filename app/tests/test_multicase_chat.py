"""Real users mix cases in one chat. The case file must follow them (live test, 6 Nov 2026):
Jio refund -> traffic police (out of scope) -> rental deposit -> back to Jio."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import pipeline  # noqa: E402


def route(cat, upd, summary="", new_topic=False):
    return lambda cf, h, t: ({"category": cat, "language": "en-IN", "state_or_city": "UP", "case_file_update": upd,
                              "missing_facts": [], "escalation_flags": ["police_misconduct"] if cat == "out_of_scope" else [],
                              "english_retrieval_query": t, "intent": ["next_steps"], "question": t,
                              "new_topic": new_topic, "summary": summary}, {"attempts": 1, "error": None})


class MultiCaseChat(unittest.TestCase):
    def setUp(self):
        self._route = pipeline.router.route

    def tearDown(self):
        pipeline.router.route = self._route

    def test_mixed_chat(self):
        s = pipeline.new_session("en-IN")
        pipeline.router.route = route("consumer", {"counterparty_name": "Jio", "resolution_wanted": "refund",
                                                   "what_happened": "Jio refund for a recharge not received after 21 days"},
                                      "Your Jio recharge refund has not arrived.")
        pipeline.handle_turn(s, "jio refund not received", lang_hint="en-IN")

        pipeline.router.route = route("out_of_scope", {"what_happened": "Traffic police seized bike over unpaid challan",
                                                       "counterparty_type": "police"},
                                      "Traffic police seized your bike over an unpaid challan.", new_topic=True)
        r2 = pipeline.handle_turn(s, "police seized my bike for a challan", lang_hint="en-IN")
        cf = s.case_file
        self.assertEqual(cf["category"], "consumer", "out-of-scope question must not change the active case")
        self.assertIn("Jio", cf["what_happened"])
        self.assertNotEqual(cf.get("counterparty_type"), "police")
        self.assertEqual(cf["summary"], "Your Jio recharge refund has not arrived.")
        self.assertIn("Traffic police seized your bike", cf["side_topics"][-1])
        self.assertIn("Traffic police seized your bike", r2.reply_text, "the reply still says what it understood")

        pipeline.router.route = route("tenancy", {"counterparty_type": "landlord", "amount_inr": 20000,
                                                  "what_happened": "Landlord kept the deposit"},
                                      "Your landlord kept your 20000 deposit.")
        pipeline.handle_turn(s, "another problem, landlord kept my 20000 deposit", lang_hint="en-IN")
        self.assertEqual(s.case_file["category"], "tenancy")
        self.assertNotIn("counterparty_name", s.case_file, "the Jio name does not leak into the deposit case")
        self.assertEqual(s.case_file["previous_cases"][-1]["counterparty_name"], "Jio")

        pipeline.router.route = route("consumer", {"order_id": "JIO-123"}, "Your Jio refund, order JIO-123.")
        r4 = pipeline.handle_turn(s, "back to the jio refund, order id JIO-123", lang_hint="en-IN")
        self.assertTrue(r4.trace["topic_switch"]["restored"])
        self.assertEqual(s.case_file["counterparty_name"], "Jio", "returning to a topic restores its case")
        self.assertEqual(s.case_file["order_id"], "JIO-123")
        self.assertNotIn("amount_inr", s.case_file, "the deposit amount stays with the deposit case")
        self.assertEqual(s.case_file["previous_cases"][-1]["category"], "tenancy")
        self.assertTrue(s.case_file["side_topics"], "out-of-scope questions are remembered for the panel")


if __name__ == "__main__":
    unittest.main()
