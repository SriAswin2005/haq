# Before / after — corrected checks, fresh full real eval

Last run: `real-20261106T150609.600967Z`. Fresh run: `real-20261106T172240.218881Z`.
Fresh app/config/corpus: commit `a1c98ccc81c18e542985922d8c569bc40847e532`, captured at 2026-11-06T17:22:39.907587+00:00. Parallel working-tree edits were preserved and excluded. The current corrected tests were copied separately. All T-001..T-055 ran once with six-second spacing and no extra `--judge`.

| Scoring view | Strict case passes |
|---|---:|
| Last run as published | 37/55 |
| Same last-run replies, corrected checks/expectations | 39/55 |
| Fresh real run, same corrected checks/expectations | 42/55 |

The model/revision comparison below uses the rescored baseline, so test-rule changes are not presented as product improvements. Original raw files and published last-run scores are untouched. The offline rescore made zero API calls; its evidence is under `rescores\policy-v2-20261106T174935.099507Z`.

Post-capture validation corrected sentence-ending URL punctuation and two duplicate-body recognitions (IRDAI's qualified internal department and the Hindi District Commission label). Both datasets use identical final checks. The fresh original scoring (40/55) is preserved in scoring-original/; final scoring is 42/55. All rescoring uses unchanged replies and zero extra API calls.

## Matched full-run metrics

| Metric | Last run rescored | Fresh run | Delta |
|---|---:|---:|---:|
| Case pass | 70.9% (39/55) | 76.4% (42/55) | +5.5 pp |
| Routing accuracy | 100.0% (55/55) | 100.0% (55/55) | +0.0 pp |
| Citation membership validity | 100.0% (138/138) | 100.0% (142/142) | +0.0 pp |
| Final citation/reference code flags | 0.0% (0/59) | 0.0% (0/59) | +0.0 pp |
| Correct-refusal rate | 92.9% (13/14) | 85.7% (12/14) | -7.1 pp |
| Escalation/referral recall | 92.3% (24/26) | 92.3% (24/26) | +0.0 pp |
| D/F strict trap pass | 66.7% (8/12) | 66.7% (8/12) | +0.0 pp |
| Language match, all turns | 93.2% (55/59) | 100.0% (59/59) | +6.8 pp |
| Hindi script match | 100.0% (10/10) | 100.0% (10/10) | +0.0 pp |
| Retrieval hit, agent-mapped IDs | 87.3% (48/55) | 87.3% (48/55) | +0.0 pp |
| Final refuse_unverified cases | 7 | 4 | -3 |
| Expected-answer cases ending refuse_unverified | 5 | 3 | -2 |
| refuse_unverified turns | 7 | 4 | -3 |
| Cases with trace.pruned (any turn) | 0 | 6 | +6 |
| Mean observed turn time | 12.59 s | 16.35 s | +3.77 |
| p50 observed turn time | 9.91 s | 10.97 s | +1.06 |
| p95 observed turn time | 30.95 s | 43.72 s | +12.77 |
| Mean trace-reported calls/turn | 4.44 | 4.63 | +0.19 |
| Independent semantic unsupported-claim rate | unavailable | unavailable | n/a |

## Latency

| Measure | Last run | Fresh run |
|---|---:|---:|
| Turns | 59 | 59 |
| p50 | 9.906 s | 10.968 s |
| p95 | 30.952 s | 43.723 s |
| Mean | 12.589 s | 16.354 s |
| Max | 41.377 s | 146.134 s |

All completed turn times and outliers are included. p50/p95 use linear interpolation at (n-1)*p; the six-second inter-turn sleep is excluded. Rescoring does not change timings. Provider load, models and app changes can all affect the observed difference.

## Referral precision/recall — T-041..T-055

| Measure | Last run rescored | Fresh run |
|---|---:|---:|
| Acceptable referral precision, specific bodies + permitted follow-ups / shown | 83.3% (15/18) | 94.7% (18/19) |
| Specific-body recall, cases naming expected body / expected cases | 93.3% (14/15) | 93.3% (14/15) |
| Cited-specific-body recall | 93.3% (14/15) | 93.3% (14/15) |
| Permitted next-step body mentions | 1 | 4 |
| Wrong-body cases | 1 | 1 |
| Referral check pass, fallback allowed | 93.3% (14/15) | 93.3% (14/15) |

Bodies/destinations are deduplicated per reply. Recall still requires the expected specific body; NCH/District Commission follow-ups do not substitute for it. The exception is limited to consumer/wages answers with the specific body first and a sequential cue or an explicitly additional later paragraph. Equal first options, earlier generic bodies and escalation replies still hard fail. Answers still require a named-and-cited expected body.

## Website and email domain grounding

| Measure | Last run rescored | Fresh run |
|---|---:|---:|
| Domain-check passing turns | 58/59 | 59/59 |
| Grounded displayed domains | 98.5% (67/68) | 100.0% (73/73) |
| Cases with domain mismatches (hard fail) | 1 | 0 |

Every website/email hostname in reply or draft must occur in a retrieved chunk (including its source URL) or the user history available on that turn. Case/IDNA and optional www are normalized. A parent domain does not authorize an unlisted subdomain. Entire-corpus or cited-but-unretrieved evidence earns no domain credit.

- Last run: T-047 turn 1: airseva.gov.in.
- Fresh run: no domain mismatches.

## Per-case delta

| Case | Last published | Last rescored → fresh | Resolved checks | New failures |
|---|---|---|---|---|
| T-001 | fail | fail → fail | none | none |
| T-002 | pass | pass → fail | none | action, must_include |
| T-003 | pass | pass → pass | none | none |
| T-004 | fail | fail → fail | none | none |
| T-005 | pass | pass → pass | none | none |
| T-006 | fail | fail → pass | language, must_include | none |
| T-007 | pass | pass → pass | none | none |
| T-008 | pass | pass → pass | none | none |
| T-009 | pass | pass → pass | none | none |
| T-010 | pass | pass → pass | none | none |
| T-011 | pass | pass → pass | none | none |
| T-012 | pass | pass → pass | none | none |
| T-013 | fail | fail → pass | must_include, needs_lawyer | none |
| T-014 | pass | pass → pass | none | none |
| T-015 | pass | pass → pass | none | none |
| T-016 | pass | pass → pass | none | none |
| T-017 | pass | pass → pass | none | none |
| T-018 | pass | pass → pass | none | none |
| T-019 | pass | pass → pass | none | none |
| T-020 | pass | pass → pass | none | none |
| T-021 | pass | pass → pass | none | none |
| T-022 | pass | pass → pass | none | none |
| T-023 | fail | fail → pass | language, must_include | none |
| T-024 | fail | fail → fail | none | none |
| T-025 | pass | pass → pass | none | none |
| T-026 | fail | fail → fail | none | none |
| T-027 | pass | pass → pass | none | none |
| T-028 | pass | pass → pass | none | none |
| T-029 | fail | fail → fail | none | none |
| T-030 | fail | fail → fail | none | none |
| T-031 | fail | fail → fail | action, needs_lawyer | none |
| T-032 | pass | pass → pass | none | none |
| T-033 | fail | fail → fail | action, case_guards | needs_lawyer |
| T-034 | pass | pass → pass | none | none |
| T-035 | fail | fail → fail | none | none |
| T-036 | pass | pass → pass | none | none |
| T-037 | pass | pass → pass | none | none |
| T-038 | fail | fail → fail | none | none |
| T-039 | pass | pass → pass | none | none |
| T-040 | fail | fail → fail | none | none |
| T-041 | pass | pass → pass | none | none |
| T-042 | pass | pass → pass | none | none |
| T-043 | pass | pass → pass | none | none |
| T-044 | fail | pass → pass | none | none |
| T-045 | pass | pass → pass | none | none |
| T-046 | fail | fail → pass | language | none |
| T-047 | fail | fail → pass | domains, language, referral | none |
| T-048 | pass | pass → pass | none | none |
| T-049 | pass | pass → fail | none | referral |
| T-050 | pass | pass → pass | none | none |
| T-051 | pass | pass → pass | none | none |
| T-052 | pass | pass → pass | none | none |
| T-053 | pass | pass → pass | none | none |
| T-054 | pass | pass → pass | none | none |
| T-055 | fail | pass → pass | none | none |

## Fresh referral observations

| Case | Category / action / lawyer | Specific body | Allowed next step | Wrong body | Referral check | Domain check |
|---|---|---|---|---|---|---|
| T-041 | out_of_scope / escalate / True | COM-DIR-CYBER | none | none | pass | pass |
| T-042 | consumer / answer / False | COM-DIR-RBI | none | none | pass | pass |
| T-043 | consumer / answer / False | COM-DIR-IRDAI | none | none | pass | pass |
| T-044 | wages / answer / True | COM-DIR-EPFO | none | none | pass | pass |
| T-045 | out_of_scope / escalate / True | COM-DIR-ECHALLAN | none | none | pass | pass |
| T-046 | consumer / answer / False | COM-DIR-RAIL | none | none | pass | pass |
| T-047 | consumer / answer / False | COM-DIR-AIRSEWA | COM-DIR-NCH | none | pass | pass |
| T-048 | out_of_scope / escalate / True | COM-DIR-SANCHAR | none | none | pass | pass |
| T-049 | out_of_scope / escalate / True | COM-DIR-RTI | none | COM-DIR-CPGRAMS | fail | pass |
| T-050 | out_of_scope / escalate / True | COM-DIR-UIDAI | none | none | pass | pass |
| T-051 | consumer / answer / False | COM-DIR-UPPCL | COM-DIR-NCH, SUPPORT:DISTRICT_COMMISSION | none | pass | pass |
| T-052 | consumer / answer / False | COM-DIR-UPRERA | none | none | pass | pass |
| T-053 | out_of_scope / escalate / True | none | none | none | pass | pass |
| T-054 | out_of_scope / escalate / True | COM-DIR-ELDERLINE | none | none | pass | pass |
| T-055 | consumer / answer / False | COM-DIR-FSSAI | COM-DIR-NCH | none | pass | pass |

## Check revisions and limits

Negated guarantees, including bullets under an explicit unverified-information heading, are not positive promises. A later affirmative promise remains a failure. PF T-044 accepts wages/answer when EPFO is named and cited; either lawyer flag is allowed, with a visible lawyer pointer required when true. All inputs, specific-body allowlists and law-verification flags are unchanged. All 55 law expectations still require human confirmation.
No app/data source was edited. Domain and statute/reference checks are textual grounding checks, not a complete legal-applicability audit. The configured app verifier stayed enabled; there was no extra harness judge. Semantic unsupported-claim rate and repeated-run stability are unavailable.
