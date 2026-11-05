"""Guard the matched-cohort counts and trace-only performance accounting."""
import unittest

from tests.checks import CHECKS, CheckResult
from tests.round3_reports import percentile, performance, summarise


def fixture_item():
    checks = {name: CheckResult("pass", "fixture") for name in CHECKS}
    result = {"reply_text": "Fixture", "reply_lang": "hi-IN", "action": "refuse_unverified",
              "citations": [], "retrieved": [], "needs_lawyer": False,
              "trace": {"llm": {"calls": 2, "models": ["main:gemini:served-A"], "fallbacks": []},
                        "models": {"main": {"model": "CONFIGURED-BUT-UNSERVED"}}}}
    second = {**result, "action": "answer", "trace": {"pruned": {}, "llm": {
        "calls": 3, "models": ["main:gemini:served-A", "main:gemini:served-B"],
        "fallbacks": [{"role": "main", "reason": "HTTP 503"}]},
        "translation": {"status": "ok", "attempts": 1}}}
    return {"status": "pass", "case": {"id": "FIXTURE", "language": "hi-IN", "group": "D_fixture",
            "expect_needs_lawyer": False, "expected_chunk_ids": []},
            "checks": checks, "turn_checks": [checks, checks],
            "raw": {"turns": [{"result": result, "latency_s": 1}, {"result": second, "latency_s": 3}]}}


class Round3ReportTests(unittest.TestCase):
    def test_quantiles_are_linear_and_do_not_remove_outliers(self):
        self.assertEqual(percentile([1, 3], .5), 2)
        self.assertAlmostEqual(percentile([1, 3], .95), 2.9)
        self.assertIsNone(percentile([], .95))
        self.assertGreater(percentile([1, 2, 1000], .95), 900)

    def test_refusal_cases_are_final_actions_but_turn_count_includes_intake(self):
        metrics = summarise([fixture_item()])
        self.assertEqual(metrics["Final refuse_unverified cases"]["numerator"], 0)
        self.assertEqual(metrics["refuse_unverified turns"]["numerator"], 1)
        self.assertEqual(metrics["Cases with trace.pruned (any turn)"]["numerator"], 1)

    def test_served_models_are_not_inferred_from_config(self):
        perf = performance([fixture_item()])
        self.assertNotIn("CONFIGURED-BUT-UNSERVED", str(perf["served_role_models"]))
        self.assertEqual(perf["fallback_or_switch_turns"], 1)
        self.assertEqual(perf["multiple_served_models_for_same_role_turns"], 1)
        self.assertEqual(perf["mean_trace_calls"], 2.5)

    def test_unobserved_translation_role_is_reported_without_fabricating_a_model(self):
        perf = performance([fixture_item()])
        self.assertEqual(perf["translated_turns_without_served_translate_model"], 1)
        self.assertEqual(perf["translation_attempts_reported"], 1)
        self.assertFalse(any(row["role"] == "translate" for row in perf["served_role_models"]))


if __name__ == "__main__":
    unittest.main()
