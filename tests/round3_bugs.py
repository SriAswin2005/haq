"""Attach trace-proven interface/observability bugs to the real-run report."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.run_eval import latest_record, utc_now, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to((ROOT / "outputs/runs").resolve()):
        raise ValueError("Select a canonical run archive")
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    done = json.loads((run / "completion.json").read_text(encoding="utf-8"))
    if manifest["mock"] or manifest["stage"] != "real" or done["pending"] or done["infra_errors"]:
        raise ValueError("Select a complete real run")
    enum_cases, translation_cases, non_english_originals = [], [], []
    for cid in manifest["case_ids"]:
        raw, path = latest_record(run / "raw", cid)
        for number, turn in enumerate(raw["turns"], 1):
            result, trace = turn["result"], turn["result"].get("trace", {})
            if result.get("verifier", {}).get("status") == "pruned":
                enum_cases.append({"case_id": cid, "turn": number, "path": str(path),
                                   "action": result.get("action"), "pruned": trace.get("pruned")})
            translation = trace.get("translation", {})
            models = trace.get("llm", {}).get("models", [])
            if translation.get("status") == "ok" and not any(isinstance(m, str) and m.startswith("translate:") for m in models):
                translation_cases.append({"case_id": cid, "turn": number, "path": str(path),
                                          "translation_attempts": translation.get("attempts"),
                                          "recorded_models": models, "recorded_calls": trace.get("llm", {}).get("calls")})
            original = translation.get("english_original", "")
            native_letters = len(re.findall(r"[\u0900-\u097f\u0b80-\u0bff\u0c00-\u0c7f]", original))
            latin_letters = len(re.findall(r"[A-Za-z]", original))
            if translation.get("status") == "ok" and native_letters > latin_letters:
                non_english_originals.append({"case_id": cid, "turn": number, "path": str(path),
                    "native_letters": native_letters, "latin_letters": latin_letters,
                    "identical_to_final": original == result.get("reply_text")})
    notes = []
    if enum_cases:
        notes += ["## Severity 2: Public verifier enum disagrees with the frozen interface", "",
                  "Observed: `verifier.status=pruned`. Section 7 of 00_ARCHITECTURE.md lists only pass/fixed/failed. "
                  "The legal answer can be successfully pruned while the public result still fails the existing interface check. "
                  "Do not confuse this schema disagreement with proof of an unsafe surviving claim.", "",
                  "Expected: preserve trace.pruned and return a contract-compatible recovery status, or have the owner explicitly revise the frozen interface. "
                  "Likely layer: pipeline result assembly.", ""]
        notes += [f"- {r['case_id']} turn {r['turn']}: action={r['action']}; raw: {r['path']}" for r in enum_cases]
        notes += [""]
    if translation_cases:
        notes += ["## Severity 2: Successful translation lacks served-model/call provenance", "",
                  "Observed: trace.translation.status=ok, but trace.llm.models has no translate-role entry. "
                  "The reported statistics cannot identify the translator or account completely for its calls. "
                  "The English pipeline statistics are captured before final translation in the evaluated code.", "",
                  "Expected: snapshot final timing/call/model statistics after translation while preserving the English original. "
                  "Likely layer: pipeline trace assembly. Performance reporting must label these fields as unavailable or incomplete instead of inferring a model from config.", ""]
        notes += [f"- {r['case_id']} turn {r['turn']}: translation attempts={r['translation_attempts']}, trace calls={r['recorded_calls']}; raw: {r['path']}" for r in translation_cases]
        notes += [""]
    if non_english_originals:
        notes += ["## Severity 2: Saved English-original translation evidence is already in the target script", "",
                  "Observed: trace.translation.english_original is predominantly Telugu in T-031 and is byte-identical to the final reply text. "
                  "The pipeline stores its pre-translation text under an English-original label without enforcing that the core answer is English. "
                  "The requested number/link/script checks pass, but the saved payload cannot demonstrate English-to-Telugu fidelity. "
                  "The deterministic token check validates retained tokens and field presence; it does not independently identify the original's language.", "",
                  "Expected: preserve an actual verified English original when that is the translation design, or label the source language accurately. "
                  "Likely layer: answer-language enforcement / translation trace assembly.", ""]
        notes += [f"- {r['case_id']} turn {r['turn']}: native-script characters={r['native_letters']}, Latin letters={r['latin_letters']}, identical to final={r['identical_to_final']}; raw: {r['path']}" for r in non_english_originals]
        notes += [""]
    original = run / "BUGS_checks_only.md"
    if not original.exists():
        original.write_bytes((run / "BUGS.md").read_bytes())
    base = original.read_text(encoding="utf-8")
    if str(run) not in base:
        raise ValueError("BUGS.md belongs to another run")
    at = base.find("\n## Severity 2:")
    if at == -1:
        at = base.find("\n## Infrastructure")
    if at == -1:
        at = len(base)
    text = base[:at] + "\n" + "\n".join(notes) + "\n" + base[at:]
    frozen = json.loads((run / "frozen_inputs.json").read_text(encoding="utf-8"))
    context = (f"Evaluated frozen inputs: {frozen['frozen_at']}. Later checkout edits are outside this report.\n\n"
               "Scoring context: the original T-001 refusal expectation is deliberately retained, while the new T-033 explicitly expects an answer with a no-cases line and referral. "
               "An action-only mismatch on that legacy case is not evidence that useful advice is a new app defect. Lexical alternatives and the frozen verifier enum are also reported unchanged; the trace notes below distinguish these from unsafe legal claims.\n")
    text = text.replace("# Evaluation bugs\n", "# Evaluation bugs\n\n" + context, 1)
    (run / "BUGS_automated.md").write_text(text, encoding="utf-8")
    (run / "BUGS.md").write_text(text, encoding="utf-8")
    (ROOT / "tests/BUGS.md").write_text(text, encoding="utf-8")
    write_json(run / "round3_trace_bugs.json", {"generated_at": utc_now(), "enum_observations": enum_cases,
               "translation_observations": translation_cases, "non_english_original_observations": non_english_originals,
               "additional_api_calls": 0})
    print(f"Attached trace-proven notes: {len(enum_cases)} enum observations, {len(translation_cases)} translation observations.")


if __name__ == "__main__":
    main()
