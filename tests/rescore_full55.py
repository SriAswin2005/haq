"""Offline alias-only rescore of the complete real capture; no model calls."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.checks import check_referral
from tests.reporting import analyse, write_reports
from tests.run_eval import digest, latest_record, utc_now, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to((ROOT / "outputs/runs").resolve()):
        raise ValueError("Select a canonical archive")
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    done = json.loads((run / "completion.json").read_text(encoding="utf-8"))
    if manifest["mock"] or manifest["stage"] != "real" or done["pending"] or done["infra_errors"] or manifest["case_ids"] != [f"T-{n:03d}" for n in range(1,56)]:
        raise ValueError("Use a complete 55-case real run")
    frozen = json.loads((run / "frozen_inputs.json").read_text(encoding="utf-8"))
    snapshot = Path(frozen["snapshot_root"]).resolve()
    if not snapshot.is_relative_to((ROOT / "tests/_scratch").resolve()) or digest(snapshot / "tests/checks.py") != manifest["fingerprints"]["checks"]:
        raise ValueError("Frozen original checker changed")
    original = run / "scoring-original"
    if not original.exists():
        original.mkdir()
        for name in ["results.csv", "summary.md", "calibration.md", "BUGS.md", "completion.json"]:
            shutil.copyfile(run / name, original / name)
        shutil.copyfile(snapshot / "tests/checks.py", original / "checks.py")
    spec = importlib.util.spec_from_file_location("full55_original_checks", original / "checks.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    rows = {r["case_id"]:r for r in csv.DictReader((original / "results.csv").open(encoding="utf-8"))}
    corpus = json.loads((run / "corpus_snapshot.json").read_text(encoding="utf-8"))
    records, raw_hashes, deltas = [], {}, []
    for cid in manifest["case_ids"]:
        raw, path = latest_record(run / "raw", cid)
        rel = path.relative_to(run)
        if not raw or raw.get("error") or digest(path) != digest(snapshot / "outputs/runs" / run.name / rel):
            raise ValueError("Missing/changed raw: " + cid)
        raw_hashes[str(rel)] = digest(path)
        record = {"case": raw["case"], "repeat": 1, "raw": raw, "path": path}
        records.append(record)
        item = analyse(record, corpus)
        if int(cid[2:]) <= 40 and item["status"] != rows[cid]["status"]:
            raise ValueError("Alias correction changed an original-40 score")
        if "expected_referral_any" in raw["case"]:
            result = raw["turns"][-1]["result"]
            old, new = module.check_referral(result, raw["case"], corpus), check_referral(result, raw["case"], corpus)
            deltas.append({"case_id": cid, "strict_before": rows[cid]["status"], "strict_after": item["status"],
                "referral_before": old.status, "referral_after": new.status, "old_observation": old.details, "new_observation": new.details})
    report = write_reports(run, manifest, records, corpus)
    original_done = json.loads((original / "completion.json").read_text(encoding="utf-8"))
    write_json(run / "completion.json", {**original_done, **report, "offline_rescored_at": utc_now(), "additional_api_calls": 0})
    for name in ["summary.md", "results.csv", "calibration.md"]:
        shutil.copyfile(run / name, ROOT / "outputs" / name)
    shutil.copyfile(run / "BUGS.md", run / "BUGS_checks_only.md")
    if any(digest(run / rel) != sha for rel, sha in raw_hashes.items()):
        raise ValueError("Raw bytes changed during report generation")
    write_json(run / "checks_revision.json", {"rescored_at": utc_now(), "reason":
        "Added the full official English IRDAI name as a canonical alias. The shorter name without the portal suffix and the full source footer must not be counted as two bodies. No case expectation, acceptable ID, input or raw response changed; wrong bodies still hard fail.",
        "original_checks_sha256": manifest["fingerprints"]["checks"], "revised_checks_sha256": digest(ROOT / "tests/checks.py"),
        "raw_sha256": raw_hashes, "raw_hashes_unchanged": True, "original_40_scores_unchanged": True,
        "case_expectations_unchanged": True, "additional_api_calls": 0, "case_deltas": deltas})
    print(f"Offline rescore: {report['passed']}/55 strict passes; all captures and original scores preserved.")


if __name__ == "__main__":
    main()
