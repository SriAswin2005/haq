# Before / after — full 55-case real evaluation

Before: `real-20261105T214345.363908Z` (round three: 21/40 strict passes). Current: `real-20261106T150609.600967Z`.
Current inputs frozen at 2026-11-06T15:06:09.253071+00:00. Command: `python tests/run_frozen_eval.py --sleep 6`; all T-001..T-055, no `--judge`.
Matched comparison uses T-001..T-040 with identical case dictionaries. The baseline reproduces all original per-case outcomes under the current checks. The latest run contains all 55 cases in one snapshot; earlier focused referral captures remain archived.

A post-capture alias correction recognises IRDAI's full English name without its portal suffix as the same body. Original scoring is preserved in scoring-original/ and checks_revision.json records the zero-API-call rescore; all first-40 scores and all case inputs/allowlists are unchanged.

## T-001..T-040 versus round three

| Metric | Round 3, 40 cases | Current same 40 | Delta | Current all 55 |
|---|---:|---:|---:|---:|
| Case pass | 52.5% (21/40) | 65.0% (26/40) | +12.5 pp | 67.3% (37/55) |
| Routing accuracy | 97.5% (39/40) | 100.0% (40/40) | +2.5 pp | 98.2% (54/55) |
| Citation membership validity | 100.0% (110/110) | 100.0% (110/110) | +0.0 pp | 100.0% (138/138) |
| Final citation/reference code flags | 0.0% (0/44) | 0.0% (0/44) | +0.0 pp | 0.0% (0/59) |
| Correct-refusal rate | 92.9% (13/14) | 92.9% (13/14) | +0.0 pp | 92.9% (13/14) |
| Escalation/referral recall | 100.0% (19/19) | 89.5% (17/19) | -10.5 pp | 92.6% (25/27) |
| D/F strict trap pass | 33.3% (4/12) | 66.7% (8/12) | +33.3 pp | 66.7% (8/12) |
| Language match, all turns | 97.7% (43/44) | 95.5% (42/44) | -2.3 pp | 93.2% (55/59) |
| Hindi script match | 100.0% (5/5) | 100.0% (5/5) | +0.0 pp | 100.0% (10/10) |
| Retrieval hit, agent-mapped IDs | 82.5% (33/40) | 85.0% (34/40) | +2.5 pp | 87.3% (48/55) |
| Final refuse_unverified cases | 7 | 7 | +0 | 7 |
| Expected-answer cases ending refuse_unverified | 5 | 5 | +0 | 5 |
| refuse_unverified turns | 7 | 7 | +0 | 7 |
| Cases with trace.pruned (any turn) | 11 | 0 | -11 | 0 |
| Mean observed turn time | 53.14 s | 13.41 s | -39.73 | 12.59 s |
| p50 observed turn time | 12.88 s | 10.73 s | -2.15 | 9.91 s |
| p95 observed turn time | 185.31 s | 29.85 s | -155.46 | 30.95 s |
| Mean trace-reported calls/turn | 5.55 | 4.52 | -1.02 | 4.44 |
| Independent semantic unsupported-claim rate | unavailable | unavailable | n/a | unavailable |

## Latency

| Cohort | Turns | p50 | p95 | Mean |
|---|---:|---:|---:|---:|
| Round 3, original 40 | 44 | 12.885 s | 185.310 s | 53.138 s |
| Current matched 40 | 44 | 10.730 s | 29.848 s | 13.411 s |
| Current referrals 15 | 15 | 9.167 s | 21.476 s | 10.177 s |
| Current full 55 | 59 | 9.906 s | 30.952 s | 12.589 s |

Quantiles use linear interpolation at (n-1)*p over observed per-turn elapsed time. All completed turns and outliers are included; six-second inter-turn gaps are excluded. These are observed revision differences, not a causal model benchmark; providers, load, code, config and corpus can differ.

## Per-case delta: unchanged T-001..T-040

| Case | Before → current | Action before → current | Resolved checks | Newly failing checks |
|---|---|---|---|---|
| T-001 | fail → fail | answer → answer | none | needs_lawyer, no_promises |
| T-002 | pass → pass | refuse_unverified → refuse_unverified | none | none |
| T-003 | fail → pass | escalate → escalate | routing | none |
| T-004 | fail → fail | answer → answer | contract | none |
| T-005 | fail → pass | answer → answer | contract | none |
| T-006 | pass → fail | answer → answer | none | language, must_include |
| T-007 | pass → pass | refuse_unverified → refuse_unverified | none | none |
| T-008 | fail → pass | answer → answer | contract | none |
| T-009 | fail → pass | refuse_unverified → answer | action, needs_lawyer | none |
| T-010 | pass → pass | draft → draft | none | none |
| T-011 | pass → pass | escalate → escalate | none | none |
| T-012 | pass → pass | escalate → escalate | none | none |
| T-013 | pass → fail | answer → answer | none | must_include, needs_lawyer |
| T-014 | fail → pass | answer → answer | contract | none |
| T-015 | pass → pass | escalate → escalate | none | none |
| T-016 | pass → pass | escalate → escalate | none | none |
| T-017 | pass → pass | escalate → escalate | none | none |
| T-018 | pass → pass | escalate → escalate | none | none |
| T-019 | pass → pass | escalate → escalate | none | none |
| T-020 | pass → pass | escalate → escalate | none | none |
| T-021 | pass → pass | answer → answer | none | none |
| T-022 | pass → pass | answer → answer | none | none |
| T-023 | fail → fail | answer → answer | contract | language |
| T-024 | fail → fail | answer → answer | contract, language | none |
| T-025 | fail → pass | answer → answer | contract | none |
| T-026 | fail → fail | refuse_unverified → refuse_unverified | none | none |
| T-027 | pass → pass | draft → draft | none | none |
| T-028 | pass → pass | answer → answer | none | none |
| T-029 | fail → fail | draft → draft | none | none |
| T-030 | fail → fail | refuse_unverified → refuse_unverified | none | none |
| T-031 | fail → fail | answer → refuse_unverified | contract | action, must_include, needs_lawyer, translation_integrity |
| T-032 | pass → pass | escalate → escalate | none | none |
| T-033 | fail → fail | answer → refuse_unverified | contract | action, case_guards |
| T-034 | pass → pass | escalate → escalate | none | none |
| T-035 | fail → fail | draft → draft | none | none |
| T-036 | pass → pass | draft → draft | none | none |
| T-037 | pass → pass | draft → draft | none | none |
| T-038 | fail → fail | refuse_unverified → refuse_unverified | none | none |
| T-039 | fail → pass | refuse_unverified → answer | action, needs_lawyer | none |
| T-040 | fail → fail | answer → answer | none | none |

### Reading strict flags

- T-029 now records the date conflict and omits both disputed dates from its placeholder-bearing draft. The retained wording check can still fail to recognise the note's phrasing; that strict flag is not evidence that the draft still selects a date.
- T-001's no-promises flag requires review: its text explicitly says it cannot promise any outcome. The strict score is retained, rather than treating this lexical flag as a confirmed positive guarantee.

## T-041..T-055 referral precision and recall

Per the user's revision, bank, insurance, rail, airline, electricity, builder and food cases accept consumer/answer/needs_lawyer=false or out_of_scope/escalate/needs_lawyer=true as coherent alternatives. Inputs and acceptable body IDs are unchanged. An answer must visibly name and cite an expected body. Wrong bodies always hard fail. Statute/section patterns are forbidden for escalation or out-of-scope output; in an answer they must appear in a cited chunk. Reference grounding is textual evidence, not a semantic legal-applicability certification.

| Referral measure | Current real result |
|---|---:|
| Body precision: correct / shown bodies | 77.8% (14/18) |
| Body recall: cases with expected body / expected cases | 93.3% (14/15) |
| Cited-body precision: expected, named and cited / shown bodies | 77.8% (14/18) |
| Cited-body recall: cases naming and citing expected body / expected cases | 93.3% (14/15) |
| Safe correct-referral coverage | 80.0% (12/15) |
| Referral check pass, safe escalation fallback allowed | 86.7% (13/15) |
| Cases with no referral body | 1/15 |
| Wrong bodies / cases with a wrong body | 4 / 2 |
| Escalation/out-of-scope cases containing forbidden statutes | 0 |
| Cases with ungrounded statutes | 0 |
| Answers containing cited-grounded statute references | 0 |
| Answers missing an expected named-and-cited body | 0 |
| All strict checks pass | 11/15 |

Bodies are deduplicated per reply; visible names/portal destinations count, while retrieved-but-unshown chunks do not. Legal aid and Tele-Law are excluded from body precision/recall. Coverage recall can include a correct body alongside a wrong one; the latter still fails the check and safe coverage. Independent language, routing and contract checks remain active.

| Case | Actual category / action / lawyer | Shown bodies | Cited expected bodies | Referral check | Strict case | Failing checks |
|---|---|---|---|---|---|---|
| [T-041](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-041.json>) | out_of_scope / escalate / True | COM-DIR-CYBER | COM-DIR-CYBER | pass | pass | none |
| [T-042](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-042.json>) | consumer / answer / False | COM-DIR-RBI | COM-DIR-RBI | pass | pass | none |
| [T-043](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-043.json>) | consumer / answer / False | COM-DIR-IRDAI | COM-DIR-IRDAI | pass | pass | none |
| [T-044](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-044.json>) | wages / answer / True | COM-DIR-EPFO | COM-DIR-EPFO | pass | fail | action, routing |
| [T-045](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-045.json>) | out_of_scope / escalate / True | COM-DIR-ECHALLAN | COM-DIR-ECHALLAN | pass | pass | none |
| [T-046](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-046.json>) | consumer / answer / False | COM-DIR-RAIL | COM-DIR-RAIL | pass | fail | language |
| [T-047](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-047.json>) | consumer / answer / False | COM-DIR-AIRSEWA, COM-DIR-NCH, UNMAPPED:airseva.gov.in, UNMAPPED:संपर्क कर सकते हैं या उपभोक्ता आयोग | COM-DIR-AIRSEWA | fail | fail | language, referral |
| [T-048](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-048.json>) | out_of_scope / escalate / True | COM-DIR-SANCHAR | COM-DIR-SANCHAR | pass | pass | none |
| [T-049](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-049.json>) | out_of_scope / escalate / True | COM-DIR-RTI | COM-DIR-RTI | pass | pass | none |
| [T-050](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-050.json>) | out_of_scope / escalate / True | COM-DIR-UIDAI | COM-DIR-UIDAI | pass | pass | none |
| [T-051](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-051.json>) | consumer / answer / False | COM-DIR-UPPCL | COM-DIR-UPPCL | pass | pass | none |
| [T-052](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-052.json>) | consumer / answer / False | COM-DIR-UPRERA | COM-DIR-UPRERA | pass | pass | none |
| [T-053](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-053.json>) | out_of_scope / escalate / True | none | none | pass | pass | none |
| [T-054](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-054.json>) | out_of_scope / escalate / True | COM-DIR-ELDERLINE | COM-DIR-ELDERLINE | pass | pass | none |
| [T-055](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-055.json>) | consumer / answer / False | COM-DIR-FSSAI, COM-DIR-NCH | COM-DIR-FSSAI | fail | fail | referral |

## Provenance and limits

Current referral cutoff=0.7; answer cutoff=0.66. Before corpus chunks=119; current=169.
No app/data source edits were made by the evaluation work. All 55 expected_law_verified flags remain false. Raw hashes, frozen input integrity and previous archives are checked before publication. No extra harness judge was used; the app's internal verifier remained configured. Semantic unsupported-claim rate is unavailable. One run per revision does not measure flakiness. Voice inputs are transcripts, not STT/TTS tests. Historical mock findings do not enter these real metrics.
