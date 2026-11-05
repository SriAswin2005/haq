# Test expectation changes

- 2026-11-05: T-025 input mode changed from text to synthetic voice transcript after the case-count audit found only four voice cases; no pass/fail expectation changed.
- 2026-11-05: Corrected T-013/T-014/T-030 expected_action from escalate to answer and removed refusal_expected: architecture sections 6/9 allow verified general information with a lawyer referral for limitation risk, high amount and an uncovered state. The lawyer expectation remains true. This fixes an overstrict test interpretation; missing referrals still fail, and both earlier raw runs are preserved.
- 2026-11-05: Added independent jurisdiction metadata (UP cases allow central/UP; Karnataka case allows central only) and a retrieval-scope check. Tightened Hindi script detection after raw inspection showed that a Hindi greeting concealed an otherwise English answer; expectations still require the user's language.

- 2026-11-05 (round 2): Mapped expected_chunk_ids for all 30 cases to actual in-force corpus chunks, retaining expected_law_verified=false. Added topic versus safe_referral labels and tests/CHUNK_MAPPING.md; no category/action/content/legal expectation was changed. Retrieval targets are alternatives and have not been human-confirmed.
- 2026-11-05 (round 2): Regenerate tests/BUGS.md only from real runs; mock/sample findings stay in their run archive. Recognise new provider-fallback network/budget errors as infrastructure rather than model failures.

- 2026-11-05 (round 2 real review): Fixed a checker false positive for a long negated guarantee and a false pass where generic source-review language concealed conflicting dates. Added regressions; no case expectation changed. An offline rescore of the 122-chunk captures is stored in check_revision_review.json, with raw hashes unchanged and zero additional API calls.
- 2026-11-05 (round 2 calibration): Candidate thresholds now cover non-dominated acceptance/refusal tradeoffs, and error rates are computed at the exact six-decimal values printed for config.

- 2026-11-06: Published the completed frozen 119-chunk real run real-20261105T161021.563148Z. All 30 expected-law flags remain false. Current real_findings.jsonl contains only the date-conflict finding reproduced in this run; the earlier interest-claim finding is preserved in the pre-fix run's agent_review.json and is not carried forward as a current failure.
- 2026-11-06: Added snapshot execution/collection and source-checked review tooling. The final capture has 30 unchanged raw files / 33 turns, with no additional API calls for collection or review.

- 2026-11-06 (round 3): Added T-031..T-040 as requested; original 30 case dictionaries are unchanged. All 40 expected_law_verified flags remain false. Added translation token/script and amount-conflict guards that activate only for the new requirements. T-033 expects answer per the new instruction, while the old T-001 refusal expectation is retained for baseline comparability.
