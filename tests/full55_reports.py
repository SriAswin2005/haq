"""Compare a complete current 55-case real run against the round-three 40."""
import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.reporting import rate, referral_metrics
from tests.round3_reports import load_run, summarise, show, delta, failed_checks, has_pruned, performance
from tests.run_eval import digest, utc_now, write_json

BEFORE = ROOT / "outputs/runs/real-20261105T214345.363908Z"


def seconds(value):
    return "unavailable" if value is None else f"{value:.3f} s"


def generate(run):
    if not run.is_relative_to((ROOT / "outputs/runs").resolve()):
        raise ValueError("Select a canonical run archive")
    bm, before = load_run(BEFORE)
    am, after = load_run(run)
    if list(before) != [f"T-{n:03d}" for n in range(1, 41)] or list(after) != [f"T-{n:03d}" for n in range(1, 56)]:
        raise ValueError("Expected the complete 40-case baseline and full 55-case after run")
    if am["judge"] or any(i["status"] in {"pending", "infra_error"} for i in after.values()):
        raise ValueError("Finish all 55 real cases without the extra judge before publishing")
    for name, key in [("checks.py", "checks"), ("cases.jsonl", "cases"), ("reporting.py", "reporting")]:
        if digest(ROOT / "tests" / name) != am["fingerprints"][key]:
            if name != "checks.py" or not (run / "checks_revision.json").exists():
                raise ValueError(f"Current {name} differs from frozen capture")
            revision = json.loads((run / "checks_revision.json").read_text(encoding="utf-8"))
            if (revision.get("original_checks_sha256") != am["fingerprints"]["checks"]
                    or revision.get("revised_checks_sha256") != digest(ROOT / "tests/checks.py")
                    or revision.get("raw_hashes_unchanged") is not True or revision.get("original_40_scores_unchanged") is not True
                    or revision.get("additional_api_calls") != 0):
                raise ValueError("Unaudited checker revision")
    original_rows = {row["case_id"]: row for row in csv.DictReader((BEFORE / "results.csv").open(encoding="utf-8"))}
    if sum(i["status"] == "pass" for i in before.values()) != 21:
        raise ValueError("The round-three baseline no longer reproduces 21/40")
    if any(i["status"] != original_rows[cid]["status"] for cid, i in before.items()):
        raise ValueError("Baseline per-case outcomes changed")
    for cid, old in before.items():
        if old["case"] != after[cid]["case"]:
            raise ValueError("Original 40-case expectation/input changed: " + cid)
    guard = json.loads((ROOT / "tests/full55_before_manifest.json").read_text(encoding="utf-8"))
    for directory, field in [(BEFORE, "round3_raw_sha256"), (ROOT / guard["earlier_referral_run"], "earlier_referral_raw_sha256")]:
        if any(digest(directory / "raw" / name) != sha for name, sha in guard[field].items()):
            raise ValueError("Historical raw hashes changed")
    frozen = json.loads((run / "frozen_inputs.json").read_text(encoding="utf-8"))
    snapshot = Path(frozen["snapshot_root"]).resolve()
    if not snapshot.is_relative_to((ROOT / "tests/_scratch").resolve()):
        raise ValueError("Unexpected snapshot path")
    if any(digest(snapshot / rel) != sha for rel, sha in frozen["input_sha256"].items()):
        raise ValueError("Frozen inputs changed")
    raw_hashes = {}
    for cid, item in after.items():
        path = item["path"]
        rel = path.relative_to(run)
        if digest(path) != digest(snapshot / "outputs/runs" / run.name / rel):
            raise ValueError("Raw capture collection mismatch: " + cid)
        if digest(path) != digest(ROOT / "outputs/raw" / (cid + ".json")):
            raise ValueError("Published raw mismatch: " + cid)
        if item["case"]["expected_law_verified"] is not False:
            raise ValueError("Unexpected human-verification flag")
        raw_hashes[str(rel)] = digest(path)
    if (run / "checks_revision.json").exists():
        revision = json.loads((run / "checks_revision.json").read_text(encoding="utf-8"))
        if raw_hashes != revision["raw_sha256"]:
            raise ValueError("Raw bytes differ from the offline checker revision audit")
    matched = [after[cid] for cid in before]
    added = [after[f"T-{n:03d}"] for n in range(41, 56)]
    all_items = list(after.values())
    old_metrics, current_metrics, all_metrics = summarise(list(before.values())), summarise(matched), summarise(all_items)
    perf_before, perf_matched, perf_all, perf_referral = (performance(cohort) for cohort in
        [list(before.values()), matched, all_items, added])
    refs = referral_metrics(added)
    observations = []
    for item in added:
        result = item["raw"]["turns"][-1]["result"]
        outcome = item["turn_checks"][-1]["check_referral"]
        observations.append({"case_id": item["case"]["id"], "category": result.get("category"), "action": result.get("action"),
            "needs_lawyer": result.get("needs_lawyer"), "strict_status": item["status"], "referral_check": outcome.status,
            "reason": outcome.reason, "failed_checks": sorted(failed_checks(item)), "raw_file": str(item["path"]), **outcome.details})
    lines = ["# Before / after — full 55-case real evaluation", "",
        f"Before: `{BEFORE.name}` (round three: 21/40 strict passes). Current: `{run.name}`.",
        f"Current inputs frozen at {frozen['frozen_at']}. Command: `python tests/run_frozen_eval.py --sleep 6`; all T-001..T-055, no `--judge`.",
        "Matched comparison uses T-001..T-040 with identical case dictionaries. The baseline reproduces all original per-case outcomes under the current checks. "
        "The latest run contains all 55 cases in one snapshot; earlier focused referral captures remain archived.", "",
        "A post-capture alias correction recognises IRDAI's full English name without its portal suffix as the same body. "
        "Original scoring is preserved in scoring-original/ and checks_revision.json records the zero-API-call rescore; all first-40 scores and all case inputs/allowlists are unchanged.", "",
        "## T-001..T-040 versus round three", "", "| Metric | Round 3, 40 cases | Current same 40 | Delta | Current all 55 |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {label} | {show(value)} | {show(current_metrics[label])} | {delta(value, current_metrics[label])} | {show(all_metrics[label])} |" for label, value in old_metrics.items()]
    lines += ["", "## Latency", "", "| Cohort | Turns | p50 | p95 | Mean |", "|---|---:|---:|---:|---:|"]
    for label, perf in [("Round 3, original 40", perf_before), ("Current matched 40", perf_matched), ("Current referrals 15", perf_referral), ("Current full 55", perf_all)]:
        lines.append(f"| {label} | {perf['turns']} | {seconds(perf['p50_s'])} | {seconds(perf['p95_s'])} | {seconds(perf['mean_s'])} |")
    lines += ["", "Quantiles use linear interpolation at (n-1)*p over observed per-turn elapsed time. All completed turns and outliers are included; six-second inter-turn gaps are excluded. "
        "These are observed revision differences, not a causal model benchmark; providers, load, code, config and corpus can differ.", "",
        "## Per-case delta: unchanged T-001..T-040", "", "| Case | Before → current | Action before → current | Resolved checks | Newly failing checks |", "|---|---|---|---|---|"]
    for cid, old in before.items():
        new = after[cid]
        lines.append(f"| {cid} | {old['status']} → {new['status']} | {old['raw']['turns'][-1]['result']['action']} → {new['raw']['turns'][-1]['result']['action']} | {', '.join(sorted(failed_checks(old)-failed_checks(new))) or 'none'} | {', '.join(sorted(failed_checks(new)-failed_checks(old))) or 'none'} |")
    behavior_notes = []
    date_result = after["T-029"]["raw"]["turns"][-1]["result"]
    draft = date_result.get("draft_text") or ""
    if date_result.get("trace", {}).get("conflicts") and "[●" in draft and not any(d in draft for d in ["2026-10-10", "2026-10-20"]):
        behavior_notes.append("T-029 now records the date conflict and omits both disputed dates from its placeholder-bearing draft. "
            "The retained wording check can still fail to recognise the note's phrasing; that strict flag is not evidence that the draft still selects a date.")
    promise_result = after["T-001"]["raw"]["turns"][-1]["result"]
    if "no_promises" in failed_checks(after["T-001"]) and "cannot promise any outcome" in promise_result.get("reply_text", ""):
        behavior_notes.append("T-001's no-promises flag requires review: its text explicitly says it cannot promise any outcome. "
            "The strict score is retained, rather than treating this lexical flag as a confirmed positive guarantee.")
    if behavior_notes:
        lines += ["", "### Reading strict flags", ""] + ["- " + note for note in behavior_notes]
    referral_lines = ["## T-041..T-055 referral precision and recall", "",
        "Per the user's revision, bank, insurance, rail, airline, electricity, builder and food cases accept consumer/answer/needs_lawyer=false or out_of_scope/escalate/needs_lawyer=true as coherent alternatives. "
        "Inputs and acceptable body IDs are unchanged. An answer must visibly name and cite an expected body. Wrong bodies always hard fail. "
        "Statute/section patterns are forbidden for escalation or out-of-scope output; in an answer they must appear in a cited chunk. Reference grounding is textual evidence, not a semantic legal-applicability certification.", "",
        "| Referral measure | Current real result |", "|---|---:|",
        f"| Body precision: correct / shown bodies | {rate(refs['correct_bodies'], refs['shown_bodies'])} |",
        f"| Body recall: cases with expected body / expected cases | {rate(refs['correct_cases'], refs['expected_cases'])} |",
        f"| Cited-body precision: expected, named and cited / shown bodies | {rate(refs['cited_correct_bodies'], refs['shown_bodies'])} |",
        f"| Cited-body recall: cases naming and citing expected body / expected cases | {rate(refs['cited_correct_cases'], refs['expected_cases'])} |",
        f"| Safe correct-referral coverage | {rate(refs['safe_correct_cases'], refs['expected_cases'])} |",
        f"| Referral check pass, safe escalation fallback allowed | {rate(refs['referral_check_passes'], refs['expected_cases'])} |",
        f"| Cases with no referral body | {refs['fallback_cases']}/{refs['expected_cases']} |",
        f"| Wrong bodies / cases with a wrong body | {refs['wrong_bodies']} / {refs['wrong_body_cases']} |",
        f"| Escalation/out-of-scope cases containing forbidden statutes | {refs['forbidden_statute_cases']} |",
        f"| Cases with ungrounded statutes | {refs['ungrounded_statute_cases']} |",
        f"| Answers containing cited-grounded statute references | {refs['grounded_answer_statute_cases']} |",
        f"| Answers missing an expected named-and-cited body | {refs['answer_missing_cited_referral_cases']} |",
        f"| All strict checks pass | {sum(i['status']=='pass' for i in added)}/{len(added)} |", "",
        "Bodies are deduplicated per reply; visible names/portal destinations count, while retrieved-but-unshown chunks do not. Legal aid and Tele-Law are excluded from body precision/recall. "
        "Coverage recall can include a correct body alongside a wrong one; the latter still fails the check and safe coverage. Independent language, routing and contract checks remain active.", "",
        "| Case | Actual category / action / lawyer | Shown bodies | Cited expected bodies | Referral check | Strict case | Failing checks |", "|---|---|---|---|---|---|---|"]
    for o in observations:
        path = Path(o["raw_file"]).as_posix()
        referral_lines.append(f"| [{o['case_id']}](<{path}>) | {o['category']} / {o['action']} / {o['needs_lawyer']} | {', '.join(o['shown']) or 'none'} | {', '.join(o['cited_correct']) or 'none'} | {o['referral_check']} | {o['strict_status']} | {', '.join(o['failed_checks']) or 'none'} |")
    lines += ["", *referral_lines, "", "## Provenance and limits", "",
        f"Current referral cutoff={am.get('retrieval_referral_min_score')}; answer cutoff={am.get('retrieval_min_score')}. "
        f"Before corpus chunks={len(json.loads((BEFORE/'corpus_snapshot.json').read_text(encoding='utf-8')))}; current={len(json.loads((run/'corpus_snapshot.json').read_text(encoding='utf-8')))}.",
        "No app/data source edits were made by the evaluation work. All 55 expected_law_verified flags remain false. "
        "Raw hashes, frozen input integrity and previous archives are checked before publication. "
        "No extra harness judge was used; the app's internal verifier remained configured. Semantic unsupported-claim rate is unavailable. "
        "One run per revision does not measure flakiness. Voice inputs are transcripts, not STT/TTS tests. Historical mock findings do not enter these real metrics."]
    comparison = "\n".join(lines) + "\n"
    for directory in [run, ROOT / "outputs"]:
        (directory / "BEFORE_AFTER.md").write_text(comparison, encoding="utf-8")
        (directory / "referrals.md").write_text("# Referrals — current full real run\n\n" + "\n".join(referral_lines) + "\n", encoding="utf-8")
    with (run / "referrals.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(observations[0]))
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k,v in o.items()} for o in observations)
    shutil.copyfile(run / "referrals.csv", ROOT / "outputs/referrals.csv")
    perf_lines = ["# Performance — current full real run", "", f"Run: `{run.name}`; {perf_all['turns']} turns.",
        f"p50={seconds(perf_all['p50_s'])}; p95={seconds(perf_all['p95_s'])}; mean={seconds(perf_all['mean_s'])}; max={seconds(perf_all['max_s'])}.",
        f"Mean trace calls/turn={perf_all['mean_trace_calls']:.2f}; fallback/switch turns={perf_all['fallback_or_switch_turns']}/{perf_all['turns']}; "
        f"multiple actually served models for one role={perf_all['multiple_served_models_for_same_role_turns']}/{perf_all['turns']}.",
        "Quantiles include all observed elapsed turn times, without inter-turn gaps or outlier removal. Models below come only from trace.llm.models.", "",
        "| Role | Served model | Trace entries |", "|---|---|---:|"]
    perf_lines += [f"| {m['role']} | {m['model']} | {m['entries']} |" for m in perf_all['served_role_models']]
    perf_lines += ["", f"Translated turns without a served translator entry: {perf_all['translated_turns_without_served_translate_model']}; separately reported translation attempts: {perf_all['translation_attempts_reported']}. "
        "Trace calls/model provenance can be incomplete if translation happens after the stats snapshot; no translator is inferred from config.", "",
        "| Case / turn | Elapsed s | Trace calls | Switch |", "|---|---:|---:|---|"]
    perf_lines += [f"| {r['case_id']} / {r['turn']} | {r['elapsed_s']:.3f} | {r['trace_calls']} | {r['fallback_or_switch']} |" for r in perf_all['per_turn']]
    for directory in [run, ROOT / "outputs"]:
        (directory / "perf.md").write_text("\n".join(perf_lines) + "\n", encoding="utf-8")
    original_bugs = run / "BUGS_checks_only.md"
    if not original_bugs.exists():
        original_bugs.write_bytes((run / "BUGS.md").read_bytes())
    context = f"# Evaluation bugs\n\nFull T-001..T-055 real run, frozen at {frozen['frozen_at']}. Later checkout edits are outside this report. "
    context += ("Round-four consumer-service answers are permitted with a cited expected body; cited-grounded statutes in answers are allowed. "
                "Wrong bodies and statute-bearing escalation/out-of-scope replies remain hard failures. Historical reports remain in their own archives.\n")
    bugs = original_bugs.read_text(encoding="utf-8").replace("# Evaluation bugs\n", context, 1)
    if behavior_notes:
        bugs = bugs.replace("# Evaluation bugs\n", "# Evaluation bugs\n\n" + "\n\n".join(behavior_notes) + "\n", 1)
    bugs = "\n".join(line.rstrip() for line in bugs.splitlines()).rstrip() + "\n"
    for path in [run / "BUGS.md", ROOT / "tests/BUGS.md"]:
        path.write_text(bugs, encoding="utf-8")
    payload = {"generated_at": utc_now(), "before_run": str(BEFORE), "after_run": str(run),
        "before_40": old_metrics, "current_matched_40": current_metrics, "current_all_55": all_metrics,
        "referrals": refs, "referral_observations": observations,
        "performance_before_40": perf_before, "performance_matched_40": perf_matched, "performance_all_55": perf_all,
        "performance_referrals_15": perf_referral, "raw_sha256": raw_hashes,
        "original_40_expectations_identical": True, "before_raw_hashes_preserved": True,
        "frozen_inputs_unchanged": True, "raw_capture_and_publication_byte_identity": True,
        "additional_api_calls": 0, "analysis_sha256": {n: digest(ROOT / "tests" / n) for n in
            ["checks.py", "reporting.py", "full55_reports.py"]}}
    write_json(run / "full55_metrics.json", payload)
    write_json(run / "referral_metrics.json", {"counts": refs, "observations": observations, "source_full_run": str(run), "additional_api_calls": 0})
    from dotenv import dotenv_values
    values = [*dotenv_values(ROOT / ".env", encoding="utf-8-sig").items(), *os.environ.items()]
    secrets = [v.encode() for k,v in values if v and len(v) >= 8 and any(word in k.upper() for word in ["KEY", "TOKEN", "SECRET", "PASSWORD"])]
    artifacts = [p for p in run.rglob("*") if p.is_file()]
    artifacts += [ROOT / "outputs" / name for name in ["BEFORE_AFTER.md", "referrals.md", "referrals.csv", "perf.md"]]
    artifacts += [ROOT / "tests/BUGS.md"]
    if (snapshot / ".env").exists() or any(secret in path.read_bytes() for path in artifacts for secret in secrets):
        raise ValueError("Credential exposure detected; values withheld")
    for name in ["BEFORE_AFTER.md", "referrals.md", "referrals.csv", "perf.md", "summary.md", "results.csv", "calibration.md"]:
        if digest(ROOT / "outputs" / name) != digest(run / name):
            raise ValueError("Published report mismatch: " + name)
    write_json(run / "audit.json", {"audited_at": utc_now(), "raw_cases": len(after), "turns": perf_all["turns"],
        "raw_sha256": raw_hashes, "original_40_expectations_identical": True, "baseline_reproduces_21_of_40": True,
        "historical_raw_hashes_preserved": True, "frozen_inputs_unchanged": True, "raw_publication_byte_identity": True,
        "all_law_expectations_unverified": True, "published_reports_match_archive": True,
        "credential_value_matches": 0, "additional_api_calls": 0, "referrals": refs,
        "full55_p50_s": perf_all["p50_s"], "full55_p95_s": perf_all["p95_s"]})
    print(json.dumps({"matched_40_passes": current_metrics['Case pass']['numerator'], "all_55_passes": all_metrics['Case pass']['numerator'],
        "referrals": refs, "p50_s": perf_all['p50_s'], "p95_s": perf_all['p95_s']}, sort_keys=True))
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    generate(args.run.resolve())


if __name__ == "__main__":
    main()
