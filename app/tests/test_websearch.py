"""Live web answers keep only the sentences Google ties to an acceptable source."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import llm, websearch  # noqa: E402

TEXT = """Short answer:
Same-sex marriage is not legally recognised in India. The Supreme Court left the question to Parliament.

What the law says:
- Consensual same-sex relationships are not a crime.
- Everyone on Reddit says you can marry abroad and it counts here.
- My cousin did it and it was fine.

What to do:
"""

META = {
    "webSearchQueries": ["same sex marriage India supreme court"],
    "groundingChunks": [{"web": {"uri": "https://redirect/1", "title": "sci.gov.in"}},
                        {"web": {"uri": "https://redirect/2", "title": "livelaw.in"}},
                        {"web": {"uri": "https://redirect/3", "title": "reddit.com"}}],
    "groundingSupports": [
        {"segment": {"text": "Same-sex marriage is not legally recognised in India."}, "groundingChunkIndices": [0, 1]},
        {"segment": {"text": "The Supreme Court left the question to Parliament."}, "groundingChunkIndices": [1]},
        {"segment": {"text": "Consensual same-sex relationships are not a crime."}, "groundingChunkIndices": [0]},
        {"segment": {"text": "Everyone on Reddit says you can marry abroad and it counts here."}, "groundingChunkIndices": [2]},
    ],
    "searchEntryPoint": {"renderedContent": "<div>chips</div>"},
}


class WebAnswer(unittest.TestCase):
    def setUp(self):
        self._g, self._m = llm.generate_grounded, llm.is_mock
        llm.is_mock = lambda: False
        llm.generate_grounded = lambda msgs, role="search": (TEXT, META)

    def tearDown(self):
        llm.generate_grounded, llm.is_mock = self._g, self._m

    def test_keeps_only_supported_sentences_with_numbered_sources(self):
        w = websearch.answer("Is same-sex marriage legal?", "is same sex marriage legal", "en-IN", "IN", None)
        self.assertIsNotNone(w)
        self.assertIn("not legally recognised in India. [1][2]", w["text"])
        self.assertIn("left the question to Parliament. [2]", w["text"])
        self.assertIn("- Consensual same-sex relationships are not a crime. [1]", w["text"])
        self.assertNotIn("Reddit", w["text"], "a forum never counts as support")
        self.assertNotIn("cousin", w["text"], "unsupported sentences are dropped")
        self.assertNotIn("What to do:", w["text"], "a heading with nothing under it is dropped")
        self.assertEqual([s["domain"] for s in w["sources"]], ["sci.gov.in", "livelaw.in"])
        self.assertTrue(w["sources"][0]["official"])
        self.assertEqual(w["search_html"], "<div>chips</div>")

    def test_too_little_support_returns_none(self):
        llm.generate_grounded = lambda msgs, role="search": ("Short answer:\nIt depends.", {"groundingChunks": []})
        self.assertIsNone(websearch.answer("q", "q", "en-IN", "IN", None))

    def test_mock_mode_never_searches(self):
        llm.is_mock = lambda: True
        self.assertIsNone(websearch.answer("q", "q", "en-IN", "IN", None))


if __name__ == "__main__":
    unittest.main()
