# Retrieval calibration

Human decision required. Labels come from independent case intent; they are not inferred from app actions.
Hard-routed out-of-scope and escalation cases are excluded: their bypassed retrieval cannot measure a gate.
Skipped observations: {}. Repeats are correlated, not independent samples.

| Population | n | min | median | max |
|---|---:|---:|---:|---:|
| answer | 7 | 0.6419 | 0.7120 | 0.7461 |
| refuse | 3 | 0.6598 | 0.6893 | 0.7310 |

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

Observed score-range overlap: [0.6598, 0.7310].

Gate refuses when top score < threshold. Candidate errors below are in-sample estimates, not validation guarantees.

| Candidate min_score | Good cases wrongly refused | Bad cases slipping through |
|---:|---:|---:|
| 0.641949 | 0.0% | 100.0% |
| 0.695961 | 14.3% | 33.3% |
| 0.734366 | 71.4% | 0.0% |

Provisional recommendation: retrieval.min_score=0.695961 (lowest balanced in-sample error; ties prioritise rejecting bad cases).
Candidates span non-dominated acceptance/refusal tradeoffs where available, rather than only neighbouring thresholds. The printed values themselves were scored.
The human must confirm law expectations, choose the tradeoff and validate on new cases. High topic similarity cannot establish legal support; keep the verifier and refusal paths.

Observed case scores:

- answer: T-021: 0.737687
- answer: T-022: 0.710528
- answer: T-023: 0.702665
- answer: T-024: 0.719528
- answer: T-025: 0.712011
- answer: T-026: 0.641950
- answer: T-028: 0.746098
- refuse: T-001: 0.689258
- refuse: T-002: 0.659783
- refuse: T-007: 0.731044
