"""Two different values for the same fact are recorded, shown, and left blank in drafts."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import drafts, pipeline  # noqa: E402


class Conflicts(unittest.TestCase):
    def test_conflict_recorded_and_blank_in_draft(self):
        s = pipeline.new_session("en-IN")
        orig = pipeline.router.route

        def fake_route(cf, hist, text):
            v = "2026-09-10" if "first" in text else "2026-09-20"
            rj = {"category": "tenancy", "language": "en-IN", "state_or_city": "UP",
                  "case_file_update": {"vacated_date": v, "amount_inr": 20000}, "missing_facts": [],
                  "escalation_flags": [], "english_retrieval_query": "deposit not returned"}
            return rj, {"attempts": 1, "error": None}
        pipeline.router.route = fake_route
        try:
            pipeline.handle_turn(s, "first message: I left on 10 Sept", lang_hint="en-IN")
            s.mode = "draft"
            r = pipeline.handle_turn(s, "second message: I left on 20 Sept", lang_hint="en-IN")
        finally:
            pipeline.router.route = orig
        self.assertEqual(s.case_file["conflicts"][0]["field"], "vacated_date")
        self.assertIn("two different values", r.reply_text)
        self.assertIn("[● date you vacated]", r.draft_text)     # left blank, not silently filled
        self.assertNotIn("2026-09-20 under", r.draft_text)


if __name__ == "__main__":
    unittest.main()
