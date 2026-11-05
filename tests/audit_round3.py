"""Audit capture identity, baseline preservation and secrets without API calls."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.run_eval import digest, latest_record, utc_now, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to((ROOT / "outputs/runs").resolve()):
        raise ValueError("Select a canonical run archive")
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    done = json.loads((run / "completion.json").read_text(encoding="utf-8"))
    if manifest["mock"] or manifest["judge"] or len(manifest["case_ids"]) != 40 or done["pending"] or done["infra_errors"]:
        raise ValueError("Select a complete 40-case real run without --judge")
    frozen = json.loads((run / "frozen_inputs.json").read_text(encoding="utf-8"))
    snapshot = Path(frozen["snapshot_root"]).resolve()
    if not snapshot.is_relative_to((ROOT / "tests/_scratch").resolve()):
        raise ValueError("Unexpected snapshot location")
    source_run = snapshot / "outputs/runs" / run.name
    raw_hashes, turns, retrieval = {}, 0, {}
    for cid in manifest["case_ids"]:
        raw, path = latest_record(run / "raw", cid)
        if raw is None or raw.get("error") or raw["case"]["expected_law_verified"] is not False:
            raise ValueError("Missing/error/human-verified raw case: " + cid)
        raw_hashes[path.name] = digest(path)
        if digest(path) != digest(source_run / "raw" / path.name) or digest(path) != digest(ROOT / "outputs/raw" / (cid + ".json")):
            raise ValueError("Raw capture/collection/publication mismatch: " + cid)
        turns += len(raw["turns"])
        kind = raw["case"]["retrieval_expectation_kind"]
        hit = bool(set(raw["case"]["expected_chunk_ids"]) & {r["id"] for r in raw["turns"][-1]["result"].get("retrieved", [])})
        row = retrieval.setdefault(kind, {"hits": 0, "eligible": 0})
        row["hits"] += hit
        row["eligible"] += 1
    if any(digest(snapshot / rel) != h for rel, h in frozen["input_sha256"].items()):
        raise ValueError("Frozen source inputs changed")
    protected = json.loads((ROOT / "tests/round3_before_manifest.json").read_text(encoding="utf-8"))
    before = ROOT / protected["before_run"]
    if any(digest(before / "raw" / name) != h for name, h in protected["raw_sha256"].items()):
        raise ValueError("Before archive raw bytes changed")
    cases = [json.loads(line) for line in (snapshot / "tests/cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(cases) != 40 or any(c["expected_law_verified"] is not False for c in cases):
        raise ValueError("Case inventory/law-verification flag mismatch")
    for name in ("summary.md", "results.csv", "calibration.md", "BEFORE_AFTER.md", "perf.md"):
        if digest(run / name) != digest(ROOT / "outputs" / name):
            raise ValueError("Published report differs from canonical archive: " + name)
    if digest(run / "BUGS.md") != digest(ROOT / "tests/BUGS.md"):
        raise ValueError("BUGS.md differs from canonical archive")
    from dotenv import dotenv_values
    values = dotenv_values(ROOT / ".env", encoding="utf-8-sig")
    secrets = [v.encode() for k, v in values.items() if v and len(v) >= 8 and any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD"))]
    artifacts = [p for p in run.rglob("*") if p.is_file()]
    artifacts += list((ROOT / "outputs/raw").glob("*.json"))
    artifacts += [ROOT / "tests/BUGS.md", ROOT / "docs/codex_report.md"]
    matches = sum(any(secret in p.read_bytes() for secret in secrets) for p in artifacts)
    if matches or (snapshot / ".env").exists():
        raise ValueError("Credential exposure detected; values withheld")
    corpus = json.loads((run / "corpus_snapshot.json").read_text(encoding="utf-8"))
    write_json(run / "audit.json", {
        "audited_at": utc_now(), "raw_case_files": len(raw_hashes), "turns": turns, "raw_sha256": raw_hashes,
        "graded_raw_byte_identity": True, "frozen_capture_byte_identity": True, "frozen_inputs_unchanged": True,
        "before_raw_hashes_preserved": True, "all_expected_law_verified_false": True,
        "voice_transcript_cases": sum(c["input_mode"] == "voice" for c in cases),
        "retrieval_hit_breakdown": retrieval, "corpus_chunks": len(corpus),
        "corpus_human_check_required": sum(c.get("human_check_required") is True for c in corpus.values()),
        "corpus_source_types": dict(Counter(c.get("source_type") for c in corpus.values())),
        "credential_value_matches": matches, "credential_values_checked": len(secrets),
        "independent_judge_enabled": False, "additional_api_calls": 0,
        "derived_report_code_sha256": {name: digest(ROOT / "tests" / name) for name in
            ("checks.py", "reporting.py", "round3_reports.py", "round3_bugs.py", "add_real_review.py", "audit_round3.py")}
    })
    print(f"Audit passed: {len(raw_hashes)} immutable real cases, {turns} turns; before archive preserved; no credential matches.")


if __name__ == "__main__":
    main()
