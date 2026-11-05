# Retrieval calibration

Human decision required. Labels come from independent case intent; they are not inferred from app actions.
Hard-routed out-of-scope and escalation cases are excluded: their bypassed retrieval cannot measure a gate.
Skipped observations: {}. Repeats are correlated, not independent samples.

| Population | n | min | median | max |
|---|---:|---:|---:|---:|
| answer | 7 | 0.6597 | 0.6932 | 0.7461 |
| refuse | 3 | 0.6509 | 0.6993 | 0.7190 |

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

Observed score-range overlap: [0.6597, 0.7190].

Gate refuses when top score < threshold. Candidate errors below are in-sample estimates, not validation guarantees.

| Candidate min_score | Good cases wrongly refused | Bad cases slipping through |
|---:|---:|---:|
| 0.655299 | 0.0% | 66.7% |
| 0.732558 | 85.7% | 0.0% |

Provisional recommendation: retrieval.min_score=0.655299 (lowest balanced in-sample error; ties prioritise rejecting bad cases).
Candidates span non-dominated acceptance/refusal tradeoffs where available, rather than only neighbouring thresholds. The printed values themselves were scored.
The human must confirm law expectations, choose the tradeoff and validate on new cases. High topic similarity cannot establish legal support; keep the verifier and refusal paths.

Observed case scores:

- answer: T-021: 0.706397
- answer: T-022: 0.684722
- answer: T-023: 0.693221
- answer: T-024: 0.679105
- answer: T-025: 0.711401
- answer: T-026: 0.659714
- answer: T-028: 0.746098
- refuse: T-001: 0.699257
- refuse: T-002: 0.650884
- refuse: T-007: 0.719018
