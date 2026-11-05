# Evaluation summary

Stage: **sample**. Backend: `app.pipeline`.
Only a full real-corpus run is gradeable; sample runs are development checks.

Selected case-runs: 30; passed: 0; failed: 0; infra_error: 1; pending: 29.
A pass means no observed hard failure. Warnings and unavailable checks remain open for review.
Infra errors and pending cases are excluded from model metrics. Safety checks include every completed turn, not just the last reply.

| Metric | Result |
|---|---|
| Routing accuracy (final turn) | unavailable (no eligible observations) |
| Citation validity (cited IDs in retrieved set) | unavailable (no eligible observations) |
| Unsupported-claim rate (semantic, independent judge) | unavailable (no eligible observations) |
| Final-output citation/reference flags (code; not semantic support) | unavailable (no eligible observations) |
| Correct-refusal rate (safe action + lawyer flag) | unavailable (no eligible observations) |
| Escalation recall (lawyer flag + visible referral) | unavailable (no eligible observations) |
| Trap pass rate (D/F, all checks) | unavailable (no eligible observations) |
| Language match (all turns, metadata + best-effort detection) | unavailable (no eligible observations) |
| Retrieval hit rate (human-mapped expected IDs) | unavailable (no eligible observations) |
| Mean turn latency (includes optional judge) | unavailable |
| App calls per turn (trace-reported) | unavailable (trace does not expose counts) |
| Additional independent judge calls | 0 |
| Judge/code flag agreement | unavailable (no eligible observations) |
| Final structured legal blocks observable | 0 |

Citation membership is not proof of entailment. No-citation answers have no citation denominator, rather than an invented 100% score.
Without the optional independent judge, semantic unsupported-claim rate is unavailable. Code flags are a narrower audit.
Retrieval hit rate is unavailable until expected_chunk_ids are human-mapped; expected_topics text is not silently treated as a scored hit.

| Group | Pass | Fail | Infra error | Pending |
|---|---:|---:|---:|---:|
| A_happy_path | 0 | 0 | 0 | 7 |
| B_messy_input | 0 | 0 | 0 | 3 |
| C_out_of_scope | 0 | 0 | 0 | 5 |
| D_hallucination_traps | 0 | 0 | 1 | 6 |
| F_prompt_injection | 0 | 0 | 0 | 3 |
| G_escalation | 0 | 0 | 0 | 5 |

## Failure list

No hard failures observed.

## Infrastructure and unfinished cases

- T-001 repeat 1: infra_error; {'type': 'AppHandledAPIError', 'message': 'missing environment variable GEMINI_API_KEY', 'status_code': None, 'source': 'TurnResult.trace/verifier'}
- T-002 repeat 1: pending; not attempted
- T-003 repeat 1: pending; not attempted
- T-004 repeat 1: pending; not attempted
- T-005 repeat 1: pending; not attempted
- T-006 repeat 1: pending; not attempted
- T-007 repeat 1: pending; not attempted
- T-008 repeat 1: pending; not attempted
- T-009 repeat 1: pending; not attempted
- T-010 repeat 1: pending; not attempted
- T-011 repeat 1: pending; not attempted
- T-012 repeat 1: pending; not attempted
- T-013 repeat 1: pending; not attempted
- T-014 repeat 1: pending; not attempted
- T-015 repeat 1: pending; not attempted
- T-016 repeat 1: pending; not attempted
- T-017 repeat 1: pending; not attempted
- T-018 repeat 1: pending; not attempted
- T-019 repeat 1: pending; not attempted
- T-020 repeat 1: pending; not attempted
- T-021 repeat 1: pending; not attempted
- T-022 repeat 1: pending; not attempted
- T-023 repeat 1: pending; not attempted
- T-024 repeat 1: pending; not attempted
- T-025 repeat 1: pending; not attempted
- T-026 repeat 1: pending; not attempted
- T-027 repeat 1: pending; not attempted
- T-028 repeat 1: pending; not attempted
- T-029 repeat 1: pending; not attempted
- T-030 repeat 1: pending; not attempted

## Repeated-run variation

Not measured: only one run requested.

## Warnings and limits


All unverified law expectations require human review. Five voice inputs are text transcripts: no STT, microphone or TTS quality is tested.
Numbers written as words, implicit legal claims, negation and template-specific facts require review. Language uses optional langdetect or en/hi script checks.
Optional judge results are model assessments, not legal verification. Raw TurnResult fields, including trace, are retained without editing.
Resume skips saved files; --retry-infra appends attempts. Start a fresh run after any app, config, corpus, case or checker change.
