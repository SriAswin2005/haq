# Performance — real-20261106T172240.218881Z

59 turns; p50 10.968 s; p95 43.723 s; mean 16.354 s.

All observed turn times included; inter-turn sleeps excluded. See BEFORE_AFTER.md for the matched baseline.

| Role | Served model | Entries |
|---|---|---:|
| embed | gemini:gemini-embedding-001 | 132 |
| judge | gemini:gemini-3.1-flash-lite | 39 |
| main | gemini:gemini-3.5-flash-lite | 40 |
| router | gemini:gemini-3.1-flash-lite | 57 |
| router | gemini:gemini-3.5-flash-lite | 2 |
