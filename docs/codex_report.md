# Codex report — corrected checks and fresh full evaluation

Completed all **55 cases / 59 turns** against commit
`a1c98ccc81c18e542985922d8c569bc40847e532`. Final score: **42/55 strict passes,
13 failures, zero infrastructure errors, zero pending cases**. Inputs were
captured at **22:52 IST on 6 November 2026**; real calls finished at **23:14 IST**.
Parallel uncommitted web UI edits were preserved and excluded. Codex made no
root `app/` or `data/` source edits.

| Scoring view | Strict passes |
|---|---:|
| Last run, real-20261106T150609, as published | 37/55 |
| Same saved replies, corrected checks/expectations | 39/55 |
| Fresh real run, identical corrected checks/expectations | 42/55 |

The comparison uses **39/55** as its baseline so checker changes are not counted
as product improvements. The old rescore changes T-044 and T-055 to pass. It
makes zero model calls and leaves original reports/raw files untouched.

## Results and evidence

- [BEFORE_AFTER.md](../outputs/BEFORE_AFTER.md): all metrics, 55 per-case deltas,
  referrals, domains and p50/p95 against the rescored last run.
- [Current summary](../outputs/summary.md), [results CSV](../outputs/results.csv),
  [referrals](../outputs/referrals.md), [performance](../outputs/perf.md),
  [real-only bugs](../tests/BUGS.md).
- [Fresh archive](../outputs/runs/real-20261106T172240.218881Z/),
  [frozen inputs](../outputs/runs/real-20261106T172240.218881Z/frozen_inputs.json),
  [metrics](../outputs/runs/real-20261106T172240.218881Z/policy_v2_metrics.json),
  [audit](../outputs/runs/real-20261106T172240.218881Z/audit.json).
- [Last-run archive](../outputs/runs/real-20261106T150609.600967Z/),
  [baseline rescore pointer](../tests/policy_v2_baseline.json),
  [offline rescore summary](../outputs/rescore_summary.md).

| Measure | Last run rescored | Fresh run |
|---|---:|---:|
| Acceptable referral precision | 15/18 (83.3%) | 18/19 (94.7%) |
| Specific-body recall | 14/15 (93.3%) | 14/15 (93.3%) |
| Cited-specific-body recall | 14/15 | 14/15 |
| Allowed next-step body mentions | 1 | 4 |
| Referral check pass, safe fallback allowed | 14/15 | 14/15 |
| Wrong-body cases | 1 | 1 |
| Domain-check passing turns | 58/59 | 59/59 |
| Grounded displayed domains | 67/68 | 73/73 |
| p50 turn time | 9.906 s | 10.968 s |
| p95 turn time | 30.952 s | 43.723 s |
| Mean / max turn time | 12.589 / 41.377 s | 16.354 / 146.134 s |

All turn times and outliers are included. Quantiles use linear interpolation at
`(n-1)*p`; the six-second inter-turn gaps are excluded. Provider load, model
selection and app changes can affect latency; this single run does not establish
a causal performance effect or repeated-run stability.

## Applied check fixes

1. Negated guarantees and bullets explicitly labelled unverified are not positive
   promises. Later affirmative promises remain failures. T-001's promise check
   passes; its separate unmet expectations are retained.
2. PF T-044 accepts `wages/answer` when EPFO is named and cited. Either lawyer flag
   is permitted; true still requires a visible lawyer/legal-aid pointer.
3. In consumer/wages answers, NCH and District Commission may be later steps after
   the expected specific body. A sequential cue or explicitly additional later
   paragraph qualifies; equal first options and escalation/out-of-scope replies
   do not. Specific-body recall still requires the specific body, while precision
   also credits allowed follow-ups. Targets and input messages are unchanged.
4. Every website/email hostname in reply or draft must occur in retrieved chunks
   or the user history available on that turn. Case, IDNA and optional `www.` are
   normalized; a listed parent domain does not authorize an unlisted subdomain.
   Bare domains, emails, quoted URLs and sentence punctuation are covered.
   Any mismatch is a Severity 1 hard failure. The last run's `airseva.gov.in`
   mismatch remains flagged; the fresh run has none.

Wrong bodies remain hard failures. The fresh RTI escalation T-049 still offers
CPGRAMS alongside RTI Online and fails. A legal-aid-only T-053 fallback passes
safety but earns no directory recall. T-051's NCH/District Commission follow-up
and T-055's NCH follow-up are accepted under the new policy. Grounded statute
references remain allowed in answers, with blanket rejection retained for
escalation/out-of-scope output.

**73 offline tests pass**. Post-capture validation fixed URL punctuation and two
duplicate-body detections: IRDAI's qualified internal department and the short
Hindi District Commission label beside its English name. Both datasets were
rescored with the identical final checks and zero additional API calls. Fresh
original scoring was 40/55; it is preserved in
[scoring-original](../outputs/runs/real-20261106T172240.218881Z/scoring-original/).
The final 42/55 changes only those two false-positive cases. No raw response,
input, specific-body allowlist or model execution was changed by rescoring.

## Execution and limits

Executed `python tests/run_frozen_eval.py --sleep 6 --commit-sources HEAD`, with
no extra `--judge`. The configured app verifier remained enabled. The snapshot
copies committed app/config/corpus separately from the corrected test harness;
all **57 committed source files** were checked against Git, with platform text
line endings normalized. Frozen file hashes and canonical/public raw byte
identity are verified. Credentials stay in process environment; no `.env` is
copied and no credential values were found in artifacts.

Language/script match improves from 55/59 to 59/59 turns. Final
`refuse_unverified` cases fall from 7 to 4, and six cases contain pruning traces.
All 142 displayed citation IDs belong to returned retrieval sets. These checks
do not establish legal applicability or completeness: the independent semantic
unsupported-claim rate remains unavailable. All **55 law expectations remain
unverified**, and the corpus's legal conditions, current thresholds, contacts and
applicability still require human review. Voice cases are transcripts only;
STT/TTS were not tested. Historical mock findings are excluded from current real
metrics and BUGS.md. Earlier round-three and focused round-four captures remain
in their own immutable archives.
