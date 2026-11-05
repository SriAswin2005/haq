"""Sequential, resumable evaluation through the frozen public pipeline only.

Examples (run from the repository root):
  python tests/run_eval.py --mock --sleep 0
  python tests/run_eval.py --mock --sleep 0 --runs 2 --only D
  python tests/run_eval.py --sleep 4 --judge
  python tests/run_eval.py --resume outputs/runs/real-... --retry-infra

Non-mock execution is gated on a populated docs/claude_code_report.md.
Gradeable publication additionally requires a validated real corpus. All raw
case files are immutable: retries create separate attempt files.
"""
from __future__ import annotations

import argparse
import dataclasses
from datetime import datetime, timezone
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.checks import CHECKS, load_corpus


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def json_value(value):
    """Lossless JSON conversion of contract dataclasses; no reply/trace editing."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return json_value(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(v) for v in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError(f"TurnResult is not JSON serializable: {type(value).__name__}")


def write_json(path, data, *, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def read_config():
    path = ROOT / "config.yaml"
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError as exc:
        raise ValueError("config.yaml exists; install the app dependencies (PyYAML is needed to audit it).") from exc
    config = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict):
        raise ValueError("config.yaml must contain a mapping")
    return config


def load_cases(path, groups=None):
    cases, ids = [], set()
    required = {"id", "group", "category_expected", "language", "input_mode", "turns",
                "expected_action", "expect_needs_lawyer", "expected_topics", "must_include_any",
                "must_not_include", "expected_chunk_ids", "notes", "expected_law_verified"}
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        case = json.loads(line)
        if not isinstance(case, dict) or required - case.keys():
            raise ValueError(f"{path}:{n}: missing case fields")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", case["id"]) or case["id"] in ids:
            raise ValueError(f"{path}:{n}: unsafe or duplicate case id")
        if not isinstance(case["turns"], list) or not case["turns"] or any(not isinstance(t, str) or not t.strip() for t in case["turns"]):
            raise ValueError(f"{case['id']}: turns must be nonempty strings")
        if case["input_mode"] not in {"text", "voice"}:
            raise ValueError(f"{case['id']}: invalid input_mode")
        if any(not isinstance(a, list) or not a or any(not isinstance(p, str) or not p for p in a) for a in case["must_include_any"]):
            raise ValueError(f"{case['id']}: invalid concept alternatives")
        ids.add(case["id"])
        labels = [case["group"], case["group"].split("_")[0], *case.get("tags", [])]
        if not groups or any(g == label or label.startswith(g + "_") for g in groups for label in labels):
            cases.append(case)
    if not cases:
        raise ValueError("No cases selected")
    return cases


def protect_real_gate(config, sample):
    report = ROOT / "docs/claude_code_report.md"
    if not report.is_file() or not report.read_text(encoding="utf-8-sig").strip():
        raise ValueError("Real evaluation blocked: docs/claude_code_report.md must exist and be populated. No app/model was called.")
    if not (ROOT / "app/pipeline.py").is_file():
        raise ValueError("Real evaluation blocked: app/pipeline.py does not exist.")
    if str(os.getenv("AI_LAWYER_MOCK", "")).lower() not in {"", "0", "false", "no"} or config.get("mock"):
        raise ValueError("Real evaluation blocked: mock mode is enabled in environment/config. Use --mock or disable it explicitly.")
    configured = Path(config.get("corpus", {}).get("path", "data/corpus"))
    path = configured if configured.is_absolute() else ROOT / configured
    if not sample and path.resolve() != (ROOT / "data/corpus").resolve():
        raise ValueError("Gradeable real evaluation requires config corpus.path=data/corpus. Use --sample for a sample shakeout.")
    return path


def validate_real_corpus(run_dir, corpus_path, corpus):
    if not corpus or any(cid.startswith("SAMPLE-") or "[SAMPLE" in c.get("text", "") for cid, c in corpus.items()):
        raise ValueError("Real corpus is empty or contains sample chunks; no API calls made.")
    validator = ROOT / "data/validate_corpus.py"
    if not validator.is_file():
        raise ValueError("Real evaluation requires data/validate_corpus.py; no API calls made.")
    validation = subprocess.run([sys.executable, str(validator)], cwd=ROOT, text=True,
                                capture_output=True, encoding="utf-8", errors="replace", timeout=120)
    (run_dir / "corpus_validation.txt").write_text(
        f"command: python data/validate_corpus.py\nexit_code: {validation.returncode}\n"
        + validation.stdout + "\n" + validation.stderr, encoding="utf-8")
    if validation.returncode:
        raise ValueError(f"Corpus validator failed; see {run_dir / 'corpus_validation.txt'}. No model was called.")


def select_backend(mock):
    if mock:
        os.environ["AI_LAWYER_MOCK"] = "1"  # before importing any app modules
    if (ROOT / "app/pipeline.py").is_file():
        return importlib.import_module("app.pipeline"), "app.pipeline"
    if mock:
        return importlib.import_module("tests.mock_pipeline"), "tests.mock_pipeline (fixture only; APP ABSENT)"
    raise ValueError("Application absent; no real evaluation possible")


def safe_error(exc):
    # Exception strings sometimes contain credential-bearing URLs. Preserve the
    # type/status and scrub env secrets from diagnostic text, never TurnResult.
    message = str(exc)
    for key, value in os.environ.items():
        if re.search(r"KEY|TOKEN|SECRET|PASSWORD", key, re.I) and len(value) >= 6:
            message = message.replace(value, "[REDACTED]")
    message = re.sub(r"(?i)([?&](?:key|api_key|token)=)[^&\s]+", r"\1[REDACTED]", message)
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    return {"type": type(exc).__name__, "message": message, "status_code": status}


def returned_infra_error(result):
    """Recognise API errors caught by the app without changing its raw result.

    Invalid model JSON is a model failure, not an infrastructure excuse. Missing
    credentials, HTTP failures and quota/transport errors are infrastructure.
    """
    if not isinstance(result, dict):
        return None
    trace = result.get("trace", {})
    if not isinstance(trace, dict):
        return None
    messages = [trace.get("fatal_error"), trace.get("judge")]
    info = trace.get("router_info", {})
    if isinstance(info, dict):
        messages.append(info.get("error"))
    messages += result.get("verifier", {}).get("issues", []) if isinstance(result.get("verifier"), dict) else []
    for message in messages:
        if isinstance(message, str) and re.search(r"missing environment variable|missing (?:api )?key|HTTP\s*[45]\d\d|"
                                                r"quota|rate.?limit|timed?\s*out|timeout|connection(?:error| refused)|"
                                                r"request failed|network error|proxyerror|sslerror|local daily budget|"
                                                r"busy for ~|unauthori[sz]ed|unavailable.*(?:API|provider)", message, re.I):
            error = safe_error(RuntimeError(message))
            error.update(type="AppHandledAPIError", source="TurnResult.trace/verifier")
            return error
    return None


def run_judge(result, user_turns, corpus):
    llm = importlib.import_module("app.llm")
    prompt = (ROOT / "tests/prompts/faithfulness.md").read_text(encoding="utf-8")
    payload = {"user_messages": user_turns, "reply_text": result["reply_text"], "draft_text": result["draft_text"],
               "cited_sources": [corpus[c] for c in result["citations"] if c in corpus]}
    response = llm.generate([{"role": "system", "content": prompt},
                             {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
                            role="judge", json_schema={"type": "object"}, temperature=0)
    original = json_value(response)
    parsed = response if isinstance(response, dict) else json.loads(response)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("claims"), list) or type(parsed.get("all_supported")) is not bool:
        raise ValueError("Judge did not return the expected claims/all_supported JSON shape")
    if any(not isinstance(c, dict) or type(c.get("supported")) is not bool or not isinstance(c.get("text"), str) for c in parsed["claims"]):
        raise ValueError("Malformed judge claim")
    if parsed["all_supported"] != all(c["supported"] for c in parsed["claims"]):
        raise ValueError("Inconsistent judge all_supported flag")
    return {"raw_response": original, "assessment": parsed}


def evaluate_case(pipeline, case, repeat, context, corpus, sleep_s, judge, turn_clock):
    raw = {"schema_version": 1, "case_id": case["id"], "case": case, "repeat": repeat,
           "mock": context["mock"], "backend": context["backend"], "stage": context["stage"],
           "configured_models": context["models"], "started_at": utc_now(), "turns": [], "error": None}
    try:
        session = pipeline.new_session(lang_hint=case["language"])
        session.mode = case.get("mode", "advice")
        for idx, user_text in enumerate(case["turns"]):
            remaining = sleep_s - (time.monotonic() - turn_clock[0])
            if remaining > 0:
                time.sleep(remaining)
            entry = {"input": user_text, "input_mode": case["input_mode"], "lang_hint": case["language"], "started_at": utc_now()}
            raw["turns"].append(entry)
            start = time.perf_counter()
            try:
                result = pipeline.handle_turn(session, user_text, input_mode=case["input_mode"], lang_hint=case["language"])
                entry["result"] = json_value(result)
                # Explicitly retain model names from the full unmodified trace.
                trace = entry["result"].get("trace", {})
                if isinstance(trace, dict):
                    stats = trace.get("llm", {})
                    entry["model_names_used"] = stats.get("models") if isinstance(stats, dict) and stats.get("models") else trace.get("model_names", trace.get("models"))
                else:
                    entry["model_names_used"] = None
                handled_error = returned_infra_error(entry["result"])
                if handled_error:
                    entry["error"] = raw["error"] = handled_error
                    break
                if judge:
                    entry["judge"] = run_judge(entry["result"], case["turns"][:idx + 1], corpus)
            except Exception as exc:
                entry["error"] = safe_error(exc)
                raise
            finally:
                entry["latency_s"] = time.perf_counter() - start
                entry["finished_at"] = utc_now()
                turn_clock[0] = time.monotonic()
    except Exception as exc:
        raw["error"] = safe_error(exc)
    raw["finished_at"] = utc_now()
    return raw


def raw_dir(run_dir, repeat, runs):
    return run_dir / "raw" if runs == 1 else run_dir / f"repeat-{repeat:03d}" / "raw"


def latest_record(directory, case_id):
    primary = directory / f"{case_id}.json"
    paths = ([primary] if primary.exists() else []) + sorted((directory / "attempts").glob(f"{case_id}.attempt-*.json"))
    if not paths:
        return None, None
    path = paths[-1]
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw, path


def next_raw_path(directory, case_id):
    path = directory / f"{case_id}.json"
    if path.exists():
        for attempt in range(2, 10000):
            path = directory / "attempts" / f"{case_id}.attempt-{attempt:04d}.json"
            if not path.exists():
                break
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cases", type=Path, default=ROOT / "tests/cases.jsonl")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--sample", action="store_true", help="Non-graded real-model shakeout on configured sample data")
    parser.add_argument("--only", action="append", help="Group/prefix/tag; repeat or comma-separate, e.g. D,F,G")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--sleep", type=float, default=4, help="Gap after each completed turn, default 4 seconds")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--retry-infra", action="store_true", help="On resume, append a new attempt for saved infrastructure errors")
    parser.add_argument("--judge", action="store_true", help="Optional independent app.llm judge role; real app only")
    parser.add_argument("--keep-going-on-infra", action="store_true")
    args = parser.parse_args(argv)
    if args.runs < 1 or not math.isfinite(args.sleep) or args.sleep < 0:
        parser.error("--runs must be positive and --sleep finite/nonnegative")
    if args.mock and args.sample:
        parser.error("--mock and --sample are separate stages")
    if args.mock and args.judge:
        parser.error("--judge is a real-model assessment and is disabled in mock mode")
    config = read_config()
    groups = [g.strip() for value in args.only or [] for g in value.split(",") if g.strip()]
    cases = load_cases(args.cases.resolve(), groups)
    corpus_path = ROOT / config.get("corpus", {}).get("path", "data/corpus")
    if not args.mock:
        corpus_path = protect_real_gate(config, args.sample)
    corpus = load_corpus(corpus_path)
    for case in cases:
        if case.get("amount_inr") is not None and case["amount_inr"] <= config.get("escalation", {}).get("high_amount_inr", 500000):
            raise ValueError(f"{case['id']}: fixture amount is not above configured escalation threshold; review expectation before running")
    backend_name = "app.pipeline" if (ROOT / "app/pipeline.py").is_file() else "tests.mock_pipeline (fixture only; APP ABSENT)"
    stage = "fixture_mock" if args.mock and backend_name != "app.pipeline" else "app_mock" if args.mock else "sample" if args.sample else "real"
    fingerprints = {"cases": digest(args.cases), "checks": digest(ROOT / "tests/checks.py"),
                    "runner": digest(Path(__file__)), "reporting": digest(ROOT / "tests/reporting.py"),
                    "config": digest(ROOT / "config.yaml"),
                    "corpus": hashlib.sha256(json.dumps(corpus, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                    "app": {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT / "app").rglob("*.py"))},
                    "app_resources": {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT / "app").rglob("*")) if p.is_file() and p.suffix in {".md", ".json", ".txt"}},
                    "judge_prompt": digest(ROOT / "tests/prompts/faithfulness.md"),
                    "fixture": digest(ROOT / "tests/mock_pipeline.py") if stage == "fixture_mock" else None}
    identity = {"mock": args.mock, "stage": stage, "backend": backend_name, "runs": args.runs,
                "case_ids": [c["id"] for c in cases], "fingerprints": fingerprints, "judge": args.judge}
    runs_root = ROOT / "outputs/runs"
    if args.resume:
        run_dir = args.resume.resolve()
        if not run_dir.is_relative_to(runs_root.resolve()):
            raise ValueError("--resume must point inside outputs/runs")
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        if any(manifest.get(k) != v for k, v in identity.items()):
            raise ValueError("Resume inputs/mode/code differ from saved manifest. Use original flags or start a new run to preserve comparability.")
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        run_dir = runs_root / f"{'mock' if args.mock else stage}-{stamp}"
        run_dir.mkdir(parents=True, exist_ok=False)
        manifest = {**identity, "started_at": utc_now(), "sleep_s": args.sleep,
                    "models": config.get("models", {}), "corpus_path": str(corpus_path),
                    "retrieval_min_score": config.get("retrieval", {}).get("min_score"),
                    "law_expectations_human_verified": sum(c["expected_law_verified"] is True for c in cases)}
        write_json(run_dir / "manifest.json", manifest, exclusive=True)
        write_json(run_dir / "corpus_snapshot.json", corpus, exclusive=True)
    if stage == "real":
        validate_real_corpus(run_dir, corpus_path, corpus)
    pipeline, actual_backend = select_backend(args.mock)
    if actual_backend != backend_name:
        raise ValueError("App availability changed during setup; rerun for a consistent backend")
    if not args.mock and str(os.getenv("AI_LAWYER_MOCK", "")).lower() not in {"", "0", "false", "no"}:
        raise ValueError("Real evaluation blocked: app import/.env enabled AI_LAWYER_MOCK. No turn was called.")
    print(f"Run: {run_dir}\nStage: {stage}; backend: {actual_backend}", flush=True)
    turn_clock = [float("-inf")]
    stopped = False
    for repeat in range(1, args.runs + 1):
        for case in cases:
            directory = raw_dir(run_dir, repeat, args.runs)
            previous, _ = latest_record(directory, case["id"])
            if previous is not None and not (args.retry_infra and previous.get("error")):
                continue
            raw = evaluate_case(pipeline, case, repeat, manifest, corpus, args.sleep, args.judge, turn_clock)
            filename = next_raw_path(directory, case["id"])
            write_json(filename, raw, exclusive=True)
            print(f"{repeat}/{args.runs} {case['id']}: {'infra_error' if raw['error'] else 'saved'}", flush=True)
            if raw["error"] and not args.keep_going_on_infra:
                stopped = True
                break
        if stopped:
            break
    records = []
    for repeat in range(1, args.runs + 1):
        for case in cases:
            raw, path = latest_record(raw_dir(run_dir, repeat, args.runs), case["id"])
            records.append({"case": case, "repeat": repeat, "raw": raw, "path": path})
    from tests.reporting import write_reports
    report = write_reports(run_dir, manifest, records, corpus)
    write_json(run_dir / "completion.json", {"finished_at": utc_now(), **report})
    # A complete, unfiltered real run alone may update graded deliverables.
    all_cases = load_cases(args.cases.resolve())
    publish = stage == "real" and not groups and len(cases) == len(all_cases) and not report["infra_errors"] and not report["pending"]
    if publish:
        final_directory = raw_dir(run_dir, args.runs, args.runs)
        target = ROOT / "outputs/raw"
        target.mkdir(parents=True, exist_ok=True)
        for case in cases:
            _, source = latest_record(final_directory, case["id"])
            shutil.copyfile(source, target / f"{case['id']}.json")
        for name in ("results.csv", "summary.md", "calibration.md"):
            shutil.copyfile(run_dir / name, ROOT / "outputs" / name)
    print(f"Cases: {report['passed']} passed, {report['failed']} failed, {report['infra_errors']} infra_error, {report['pending']} pending.\nSummary: {run_dir / 'summary.md'}", flush=True)
    return 2 if report["infra_errors"] or report["pending"] else 1 if report["failed"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, ImportError, subprocess.TimeoutExpired) as error:
        print(f"Evaluation setup error: {safe_error(error)['message']}", file=sys.stderr)
        raise SystemExit(2)
