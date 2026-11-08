#!/usr/bin/env python3
"""
validate_corpus.py

Validates all JSONL files in data/corpus/ against the data contract defined in
00_ARCHITECTURE.md (Section 5) and 02_ANTIGRAVITY_CORPUS.md.

Exits with code 0 on success, non-zero on failure.
"""

import os
import sys
import json
import re
from pathlib import Path

# Required fields in each chunk
REQUIRED_FIELDS = [
    "id",
    "category",
    "doc_title",
    "doc_type",
    "jurisdiction",
    "unit",
    "unit_number",
    "heading",
    "text",
    "status",
    "status_note",
    "effective_from",
    "source_url",
    "source_type",
    "fetched_on",
    "verified",
    "human_check_required",
    "language",
]

ALLOWED_CATEGORIES = {
    "consumer",
    "wages",
    "tenancy",
    "common",
    "rights",
    "criminal",
    "family",
    "civic",
    "money",
    "property",
}
ALLOWED_DOC_TYPES = {
    "statute",
    "rule",
    "govt_guidance",
    "portal_procedure",
    "helpline",
    "judgment",
}
ALLOWED_STATUSES = {
    "in_force",
    "repealed",
    "superseded",
    "not_yet_in_force",
    "model_only",
    "unclear",
}
ALLOWED_SOURCE_TYPES = {"official", "secondary"}
ALLOWED_VERIFIED = {"agent", "human"}

# Regex for ID: {CAT}-{ACTCODE}-{UNITLETTER}{NUMBER}(optional subchunk)
# CAT: CONS, WAGE, TEN, COM, RGT, CRM, FAM, CIV, MON, PRP
# UNITLETTER: S, R, O, P, J, H, A, L, or COM-DIR-{SHORTNAME} for grievance directory
ID_PATTERN = re.compile(
    r"^((CONS|WAGE|TEN|COM|RGT|CRM|FAM|CIV|MON|PRP)-[A-Z0-9]+-[SROPJHAL][A-Za-z0-9_-]+|COM-DIR-[A-Za-z0-9_-]+)$"
)

# Pattern for numbers/deadlines/money that trigger human_check_required
# digits followed by words like days, months, years, rupees, lakh, crore, or %
NUM_TRIGGER_PATTERN = re.compile(
    r"(\d+\s*(days?|months?|years?|rupees?|rs\.?|lakh|crore|percent|%|\/[-]))|(₹\s*\d+)",
    re.IGNORECASE,
)

FILE_CATEGORY_MAP = {
    "consumer": "consumer",
    "wages": "wages",
    "tenancy": "tenancy",
    "common": "common",
    "directory": "common",
    "rights": "rights",
    "criminal": "criminal",
    "family": "family",
    "civic": "civic",
    "money": "money",
    "property": "property",
}


def validate_file(file_path: Path, seen_ids: set) -> list[str]:
    errors = []
    file_stem = file_path.stem

    if file_stem not in FILE_CATEGORY_MAP:
        errors.append(f"Filename {file_path.name} does not match allowed corpus files {list(FILE_CATEGORY_MAP.keys())}")
        return errors

    expected_category = FILE_CATEGORY_MAP[file_stem]

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue

            try:
                chunk = json.loads(line_str)
            except Exception as e:
                errors.append(f"{file_path.name}:{line_num}: JSON decode error: {e}")
                continue

            chunk_id = chunk.get("id")

            # Check required fields
            for rf in REQUIRED_FIELDS:
                if rf not in chunk:
                    errors.append(f"{file_path.name}:{line_num} ({chunk_id}): missing required field '{rf}'")

            if not chunk_id:
                errors.append(f"{file_path.name}:{line_num}: missing 'id'")
                continue

            # ID format
            if not ID_PATTERN.match(chunk_id):
                errors.append(
                    f"{file_path.name}:{line_num} ({chunk_id}): ID does not match contract format {{CAT}}-{{ACTCODE}}-{{UNITLETTER}}{{NUMBER}}"
                )

            # ID uniqueness
            if chunk_id in seen_ids:
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): duplicate ID")
            seen_ids.add(chunk_id)

            # Category
            cat = chunk.get("category")
            if cat != expected_category:
                errors.append(
                    f"{file_path.name}:{line_num} ({chunk_id}): category '{cat}' does not match expected category '{expected_category}'"
                )
            if cat not in ALLOWED_CATEGORIES:
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): invalid category '{cat}'")

            # doc_type
            dt = chunk.get("doc_type")
            if dt not in ALLOWED_DOC_TYPES:
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): invalid doc_type '{dt}'")

            # status
            st = chunk.get("status")
            if st not in ALLOWED_STATUSES:
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): invalid status '{st}'")

            # source_type
            stype = chunk.get("source_type")
            if stype not in ALLOWED_SOURCE_TYPES:
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): invalid source_type '{stype}'")

            # verified
            ver = chunk.get("verified")
            if ver not in ALLOWED_VERIFIED:
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): invalid verified '{ver}'")
            if ver == "human":
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): agent must not set verified to 'human'")

            # language
            if chunk.get("language") != "en":
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): language must be 'en' in v1")

            # text must be non-empty string
            txt = chunk.get("text", "")
            if not isinstance(txt, str) or not txt.strip():
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): 'text' is empty or not string")

            # source_url must be present
            url = chunk.get("source_url", "")
            if not isinstance(url, str) or not url.startswith("http"):
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): 'source_url' must be valid http(s) URL")

            # human_check_required rules:
            # 1. Any secondary source must have human_check_required: true
            # 2. Any helpline must have human_check_required: true
            # 3. Any chunk containing digits followed by days/months/years/rupees/lakh/crore/% must have human_check_required: true
            hcr = chunk.get("human_check_required")
            if not isinstance(hcr, bool):
                errors.append(f"{file_path.name}:{line_num} ({chunk_id}): 'human_check_required' must be boolean")
            else:
                if stype == "secondary" and not hcr:
                    errors.append(
                        f"{file_path.name}:{line_num} ({chunk_id}): secondary source requires human_check_required: true"
                    )
                if (
                    dt == "helpline"
                    or chunk.get("unit") == "helpline"
                    or bool(re.search(r"-[A-Z0-9]+-H[A-Za-z0-9_]+", chunk_id))
                ) and not hcr:
                    errors.append(
                        f"{file_path.name}:{line_num} ({chunk_id}): helpline chunk requires human_check_required: true"
                    )
                if NUM_TRIGGER_PATTERN.search(txt) and not hcr:
                    errors.append(
                        f"{file_path.name}:{line_num} ({chunk_id}): text contains money/deadline/number trigger but human_check_required is false"
                    )

    return errors


def main():
    repo_root = Path(__file__).resolve().parent.parent
    corpus_dir = repo_root / "data" / "corpus"

    if not corpus_dir.exists():
        print(f"ERROR: corpus directory {corpus_dir} does not exist.")
        sys.exit(1)

    jsonl_files = sorted(corpus_dir.glob("*.jsonl"))
    if not jsonl_files:
        print(f"ERROR: no jsonl files found in {corpus_dir}.")
        sys.exit(1)

    all_errors = []
    seen_ids = set()
    total_chunks = 0

    print(f"Validating corpus in {corpus_dir}...")
    for jf in jsonl_files:
        errs = validate_file(jf, seen_ids)
        file_chunk_count = sum(1 for line in open(jf, "r", encoding="utf-8") if line.strip())
        total_chunks += file_chunk_count
        if errs:
            print(f"FAIL: {jf.name} ({file_chunk_count} chunks, {len(errs)} errors)")
            for e in errs[:10]:
                print(f"  - {e}")
            if len(errs) > 10:
                print(f"  ... and {len(errs) - 10} more errors")
            all_errors.extend(errs)
        else:
            print(f"PASS: {jf.name} ({file_chunk_count} chunks)")

    print("-" * 50)
    print(f"Total chunks checked: {total_chunks}")
    print(f"Total unique IDs: {len(seen_ids)}")

    if all_errors:
        print(f"Validation FAILED with {len(all_errors)} total error(s).")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()
