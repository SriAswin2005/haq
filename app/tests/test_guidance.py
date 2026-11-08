"""General guidance: helpful answers outside the verified corpus, with every sourced detail removed by code."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import guidance, pipeline, retrieval, router, websearch  # noqa: E402


def _oos(text, kind="legal"):
    d = router._validate({"kind": kind, "category": "other_law", "language": "en-IN", "state_or_city": None,
                          "case_file_update": {}, "missing_facts": [], "escalation_flags": [],
                          "english_retrieval_query": text, "intent": ["explain_rights"], "question": text,
                          "new_topic": True, "summary": ""})
    return lambda cf, hist, t: (d, {"attempts": 1, "error": None})


class Clean(unittest.TestCase):
    allowed = "my friend owes me 50000. Office: National Cyber Crime Reporting Portal, call 1930, https://cybercrime.gov.in/"

    def test_keeps_general_and_allowed_details(self):
        text = ("- You can ask for the 50000 back in writing and keep the messages.\n"
                "- If money was taken by fraud, call 1930 or report it on cybercrime.gov.in.\n"
                "- If anyone is in danger, call 112.")
        out, removed = guidance.clean(text, self.allowed)
        self.assertEqual(removed, [])
        self.assertIn("1930", out)
        self.assertIn("112", out)

    def test_removes_anything_that_needs_a_source(self):
        text = ("- Under Section 420 IPC this is cheating.\n"
                "- In Navtej Singh Johar v. Union of India the court decided this.\n"
                "- You must file within 30 days.\n"
                "- The Partnership Act, 1932 applies.\n"
                "- Visit www.legalhelp-india.com for forms.\n"
                "- You will definitely win this case.\n"
                "- Keep every message and receipt.")
        out, removed = guidance.clean(text, self.allowed)
        self.assertEqual(out, "- Keep every message and receipt.")
        self.assertEqual(len(removed), 6)


class Wiring(unittest.TestCase):
    def setUp(self):
        self._answer, self._route, self._web, self._gate = guidance.answer, router.route, websearch.answer, retrieval.passes_gate

    def tearDown(self):
        guidance.answer, router.route, websearch.answer, retrieval.passes_gate = self._answer, self._route, self._web, self._gate

    def test_no_library_passage_uses_live_web_search_with_sources(self):
        retrieval.passes_gate = lambda score: False
        websearch.answer = lambda *a, **k: {"text": "Short answer:\nYou can file an RTI request. [1]", "queries": ["rti"],
                                            "dropped": [], "search_html": "",
                                            "sources": [{"n": 1, "domain": "rti.gov.in", "uri": "https://x", "official": True}]}
        router.route = _oos("my college mess manager won't give me the bills, can I use RTI")
        r = pipeline.handle_turn(pipeline.new_session("en-IN"), "can I use RTI for mess bills", lang_hint="en-IN")
        self.assertEqual(r.action, "answer")
        self.assertIn("searched official and legal sources", r.reply_text)
        self.assertIn("WEB-1", r.citations)
        self.assertNotIn("I don't cover this topic", r.reply_text)

    def test_web_search_unavailable_falls_back_to_labelled_general_information(self):
        retrieval.passes_gate = lambda score: False
        websearch.answer = lambda *a, **k: None
        guidance.answer = lambda *a, **k: {"type": "guidance", "text": "- Keep the messages.\n- Ask in writing.",
                                           "removed": [], "judge": "ok"}
        router.route = _oos("my business partner won't pay his share of the loss")
        r = pipeline.handle_turn(pipeline.new_session("en-IN"), "my business partner won't pay his share of the loss",
                                 lang_hint="en-IN")
        self.assertIn("General information", r.reply_text)
        self.assertIn("Keep the messages.", r.reply_text)
        self.assertNotIn("I don't cover this topic", r.reply_text)

    def test_small_talk_gets_a_normal_reply(self):
        guidance.answer = lambda *a, **k: {"type": "chat", "text": "Yes, of course you can drink water.",
                                           "removed": [], "judge": "skipped"}
        router.route = _oos("can i drink water", kind="chat")
        r = pipeline.handle_turn(pipeline.new_session("en-IN"), "can i drink water", lang_hint="en-IN")
        self.assertEqual(r.action, "clarify")
        self.assertIn("drink water", r.reply_text)
        self.assertFalse(r.needs_lawyer)

    def test_harmful_request_is_refused_without_steps(self):
        router.route = _oos("how do I kill him and escape", kind="harmful")
        r = pipeline.handle_turn(pipeline.new_session("en-IN"), "how do I kill him and escape", lang_hint="en-IN")
        self.assertIn("I won't help with that", r.reply_text)
        self.assertIn("112", r.reply_text)

    def test_mock_mode_keeps_the_safe_response(self):
        self.assertIsNone(self._answer("hello", "", "en-IN", "out_of_scope", []))


class VoiceChoice(unittest.TestCase):
    def test_chosen_provider_goes_first_and_the_other_stays_as_fallback(self):
        from app import voice
        chain = [{"provider": "gemini", "model": "g1"}, {"provider": "sarvam", "model": "s1"}, {"provider": "gemini", "model": "g2"}]
        self.assertEqual([e["model"] for e in voice._ordered(chain, "sarvam")], ["s1", "g1", "g2"])
        self.assertEqual([e["model"] for e in voice._ordered(chain, "google")], ["g1", "g2", "s1"])
        self.assertEqual(voice._ordered(chain, None), chain)


if __name__ == "__main__":
    unittest.main()
