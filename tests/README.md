# Evaluation

Run from the repository root. Python 3.10+ is supported. Install the application's
requirements for app-backed runs. The checks and orchestration tests use the
standard library; PyYAML reads the app config. `langdetect` is optional: without
it, language checks use metadata and the predominant en/hi script. No dependency
or application source files are changed by this harness.

```powershell
python -m unittest tests.test_checks tests.test_harness -v
python tests/run_eval.py --mock --sleep 0 --runs 2
python tests/run_eval.py --mock --sleep 0 --only D,F,G
```

`--mock` sets `AI_LAWYER_MOCK=1` before importing `app.pipeline`. If that module
does not exist, the tests-only `mock_pipeline` fixture exercises orchestration;
the manifest explicitly records `fixture_mock`. The fixture never reads case
expectations and cannot validate app quality. Mock outputs always stay under
`outputs/runs/mock-<UTC timestamp>/` and never populate graded `outputs/raw/`.

Non-mock execution requires a populated `docs/claude_code_report.md` before any
app import or model call. A development sample attempt uses:

```powershell
python tests/run_eval.py --sample --sleep 4
```

For a gradeable run, the app owner must configure `corpus.path: data/corpus`,
populate the real corpus, make its validator pass and provide the configured
provider's credentials. Config/environment mock settings must be disabled.

```powershell
# Round 2 baseline: do not add the independent harness judge on the first run.
python tests/run_eval.py --sleep 6
# Optional later assessment:
python tests/run_eval.py --sleep 6 --judge
```

`--judge` is optional and uses `app.llm.generate(..., role="judge")` with the
prompt under `tests/prompts/`. It performs extra real-model calls. The app's
own judge remains controlled by config. Neither judge replaces human legal
review. Omit `--judge` for the P0 deterministic run; semantic claim support then
remains unavailable, even if all citation/reference checks pass.

Every run saves a manifest with case/code/config/corpus fingerprints, a corpus
snapshot, full raw case results, CSV, summary and a calibration file. Each raw
case contains its original input, every complete TurnResult (including trace),
reported model names, timing and any error. Two repeats use `repeat-001/raw/`
and `repeat-002/raw/`. No raw reply or trace is edited after capture. Exception
diagnostics scrub environment secrets. The app also writes its own live trace.

The runner stops at the first infrastructure error by default. Provider/key,
quota and transport failures returned through a SAFE RESPONSE are also counted
as infrastructure. Malformed model JSON is not relabelled as infrastructure.

```powershell
# Use the original mode, --runs, --only and --judge flags when resuming.
python tests/run_eval.py --sample --sleep 4 --resume outputs/runs/sample-<timestamp> --retry-infra
```

Resume skips saved cases. `--retry-infra` appends a new attempt and preserves the
old error file; metrics use the latest saved attempt. Changed code/config/cases
or corpus requires a new run. `--keep-going-on-infra` is available for diagnosing
independent service errors, but is usually inappropriate after quota exhaustion.
Exit codes: 0 = no hard failures, 1 = case failures, 2 = infrastructure/pending or
setup error. Warnings do not become hard failures and remain visible in reports.

Only a complete, unfiltered, infrastructure-free real-corpus run publishes
`outputs/raw/`, `outputs/results.csv`, `outputs/summary.md` and
`outputs/calibration.md`; immutable archives remain under `outputs/runs/`.
Partial and sample runs retain their own artifacts. `tests/BUGS.md` is generated
from real-corpus runs only, grouped by severity and linked to raw evidence.
Mock/sample bug reports stay inside their own run directory.

Legal expectations are independent of the corpus. Official links are embedded
in relevant cases; every case still requires human confirmation. Round 2 maps
all 30 cases to in-force corpus IDs in `tests/CHUNK_MAPPING.md`, with
`expected_law_verified=false`. The case labels distinguish 18 substantive-topic
targets from 12 safe-referral paths. Missing retrieval
hit evidence, semantic claim evidence or a citation denominator is reported as
unavailable, not as a successful score. Calibration uses real observed top-1
scores and independent answer/refusal labels; absent scores are never zero-filled.

Limitations: these 30 cases prioritise D/F/G traps, not the entire stretch brief.
Five voice inputs are synthetic text transcripts, with no STT/TTS measurement.
Numbers written as words, paraphrased claims, all draft fields, and applicability
of law still require manual review. Exact final action checks are deliberately
strict; earlier intake turns retain independent safety checks. See
`tests/CHANGELOG.md` for justified expectation corrections and preserved history.

Source-application observations can be attached to a completed real report with
`python tests/add_real_review.py --run outputs/runs/real-<timestamp> --findings tests/real_findings.jsonl`.
This validates every quote against the selected run's raw replies, inputs and
corpus snapshot, preserves `BUGS_automated.md`, and changes no raw files or
quantitative metrics. It is a targeted agent review with human confirmation
pending, not a replacement for a full independent judge run.

When app, config or corpus files are changing in parallel, use
`python tests/run_frozen_eval.py --sleep 6`. It copies the required inputs into
ignored `tests/_scratch`, passes credentials only through the process environment,
and runs the real pipeline there. It then copies raw bytes into the canonical
`outputs/runs/` archive and regenerates derived reports using the same checks.
`frozen_inputs.json` and `collection.json` record the tested revision and byte
identity. Later checkout changes require their own run; these results do not
silently claim to cover them. The frozen app's quota cache is isolated too.

## Round 3

`tests/cases.jsonl` now has 40 cases. T-001..T-030 are unchanged from the 21:40 before archive; T-031..T-040 add the requested language, draft, conflict and injection scenarios. All law-verification flags remain false.

Run `python tests/test_server_api.py` for the offline TestClient suite. It blocks outbound requests, uses temporary feedback/cache/trace files, and covers SSE stage/result ordering, terminal errors, shared 429 limiting, consent-gated conversation text, and browser-state restoration. `--real` requires GEMINI_API_KEY already in the process environment; a key in .env does not opt in. In Codex's restricted Windows sandbox, async socket-pair setup may block; run the mock suite in the normal terminal/outside that restriction.

After the 40-case real run completes, generate the cohort comparison and trace performance report with `python tests/round3_reports.py --run outputs/runs/<new-real-run>`. It verifies all 30 old case dictionaries and baseline raw hashes, separates the ten additions, reports exact trace.pruned presence and final refusal counts, uses linear p50/p95 quantiles without dropping outliers, and never infers a served model from configuration.

Final round-three archive: outputs/runs/real-20261105T214345.363908Z (21/40 strict passes; unchanged original cohort 17/30 versus 12/30). Reproduce derived artifacts without API calls, in order:

```powershell
python tests/round3_reports.py --run outputs/runs/real-20261105T214345.363908Z
python tests/round3_bugs.py --run outputs/runs/real-20261105T214345.363908Z
python tests/add_real_review.py --run outputs/runs/real-20261105T214345.363908Z --findings tests/round3_real_findings.jsonl
python tests/audit_round3.py --run outputs/runs/real-20261105T214345.363908Z
```

The first step rebuilds summary/CSV/calibration and comparison/performance reports; the next two attach trace and quote-validated reviews. The audit checks frozen inputs, before preservation, raw publication identity, report identity, unverified-law flags and secret-value absence. Mock API evidence is separate from the real legal evaluation. API result files now record source hashes before/after their tests so parallel edits are visible.

## Round 4

The catalogue now has 55 cases; --only round4 selects T-041..T-055. Run the new real cohort during parallel app edits with:

```powershell
python tests/run_frozen_eval.py --sleep 6 --only round4
```

The filtered run stays in outputs/runs/ and does not overwrite the full-run root summary/raw publication. Precision counts acceptable visible bodies divided by all shown bodies, deduplicated per reply; recall counts cases showing at least one expected body divided by the 15 expected cases. Legal-aid-only fallbacks pass safety but earn no recall credit. Extra bodies and statute/section patterns hard fail, including when a correct body is also present.

Published run: real-20261106T090855.555013Z. Its initial checker had generic-label false positives. Original scoring is preserved, and the corrected offline rescore changes no expected IDs, inputs or raw bytes:

```powershell
python tests/rescore_round4.py --run outputs/runs/real-20261106T090855.555013Z
python tests/round4_reports.py --run outputs/runs/real-20261106T090855.555013Z
python -m unittest tests.test_checks tests.test_harness tests.test_round3_reports tests.test_referrals
```

The report generator replaces only its marked round-four section in BEFORE_AFTER.md, preserving old tables and any unrelated surrounding content. It checks frozen input hashes, before-archive hashes, rescore provenance, captured raw identity and credential absence. Evidence is in referrals.md, referrals.csv, referral_metrics.json and checks_revision.json. Mock findings are not used for these real metrics.
