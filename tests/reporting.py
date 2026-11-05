"""Generate all derived artifacts from immutable raw runs; never edit outputs manually."""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

from tests.checks import CHECKS, CheckResult, final_blocks, run_checks, visible_text


def rate(n, d):
    return f"{n / d:.1%} ({n}/{d})" if d else "unavailable (no eligible observations)"


def analyse(record, corpus):
    raw, case = record["raw"], record["case"]
    if raw is None or raw.get("error"):
        status = "pending" if raw is None else "infra_error"
        return {**record, "status": status, "turn_checks": [], "checks": {
            name: CheckResult("skip", status) for name in CHECKS}}
    turns = raw.get("turns", [])
    checked = []
    for idx, turn in enumerate(turns):
        partial_case = {**case, "turns": case["turns"][:idx + 1]}
        checked.append(run_checks(turn.get("result", {}), partial_case, corpus, final_turn=idx == len(case["turns"]) - 1))
    if len(turns) != len(case["turns"]):
        checked.append({"check_contract": CheckResult("fail", "Not all requested turns were executed.")})
    combined = {}
    rank = {"skip": 0, "pass": 1, "warning": 2, "fail": 3}
    for name in CHECKS:
        values = [(n + 1, row[name]) for n, row in enumerate(checked) if name in row]
        worst = max((v.status for _, v in values), key=rank.get, default="skip")
        combined[name] = CheckResult(worst, " | ".join(f"turn {n}: {v.reason}" for n, v in values if v.status != "skip") or "unobservable")
    failed = any(v.status == "fail" for v in combined.values())
    judge_failed = any(t.get("judge", {}).get("assessment", {}).get("all_supported") is False for t in turns)
    return {**record, "status": "fail" if failed or judge_failed else "pass", "checks": combined,
            "turn_checks": checked, "judge_failed": judge_failed}


def failure_reasons(item):
    reasons = [f"{name}: {outcome.reason}" for name, outcome in item["checks"].items() if outcome.status == "fail"]
    if item.get("judge_failed"):
        reasons.append("llm_judge: unsupported final legal claim")
    return reasons


def severity(item):
    names = {n for n, c in item["checks"].items() if c.status == "fail"}
    critical = {"check_no_invented_law", "check_citations_valid", "check_legal_blocks_cited", "check_retrieval_scope"}
    missing_escalation = item["case"]["expect_needs_lawyer"] and "check_needs_lawyer" in names
    return 1 if names & critical or missing_escalation or item.get("judge_failed") else 2


def call_count(result):
    trace = result.get("trace", {})
    if not isinstance(trace, dict):
        return None
    value = next((trace[k] for k in ("llm_calls", "call_counts", "calls") if k in trace), None)
    if value is None and isinstance(trace.get("llm"), dict):
        value = trace["llm"].get("calls")
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    if isinstance(value, dict) and all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in value.values()):
        return sum(value.values())
    return None


def flaky_cases(analysed):
    by_case = defaultdict(list)
    for item in analysed:
        if item["status"] in {"pass", "fail"}:
            raw = item["raw"]
            outputs = [{k: turn.get("result", {}).get(k) for k in (
                "reply_text", "reply_lang", "category", "action", "citations", "needs_lawyer", "draft_text", "verifier")}
                       for turn in raw["turns"]]
            output_sig = hashlib.sha256(json.dumps(outputs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            outcome_sig = tuple((n, v.status) for n, v in item["checks"].items()) + (("judge_failed", item.get("judge_failed", False)),)
            by_case[item["case"]["id"]].append((output_sig, outcome_sig))
    return {cid: {"output_changed": len({v[0] for v in values}) > 1,
                  "checks_changed": len({v[1] for v in values}) > 1, "observations": len(values)}
            for cid, values in by_case.items() if len(values) > 1 and len(set(values)) > 1}


def metrics(items):
    completed = [i for i in items if i["status"] in {"pass", "fail"}]
    finals = [(i, i["raw"]["turns"][-1]["result"]) for i in completed if i["raw"]["turns"]]
    turn_pairs = [(i, t, c) for i in completed for t, c in zip(i["raw"]["turns"], i["turn_checks"]) if "result" in t]
    citation_n = sum(len(t["result"].get("citations", [])) for _, t, _ in turn_pairs)
    citation_valid = sum(sum(cid in {r.get("id") for r in t["result"].get("retrieved", []) if isinstance(r, dict)}
                             for cid in t["result"].get("citations", [])) for _, t, _ in turn_pairs)
    refusals = [(i, r) for i, r in finals if i["case"].get("refusal_expected")]
    escalation = [(i, r) for i, r in finals if i["case"]["expect_needs_lawyer"]]
    traps = [i for i in completed if i["case"]["group"].startswith(("D_", "F_"))]
    hits = [(i, r) for i, r in finals if i["case"].get("expected_chunk_ids")]
    counts = [call_count(t["result"]) for _, t, _ in turn_pairs]
    known_calls = [v for v in counts if v is not None]
    judged = [(t, t.get("judge", {}).get("assessment")) for _, t, _ in turn_pairs if t.get("judge", {}).get("assessment") is not None]
    claims = [c for _, assessment in judged for c in assessment["claims"]]
    code_flags = [any(c[n].status == "fail" for n in ("check_no_invented_law", "check_citations_valid", "check_legal_blocks_cited")) for _, _, c in turn_pairs]
    agreement = sum((not assessment["all_supported"]) == any(c[n].status == "fail" for n in ("check_no_invented_law", "check_citations_valid", "check_legal_blocks_cited"))
                    for _, t, c in turn_pairs if (assessment := t.get("judge", {}).get("assessment")) is not None)
    legal_blocks = [b for _, t, _ in turn_pairs for b in final_blocks(t["result"]) or [] if b.get("type") == "legal"]
    values = [
        ("Routing accuracy (final turn)", rate(sum(i["checks"]["check_routing"].status == "pass" for i in completed), len(completed))),
        ("Citation validity (cited IDs in retrieved set)", rate(citation_valid, citation_n)),
        ("Unsupported-claim rate (semantic, independent judge)", rate(sum(not c["supported"] for c in claims), len(claims))),
        ("Final-output citation/reference flags (code; not semantic support)", rate(sum(code_flags), len(code_flags))),
        ("Correct-refusal rate (safe action + lawyer flag)", rate(sum(r.get("action") in {"refuse_unverified", "escalate"} and r.get("needs_lawyer") is True for _, r in refusals), len(refusals))),
        ("Escalation recall (lawyer flag + visible referral)", rate(sum(i["checks"]["check_needs_lawyer"].status == "pass" for i, _ in escalation), len(escalation))),
        ("Trap pass rate (D/F, all checks)", rate(sum(i["status"] == "pass" for i in traps), len(traps))),
        ("Language match (all turns, metadata + best-effort detection)", rate(sum(c["check_language"].status == "pass" for _, _, c in turn_pairs), len(turn_pairs))),
        ("Retrieval hit rate (agent-mapped IDs; human review pending)", rate(sum(bool(set(i["case"]["expected_chunk_ids"]) & {x.get("id") for x in r.get("retrieved", [])}) for i, r in hits), len(hits))),
        ("Mean turn latency (includes optional judge)", f"{statistics.mean(t['latency_s'] for _, t, _ in turn_pairs):.4f} s" if turn_pairs else "unavailable"),
        ("App calls per turn (trace-reported)", f"{statistics.mean(known_calls):.2f}; observed {len(known_calls)}/{len(counts)} turns" if known_calls else "unavailable (trace does not expose counts)"),
        ("Additional independent judge calls", str(len(judged))),
        ("Judge/code flag agreement", rate(agreement, len(judged))),
        ("Final structured legal blocks observable", str(len(legal_blocks))),
    ]
    return values


def calibration_text(items, manifest):
    if manifest["stage"] != "real":
        return ("# Retrieval calibration\n\nNot performed: this is a " + manifest["stage"]
                + " run. Mock/sample scores cannot justify a production threshold.\n"
                "A validated real-corpus run must provide both answerable and unverifiable top-1 scores.\n")
    populations = {"answer": [], "refuse": []}
    skipped = Counter()
    for item in items:
        label = item["case"].get("calibration_label", "exclude")
        if label not in populations:
            continue
        if item["status"] not in {"pass", "fail"}:
            skipped["pending/infra"] += 1
            continue
        retrieved = item["raw"]["turns"][-1]["result"].get("retrieved", [])
        if not retrieved or not isinstance(retrieved[0].get("score"), (float, int)):
            skipped["no score (not imputed as zero)"] += 1
            continue
        populations[label].append((item["case"]["id"], float(retrieved[0]["score"])))
    lines = ["# Retrieval calibration", "", "Human decision required. Labels come from independent case intent; they are not inferred from app actions.",
             "Hard-routed out-of-scope and escalation cases are excluded: their bypassed retrieval cannot measure a gate.",
             f"Skipped observations: {dict(skipped)}. Repeats are correlated, not independent samples.", "", "| Population | n | min | median | max |", "|---|---:|---:|---:|---:|"]
    for label, data in populations.items():
        scores = [score for _, score in data]
        lines.append(f"| {label} | {len(scores)} | " + (f"{min(scores):.4f} | {statistics.median(scores):.4f} | {max(scores):.4f} |" if scores else "n/a | n/a | n/a |"))
    lines.extend(["", "```text", "Score histogram (cosine score bins; a count is one saved final turn)"])
    for label, data in populations.items():
        lines.append(label + ":")
        for k in range(10):
            lo, hi = -1 + k * .2, -1 + (k + 1) * .2
            n = sum(lo <= s < hi or k == 9 and s == hi for _, s in data)
            lines.append(f"  [{lo: .1f}, {hi: .1f}{']' if k == 9 else ')'} {'#' * n} {n}")
    lines.extend(["```", ""])
    good, bad = ([s for _, s in populations[label]] for label in ("answer", "refuse"))
    if not good or not bad:
        lines.append("No threshold recommendation: both populations are required. Do not tune the gate from this incomplete run.")
        return "\n".join(lines) + "\n"
    overlap_lo, overlap_hi = max(min(good), min(bad)), min(max(good), max(bad))
    lines.append(f"Observed score-range overlap: [{overlap_lo:.4f}, {overlap_hi:.4f}]." if overlap_lo <= overlap_hi else "Observed score ranges do not overlap; small samples are not proof of separation.")
    scores = sorted(set(good + bad))
    # Score the exact six-decimal values printed in the config recommendation.
    candidates = sorted(set([math.floor(scores[0] * 1e6) / 1e6,
                             (math.floor(scores[-1] * 1e6) + 1) / 1e6]
                            + [round((a + b) / 2, 6) for a, b in zip(scores, scores[1:])]))
    def errors(t):
        return sum(s < t for s in good) / len(good), sum(s >= t for s in bad) / len(bad)
    ranked = sorted(candidates, key=lambda t: (sum(errors(t)), errors(t)[1], t))
    best = ranked[0]
    frontier = [t for t in candidates if not any(
        errors(other)[0] <= errors(t)[0] and errors(other)[1] <= errors(t)[1]
        and errors(other) != errors(t) for other in candidates)]
    unique_frontier = {}
    for threshold in frontier:
        unique_frontier.setdefault(errors(threshold), threshold)
    frontier = sorted(unique_frontier.values())
    choices = sorted(set([frontier[0], best, frontier[-1]]))
    if len(choices) == 1:
        choices = sorted(set(choices + sorted((t for t in candidates if t != best), key=lambda t: abs(t - best))[:2]))
    lines += ["", "Gate refuses when top score < threshold. Candidate errors below are in-sample estimates, not validation guarantees.",
              "", "| Candidate min_score | Good cases wrongly refused | Bad cases slipping through |", "|---:|---:|---:|"]
    for threshold in choices:
        false_refuse, false_allow = errors(threshold)
        lines.append(f"| {threshold:.6f} | {false_refuse:.1%} | {false_allow:.1%} |")
    lines += ["", f"Provisional recommendation: retrieval.min_score={best:.6f} (lowest balanced in-sample error; ties prioritise rejecting bad cases).",
              "Candidates span non-dominated acceptance/refusal tradeoffs where available, rather than only neighbouring thresholds. The printed values themselves were scored.",
              "The human must confirm law expectations, choose the tradeoff and validate on new cases. High topic similarity cannot establish legal support; keep the verifier and refusal paths.",
              "", "Observed case scores:", ""]
    lines += [f"- {label}: {cid}: {score:.6f}" for label, data in populations.items() for cid, score in data]
    return "\n".join(lines) + "\n"


def write_bug_report(root, items, manifest, run_dir):
    if manifest["stage"] == "fixture_mock":
        return  # Canned fixture failures are not app bugs.
    lines = ["# Evaluation bugs", "", f"Generated from {run_dir}. Stage: {manifest['stage']}.",
             ("Real-corpus run only. Historical mock findings are excluded. No failed expectation has been weakened to hide a failure."
              if manifest["stage"] == "real" else "MOCK/SAMPLE ONLY: these findings do not establish real-model behaviour."), ""]
    failures = sorted([i for i in items if i["status"] == "fail"], key=lambda i: (severity(i), i["case"]["id"], i["repeat"]))
    layer_map = {"check_routing": "router", "check_action": "gate/router/draft", "check_citations_valid": "retrieval/verifier",
                 "check_no_invented_law": "answer prompt/verifier", "check_retrieval_scope": "router/retrieval", "check_needs_lawyer": "escalation",
                 "check_draft_placeholders": "draft", "check_language": "router/rendering"}
    for item in failures:
        lines += [f"## Severity {severity(item)}: {item['case']['id']} (repeat {item['repeat']})", "",
                  f"Raw evidence: {item['path']}", "", "Observed visible output:", ""]
        for n, turn in enumerate(item["raw"]["turns"], 1):
            text = visible_text(turn.get("result", {}))
            lines += [f"Turn {n}:", "", *("> " + part for part in text.splitlines()), ""]
        lines += [f"Expected: category={item['case']['category_expected']}; action={item['case']['expected_action']}; "
                  f"needs_lawyer={item['case']['expect_needs_lawyer']}. {item['case']['notes']}", "",
                  *[f"- {reason}" for reason in failure_reasons(item)], "",
                  "Likely layers: " + ", ".join(sorted({layer_map.get(n, "answer/verifier") for n, c in item["checks"].items() if c.status == "fail"})), ""]
    if not failures:
        if not any(i["status"] in {"pass", "fail"} for i in items):
            lines += ["No model-evaluable cases completed; no app-quality conclusions are available.", ""]
        else:
            lines += ["No deterministic hard failures observed. This does not prove semantic faithfulness.", ""]
    infra = [i for i in items if i["status"] == "infra_error"]
    pending = [i for i in items if i["status"] == "pending"]
    lines += ["## Infrastructure and incomplete coverage", "",
              f"Infrastructure errors: {len(infra)}; unattempted case-runs: {len(pending)}.", ""]
    lines += [f"- {i['case']['id']}: {i['raw'].get('error')}; raw: {i['path']}" for i in infra]
    warnings = [(i, name, c) for i in items for name, c in i["checks"].items() if c.status == "warning"]
    lines += ["## Findings requiring review", ""] + [f"- {i['case']['id']} repeat {i['repeat']}, {name}: {c.reason}" for i, name, c in warnings]
    text = "\n".join(lines) + "\n"
    (run_dir / "BUGS.md").write_text(text, encoding="utf-8")
    if manifest["stage"] == "real":
        (root / "tests/BUGS.md").write_text(text, encoding="utf-8")


def write_reports(run_dir: Path, manifest: dict, records: list, corpus: dict):
    items = [analyse(r, corpus) for r in records]
    counts = Counter(i["status"] for i in items)
    fields = ["case_id", "group", "repeat", "status", "overall_pass", "raw_file", "infra_error"]
    fields += [field for name in CHECKS for field in (name, name + "_reason")]
    with (run_dir / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in items:
            row = {"case_id": item["case"]["id"], "group": item["case"]["group"], "repeat": item["repeat"],
                   "status": item["status"], "overall_pass": item["status"] == "pass", "raw_file": str(item["path"] or ""),
                   "infra_error": json.dumps(item["raw"].get("error"), ensure_ascii=False) if item["raw"] and item["raw"].get("error") else ""}
            for name, outcome in item["checks"].items():
                row[name], row[name + "_reason"] = outcome.status, outcome.reason
            writer.writerow(row)
    groups = defaultdict(Counter)
    for item in items:
        groups[item["case"]["group"]][item["status"]] += 1
    lines = ["# Evaluation summary", "", f"Stage: **{manifest['stage']}**. Backend: `{manifest['backend']}`.",
             "**Mock results do not measure app/legal quality and never count as graded raw outputs.**" if manifest["mock"] else "Only a full real-corpus run is gradeable; sample runs are development checks.",
             "", f"Selected case-runs: {len(items)}; passed: {counts['pass']}; failed: {counts['fail']}; "
             f"infra_error: {counts['infra_error']}; pending: {counts['pending']}.",
             "A pass means no observed hard failure. Warnings and unavailable checks remain open for review.",
             "Infra errors and pending cases are excluded from model metrics. Safety checks include every completed turn, not just the last reply.",
             "", "| Metric | Result |", "|---|---|"]
    lines += [f"| {name} | {value} |" for name, value in metrics(items)]
    lines += ["", "Citation membership is not proof of entailment. No-citation answers have no citation denominator, rather than an invented 100% score.",
              "Without the optional independent judge, semantic unsupported-claim rate is unavailable. Code flags are a narrower audit.",
              "Retrieval hit rate uses agent-mapped expected_chunk_ids, pending human confirmation. Referral targets and substantive-topic targets are identified in the cases; expected_topics text is not silently scored.",
              "", "| Group | Pass | Fail | Infra error | Pending |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {g} | {c['pass']} | {c['fail']} | {c['infra_error']} | {c['pending']} |" for g, c in sorted(groups.items())]
    lines += ["", "## Failure list", ""]
    failures = sorted([i for i in items if i["status"] == "fail"], key=lambda i: (severity(i), i["case"]["id"], i["repeat"]))
    lines += [f"- S{severity(i)} {i['case']['id']} repeat {i['repeat']}: " + "; ".join(failure_reasons(i)) for i in failures] or ["No hard failures observed."]
    lines += ["", "## Infrastructure and unfinished cases", ""]
    lines += [f"- {i['case']['id']} repeat {i['repeat']}: {i['status']}; {i['raw'].get('error') if i['raw'] else 'not attempted'}" for i in items if i["status"] in {"infra_error", "pending"}] or ["None."]
    flaky = flaky_cases(items)
    lines += ["", "## Repeated-run variation", ""]
    lines += [f"- {cid}: output_changed={v['output_changed']}; checks_changed={v['checks_changed']}; {v['observations']} observations." for cid, v in sorted(flaky.items())] or ["None observed." if manifest["runs"] > 1 else "Not measured: only one run requested."]
    lines += ["", "## Warnings and limits", ""]
    lines += [f"- {i['case']['id']} repeat {i['repeat']}, {name}: {outcome.reason}" for i in items for name, outcome in i["checks"].items() if outcome.status == "warning"]
    lines += ["", "All unverified law expectations require human review. Five voice inputs are text transcripts: no STT, microphone or TTS quality is tested.",
              "Numbers written as words, implicit legal claims, negation and template-specific facts require review. Language uses optional langdetect or en/hi script checks.",
              "Optional judge results are model assessments, not legal verification. Raw TurnResult fields, including trace, are retained without editing.",
              "Resume skips saved files; --retry-infra appends attempts. Start a fresh run after any app, config, corpus, case or checker change."]
    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run_dir / "calibration.md").write_text(calibration_text(items, manifest), encoding="utf-8")
    write_bug_report(run_dir.parents[2], items, manifest, run_dir)
    return {"passed": counts["pass"], "failed": counts["fail"], "infra_errors": counts["infra_error"], "pending": counts["pending"], "flaky": flaky}
