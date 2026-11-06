"""Preserve original scoring and rescore immutable referral captures offline."""
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
        raise ValueError("Select a canonical run archive")
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    done = json.loads((run / "completion.json").read_text(encoding="utf-8"))
    if manifest["mock"] or manifest["stage"] != "real" or done["pending"] or done["infra_errors"]:
        raise ValueError("Use a complete real run")
    if manifest["case_ids"] != [f"T-{n:03d}" for n in range(41, 56)]:
        raise ValueError("Use the 15 round-four cases")
    frozen = json.loads((run / "frozen_inputs.json").read_text(encoding="utf-8"))
    snapshot = Path(frozen["snapshot_root"]).resolve()
    if not snapshot.is_relative_to((ROOT / "tests/_scratch").resolve()):
        raise ValueError("Unexpected frozen workspace")
    original_code = snapshot / "tests/checks.py"
    if digest(original_code) != manifest["fingerprints"]["checks"]:
        raise ValueError("Original frozen checker changed")
    original = run / "scoring-original"
    if not original.exists():
        original.mkdir()
        for name in ("results.csv", "summary.md", "calibration.md", "BUGS.md", "completion.json"):
            shutil.copyfile(run / name, original / name)
        shutil.copyfile(original_code, original / "checks.py")
    spec = importlib.util.spec_from_file_location("round4_original_checks", original / "checks.py")
    old_checks = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = old_checks
    spec.loader.exec_module(old_checks)
    corpus = json.loads((run / "corpus_snapshot.json").read_text(encoding="utf-8"))
    original_rows = {row["case_id"]: row for row in csv.DictReader((original / "results.csv").open(encoding="utf-8"))}
    records, raw_hashes, deltas = [], {}, []
    for cid in manifest["case_ids"]:
        raw, path = latest_record(run / "raw", cid)
        if not raw or raw.get("error"):
            raise ValueError("Missing real raw case: " + cid)
        source = snapshot / "outputs/runs" / run.name / "raw" / path.relative_to(run / "raw")
        if digest(path) != digest(source):
            raise ValueError("Raw capture changed")
        raw_hashes[str(path.relative_to(run))] = digest(path)
        records.append({"case": raw["case"], "repeat": 1, "raw": raw, "path": path})
        result = raw["turns"][-1]["result"]
        old = old_checks.check_referral(result, raw["case"], corpus)
        new = check_referral(result, raw["case"], corpus)
        item = analyse(records[-1], corpus)
        deltas.append({"case_id": cid, "strict_before": original_rows[cid]["status"], "strict_after": item["status"],
            "referral_before": old.status, "referral_after": new.status,
            "old_observation": old.details, "new_observation": new.details})
    summary = write_reports(run, manifest, records, corpus)
    original_done = json.loads((original / "completion.json").read_text(encoding="utf-8"))
    write_json(run / "completion.json", {**original_done, **summary, "offline_rescored_at": utc_now(), "additional_api_calls": 0})
    shutil.copyfile(run / "BUGS.md", run / "BUGS_checks_only.md")
    if any(digest(run / rel) != sha for rel, sha in raw_hashes.items()):
        raise ValueError("Raw hashes changed while regenerating reports")
    write_json(run / "checks_revision.json", {"rescored_at": utc_now(), "reason":
        "Corrected false extra-body detections from generic helpline/portal descriptors and masked sentence fragments; added canonical translated regulator/railway aliases. Acceptable directory IDs and all case expectations remain unchanged. Unknown named bodies, mixed correct/wrong bodies and statute/section patterns still hard fail.",
        "original_checks_sha256": manifest["fingerprints"]["checks"], "revised_checks_sha256": digest(ROOT / "tests/checks.py"),
        "raw_sha256": raw_hashes, "raw_hashes_unchanged": True, "case_expectations_unchanged": True,
        "additional_api_calls": 0, "case_deltas": deltas})
    print(f"Offline rescore complete: {summary['passed']} strict passes / {len(records)}; original scores and all raw bytes preserved.")


if __name__ == "__main__":
    main()
