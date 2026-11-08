"""'What I understood' must be in the user's language, not an English facts dump (live test, 6 Nov 2026)."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import pipeline  # noqa: E402


class SummaryLanguage(unittest.TestCase):
    def setUp(self):
        self._route = pipeline.router.route

    def tearDown(self):
        pipeline.router.route = self._route

    def _run(self, summary):
        pipeline.router.route = lambda cf, h, t: ({
            "category": "out_of_scope", "language": "hi-IN", "state_or_city": None,
            "case_file_update": {"what_happened": "Bike seized by traffic police over an unpaid challan; officer was rude",
                                 "counterparty_type": "police"},
            "missing_facts": [], "escalation_flags": ["police_misconduct"], "english_retrieval_query": "traffic challan bike seized",
            "intent": ["next_steps"], "question": "What should I do?", "new_topic": False, "summary": summary},
            {"attempts": 1, "error": None})
        s = pipeline.new_session("hi-IN")
        return pipeline.handle_turn(s, "ट्रैफिक पुलिस ने चालान के लिए मेरी बाइक ज़ब्त कर ली", lang_hint="hi-IN")

    def test_hindi_reply_never_shows_english_facts(self):
        r = self._run("आपकी बाइक बकाया चालान की वजह से ट्रैफ़िक पुलिस ने ज़ब्त कर ली और police वाले ने बदतमीज़ी की।")
        self.assertNotIn("what happened", r.reply_text.lower())
        self.assertNotIn("Bike seized", r.reply_text)

    def test_english_summary_on_hindi_reply_is_rejected(self):
        r = self._run("Your bike was seized by traffic police.")
        self.assertIn("summary_rejected", r.trace)
        self.assertNotIn("Your bike was seized", r.reply_text)
        self.assertNotIn("Bike seized by traffic police", r.reply_text, "fallback must not show English sentences")


if __name__ == "__main__":
    unittest.main()
