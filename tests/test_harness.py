"""Offline orchestration tests: gating, immutable resume, quota recovery, metrics."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests import mock_pipeline, reporting, run_eval


@contextlib.contextmanager
def scratch_directory(prefix):
    base = Path(__file__).resolve().parent / "_scratch"
    base.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=prefix, dir=base) as temp:
        resolved = Path(temp).resolve()
        if not resolved.is_relative_to(base.resolve()):
            raise ValueError("Scratch cleanup target must stay inside tests/_scratch")
        yield resolved


class HarnessTests(unittest.TestCase):
    def test_priority_inventory(self):
        cases = run_eval.load_cases(run_eval.ROOT / "tests/cases.jsonl")
        self.assertEqual(len(cases), 30)
        self.assertEqual(sum(c["input_mode"] == "voice" for c in cases), 5)
        self.assertEqual(sum(c["group"].startswith("D_") for c in cases), 7)
        self.assertEqual(sum(c["group"].startswith("F_") for c in cases), 3)
        self.assertEqual(sum(c["group"].startswith("G_") for c in cases), 5)
        self.assertTrue(all(c["expected_law_verified"] is False for c in cases))
        self.assertTrue(all(isinstance(c["expected_chunk_ids"], list) and c["expected_chunk_ids"] for c in cases))

    def test_mapped_ids_exist_and_are_eligible_for_case_scope(self):
        corpus = run_eval.load_corpus(run_eval.ROOT / "data/corpus")
        cases = run_eval.load_cases(run_eval.ROOT / "tests/cases.jsonl")
        for case in cases:
            for cid in case["expected_chunk_ids"]:
                with self.subTest(case_id=case["id"], chunk_id=cid):
                    self.assertIn(cid, corpus)
                    self.assertEqual(corpus[cid]["status"], "in_force")
                    self.assertIn(corpus[cid]["jurisdiction"], case["jurisdictions_expected"])
                    self.assertIn(corpus[cid]["category"], {case["category_expected"], "common"})

    def test_gate_blocks_before_app_import_when_report_missing(self):
        with scratch_directory("gate-") as temp:
            with patch.object(run_eval, "ROOT", Path(temp)), patch.object(run_eval.importlib, "import_module") as importer:
                with self.assertRaisesRegex(ValueError, "claude_code_report"):
                    run_eval.protect_real_gate({}, False)
                importer.assert_not_called()

    def test_caught_api_errors_are_infra_but_invalid_model_json_is_not(self):
        for message in ("HTTP 429", "request failed after 3 tries (HTTP 503)", "missing environment variable GEMINI_API_KEY",
                        "all models failed for role 'router': network error (ProxyError)", "local daily budget of 495 used"):
            result = {"trace": {"router_info": {"error": message}}, "verifier": {"issues": []}}
            self.assertEqual(run_eval.returned_infra_error(result)["type"], "AppHandledAPIError")
        result = {"trace": {"router_info": {"error": "invalid router JSON"}}, "verifier": {"issues": []}}
        self.assertIsNone(run_eval.returned_infra_error(result))

    def test_nested_call_counts(self):
        self.assertEqual(reporting.call_count({"trace": {"llm": {"calls": 3}}}), 3)
        self.assertIsNone(reporting.call_count({"trace": {}}))

    def test_empty_metrics_are_not_fabricated_hundred_percent(self):
        metrics = dict(reporting.metrics([]))
        self.assertIn("unavailable", metrics["Citation validity (cited IDs in retrieved set)"])
        self.assertIn("unavailable", metrics["Unsupported-claim rate (semantic, independent judge)"])

    def test_mock_metrics_never_calibrate_real_gate(self):
        text = reporting.calibration_text([], {"stage": "app_mock"})
        self.assertIn("Not performed", text)
        self.assertNotIn("Provisional recommendation:", text)

    def test_calibration_uses_scores_not_actions(self):
        def item(label, scores):
            return [{"status": "pass", "case": {"id": f"{label}-{n}", "calibration_label": label},
                     "raw": {"turns": [{"result": {"retrieved": [{"id": "FAKE", "score": score}]}}]}}
                    for n, score in enumerate(scores)]
        text = reporting.calibration_text(item("answer", [.7, .8, .9]) + item("refuse", [.1, .2, .4]), {"stage": "real"})
        self.assertIn("Provisional recommendation:", text)
        self.assertIn("0.0% | 0.0%", text)

    def test_calibration_shows_distinct_tradeoffs_when_scores_overlap(self):
        items = [{"status": "pass", "case": {"id": f"{label}-{n}", "calibration_label": label},
                  "raw": {"turns": [{"result": {"retrieved": [{"score": score}]}}]}}
                 for label, scores in (("answer", [.68, .69, .70, .71, .72, .75, .82]),
                                        ("refuse", [.65, .713, .719])) for n, score in enumerate(scores)]
        text = reporting.calibration_text(items, {"stage": "real"})
        table = text.split("| Candidate min_score |")[1].split("Provisional recommendation:")[0]
        rows = [row for row in table.splitlines() if row.startswith("| 0.")]
        self.assertIn(len(rows), (2, 3))
        self.assertTrue(any("| 0.0% |" in row for row in rows))
        self.assertGreater(len({row.split("|")[2].strip() for row in rows}), 1)

    def test_resume_preserves_raw_bytes_and_checks_inputs(self):
        original_cases = run_eval.ROOT / "tests/cases.jsonl"
        with scratch_directory("resume-") as temp:
            root = Path(temp)
            args = ["--cases", str(original_cases), "--mock", "--sleep", "0", "--only", "F", "--runs", "2"]
            with patch.object(run_eval, "ROOT", root), contextlib.redirect_stdout(io.StringIO()):
                run_eval.main(args)
                directory = next((root / "outputs/runs").iterdir())
                paths = list(directory.glob("repeat-*/raw/*.json"))
                before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
                self.assertEqual(len(before), 6)
                run_eval.main(args + ["--resume", str(directory)])
                self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
                with self.assertRaisesRegex(ValueError, "Resume inputs"):
                    run_eval.main(args[:-2] + ["--resume", str(directory)])
                self.assertFalse((root / "outputs/raw").exists())

    def test_quota_error_stops_and_retry_appends_attempt(self):
        original_cases = run_eval.ROOT / "tests/cases.jsonl"
        with scratch_directory("quota-") as temp:
            root = Path(temp)
            args = ["--cases", str(original_cases), "--mock", "--sleep", "0", "--only", "F"]
            with patch.object(run_eval, "ROOT", root), contextlib.redirect_stdout(io.StringIO()):
                with patch.object(mock_pipeline, "handle_turn", side_effect=RuntimeError("HTTP 429 quota")):
                    self.assertEqual(run_eval.main(args), 2)
                directory = next((root / "outputs/runs").iterdir())
                original = directory / "raw/T-008.json"
                before = original.read_bytes()
                raw = json.loads(before)
                self.assertIn("429", raw["error"]["message"])
                run_eval.main(args + ["--resume", str(directory), "--retry-infra"])
                self.assertEqual(original.read_bytes(), before)
                self.assertEqual(len(list((directory / "raw/attempts").glob("T-008.*.json"))), 1)
                completion = json.loads((directory / "completion.json").read_text())
                self.assertEqual(completion["infra_errors"], 0)
                self.assertEqual(completion["pending"], 0)


if __name__ == "__main__":
    unittest.main()
