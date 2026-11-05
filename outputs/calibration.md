# Retrieval calibration

Human decision required. Labels come from independent case intent; they are not inferred from app actions.
Hard-routed out-of-scope and escalation cases are excluded: their bypassed retrieval cannot measure a gate.
Skipped observations: {}. Repeats are correlated, not independent samples.

| Population | n | min | median | max |
|---|---:|---:|---:|---:|
| answer | 7 | 0.6816 | 0.7105 | 0.7461 |
| refuse | 3 | 0.6493 | 0.7132 | 0.7190 |

```text
Score histogram (cosine score bins; a count is one saved final turn)
answer:
  [-1.0, -0.8)  0
  [-0.8, -0.6)  0
  [-0.6, -0.4)  0
  [-0.4, -0.2)  0
  [-0.2,  0.0)  0
  [ 0.0,  0.2)  0
  [ 0.2,  0.4)  0
  [ 0.4,  0.6)  0
  [ 0.6,  0.8) ####### 7
  [ 0.8,  1.0]  0
refuse:
  [-1.0, -0.8)  0
  [-0.8, -0.6)  0
  [-0.6, -0.4)  0
  [-0.4, -0.2)  0
  [-0.2,  0.0)  0
  [ 0.0,  0.2)  0
  [ 0.2,  0.4)  0
  [ 0.4,  0.6)  0
  [ 0.6,  0.8) ### 3
  [ 0.8,  1.0]  0
```

Observed score-range overlap: [0.6816, 0.7190].

Gate refuses when top score < threshold. Candidate errors below are in-sample estimates, not validation guarantees.

| Candidate min_score | Good cases wrongly refused | Bad cases slipping through |
|---:|---:|---:|
| 0.665437 | 0.0% | 66.7% |
| 0.720954 | 57.1% | 0.0% |

Provisional recommendation: retrieval.min_score=0.720954 (lowest balanced in-sample error; ties prioritise rejecting bad cases).
Candidates span non-dominated acceptance/refusal tradeoffs where available, rather than only neighbouring thresholds. The printed values themselves were scored.
The human must confirm law expectations, choose the tradeoff and validate on new cases. High topic similarity cannot establish legal support; keep the verifier and refusal paths.

Observed case scores:

- answer: T-021: 0.706397
- answer: T-022: 0.710528
- answer: T-023: 0.723943
- answer: T-024: 0.681562
- answer: T-025: 0.722891
- answer: T-026: 0.682679
- answer: T-028: 0.746098
- refuse: T-001: 0.713208
- refuse: T-002: 0.649311
- refuse: T-007: 0.719018
