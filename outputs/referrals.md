# Referral and domain results

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
