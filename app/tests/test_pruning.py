"""Claim-level pruning: a claim that fails verification is dropped, verified claims survive."""
import os
import unittest

os.environ["AI_LAWYER_MOCK"] = "1"

from app import pipeline, verifier  # noqa: E402


class Pruning(unittest.TestCase):
    def setUp(self):
        self._gen, self._judge = pipeline._generate_answer, verifier.judge

    def tearDown(self):
        pipeline._generate_answer, verifier.judge = self._gen, self._judge

    def _run(self, judge_fn):
        def gen(msgs):
            chunks = pipeline.retrieval.get_index()["chunks"]
            cid = next(c["id"] for c in chunks if c["id"].startswith("TEN-UPTA2021-S11"))
            return {"blocks": [
                {"text": "GOOD CLAIM: the deposit is refunded when you hand over possession.", "type": "legal", "cites": [cid]},
                {"text": "BAD CLAIM: the landlord always owes you interest.", "type": "legal", "cites": [cid]},
                {"text": "Keep your receipts.", "type": "practical", "cites": []}],
                "needs_lawyer": False, "gaps": []}
        pipeline._generate_answer = gen
        verifier.judge = judge_fn
        s = pipeline.new_session("en-IN")
        return pipeline.handle_turn(s, "landlord not returning my 20000 deposit, Lucknow UP, I moved out", lang_hint="en-IN")

    def test_bad_block_pruned_good_kept(self):
        def judge(answer, retrieved):
            bad = [i for i, b in enumerate(answer["blocks"]) if b["text"].startswith("BAD")]
            return [f"block {i}: claim not supported by its cited source (test)" for i in bad], "ok"
        r = self._run(judge)
        self.assertEqual(r.verifier["status"], "fixed")
        self.assertTrue(r.verifier.get("pruned"))
        self.assertIn("GOOD CLAIM", r.reply_text)
        self.assertNotIn("BAD CLAIM", r.reply_text)
        self.assertIn("could not match it exactly", r.reply_text)
        self.assertIn(r.action, ("answer", "clarify"))

    def test_all_legal_blocks_bad_falls_back_to_safe_response(self):
        def judge(answer, retrieved):
            return [f"block {i}: unsupported (test)" for i, b in enumerate(answer["blocks"]) if b["type"] == "legal"], "ok"
        r = self._run(judge)
        self.assertEqual(r.action, "refuse_unverified")
        self.assertNotIn("BAD CLAIM", r.reply_text)
        self.assertNotIn("GOOD CLAIM", r.reply_text)


if __name__ == "__main__":
    unittest.main()
