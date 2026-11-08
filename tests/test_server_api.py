"""FastAPI transport/state/privacy tests. No network by default.

Run: python tests/test_server_api.py
Real pipeline opt-in: GEMINI_API_KEY must already be in the environment AND
--real must be passed. Having a key in .env alone does not enable real mode.
No app/data files are edited; caches, feedback and traces use tests/_scratch.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REAL = False


def source_fingerprints():
    paths = [ROOT / "config.yaml", *sorted((ROOT / "data/corpus").glob("*.jsonl"))]
    paths += [p for p in (ROOT / "app").rglob("*") if p.is_file() and "__pycache__" not in p.parts
              and p.suffix in {".py", ".md", ".json", ".txt"}]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def parse_sse(response):
    events, kind, parts = [], None, []
    for line in [*response.iter_lines(), ""]:
        if not line:
            if kind is not None:
                events.append((kind, json.loads("\n".join(parts))))
            kind, parts = None, []
        elif line.startswith("event:"):
            kind = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            parts.append(line.split(":", 1)[1].lstrip())
    return events


class ServerAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack = contextlib.ExitStack()
        cls.addClassCleanup(cls.stack.close)
        if REAL:
            if not os.environ.get("GEMINI_API_KEY"):
                raise RuntimeError("--real requires GEMINI_API_KEY in the process environment")
            if os.environ.get("AI_LAWYER_MOCK", "").lower() in {"1", "true", "yes"}:
                raise RuntimeError("--real cannot run with AI_LAWYER_MOCK enabled")
        else:
            cls.stack.enter_context(patch.dict(os.environ, {"AI_LAWYER_MOCK": "1"}))
            cls.network_guard = cls.stack.enter_context(patch("requests.sessions.Session.request",
                                          side_effect=AssertionError("Unexpected outbound network in mock API suite")))
        cls.server = importlib.import_module("app.server")
        from fastapi.testclient import TestClient
        cls.TestClient = TestClient
        if REAL and cls.server.is_mock():
            raise RuntimeError("--real is blocked by the app's mock config")

    @classmethod
    def tearDownClass(cls):
        if not REAL and cls.network_guard.call_count:
            raise AssertionError(f"Mock API suite attempted {cls.network_guard.call_count} outbound requests")

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        base = ROOT / "tests/_scratch"
        base.mkdir(exist_ok=True)
        self.temp = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="api-", dir=base))).resolve()
        self.assertTrue(self.temp.is_relative_to(base.resolve()))
        self.stack.enter_context(patch.dict(self.server._sessions, clear=True))
        self.stack.enter_context(patch.dict(self.server._hits, clear=True))
        self.stack.enter_context(patch.object(self.server, "FEEDBACK", self.temp / "feedback.jsonl"))
        self.stack.enter_context(patch.dict(self.server.retrieval._state, clear=True))
        self.stack.enter_context(patch.object(self.server.retrieval, "_cache_file", return_value=self.temp / "embeddings.json"))

        def trace_write(trace):
            with (self.temp / "trace.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(trace, ensure_ascii=False) + "\n")

        self.stack.enter_context(patch.object(self.server.pipeline, "_trace_write", side_effect=trace_write))
        if not REAL:
            # Hash embeddings have unrelated scores; exercise the answer stages
            # without changing the human's real-eval threshold or config file.
            self.stack.enter_context(patch.dict(self.server.load_config()["retrieval"], {"min_score": 0.0}))
        self.client = self.stack.enter_context(self.TestClient(self.server.app))

    def request(self, **overrides):
        body = {"text": "My landlord in Lucknow UP kept my Rs 20000 rental deposit after I vacated on 20 October 2026. I have the agreement.",
                "lang": "en-IN", "mode": "advice", "input_mode": "text"}
        return {**body, **overrides}

    def test_stream_stage_order_and_final_result(self):
        with self.client.stream("POST", "/api/turn/stream", json=self.request()) as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/event-stream", response.headers["content-type"])
            self.assertEqual(response.headers.get("x-accel-buffering"), "no")
            events = parse_sse(response)
        self.assertTrue(events)
        self.assertEqual(events[-1][0], "result")
        self.assertEqual(sum(k == "result" for k, _ in events), 1)
        self.assertFalse(any(k == "error" for k, _ in events), events)
        self.assertTrue(all(k == "stage" for k, _ in events[:-1]))
        stages = [d["stage"] for k, d in events if k == "stage"]
        self.assertEqual(stages[0], "understanding")
        self.assertLess(stages.index("understanding"), stages.index("searching"))
        self.assertLess(stages.index("searching"), stages.index("writing"))
        self.assertLess(stages.index("writing"), stages.index("checking"))
        for n, stage in enumerate(stages):
            if stage == "rewriting":
                self.assertIn("checking", stages[:n])
                self.assertIn("checking", stages[n + 1:])
        result = events[-1][1]
        self.assertTrue(result["result"]["reply_text"])
        self.assertTrue(result["session_id"])
        self.assertIn("case_file", result["state"])
        self.assertIn("history", result["state"])
        if not REAL:
            self.assertIs(result["result"]["trace"]["mock"], True)

    def test_stream_error_is_terminal_and_does_not_echo_exception_text(self):
        with patch.object(self.server.pipeline, "handle_turn", side_effect=RuntimeError("PRIVATE_EXCEPTION_PAYLOAD")):
            with self.client.stream("POST", "/api/turn/stream", json=self.request()) as response:
                events = parse_sse(response)
        self.assertEqual([kind for kind, _ in events], ["error"])
        self.assertNotIn("PRIVATE_EXCEPTION_PAYLOAD", json.dumps(events))
        self.assertIn("RuntimeError", events[0][1]["error"])

    def test_rate_limit_is_shared_by_turn_and_stream_and_blocks_work(self):
        fake = {"session_id": "api-rate-fixture", "result": {"reply_text": "Rate-limit fixture."}, "state": {}}
        with patch.dict(self.server.LIMITS, {"turn": (2, 600)}), patch.object(self.server, "_run_turn", return_value=fake) as work:
            self.assertEqual(self.client.post("/api/turn", json=self.request()).status_code, 200)
            self.assertEqual(self.client.post("/api/turn/stream", json=self.request()).status_code, 200)
            for endpoint in ("/api/turn", "/api/turn/stream"):
                response = self.client.post(endpoint, json=self.request())
                self.assertEqual(response.status_code, 429)
                self.assertIn("wait", response.json()["detail"].lower())
            self.assertEqual(work.call_count, 2)

    def test_feedback_omits_question_and_answer_by_default(self):
        body = {"message_id": "privacy-default", "rating": "down", "reason": "unclear",
                "question": "PRIVATE_QUESTION_MARKER", "answer": "PRIVATE_ANSWER_MARKER"}
        self.assertEqual(self.client.post("/api/feedback", json=body).status_code, 200)
        content = self.server.FEEDBACK.read_text(encoding="utf-8")
        record = json.loads(content)
        self.assertIs(record["shared"], False)
        self.assertNotIn("question", record)
        self.assertNotIn("answer", record)
        self.assertNotIn("PRIVATE_QUESTION_MARKER", content)
        self.assertNotIn("PRIVATE_ANSWER_MARKER", content)

    def test_feedback_explicit_false_also_omits_text(self):
        body = {"message_id": "privacy-false", "rating": "up", "share_text": False,
                "question": "PRIVATE_QUESTION_MARKER", "answer": "PRIVATE_ANSWER_MARKER"}
        self.assertEqual(self.client.post("/api/feedback", json=body).status_code, 200)
        record = json.loads(self.server.FEEDBACK.read_text(encoding="utf-8"))
        self.assertNotIn("question", record)
        self.assertNotIn("answer", record)

    def test_feedback_stores_conversation_only_with_explicit_consent(self):
        body = {"message_id": "privacy-shared", "rating": "up", "share_text": True,
                "question": "Invented shared question", "answer": "Invented shared answer"}
        self.assertEqual(self.client.post("/api/feedback", json=body).status_code, 200)
        record = json.loads(self.server.FEEDBACK.read_text(encoding="utf-8"))
        self.assertIs(record["shared"], True)
        self.assertEqual(record["question"], body["question"])
        self.assertEqual(record["answer"], body["answer"])

    def test_browser_state_restores_after_session_cache_is_cleared(self):
        first_text = self.request()["text"]
        first = self.client.post("/api/turn", json=self.request())
        self.assertEqual(first.status_code, 200)
        first = first.json()
        sid, state = first["session_id"], copy.deepcopy(first["state"])
        self.assertEqual(state["case_file"]["amount_inr"], 20000)
        previous_object = self.server._sessions[sid]
        self.server._sessions.clear()  # simulate restart/cache eviction exactly
        followup = "I also have the bank transfer receipt. Please draft a deposit demand notice."
        second = self.client.post("/api/turn", json={"text": followup, "session_id": sid,
                                                    "state": state, "mode": "draft"})
        self.assertEqual(second.status_code, 200)
        second = second.json()
        # Nov 2026: the server never adopts a session id it does not hold; it issues a new one and the
        # browser's saved state restores the conversation under it.
        self.assertNotEqual(second["session_id"], sid)
        self.assertIsNot(self.server._sessions[second["session_id"]], previous_object)
        self.assertEqual(second["state"]["case_file"]["amount_inr"], state["case_file"]["amount_inr"])
        self.assertEqual(second["state"]["case_file"]["state"], state["case_file"]["state"])
        self.assertEqual(second["state"]["lang"], state["lang"])
        users = [h["text"] for h in second["state"]["history"] if h["role"] == "user"]
        self.assertIn(first_text, users)
        self.assertEqual(users[-1], followup)

    def test_real_flag_without_environment_key_is_rejected_before_app_import(self):
        env = os.environ.copy()
        env.pop("GEMINI_API_KEY", None)
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--real"], env=env,
                              cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("requires GEMINI_API_KEY", proc.stderr)


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows = []

    def startTest(self, test):
        super().startTest(test)
        self.started = time.perf_counter()

    def record(self, test, status, details=""):
        self.rows.append({"test": test.id(), "status": status, "seconds": time.perf_counter() - self.started,
                          "details": details})

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, "pass")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, "fail", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, "error", self._exc_info_to_string(err, test))


def main():
    global REAL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", action="store_true")
    args = parser.parse_args()
    REAL = args.real
    if REAL and not os.environ.get("GEMINI_API_KEY"):
        parser.error("--real requires GEMINI_API_KEY already set in the process environment")
    started_at = datetime.now(timezone.utc).isoformat()
    inputs_before = source_fingerprints()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ServerAPITests)
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
    inputs_after = source_fingerprints()
    changed = sorted(k for k in inputs_before.keys() | inputs_after.keys() if inputs_before.get(k) != inputs_after.get(k))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    directory = ROOT / "outputs/runs" / f"api-{'real' if REAL else 'mock'}-{stamp}"
    directory.mkdir(parents=True, exist_ok=False)
    payload = {"mock": not REAL, "backend": "FastAPI TestClient", "tests_run": result.testsRun,
               "successful": result.wasSuccessful(), "results": result.rows,
               "started_at": started_at, "input_sha256": inputs_before,
               "source_inputs_stable": not changed, "source_inputs_changed_during_tests": changed,
               "scope": "SSE payload order, rate-limit gate, feedback question/answer consent, browser-state restoration; not network delivery timing"}
    (directory / "results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Server API test results", "", f"Mode: {'real opt-in' if REAL else 'mock/offline'}; {result.testsRun} tests; successful={result.wasSuccessful()}.",
             f"Source input hashes stable during tests: {not changed}. Run evidence: {directory}.",
             "TestClient checks ordered SSE content, not proxy buffering or time-to-first-event over a network.",
             "Feedback privacy assertions cover question/answer text; user-entered feedback reasons remain metadata.", ""]
    lines += [f"- {r['test']}: {r['status']} ({r['seconds']:.3f} s)" for r in result.rows]
    text = "\n".join(lines) + "\n"
    (directory / "summary.md").write_text(text, encoding="utf-8")
    (ROOT / "outputs/server_api.md").write_text(text, encoding="utf-8")
    print(f"API test evidence: {directory}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
