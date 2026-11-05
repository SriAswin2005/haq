# Retrieval calibration

Human decision required. Labels come from independent case intent; they are not inferred from app actions.
Hard-routed out-of-scope and escalation cases are excluded: their bypassed retrieval cannot measure a gate.
Skipped observations: {}. Repeats are correlated, not independent samples.

| Population | n | min | median | max |
|---|---:|---:|---:|---:|
| answer | 7 | 0.6827 | 0.7105 | 0.8251 |
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
  [ 0.6,  0.8) ###### 6
  [ 0.8,  1.0] # 1
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

Observed score-range overlap: [0.6827, 0.7190].

Gate refuses when top score < threshold. Candidate errors below are in-sample estimates, not validation guarantees.

| Candidate min_score | Good cases wrongly refused | Bad cases slipping through |
|---:|---:|---:|
| 0.711868 | 57.1% | 66.7% |
| 0.716113 | 57.1% | 33.3% |
| 0.721480 | 57.1% | 0.0% |

Provisional recommendation: retrieval.min_score=0.721480 (lowest balanced in-sample error; ties prioritise rejecting bad cases).
The human must confirm law expectations, choose the tradeoff and validate on new cases. High topic similarity cannot establish legal support; keep the verifier and refusal paths.

Observed case scores:

- answer: T-021: 0.706397
- answer: T-022: 0.710528
- answer: T-023: 0.723943
- answer: T-024: 0.690190
- answer: T-025: 0.825067
- answer: T-026: 0.682679
- answer: T-028: 0.746098
- refuse: T-001: 0.713208
- refuse: T-002: 0.649311
- refuse: T-007: 0.719018
