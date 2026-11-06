# Real referral evaluation

## Round 4: directory referrals

Real cohort: `real-20261106T090855.555013Z`; T-041..T-055, 15 cases / 15 turns.
Frozen inputs: 2026-11-06T09:08:55.243562+00:00; 169 corpus chunks, including 40 directory rows. Referral cutoff: 0.7. Command: `python tests/run_frozen_eval.py --sleep 6 --only round4`; no `--judge`.
The earlier 30/40-case tables above are preserved. These 15 cases have no before-referral score. Results from different snapshots are not combined into a fictitious 55-case run.

Scoring correction: original scores and checker are preserved in `scoring-original/`; `checks_revision.json` records the offline rescore. Generic helpline/portal descriptions were initially mistaken for additional bodies. The corrected detector has regression coverage; no case expectation, acceptable ID or raw reply changed, and no additional API call was made.

| Referral measure | Real result |
|---|---:|
| Precision: correct body mentions / shown body mentions | 73.7% (14/19) |
| Recall: cases naming an expected body / expected cases | 93.3% (14/15) |
| Safe correct-referral coverage: no wrong body or statute | 53.3% (8/15) |
| Referral safety check pass, legal-aid-only fallback allowed | 60.0% (9/15) |
| Cases with no non-legal-aid referral | 1/15 |
| Wrong bodies shown / cases with a wrong body | 5 / 5 |
| Cases containing statute or section patterns | 1/15 |
| All strict checks pass | 5/15 |
| Infrastructure errors / pending | 0 / 0 |

Precision counts distinct visible body IDs/recognised destinations per reply, not aliases, citations or retrieved-but-unshown chunks. Recall counts each expected case once, even if two acceptable bodies are named. Legal aid/Tele-Law are excluded from shown/correct counts: an empty referral can pass safety while missing recall. A correct body plus any wrong body hard fails; a statute/section pattern hard fails even with a correct referral. Coverage recall can include such a mixed reply; the separate safe-coverage and check-pass rows expose it.

Names are matched against frozen directory titles plus independent English/Hindi/Hinglish aliases and visible portal URLs. Unknown named bodies/destinations are failures, not silently discarded. This is deterministic display checking, not a semantic audit of the directory's source text; all mapped expectations and directory rows remain pending human confirmation.

| Case | Language | Acceptable IDs | Shown IDs | Referral check | Strict case | Statute/section patterns |
|---|---|---|---|---|---|---|
| [T-041](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-041.json>) | en-IN | COM-DIR-CYBER, COM-DIR-RBI | COM-DIR-CYBER | pass | pass | none |
| [T-042](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-042.json>) | hi-IN | COM-DIR-RBI | COM-DIR-NCH, COM-DIR-RBI | fail | fail | none |
| [T-043](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-043.json>) | en-IN | COM-DIR-IRDAI | COM-DIR-IRDAI | pass | fail | none |
| [T-044](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-044.json>) | en-IN | COM-DIR-EPFO | COM-DIR-EPFO | pass | fail | none |
| [T-045](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-045.json>) | hi-IN | COM-DIR-ECHALLAN, COM-DIR-VCOURT | COM-DIR-ECHALLAN | pass | pass | none |
| [T-046](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-046.json>) | en-IN | COM-DIR-RAIL | COM-DIR-RAIL | pass | fail | none |
| [T-047](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-047.json>) | en-IN | COM-DIR-AIRSEWA | COM-DIR-AIRSEWA, COM-DIR-NCH | fail | fail | none |
| [T-048](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-048.json>) | hi-IN | COM-DIR-SANCHAR, COM-DIR-UPPOLICE | COM-DIR-SANCHAR | pass | pass | none |
| [T-049](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-049.json>) | en-IN | COM-DIR-RTI | COM-DIR-CPGRAMS, COM-DIR-RTI | fail | fail | none |
| [T-050](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-050.json>) | en-IN | COM-DIR-UIDAI | COM-DIR-UIDAI | pass | pass | none |
| [T-051](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-051.json>) | hi-IN | COM-DIR-UPPCL | COM-DIR-UPPCL | pass | fail | none |
| [T-052](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-052.json>) | en-IN | COM-DIR-UPRERA | COM-DIR-UPRERA | fail | fail | Act, 2016 |
| [T-053](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-053.json>) | en-IN | COM-DIR-RBI, COM-DIR-UPPOLICE | none (fallback) | pass | pass | none |
| [T-054](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-054.json>) | hi-IN | COM-DIR-ELDERLINE | COM-DIR-CHILDLINE, COM-DIR-ELDERLINE | fail | fail | none |
| [T-055](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T090855.555013Z/raw/T-055.json>) | en-IN | COM-DIR-FSSAI | COM-DIR-FSSAI, COM-DIR-NCH | fail | fail | none |
