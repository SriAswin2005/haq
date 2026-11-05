"""Out-of-scope referrals: precision over recall. A wrong office misleads; a missing one falls back to legal aid."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import llm, pipeline, retrieval  # noqa: E402


def chunk(cid, title, score, doc_type="portal_procedure", source_type="official", heading="", text="Call 1930."):
    return {"id": cid, "score": score, "chunk": {"id": cid, "doc_title": title, "doc_type": doc_type, "status": "in_force",
            "source_type": source_type, "heading": heading, "text": text, "source_url": f"https://example.gov.in/{cid}",
            "unit_number": "", "category": "common"}}


class Referrals(unittest.TestCase):
    def setUp(self):
        self._search, self._mock = retrieval.search, llm.is_mock
        llm.is_mock = lambda: False          # use the real (strict) referral bar

    def tearDown(self):
        retrieval.search, llm.is_mock = self._search, self._mock

    def lines(self, hits):
        retrieval.search = lambda *a, **k: {"hits": hits, "old_law": [], "top_score": hits[0]["score"] if hits else 0}
        return pipeline._referral_lines("my upi money was stolen by fraud", None, pipeline._m("en-IN"))

    def test_strong_official_match_is_shown_with_hedge(self):
        text, ids, _ = self.lines([chunk("COM-DIR-CYBER", "National Cyber Crime Reporting Portal", 0.78,
                                         heading="report online financial fraud")])
        self.assertIn("National Cyber Crime Reporting Portal", text)
        self.assertIn("may handle this", text)
        self.assertIn("1930", text, "helpline numbers come verbatim from the chunk")
        self.assertEqual(ids, ["COM-DIR-CYBER"])

    def test_weak_match_is_not_shown(self):
        text, ids, _ = self.lines([chunk("COM-DIR-RAIL", "Rail Madad", 0.68)])
        self.assertEqual((text, ids), ("", []))

    def test_secondary_source_never_shown(self):
        text, _, _ = self.lines([chunk("COM-DIR-X", "Some blog list", 0.95, source_type="secondary")])
        self.assertEqual(text, "")

    def test_legal_aid_not_duplicated_as_referral(self):
        text, _, _ = self.lines([chunk("COM-NALSA", "National Legal Services Authority Helpline", 0.9, doc_type="helpline")])
        self.assertEqual(text, "")


if __name__ == "__main__":
    unittest.main()
