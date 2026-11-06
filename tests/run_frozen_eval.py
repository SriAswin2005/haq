"""Run the real eval from a frozen app/config/corpus copy during parallel edits.

Credentials stay in process environment, never in the snapshot. The snapshot is
inside ignored tests/_scratch. Captured raw files are copied byte-for-byte to
the canonical outputs archive, then derived reports are regenerated there.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.run_eval import digest, load_cases, latest_record, raw_dir, utc_now, write_json
from tests.reporting import write_reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sleep", type=float, default=6)
    parser.add_argument("--only", action="append", help="Select groups/tags, e.g. --only round4; archives the cohort without replacing the full-run publication")
    args = parser.parse_args()
    groups = [g.strip() for value in args.only or [] for g in value.split(",") if g.strip()]
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", encoding="utf-8-sig")
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY must be available through environment/.env")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    snapshot = ROOT / "tests/_scratch" / f"frozen-eval-{stamp}"
    if not snapshot.resolve().is_relative_to((ROOT / "tests/_scratch").resolve()):
        raise ValueError("Snapshot must stay within tests/_scratch")
    sources = [ROOT / "config.yaml", ROOT / "docs/claude_code_report.md", ROOT / "data/validate_corpus.py"]
    sources += [p for p in (ROOT / "app").rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    sources += list((ROOT / "data/corpus").glob("*.jsonl"))
    sources += [ROOT / "tests" / name for name in ("__init__.py", "run_eval.py", "checks.py", "reporting.py", "cases.jsonl", "mock_pipeline.py")]
    sources += list((ROOT / "tests/prompts").glob("*.md"))
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    snapshot.mkdir(parents=True, exist_ok=False)
    for source in sources:
        if not source.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError("Snapshot source escapes workspace")
        dest = snapshot / source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    if any(digest(ROOT / rel) != h or digest(snapshot / rel) != h for rel, h in source_hashes.items()):
        raise ValueError("Inputs changed during snapshot creation; start a new frozen run")
    # Reuse public corpus embeddings/model metadata and current local budgets.
    # The isolated app manages its own cache thereafter; it cannot reload source
    # files which another agent changes in the canonical checkout.
    for source in (ROOT / "data/index").glob("*.json"):
        dest = snapshot / "data/index" / source.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    origin = {"frozen_at": utc_now(), "canonical_root": str(ROOT), "snapshot_root": str(snapshot),
              "input_sha256": source_hashes, "credentials_copied": False, "harness_judge": False, "sleep_s": args.sleep,
              "selected_groups": groups}
    write_json(snapshot / "frozen_inputs.json", origin, exclusive=True)
    print(f"Frozen application: {snapshot}", flush=True)
    selected_cases = load_cases(snapshot / "tests/cases.jsonl", groups)
    command = [sys.executable, "-u", "tests/run_eval.py", "--sleep", str(args.sleep)]
    for value in args.only or []:
        command += ["--only", value]
    result = subprocess.run(command, cwd=snapshot)
    runs = sorted((snapshot / "outputs/runs").glob("real-*"))
    if len(runs) != 1 or not (runs[0] / "completion.json").is_file():
        print("No completed attempt to collect; inspect the frozen workspace.", flush=True)
        return 2
    source_run = runs[0]
    target = ROOT / "outputs/runs" / source_run.name
    if target.exists():
        raise ValueError("Canonical run archive already exists")
    shutil.copytree(source_run, target)
    write_json(target / "frozen_inputs.json", origin, exclusive=True)
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    corpus = json.loads((target / "corpus_snapshot.json").read_text(encoding="utf-8"))
    records = []
    for repeat in range(1, manifest["runs"] + 1):
        for case in selected_cases:
            raw, path = latest_record(raw_dir(target, repeat, manifest["runs"]), case["id"])
            records.append({"case": case, "repeat": repeat, "raw": raw, "path": path})
    summary = write_reports(target, manifest, records, corpus)
    raw_files = list((source_run / "raw").rglob("*.json"))
    exact = all(digest(path) == digest(target / path.relative_to(source_run)) for path in raw_files)
    if not exact:
        raise ValueError("Collected raw bytes do not match frozen capture")
    write_json(target / "collection.json", {"collected_at": utc_now(), "raw_copied_byte_for_byte": exact,
               "source_run": str(source_run), "raw_files": len(raw_files), "additional_api_calls_for_collection": 0})
    if not groups and not summary["infra_errors"] and not summary["pending"]:
        raw_target = ROOT / "outputs/raw"
        raw_target.mkdir(exist_ok=True)
        for case in selected_cases:
            _, raw_path = latest_record(target / "raw", case["id"])
            shutil.copyfile(raw_path, raw_target / f"{case['id']}.json")
        for name in ("summary.md", "results.csv", "calibration.md"):
            shutil.copyfile(target / name, ROOT / "outputs" / name)
    print(f"Canonical real run: {target}; raw byte identity: {exact}", flush=True)
    if summary["infra_errors"] or summary["pending"]:
        print(f"Resume from frozen workspace {snapshot} using tests/run_eval.py --sleep {args.sleep} --resume outputs/runs/{source_run.name} --retry-infra", flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
