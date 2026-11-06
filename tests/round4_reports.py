"""Append real referral metrics to BEFORE_AFTER without rerunning old cases."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.reporting import analyse, rate, referral_metrics
from tests.run_eval import digest, latest_record, load_cases, utc_now, write_json

START = "<!-- ROUND4_REFERRALS_START -->"
END = "<!-- ROUND4_REFERRALS_END -->"


def append_section(previous, section):
    block = START + "\n" + section.rstrip() + "\n" + END
    if START in previous:
        prefix, tail = previous.split(START, 1)
        _, suffix = tail.split(END, 1)
        return prefix + block + suffix
    return previous.rstrip() + "\n\n" + block + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to((ROOT / "outputs/runs").resolve()):
        raise ValueError("Select a canonical real-run archive")
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    completion = json.loads((run / "completion.json").read_text(encoding="utf-8"))
    if manifest["mock"] or manifest["stage"] != "real" or manifest["judge"] or manifest["runs"] != 1:
        raise ValueError("Use a single-repeat real run without the extra judge")
    if manifest["case_ids"] != [f"T-{n:03d}" for n in range(41, 56)] or completion["infra_errors"] or completion["pending"]:
        raise ValueError("Finish all 15 real referral cases before final reporting")
    revision = None
    if digest(ROOT / "tests/checks.py") != manifest["fingerprints"]["checks"]:
        path = run / "checks_revision.json"
        revision = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if (revision.get("original_checks_sha256") != manifest["fingerprints"]["checks"]
                or revision.get("revised_checks_sha256") != digest(ROOT / "tests/checks.py")
                or revision.get("raw_hashes_unchanged") is not True or revision.get("additional_api_calls") != 0):
            raise ValueError("Preserve original scoring and validate the offline checker revision before reporting")
    corpus = json.loads((run / "corpus_snapshot.json").read_text(encoding="utf-8"))
    frozen = json.loads((run / "frozen_inputs.json").read_text(encoding="utf-8"))
    snapshot = Path(frozen["snapshot_root"]).resolve()
    if not snapshot.is_relative_to((ROOT / "tests/_scratch").resolve()):
        raise ValueError("Unexpected snapshot path")
    if any(digest(snapshot / rel) != sha for rel, sha in frozen["input_sha256"].items()):
        raise ValueError("Frozen application/corpus inputs changed")
    guard = json.loads((ROOT / "tests/round4_before_manifest.json").read_text(encoding="utf-8"))
    before = ROOT / guard["before_run"]
    if any(digest(before / "raw" / name) != sha for name, sha in guard["raw_sha256"].items()):
        raise ValueError("Previous 40-case raw hashes changed")
    if digest(before / "BEFORE_AFTER.md") != guard["before_after_sha256"]:
        raise ValueError("Prior comparison archive changed")
    all_cases = load_cases(snapshot / "tests/cases.jsonl")
    for case in all_cases[:40]:
        old, _ = latest_record(before / "raw", case["id"])
        if old["case"] != case:
            raise ValueError("Original expectation/input changed: " + case["id"])
    items, observations, raw_hashes = [], [], {}
    for cid in manifest["case_ids"]:
        raw, path = latest_record(run / "raw", cid)
        if not raw or raw.get("error") or raw["case"]["expected_law_verified"] is not False:
            raise ValueError("Unusable or human-verified case: " + cid)
        source = snapshot / "outputs/runs" / run.name / "raw" / path.relative_to(run / "raw")
        if digest(source) != digest(path):
            raise ValueError("Canonical raw bytes differ from frozen capture")
        item = analyse({"case": raw["case"], "repeat": 1, "raw": raw, "path": path}, corpus)
        outcome = item["turn_checks"][-1]["check_referral"]
        items.append(item)
        raw_hashes[str(path.relative_to(run))] = digest(path)
        observations.append({"case_id": cid, "language": raw["case"]["language"], "raw_file": str(path),
            "strict_status": item["status"], "referral_check": outcome.status, **outcome.details})
    if revision and raw_hashes != revision["raw_sha256"]:
        raise ValueError("Raw bytes differ from the audited offline rescore")
    counts = referral_metrics(items)
    lines = ["## Round 4: directory referrals", "", f"Real cohort: `{run.name}`; T-041..T-055, 15 cases / 15 turns.",
        f"Frozen inputs: {frozen['frozen_at']}; {len(corpus)} corpus chunks, including {sum(cid.startswith('COM-DIR-') for cid in corpus)} directory rows. "
        f"Referral cutoff: {manifest.get('retrieval_referral_min_score')}. Command: `python tests/run_frozen_eval.py --sleep 6 --only round4`; no `--judge`.",
        "The earlier 30/40-case tables above are preserved. These 15 cases have no before-referral score. Results from different snapshots are not combined into a fictitious 55-case run.", "",
        ("Scoring correction: original scores and checker are preserved in `scoring-original/`; `checks_revision.json` records the offline rescore. "
         "Generic helpline/portal descriptions were initially mistaken for additional bodies. The corrected detector has regression coverage; no case expectation, acceptable ID or raw reply changed, and no additional API call was made."
         if revision else "The checker is identical to the captured run's checker."), "",
        "| Referral measure | Real result |", "|---|---:|",
        f"| Precision: correct body mentions / shown body mentions | {rate(counts['correct_bodies'], counts['shown_bodies'])} |",
        f"| Recall: cases naming an expected body / expected cases | {rate(counts['correct_cases'], counts['expected_cases'])} |",
        f"| Safe correct-referral coverage: no wrong body or statute | {rate(counts['safe_correct_cases'], counts['expected_cases'])} |",
        f"| Referral safety check pass, legal-aid-only fallback allowed | {rate(counts['referral_check_passes'], counts['expected_cases'])} |",
        f"| Cases with no non-legal-aid referral | {counts['fallback_cases']}/{counts['expected_cases']} |",
        f"| Wrong bodies shown / cases with a wrong body | {counts['wrong_bodies']} / {counts['wrong_body_cases']} |",
        f"| Cases containing statute or section patterns | {counts['statute_cases']}/{counts['expected_cases']} |",
        f"| All strict checks pass | {sum(i['status'] == 'pass' for i in items)}/{len(items)} |",
        "| Infrastructure errors / pending | 0 / 0 |", "",
        "Precision counts distinct visible body IDs/recognised destinations per reply, not aliases, citations or retrieved-but-unshown chunks. "
        "Recall counts each expected case once, even if two acceptable bodies are named. Legal aid/Tele-Law are excluded from shown/correct counts: an empty referral can pass safety while missing recall. "
        "A correct body plus any wrong body hard fails; a statute/section pattern hard fails even with a correct referral. "
        "Coverage recall can include such a mixed reply; the separate safe-coverage and check-pass rows expose it.", "",
        "Names are matched against frozen directory titles plus independent English/Hindi/Hinglish aliases and visible portal URLs. "
        "Unknown named bodies/destinations are failures, not silently discarded. This is deterministic display checking, not a semantic audit of the directory's source text; all mapped expectations and directory rows remain pending human confirmation.", "",
        "| Case | Language | Acceptable IDs | Shown IDs | Referral check | Strict case | Statute/section patterns |", "|---|---|---|---|---|---|---|"]
    for o in observations:
        raw_link = Path(o["raw_file"]).as_posix()
        lines.append(f"| [{o['case_id']}](<{raw_link}>) | {o['language']} | {', '.join(o['expected'])} | {', '.join(o['shown']) or 'none (fallback)'} | {o['referral_check']} | {o['strict_status']} | {'; '.join(o['statute_patterns']).replace('|', '/') or 'none'} |")
    section = "\n".join(lines) + "\n"
    (run / "referrals.md").write_text("# Real referral evaluation\n\n" + section, encoding="utf-8")
    shutil.copyfile(run / "referrals.md", ROOT / "outputs/referrals.md")
    with (run / "referrals.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(observations[0]))
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in o.items()} for o in observations)
    shutil.copyfile(run / "referrals.csv", ROOT / "outputs/referrals.csv")
    previous = (ROOT / "outputs/BEFORE_AFTER.md").read_text(encoding="utf-8")
    old_tables = (before / "BEFORE_AFTER.md").read_text(encoding="utf-8").rstrip()
    if not previous.startswith(old_tables):
        raise ValueError("Existing comparison prefix changed; preserve it before appending")
    combined = append_section(previous, section)
    (ROOT / "outputs/BEFORE_AFTER.md").write_text(combined, encoding="utf-8")
    (run / "BEFORE_AFTER.md").write_text(combined, encoding="utf-8")
    base_bugs = run / "BUGS_checks_only.md"
    if not base_bugs.exists():
        base_bugs.write_bytes((run / "BUGS.md").read_bytes())
    context = ("# Evaluation bugs\n\n"
        f"Current scope: T-041..T-055 only, evaluated from frozen inputs {frozen['frozen_at']}. "
        "Later checkout edits are outside this report. The 40-case round-three findings remain in their immutable archive.\n\n"
        "Generic referral-label false positives were corrected by an offline rescore; original scoring and checks are preserved in scoring-original/, with unchanged raw hashes and case expectations recorded in checks_revision.json.\n\n"
        "Referral safety passes may be legal-aid-only recall misses. Strict routing/language/action failures are separate from wrong-body or statute failures.\n")
    bugs = base_bugs.read_text(encoding="utf-8").replace("# Evaluation bugs\n", context, 1)
    bugs = "\n".join(line.rstrip() for line in bugs.splitlines()).rstrip() + "\n"
    (run / "BUGS.md").write_text(bugs, encoding="utf-8")
    (ROOT / "tests/BUGS.md").write_text(bugs, encoding="utf-8")
    from dotenv import dotenv_values
    secrets = [v.encode() for k, v in dotenv_values(ROOT / ".env", encoding="utf-8-sig").items()
        if v and len(v) >= 8 and any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD"))]
    files = [p for p in run.rglob("*") if p.is_file()]
    if (snapshot / ".env").exists() or any(secret in p.read_bytes() for p in files for secret in secrets):
        raise ValueError("Credential exposure detected; values withheld")
    write_json(run / "referral_metrics.json", {"generated_at": utc_now(), "run": str(run), "counts": counts,
        "observations": observations, "raw_sha256": raw_hashes, "before_raw_hashes_preserved": True,
        "original_40_case_dictionaries_unchanged": True, "frozen_inputs_unchanged": True,
        "frozen_capture_byte_identity": True, "credential_value_matches": 0, "additional_api_calls": 0,
        "analysis_sha256": {n: digest(ROOT / "tests" / n) for n in ("checks.py", "reporting.py", "round4_reports.py")}})
    print(json.dumps(counts, sort_keys=True))
    print("Generated outputs/referrals.md, referrals.csv and appended outputs/BEFORE_AFTER.md; raw bytes and old tables preserved.")


if __name__ == "__main__":
    main()
