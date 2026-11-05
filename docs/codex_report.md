# Codex report — updated 6 November 2026

The requested real evaluation is complete: **12/30 strict-check passes, 18 failures,
0 unresolved infrastructure errors, 0 pending cases**. All **30 cases have mapped
`expected_chunk_ids` and retain `expected_law_verified=false`**.

The published run evaluates a **frozen application/config/corpus revision captured
on 5 November at 21:40 IST**. It finished at 23:30 IST, with **30 raw case files and
33 turns**. The corpus snapshot contains **119 chunks**, all marked official;
22 require human checks. Later working-checkout changes are not covered.

## Evidence and execution

- [Real summary](../outputs/summary.md), [results CSV](../outputs/results.csv),
  [calibration](../outputs/calibration.md), [graded raw files](../outputs/raw/).
- [Run archive](../outputs/runs/real-20261105T161021.563148Z/),
  [manifest](../outputs/runs/real-20261105T161021.563148Z/manifest.json),
  [frozen inputs](../outputs/runs/real-20261105T161021.563148Z/frozen_inputs.json),
  [audit](../outputs/runs/real-20261105T161021.563148Z/audit.json).
- [Real-only BUGS.md](../tests/BUGS.md), including a quote-validated review of the
  conflicting-date draft. The unannotated automatic report is preserved alongside
  the run as `BUGS_automated.md`.
- [Mapping rationale](../tests/CHUNK_MAPPING.md): 18 substantive-topic targets and
  12 safe-referral targets. IDs are alternatives; mapping does not certify law.

Execution: `python tests/run_frozen_eval.py --sleep 6`, which runs the copied
`tests/run_eval.py --sleep 6` through the public pipeline. **No `--judge` flag was
used.** The app's configured faithfulness verifier remained enabled. Credentials
were passed in process environment; no `.env` was copied into the snapshot.

The audit confirms the frozen inputs stayed unchanged, the canonical archive and
`outputs/raw/` match the frozen raw bytes, and no credential values were found in
run artifacts. **27 checker/harness tests pass**. Codex did not edit root app,
config or corpus sources or select a production threshold.

## Real metrics

| Metric | Result |
|---|---:|
| Strict-check case pass | 12/30 (40.0%) |
| Final-turn routing accuracy | 29/30 (96.7%) |
| Displayed citation IDs in returned retrieved set | 77/88 (87.5%) |
| Final-output citation/reference flags | 9/33 turns (27.3%) |
| Correct refusal, eligible cases | 9/12 (75.0%) |
| Lawyer flag plus visible referral, eligible cases | 12/15 (80.0%) |
| D/F trap pass | 1/10 (10.0%) |
| Language metadata/body-script match | 29/33 (87.9%) |
| Retrieval hit, agent-mapped targets | 26/30 (86.7%) |
| App-reported calls per turn | 6.00 |
| Independent harness judge calls | 0 |

Retrieval hits split into **17/18 substantive-topic** and **9/12 safe-referral**
cases. All five designated G escalation inputs set `needs_lawyer=true`; the wider
referral metric also includes unavailable-information traps.

**Semantic unsupported-claim rate and independent judge agreement are unavailable.**
The extra harness judge was omitted as requested, and these traces expose no final
structured legal blocks for a complete independent claim audit. Citation and regex
checks alone cannot establish claim support.

Observed latency: **median 23.9 s, mean 194.5 s**. T-026 is a **4,732.6 s elapsed-time
outlier**, while its trace reports 101.4 s of LLM latency. The remaining elapsed
interval is unexplained by the trace; do not use the mean as a normal-service
benchmark. Recovered fallback reasons include 12 HTTP 503 and 8 HTTP 500 events.
There were no recorded 429 failures or unresolved quota errors in the final run.

## Calibration: two candidates

Seven independently labelled answerable cases and three unsupported-subtopic
cases supplied real top-1 scores. Hard-routed exclusions were not zero-filled.
Answer scores range **0.6816–0.7461**, median **0.7105**; refusal scores range
**0.6493–0.7190**, median **0.7132**. The overlap is substantial.

| `retrieval.min_score` | Answerable cases wrongly gated | Unsupported requests admitted |
|---:|---:|---:|
| **0.665437** | 0/7 (0.0%) | 2/3 (66.7%) |
| **0.720954** | 4/7 (57.1%) | 0/3 (0.0%) |

**0.720954 is the in-sample balanced-error candidate**, with a substantial coverage
cost. **0.665437 preserves coverage** and leaves two unsupported requests for the
verifier/refusal layers to handle. Neither is validated on new inputs. These are
counterfactual gate estimates, not live reruns at those settings. The human must
choose the tradeoff; I did not change `min_score`. Histograms and exact case scores
are in [calibration.md](../outputs/calibration.md).

## Five priority findings from the final real run

1. **Citation provenance breaks on fallback/aid paths.** T-004, T-009, T-013,
   T-014, T-021 and T-030 display 11 aid citations missing from their returned
   `retrieved` sets. For example, `COM-NALSA-H15100` is displayed after a separate
   aid search but omitted from the public retrieval record. Likely pipeline
   assembly: return the union of sources actually used.
2. **T-029 silently chooses a disputed date.** After the user explicitly says
   10 versus 20 October is unresolved, the draft states “I vacated the premises
   on 2026-10-10”. The verifier reports pass. A generic instruction to confirm
   legal provisions does not resolve the date. Preserve a date placeholder and
   acknowledge the conflict. Likely fact merging/draft/verifier.
3. **T-005 misses the requested forum and has incomplete source provenance.**
   Its returned retrieval includes the Rent Authority chunks S30 and S33, yet the
   reply lists “where to complain” as unverified and gives no forum. It also adds
   the repealed 1972 Act note without that old chunk in the returned set. This is
   a retrieval-use/provenance failure; the historical Act itself was not invented.
4. **Partial refusal and referral state are inconsistent.** T-001 correctly says
   verified judgments are unavailable and sets the lawyer flag, but never visibly
   refers the user to a lawyer/legal-aid service. T-002 and T-007 describe gaps
   while returning `answer` and `needs_lawyer=false`. No fake triple-refund section
   or Sunday fee appeared, but the expected refusal/referral contract fails.
5. **Hindi replies retain large English aid/contact payloads.** T-003, T-011,
   T-015 and T-017 fail the body-script check. Their Hindi safety explanation is
   followed by lengthy English contact/source text. This needs localization or a
   shorter localized presentation; the script metric is best effort.

The evaluated snapshot also lacks the consumer draft requested by T-010. Claude's
later report describes P1 draft/voice and citation/localization fixes; this frozen
run does **not** certify those later edits.

Strict scores include lexical/action mismatches. T-006 says it cannot predict or
guarantee a win, despite missing the test's exact alternative phrases. Old-law
answers may say “no longer in force” without matching “repealed/replaced/no longer
current”. These flags require review and are not evidence that a guarantee or a
fictional statute was produced. Numeric warnings also include statutory-title
years, contact numbers and amounts written as words in the input.

## Preserved history, mock labels and limits

- The first real [122-chunk run](../outputs/runs/real-20261105T153801.934588Z/)
  contains an initial missing-key infrastructure attempt. The key existed in
  `.env`; the declared `python-dotenv` dependency was absent. Installing it and
  using `--retry-infra` recovered the run while preserving the failed attempt.
- The subsequent [119-chunk development run](../outputs/runs/real-20261105T155525.053046Z/)
  caught real defects, but app/config/prompt edits landed during its final minute.
  Both earlier runs retain input-integrity reviews; neither is presented as the
  stable final revision. The final snapshot removes that ambiguity.
- A pre-fix interest claim in T-005 was recorded in the earlier run's agent review.
  It does not appear in the final reply, so it is **not carried into current BUGS.md**.
- **Mock-only history:** the earlier 15/30 mock result, missed minor/limitation
  escalation and UP-to-Karnataka leakage were canned-model findings. They remain
  labelled historical and are excluded from the real bug report. See the
  [mock archive](../outputs/runs/mock-20261105T140459.351766Z/summary.md).
- Two actual checker errors were fixed: a long negated guarantee falsely marked
  as a promise, and generic source-review wording falsely clearing a disputed
  date. Regressions pass. An offline rescore preserved all old raw hashes and
  made no API calls; see [check revision review](../outputs/runs/real-20261105T153801.934588Z/check_revision_review.json).

Flakiness is **not measured** for the final revision. Earlier real runs changed
inputs, so their differences are not repeated-run stability evidence. Five voice
cases are transcripts only: no microphone, STT, TTS or live Sarvam evaluation was
performed. Practice mode, additional languages and the wider 40-case set remain
outside this evaluation.

The human must confirm **all 30 law expectations**, their mapped retrieval IDs,
and the 22 flagged corpus chunks, including numbers, deadlines, fees, contacts,
status and applicability. Review every draft's facts and unresolved dates. Choose
a threshold, then validate the selected current revision on new inputs before
relying on these scores for release.
