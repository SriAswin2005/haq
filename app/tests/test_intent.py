"""Replays the user's live Jio chat (6 Nov 2026): in Draft mode, a question must get an answer
(the main model must run), the draft is attached after it, a follow-up is not answered with the
same template again, and what_happened keeps the dispute facts."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import llm, pipeline  # noqa: E402


class IntentAwareDraft(unittest.TestCase):
    def setUp(self):
        self._route = pipeline.router.route

    def tearDown(self):
        pipeline.router.route = self._route

    def test_jio_chat(self):
        turns = [
            ({"what_happened": "Jio accepted a refund for a recharge but it has not arrived after 21 days",
              "counterparty_name": "Jio", "product_or_service": "mobile recharge", "resolution_wanted": "refund"},
             ["what_can_i_get", "documents_needed", "draft_document"],
             "What can I do about the delayed refund, what will I get, what should I keep ready, and can you draft a complaint?"),
            ({"what_happened": "User is asking for the specific portal to file a consumer complaint"},
             ["where_to_complain", "follow_up"],
             "Which portal should I use to file a consumer complaint against Jio?"),
        ]
        state = {"i": 0}

        def fake_route(cf, hist, text):
            upd, intents, q = turns[state["i"]]
            state["i"] += 1
            return ({"category": "consumer", "language": "en-IN", "state_or_city": None, "case_file_update": upd,
                     "missing_facts": [], "escalation_flags": [], "english_retrieval_query": "consumer complaint refund",
                     "intent": intents, "question": q}, {"attempts": 1, "error": None})
        pipeline.router.route = fake_route
        s = pipeline.new_session("en-IN")
        s.mode = "draft"
        r1 = pipeline.handle_turn(s, "jio refund delayed, what can I do, what will I get, help me draft", lang_hint="en-IN")
        models1 = r1.trace["llm"]["models"]
        r2 = pipeline.handle_turn(s, "which portal should I go to", lang_hint="en-IN")
        models2 = r2.trace["llm"]["models"]

        self.assertTrue(any(m.startswith("mock:main") for m in models1), "turn 1: the answer model must run")
        self.assertIsNotNone(r1.draft_text, "turn 1: a draft was asked for, so it is attached")
        self.assertTrue(r1.trace["intent"]["has_question"])
        self.assertTrue(any(m.startswith("mock:main") for m in models2), "turn 2: a follow-up question gets an answer")
        self.assertIsNone(r2.draft_text, "turn 2: no draft asked for, so the template is not repeated")
        self.assertNotEqual(r1.reply_text, r2.reply_text)
        self.assertIn("recharge", s.case_file["what_happened"], "the dispute facts survive the follow-up")
        self.assertEqual(r2.trace.get("what_happened_ignored", "")[:8], "User is ")

    def test_facts_only_in_draft_mode_just_updates_the_draft(self):
        def fake_route(cf, hist, text):
            return ({"category": "tenancy", "language": "en-IN", "state_or_city": "UP",
                     "case_file_update": {"counterparty_name": "Mr Sharma"}, "missing_facts": [],
                     "escalation_flags": [], "english_retrieval_query": "deposit", "intent": ["other"], "question": ""},
                    {"attempts": 1, "error": None})
        pipeline.router.route = fake_route
        s = pipeline.new_session("en-IN")
        s.mode = "draft"
        r = pipeline.handle_turn(s, "landlord's name is Mr Sharma", lang_hint="en-IN")
        self.assertEqual(r.action, "draft")
        self.assertIn("Mr Sharma", r.draft_text)


if __name__ == "__main__":
    unittest.main()
