"""Apply the user's consumer-service correction, preserving inputs and body IDs."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.add_round4_cases import build_cases
from tests.run_eval import digest, utc_now, write_json


def main():
    path = ROOT / "tests/cases.jsonl"
    old = path.read_bytes()
    lines = old.splitlines(keepends=True)
    cases = [json.loads(line) for line in old.decode("utf-8-sig").splitlines() if line.strip()]
    if len(cases) != 55:
        raise ValueError("Expected exactly 55 cases")
    replacements = build_cases()
    allowed = {"category_expected", "expected_action", "expect_needs_lawyer", "expected_outcomes", "notes"}
    deltas = []
    for before, after in zip(cases[40:], replacements):
        keys = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
        if keys - allowed:
            raise ValueError("Unexpected input/allowlist change: " + before["id"])
        if keys:
            deltas.append({"case_id": before["id"], "before": {k: before.get(k) for k in sorted(keys)},
                           "after": {k: after.get(k) for k in sorted(keys)}})
    if not deltas:
        print("Consumer-service expectations already current.")
        return
    before_hash = digest(path)
    prefix = b"".join(lines[:40])
    path.write_bytes(prefix + "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in replacements).encode("utf-8"))
    assert path.read_bytes().startswith(prefix)
    write_json(ROOT / "tests/round4_expectations_revision.json", {"revised_at": utc_now(),
        "authorization": "Explicit user correction of round-four consumer-service routing and scope-aware statute checks.",
        "cases_before_sha256": before_hash, "cases_after_sha256": digest(path),
        "original_40_case_bytes_preserved": True, "all_inputs_and_body_allowlists_unchanged": True, "deltas": deltas})
    print("Revised seven consumer-service outcomes and scope notes; original 40 case bytes, all inputs and body allowlists preserved.")


if __name__ == "__main__":
    main()
