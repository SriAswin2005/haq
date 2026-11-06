# Performance — current full real run

Run: `real-20261106T150609.600967Z`; 59 turns.
p50=9.906 s; p95=30.952 s; mean=12.589 s; max=41.377 s.
Mean trace calls/turn=4.44; fallback/switch turns=28/59; multiple actually served models for one role=0/59.
Quantiles include all observed elapsed turn times, without inter-turn gaps or outlier removal. Models below come only from trace.llm.models.

| Role | Served model | Trace entries |
|---|---|---:|
| embed | gemini:gemini-embedding-001 | 128 |
| judge | gemini:gemini-3.1-flash-lite | 34 |
| main | gemini:gemini-3.5-flash-lite | 38 |
| router | gemini:gemini-3.1-flash-lite | 59 |

Translated turns without a served translator entry: 2; separately reported translation attempts: 2. Trace calls/model provenance can be incomplete if translation happens after the stats snapshot; no translator is inferred from config.

| Case / turn | Elapsed s | Trace calls | Switch |
|---|---:|---:|---|
| T-001 / 1 | 29.973 | 8 | True |
| T-002 / 1 | 14.566 | 4 | False |
| T-003 / 1 | 9.091 | 3 | False |
| T-004 / 1 | 39.757 | 5 | True |
| T-005 / 1 | 10.349 | 5 | True |
| T-006 / 1 | 14.997 | 5 | True |
| T-007 / 1 | 11.712 | 6 | False |
| T-008 / 1 | 9.326 | 5 | True |
| T-009 / 1 | 16.604 | 7 | True |
| T-010 / 1 | 7.688 | 4 | False |
| T-011 / 1 | 4.520 | 2 | False |
| T-012 / 1 | 3.291 | 2 | False |
| T-013 / 1 | 12.620 | 6 | True |
| T-014 / 1 | 19.525 | 8 | True |
| T-015 / 1 | 13.420 | 2 | False |
| T-016 / 1 | 17.104 | 2 | False |
| T-017 / 1 | 4.879 | 3 | False |
| T-018 / 1 | 5.479 | 3 | False |
| T-019 / 1 | 5.481 | 3 | False |
| T-020 / 1 | 5.236 | 3 | False |
| T-021 / 1 | 10.275 | 5 | True |
| T-022 / 1 | 29.135 | 5 | True |
| T-023 / 1 | 20.464 | 7 | True |
| T-024 / 1 | 10.724 | 5 | True |
| T-025 / 1 | 2.662 | 1 | False |
| T-025 / 2 | 16.246 | 7 | True |
| T-025 / 3 | 12.021 | 5 | True |
| T-026 / 1 | 8.457 | 5 | False |
| T-027 / 1 | 6.505 | 4 | False |
| T-028 / 1 | 11.883 | 5 | True |
| T-029 / 1 | 7.441 | 4 | False |
| T-029 / 2 | 8.301 | 4 | False |
| T-030 / 1 | 6.493 | 4 | False |
| T-031 / 1 | 20.829 | 8 | True |
| T-032 / 1 | 6.926 | 2 | False |
| T-033 / 1 | 15.468 | 7 | True |
| T-034 / 1 | 3.675 | 2 | False |
| T-035 / 1 | 10.735 | 4 | False |
| T-035 / 2 | 5.239 | 4 | False |
| T-036 / 1 | 6.278 | 4 | False |
| T-037 / 1 | 40.044 | 4 | False |
| T-038 / 1 | 24.016 | 7 | True |
| T-039 / 1 | 25.911 | 5 | True |
| T-040 / 1 | 24.718 | 5 | True |
| T-041 / 1 | 9.177 | 3 | False |
| T-042 / 1 | 41.377 | 7 | True |
| T-043 / 1 | 12.860 | 5 | True |
| T-044 / 1 | 9.167 | 6 | True |
| T-045 / 1 | 5.178 | 3 | False |
| T-046 / 1 | 12.947 | 5 | True |
| T-047 / 1 | 8.302 | 5 | True |
| T-048 / 1 | 4.363 | 3 | False |
| T-049 / 1 | 4.179 | 3 | False |
| T-050 / 1 | 5.556 | 3 | False |
| T-051 / 1 | 10.349 | 5 | True |
| T-052 / 1 | 9.373 | 5 | True |
| T-053 / 1 | 3.820 | 2 | False |
| T-054 / 1 | 6.106 | 3 | False |
| T-055 / 1 | 9.906 | 5 | True |
