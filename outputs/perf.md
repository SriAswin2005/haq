# Performance — real round-three run

Source: `real-20261105T214345.363908Z`; 44 model-evaluable turns. No mock timing is included.
p50/p95 use linear interpolation at (n-1)*p over observed per-turn elapsed time. No outlier is removed. The six-second inter-turn gap is excluded.

| Measure | Observed |
|---|---:|
| p50 turn time | 12.885 s |
| p95 turn time | 185.310 s |
| Core trace p50 / p95 | 12.880 / 181.255 s |
| Provider trace p50 / p95 | 12.835 / 179.385 s |
| Mean / max turn time | 53.138 / 217.575 s |
| Mean trace-reported calls per turn | 5.55 (44/44 observed) |
| Turns with a fallback/model-switch event | 15/44 (34.1%) |
| Turns with multiple served models for the same role | 2/44 (4.5%) |

A switch event means trace.llm.fallbacks is non-empty, including candidates skipped because of provider failures or pacing. Served-model entries below come from trace.llm.models, not configured fallback chains.

| Role | Actual model entry | Recorded service entries |
|---|---|---:|
| embed | gemini:gemini-embedding-001 | 91 |
| judge | gemini:gemini-3.1-flash-lite | 11 |
| judge | gemini:gemma-4-31b-it | 23 |
| main | gemini:gemini-3.1-flash-lite | 19 |
| main | gemini:gemini-3.5-flash-lite | 14 |
| router | gemini:gemini-3.1-flash-lite | 44 |
| translate | unavailable in trace; not inferred from config | n/a |

Successful translated turns without an actual translate-model entry: 2. Translation attempts reported separately: 2.
If translation runs after the app snapshots its call statistics, trace-reported calls undercount that work and the actual translator cannot be inferred from config. These fields are observations, not a fabricated complete call total.

## Per-turn observations

| Case / turn | Elapsed s | Core trace s | Provider trace s | Trace calls | Switch | Translation |
|---|---:|---:|---:|---:|---|---|
| T-001 / 1 | 148.952 | 148.949 | 144.57 | 8 | True | none |
| T-002 / 1 | 6.282 | 6.278 | 6.23 | 4 | False | none |
| T-003 / 1 | 4.648 | 4.638 | 4.6 | 2 | False | none |
| T-004 / 1 | 114.536 | 114.524 | 112.29 | 8 | False | none |
| T-005 / 1 | 83.762 | 83.759 | 76.49 | 10 | True | none |
| T-006 / 1 | 53.026 | 53.022 | 50.86 | 6 | False | none |
| T-007 / 1 | 61.296 | 61.288 | 57.05 | 9 | False | none |
| T-008 / 1 | 55.181 | 55.178 | 52.54 | 8 | True | none |
| T-009 / 1 | 6.427 | 6.422 | 6.38 | 4 | False | none |
| T-010 / 1 | 6.482 | 6.478 | 6.44 | 4 | False | none |
| T-011 / 1 | 3.469 | 3.466 | 3.44 | 2 | False | none |
| T-012 / 1 | 3.591 | 3.588 | 3.56 | 2 | False | none |
| T-013 / 1 | 73.993 | 73.989 | 69.8 | 8 | True | none |
| T-014 / 1 | 30.002 | 29.999 | 24.78 | 10 | True | none |
| T-015 / 1 | 3.695 | 3.692 | 3.67 | 2 | False | none |
| T-016 / 1 | 3.271 | 3.266 | 3.24 | 2 | False | none |
| T-017 / 1 | 3.348 | 3.345 | 3.3 | 2 | False | none |
| T-018 / 1 | 3.400 | 3.397 | 3.37 | 2 | False | none |
| T-019 / 1 | 9.305 | 9.3 | 9.26 | 2 | False | none |
| T-020 / 1 | 14.227 | 14.221 | 14.18 | 2 | False | none |
| T-021 / 1 | 69.384 | 69.381 | 67.22 | 8 | True | none |
| T-022 / 1 | 44.304 | 44.3 | 42.16 | 6 | True | none |
| T-023 / 1 | 163.894 | 163.886 | 152.89 | 12 | False | none |
| T-024 / 1 | 154.158 | 154.154 | 147.82 | 11 | False | none |
| T-025 / 1 | 2.165 | 2.157 | 2.12 | 1 | False | none |
| T-025 / 2 | 105.452 | 105.449 | 95.3 | 15 | True | none |
| T-025 / 3 | 73.831 | 73.828 | 73.72 | 5 | True | none |
| T-026 / 1 | 6.581 | 6.565 | 6.54 | 4 | False | none |
| T-027 / 1 | 6.212 | 6.208 | 6.15 | 4 | False | none |
| T-028 / 1 | 217.082 | 217.078 | 212.92 | 7 | True | none |
| T-029 / 1 | 10.237 | 10.234 | 10.19 | 4 | False | none |
| T-029 / 2 | 8.641 | 8.636 | 8.58 | 4 | False | none |
| T-030 / 1 | 11.543 | 11.538 | 11.49 | 4 | False | none |
| T-031 / 1 | 189.090 | 184.32 | 184.06 | 8 | True | ok |
| T-032 / 1 | 6.644 | 3.48 | 3.46 | 2 | False | ok |
| T-033 / 1 | 217.575 | 217.572 | 212.14 | 8 | True | none |
| T-034 / 1 | 3.685 | 3.682 | 3.67 | 2 | False | none |
| T-035 / 1 | 6.584 | 6.58 | 6.54 | 4 | False | none |
| T-035 / 2 | 6.678 | 6.675 | 6.63 | 4 | False | none |
| T-036 / 1 | 6.512 | 6.508 | 6.45 | 4 | False | none |
| T-037 / 1 | 25.024 | 25.022 | 24.98 | 4 | False | none |
| T-038 / 1 | 95.397 | 95.392 | 92.6 | 9 | True | none |
| T-039 / 1 | 154.606 | 154.598 | 150.27 | 12 | True | none |
| T-040 / 1 | 63.918 | 63.915 | 63.82 | 5 | True | none |

## Fallback reasons

- HTTP 500: 5
- HTTP 503: 8
- busy for ~111s: 2
- busy for ~113s: 1
- busy for ~17s: 1
- busy for ~18s: 2
- busy for ~284s: 1
- busy for ~335s: 1
- busy for ~363s: 1
- busy for ~457s: 1
- busy for ~524s: 1
- busy for ~54s: 1
- busy for ~596s: 1
- busy for ~87s: 1
- busy for ~90s: 1
- busy for ~94s: 1
- network error (ReadTimeout): 1
