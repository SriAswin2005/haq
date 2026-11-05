"""Attach source-checked agent observations to a completed real bug report.

This performs no API calls and does not alter raw captures or numeric metrics.
Every quoted reply/source/input is validated against that run's own snapshot.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.run_eval import latest_record, utc_now, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to((ROOT / "outputs/runs").resolve()):
        raise ValueError("Run must stay within outputs/runs")
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    completion = json.loads((run / "completion.json").read_text(encoding="utf-8"))
    if manifest["stage"] != "real" or manifest["mock"] or completion["pending"] or completion["infra_errors"]:
        raise ValueError("Review requires a completed real run without pending/infra cases")
    corpus = json.loads((run / "corpus_snapshot.json").read_text(encoding="utf-8"))
    findings = [json.loads(line) for line in args.findings.read_text(encoding="utf-8").splitlines() if line.strip()]
    lines = ["## Agent review of real-source applicability", "",
             "These are targeted comparisons with this run's raw replies and corpus snapshot. Human legal confirmation is pending. "
             "They are not an exhaustive semantic audit and do not change the deterministic metrics.", ""]
    for finding in sorted(findings, key=lambda f: (f["severity"], f["case_id"])):
        raw, path = latest_record(run / "raw", finding["case_id"])
        if raw is None or raw.get("error"):
            raise ValueError("Missing evaluable raw case " + finding["case_id"])
        final = raw["turns"][-1]["result"]
        visible = final["reply_text"] + "\n" + (final.get("draft_text") or "")
        if finding["reply_excerpt"] not in visible:
            raise ValueError("Reply quote not present for " + finding["case_id"])
        lines += [f"### Severity {finding['severity']}: {finding['case_id']} — {finding['title']}", "",
                  f"Raw evidence: {path}", "", "> " + finding["reply_excerpt"], ""]
        cid = finding.get("source_chunk_id")
        if cid:
            if cid not in final["citations"] or finding["source_excerpt"] not in corpus[cid]["text"]:
                raise ValueError("Source/citation quote not supported for " + finding["case_id"])
            lines += [f"Cited source `{cid}` ({corpus[cid]['heading']}):", "", "> " + finding["source_excerpt"], ""]
        if finding.get("input_excerpt"):
            if finding["input_excerpt"] not in "\n".join(raw["case"]["turns"]):
                raise ValueError("Input quote not present for " + finding["case_id"])
            lines += ["User input:", "", "> " + finding["input_excerpt"], ""]
        lines += [finding["finding"], "", "Expected: " + finding["expected"], "",
                  "Likely layers: " + finding["layer"], ""]
    base_path = run / "BUGS_automated.md"
    base = (base_path if base_path.exists() else run / "BUGS.md").read_text(encoding="utf-8")
    if str(run) not in base:
        raise ValueError("Bug report does not belong to selected run")
    # Preserve the generated checker report, then insert the real-source review
    # before the automated failure list. Never open a raw file for writing.
    if not base_path.exists():
        base_path.write_text(base, encoding="utf-8")
    first_severity = min((f["severity"] for f in findings), default=2)
    separator = f"\n## Severity {first_severity}:"
    at = base.find(separator)
    if at == -1:
        at = base.find("\n## Infrastructure")
    if at == -1:
        at = len(base)
    combined = base[:at] + "\n" + "\n".join(lines) + "\n" + base[at:]
    frozen = run / "frozen_inputs.json"
    if frozen.exists():
        revision = json.loads(frozen.read_text(encoding="utf-8"))
        notice = (f"Evaluated frozen inputs captured at {revision['frozen_at']}. "
                  "The manifest and frozen_inputs.json identify the tested revision; subsequent checkout edits are outside this report.\n")
        combined = combined.replace("# Evaluation bugs\n", "# Evaluation bugs\n\n" + notice, 1)
    (run / "BUGS.md").write_text(combined, encoding="utf-8")
    (ROOT / "tests/BUGS.md").write_text(combined, encoding="utf-8")
    write_json(run / "agent_review.json", {"reviewed_at": utc_now(), "source": str(args.findings),
               "human_verified": False, "additional_api_calls": 0, "findings": findings})
    print(f"Attached {len(findings)} source-checked real observations; raw outputs and metrics unchanged.")


if __name__ == "__main__":
    main()
