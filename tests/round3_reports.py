"""Generate before/after and performance artifacts from immutable real captures."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import shutil
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.checks import get
from tests.reporting import analyse, call_count
from tests.run_eval import digest, latest_record, raw_dir, utc_now, write_json

BEFORE = ROOT / "outputs/runs/real-20261105T161021.563148Z"


def percentile(values, fraction):
    """Linear interpolation at (n-1)*p; no outlier removal."""
    if not values:
        return None
    ordered = sorted(values)
    point = (len(ordered) - 1) * fraction
    lo, hi = math.floor(point), math.ceil(point)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (point - lo)


def load_run(directory):
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest["mock"] or manifest["stage"] != "real":
        raise ValueError("Comparison/performance requires genuine real runs")
    if manifest["runs"] != 1:
        raise ValueError("Round-three comparison expects one repeat per revision")
    corpus = json.loads((directory / "corpus_snapshot.json").read_text(encoding="utf-8"))
    items = {}
    for cid in manifest["case_ids"]:
        raw, path = latest_record(raw_dir(directory, 1, 1), cid)
        if raw is None:
            raise ValueError(f"Missing raw case {cid}; finish/resume the run before final comparison")
        items[cid] = analyse({"case": raw["case"], "repeat": 1, "raw": raw, "path": path}, corpus)
    return manifest, items


def turns(items):
    return [(item, n, turn, checks) for item in items if item["status"] in {"pass", "fail"}
            for n, (turn, checks) in enumerate(zip(item["raw"]["turns"], item["turn_checks"]), 1)
            if isinstance(turn.get("result"), dict)]


def has_pruned(item):
    return any("pruned" in t.get("result", {}).get("trace", {}) for t in item["raw"]["turns"])


def summarise(items):
    complete = [i for i in items if i["status"] in {"pass", "fail"}]
    observations = turns(complete)
    final = [(i, i["raw"]["turns"][-1]["result"]) for i in complete]
    cites = [(cid, {r.get("id") for r in turn["result"].get("retrieved", [])})
             for _, _, turn, _ in observations for cid in turn["result"].get("citations", [])]
    refusal = [(i, r) for i, r in final if i["case"].get("refusal_expected")]
    lawyer = [(i, r) for i, r in final if i["case"]["expect_needs_lawyer"]]
    traps = [i for i in complete if i["case"]["group"].startswith(("D_", "F_"))]
    hindi = [(i, n, t, c) for i, n, t, c in observations if i["case"]["language"].split("-")[0] == "hi"]
    hits = [(i, r) for i, r in final if i["case"].get("expected_chunk_ids")]
    calls = [n for _, _, t, _ in observations if (n := call_count(t["result"])) is not None]
    metric = lambda n, d=None, kind="count": {"numerator": n, "denominator": d, "kind": kind}
    return {
        "Case pass": metric(sum(i["status"] == "pass" for i in complete), len(complete), "rate"),
        "Routing accuracy": metric(sum(i["checks"]["check_routing"].status == "pass" for i in complete), len(complete), "rate"),
        "Citation membership validity": metric(sum(cid in ids for cid, ids in cites), len(cites), "rate"),
        "Final citation/reference code flags": metric(sum(any(c[k].status == "fail" for k in ("check_citations_valid", "check_no_invented_law", "check_legal_blocks_cited")) for _, _, _, c in observations), len(observations), "rate"),
        "Correct-refusal rate": metric(sum(r.get("action") in {"refuse_unverified", "escalate"} and r.get("needs_lawyer") is True for _, r in refusal), len(refusal), "rate"),
        "Escalation/referral recall": metric(sum(i["checks"]["check_needs_lawyer"].status == "pass" for i, _ in lawyer), len(lawyer), "rate"),
        "D/F strict trap pass": metric(sum(i["status"] == "pass" for i in traps), len(traps), "rate"),
        "Language match, all turns": metric(sum(c["check_language"].status == "pass" for _, _, _, c in observations), len(observations), "rate"),
        "Hindi script match": metric(sum(c["check_language"].status == "pass" for _, _, _, c in hindi), len(hindi), "rate"),
        "Retrieval hit, agent-mapped IDs": metric(sum(bool(set(i["case"]["expected_chunk_ids"]) & {r.get("id") for r in result.get("retrieved", [])}) for i, result in hits), len(hits), "rate"),
        "Final refuse_unverified cases": metric(sum(r.get("action") == "refuse_unverified" for _, r in final)),
        "refuse_unverified turns": metric(sum(t["result"].get("action") == "refuse_unverified" for _, _, t, _ in observations)),
        "Cases with trace.pruned (any turn)": metric(sum(has_pruned(i) for i in complete)),
        "Mean observed turn time": metric(statistics.mean(t["latency_s"] for _, _, t, _ in observations) if observations else None, kind="seconds"),
        "p50 observed turn time": metric(percentile([t["latency_s"] for _, _, t, _ in observations], .50), kind="seconds"),
        "p95 observed turn time": metric(percentile([t["latency_s"] for _, _, t, _ in observations], .95), kind="seconds"),
        "Mean trace-reported calls/turn": metric(statistics.mean(calls) if calls else None, kind="calls"),
        "Independent semantic unsupported-claim rate": metric(None, kind="unknown"),
    }


def show(value):
    n, d, kind = value["numerator"], value["denominator"], value["kind"]
    if n is None or kind == "unknown" or kind == "rate" and not d:
        return "unavailable"
    if kind == "rate":
        return f"{n / d:.1%} ({n}/{d})"
    return f"{n:.2f}{' s' if kind == 'seconds' else ''}" if kind in {"seconds", "calls"} else str(n)


def delta(before, after):
    if before["numerator"] is None or after["numerator"] is None:
        return "n/a"
    if before["kind"] == "rate":
        if not before["denominator"] or not after["denominator"]:
            return "n/a"
        return f"{100 * (after['numerator'] / after['denominator'] - before['numerator'] / before['denominator']):+.1f} pp"
    diff = after["numerator"] - before["numerator"]
    return f"{diff:+.2f}" if before["kind"] in {"seconds", "calls"} else f"{diff:+d}"


def failed_checks(item):
    return {name.removeprefix("check_") for name, outcome in item["checks"].items() if outcome.status == "fail"}


def performance(items):
    observations = turns(items)
    role_models, reasons = Counter(), Counter()
    fallback_turns = served_change_turns = translation_without_role = 0
    times, calls, table = [], [], []
    translation_attempts = 0
    for item, number, turn, _ in observations:
        result = turn["result"]
        trace = result.get("trace", {})
        stats = trace.get("llm", {})
        fallbacks = stats.get("fallbacks", [])
        switched = bool(fallbacks)
        fallback_turns += switched
        for f in fallbacks:
            reasons[str(f.get("reason", "unknown"))] += 1
        models_by_role = defaultdict(set)
        for entry in stats.get("models", []):
            if isinstance(entry, str) and entry.count(":") >= 2:
                role, provider, model = entry.split(":", 2)
                role_models[(role, provider + ":" + model)] += 1
                models_by_role[role].add(provider + ":" + model)
        served_change_turns += any(len(models) > 1 for models in models_by_role.values())
        translation = trace.get("translation", {})
        attempts = translation.get("attempts", 0) if isinstance(translation, dict) else 0
        translation_attempts += attempts if isinstance(attempts, int) else 0
        if translation.get("status") == "ok" and "translate" not in models_by_role:
            translation_without_role += 1
        elapsed = turn.get("latency_s")
        if isinstance(elapsed, (int, float)):
            times.append(elapsed)
        count = call_count(result)
        if count is not None:
            calls.append(count)
        table.append({"case_id": item["case"]["id"], "turn": number, "elapsed_s": elapsed,
                      "core_trace_s": trace.get("timings_s"), "provider_trace_s": stats.get("latency_s"),
                      "trace_calls": count, "fallback_or_switch": switched,
                      "models": stats.get("models", []), "translation_status": translation.get("status")})
    return {"turns": len(observations), "p50_s": percentile(times, .5), "p95_s": percentile(times, .95),
            "mean_s": statistics.mean(times) if times else None, "max_s": max(times) if times else None,
            "mean_trace_calls": statistics.mean(calls) if calls else None,
            "trace_calls_observed_turns": len(calls), "fallback_or_switch_turns": fallback_turns,
            "multiple_served_models_for_same_role_turns": served_change_turns,
            "served_role_models": [{"role": role, "model": model, "entries": count} for (role, model), count in sorted(role_models.items())],
            "fallback_reasons": dict(reasons), "translation_attempts_reported": translation_attempts,
            "translated_turns_without_served_translate_model": translation_without_role, "per_turn": table}


def generate(before_dir, after_dir):
    bm, before = load_run(before_dir)
    am, after = load_run(after_dir)
    before_ids = list(bm["case_ids"])
    if len(before_ids) != 30 or set(before_ids) - after.keys():
        raise ValueError("Expected the complete original 30-case baseline and a matching after cohort")
    if len(after) != 40 or not {f"T-{n:03d}" for n in range(31, 41)}.issubset(after):
        raise ValueError("The after run must include all 40 requested cases")
    if any(i["status"] in {"infra_error", "pending"} for i in after.values()):
        raise ValueError("Resume unresolved infrastructure/pending cases before generating the final delta")
    for cid in before_ids:
        if before[cid]["case"] != after[cid]["case"]:
            raise ValueError(f"Expectation/input changed for {cid}; do not present an apples-to-apples delta")
    if sum(i["status"] == "pass" for i in before.values()) != 12:
        raise ValueError("Baseline no longer reproduces the archived 12/30; inspect checker drift")
    protected = json.loads((ROOT / "tests/round3_before_manifest.json").read_text(encoding="utf-8"))
    if any(digest(before_dir / "raw" / name) != h for name, h in protected["raw_sha256"].items()):
        raise ValueError("Before archive raw hashes changed")
    matching = [after[cid] for cid in before_ids]
    added = [item for cid, item in after.items() if cid not in before]
    old_metrics, new_metrics, all_metrics = summarise(list(before.values())), summarise(matching), summarise(list(after.values()))
    lines = ["# Before / after — round three", "", f"Before: `{before_dir.name}` (21:40 IST, 12/30). After: `{after_dir.name}`.",
             "Matched-cohort deltas use T-001..T-030 with identical case dictionaries and the same current checks. The ten additions have no before score.",
             "A positive delta is a numeric increase, not always an improvement. pp = percentage points. Inputs/models/config/corpus may differ across revisions; this is an observed product comparison, not a causal experiment.",
             "", "| Metric | Before 30 | After same 30 | Delta | After all 40 |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {label} | {show(value)} | {show(new_metrics[label])} | {delta(value,new_metrics[label])} | {show(all_metrics[label])} |" for label, value in old_metrics.items()]
    lines += ["", "## Per-case delta: unchanged original cases", "", "| Case | Before → after | Action before → after | trace.pruned before → after | Resolved / newly failing checks |", "|---|---|---|---|---|"]
    for cid in before_ids:
        old, new = before[cid], after[cid]
        resolved, introduced = failed_checks(old) - failed_checks(new), failed_checks(new) - failed_checks(old)
        notes = ("resolved: " + ", ".join(sorted(resolved)) if resolved else "") + ("; new: " + ", ".join(sorted(introduced)) if introduced else "")
        lines.append(f"| {cid} | {old['status']} → {new['status']} | {old['raw']['turns'][-1]['result']['action']} → {new['raw']['turns'][-1]['result']['action']} | {has_pruned(old)} → {has_pruned(new)} | {notes.strip('; ') or 'unchanged failure set'} |")
    lines += ["", "## Ten added cases", "", "| Case | Group | Result | Final action | trace.pruned | Failing checks |", "|---|---|---|---|---|---|"]
    for item in added:
        lines.append(f"| {item['case']['id']} | {item['case']['group']} | {item['status']} | {item['raw']['turns'][-1]['result']['action']} | {has_pruned(item)} | {', '.join(sorted(failed_checks(item))) or 'none'} |")
    for label, cohort in (("Before", list(before.values())), ("After matched", matching), ("After all", list(after.values()))):
        refused = [i["case"]["id"] for i in cohort if i["raw"]["turns"][-1].get("result", {}).get("action") == "refuse_unverified"]
        pruned = [i["case"]["id"] for i in cohort if has_pruned(i)]
        lines += ["", f"- {label} final refuse_unverified cases: {', '.join(refused) or 'none'}.", f"- {label} cases with trace.pruned: {', '.join(pruned) or 'none'}."]
    lines += ["", "The original T-001 still expects a refusal; the new T-033 explicitly expects useful advice plus the no-cases line. That intentional difference is not hidden by changing the old case.",
              "The frozen TurnResult contract lists verifier statuses pass/fixed/failed. A returned status=pruned remains a contract-check failure while its answer/pruning behaviour is reported separately.",
              "Semantic unsupported-claim rate remains unavailable without a complete independent claim audit. A citation-membership pass is not evidence of entailment."]
    perf = performance(list(after.values()))
    rate = lambda n: f"{n}/{perf['turns']} ({n/perf['turns']:.1%})" if perf["turns"] else "unavailable"
    plines = ["# Performance — real round-three run", "", f"Source: `{after_dir.name}`; {perf['turns']} model-evaluable turns. No mock timing is included.",
              "p50/p95 use linear interpolation at (n-1)*p over observed per-turn elapsed time. No outlier is removed. The six-second inter-turn gap is excluded.",
              "", "| Measure | Observed |", "|---|---:|",
              f"| p50 turn time | {perf['p50_s']:.3f} s |", f"| p95 turn time | {perf['p95_s']:.3f} s |",
              f"| Mean / max turn time | {perf['mean_s']:.3f} / {perf['max_s']:.3f} s |",
              f"| Mean trace-reported calls per turn | {perf['mean_trace_calls']:.2f} ({perf['trace_calls_observed_turns']}/{perf['turns']} observed) |",
              f"| Turns with a fallback/model-switch event | {rate(perf['fallback_or_switch_turns'])} |",
              f"| Turns with multiple served models for the same role | {rate(perf['multiple_served_models_for_same_role_turns'])} |",
              "", "A switch event means trace.llm.fallbacks is non-empty, including candidates skipped because of provider failures or pacing. Served-model entries below come from trace.llm.models, not configured fallback chains.",
              "", "| Role | Actual model entry | Recorded service entries |", "|---|---|---:|"]
    plines += [f"| {r['role']} | {r['model']} | {r['entries']} |" for r in perf["served_role_models"]]
    plines += ["", f"Successful translated turns without an actual translate-model entry: {perf['translated_turns_without_served_translate_model']}. Translation attempts reported separately: {perf['translation_attempts_reported']}.",
               "If translation runs after the app snapshots its call statistics, trace-reported calls undercount that work and the actual translator cannot be inferred from config. These fields are observations, not a fabricated complete call total.",
               "", "## Per-turn observations", "", "| Case / turn | Elapsed s | Core trace s | Provider trace s | Trace calls | Switch | Translation |", "|---|---:|---:|---:|---:|---|---|"]
    plines += [f"| {r['case_id']} / {r['turn']} | {r['elapsed_s']:.3f} | {r['core_trace_s']} | {r['provider_trace_s']} | {r['trace_calls']} | {r['fallback_or_switch']} | {r['translation_status'] or 'none'} |" for r in perf["per_turn"]]
    plines += ["", "## Fallback reasons", ""] + [f"- {reason}: {count}" for reason, count in sorted(perf["fallback_reasons"].items())]
    comparison_text, perf_text = "\n".join(lines) + "\n", "\n".join(plines) + "\n"
    for name, content in (("BEFORE_AFTER.md", comparison_text), ("perf.md", perf_text)):
        (after_dir / name).write_text(content, encoding="utf-8")
        shutil.copyfile(after_dir / name, ROOT / "outputs" / name)
    payload = {"generated_at": utc_now(), "before_run": str(before_dir), "after_run": str(after_dir),
               "original_expectations_identical": True, "before_raw_hashes_preserved": True,
               "before_30": old_metrics, "after_matched_30": new_metrics, "after_all": all_metrics,
               "performance": perf}
    write_json(after_dir / "round3_metrics.json", payload)
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--before", type=Path, default=BEFORE)
    args = parser.parse_args()
    generated = generate(args.before.resolve(), args.run.resolve())
    print("Generated outputs/BEFORE_AFTER.md and outputs/perf.md from", generated["after_run"])


if __name__ == "__main__":
    main()
