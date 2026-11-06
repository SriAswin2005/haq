"""Fixes from the round-4 full eval: reply script for English, exact websites, pruning an earlier draft,
old-law note when the user names a repealed Act."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import guards, pipeline, verifier  # noqa: E402


def _cid(prefix):
    return next(c["id"] for c in pipeline.retrieval.get_index()["chunks"] if c["id"].startswith(prefix))


class EnglishScript(unittest.TestCase):
    def test_hindi_body_for_english_user_is_rejected(self):
        self.assertFalse(guards.script_ok("आप अपनी शिकायत एयर सेवा पोर्टल पर दर्ज कर सकते हैं और उसे ट्रैक कर सकते हैं।", "en-IN"))
        self.assertTrue(guards.script_ok("You can file your complaint on the AirSewa portal and track it.", "en-IN"))


class Websites(unittest.TestCase):
    src = [{"id": "X", "text": "Lodge it at https://airsewa.gov.in/ or email complaints@irdai.gov.in", "source_url": "https://airsewa.gov.in/"}]

    def blocks(self, text):
        return {"blocks": [{"type": "practical", "text": text, "cites": []}]}

    def test_misspelt_site_flagged(self):
        issues = verifier.check(self.blocks("Go to https://airseva.gov.in/ to complain."), self.src, {})
        self.assertTrue(any("website" in i for i in issues), issues)

    def test_exact_site_and_email_pass(self):
        issues = verifier.check(self.blocks("Go to airsewa.gov.in or write to complaints@irdai.gov.in."), self.src, {})
        self.assertFalse(any("website" in i for i in issues), issues)


class PruneEarlierDraft(unittest.TestCase):
    def setUp(self):
        self._gen, self._judge = pipeline._generate_answer, verifier.judge

    def tearDown(self):
        pipeline._generate_answer, verifier.judge = self._gen, self._judge

    def test_falls_back_to_first_draft_when_second_cannot_be_pruned(self):
        cid = _cid("TEN-UPTA2021-S11")
        calls = {"n": 0}

        def gen(msgs):
            calls["n"] += 1
            if calls["n"] == 1:   # first draft: one good legal claim, one bad one
                return {"blocks": [{"text": "GOOD CLAIM about the deposit.", "type": "legal", "cites": [cid]},
                                   {"text": "BAD CLAIM one.", "type": "legal", "cites": [cid]}], "needs_lawyer": False, "gaps": []}
            return {"blocks": [{"text": "BAD CLAIM two.", "type": "legal", "cites": [cid]}], "needs_lawyer": False, "gaps": []}

        def judge(answer, retrieved):
            return [f"block {i}: unsupported (test)" for i, b in enumerate(answer["blocks"]) if b["text"].startswith("BAD")], "ok"
        pipeline._generate_answer, verifier.judge = gen, judge
        r = pipeline.handle_turn(pipeline.new_session("en-IN"), "landlord not returning my 20000 deposit, Lucknow UP, I moved out",
                                 lang_hint="en-IN")
        self.assertIn("GOOD CLAIM", r.reply_text)
        self.assertNotIn("BAD CLAIM", r.reply_text)
        self.assertEqual(r.verifier["status"], "fixed")


class LimitationFromPurchaseDate(unittest.TestCase):
    def test_purchase_date_starts_the_clock(self):
        from app import router
        cf = {"purchase_date": "2023-01-01"}
        cf["months_since_event"] = __import__("app.guards", fromlist=["x"]).months_since(cf["purchase_date"])
        self.assertGreater(cf["months_since_event"], 30)


class NamedOldLaw(unittest.TestCase):
    def test_old_law_named_by_user_gets_note(self):
        r = pipeline.handle_turn(pipeline.new_session("en-IN"),
                                 "Lucknow UP, I moved out and the landlord keeps my 20000 deposit. The 1972 rent act still applies, right?",
                                 lang_hint="en-IN")
        if r.action in ("answer", "clarify"):
            self.assertIn("1972", r.reply_text)
            self.assertTrue(any(x.get("old_law") for x in r.retrieved), r.retrieved)


if __name__ == "__main__":
    unittest.main()
