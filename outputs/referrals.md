# Referrals — current full real run

## T-041..T-055 referral precision and recall

Per the user's revision, bank, insurance, rail, airline, electricity, builder and food cases accept consumer/answer/needs_lawyer=false or out_of_scope/escalate/needs_lawyer=true as coherent alternatives. Inputs and acceptable body IDs are unchanged. An answer must visibly name and cite an expected body. Wrong bodies always hard fail. Statute/section patterns are forbidden for escalation or out-of-scope output; in an answer they must appear in a cited chunk. Reference grounding is textual evidence, not a semantic legal-applicability certification.

| Referral measure | Current real result |
|---|---:|
| Body precision: correct / shown bodies | 77.8% (14/18) |
| Body recall: cases with expected body / expected cases | 93.3% (14/15) |
| Cited-body precision: expected, named and cited / shown bodies | 77.8% (14/18) |
| Cited-body recall: cases naming and citing expected body / expected cases | 93.3% (14/15) |
| Safe correct-referral coverage | 80.0% (12/15) |
| Referral check pass, safe escalation fallback allowed | 86.7% (13/15) |
| Cases with no referral body | 1/15 |
| Wrong bodies / cases with a wrong body | 4 / 2 |
| Escalation/out-of-scope cases containing forbidden statutes | 0 |
| Cases with ungrounded statutes | 0 |
| Answers containing cited-grounded statute references | 0 |
| Answers missing an expected named-and-cited body | 0 |
| All strict checks pass | 11/15 |

Bodies are deduplicated per reply; visible names/portal destinations count, while retrieved-but-unshown chunks do not. Legal aid and Tele-Law are excluded from body precision/recall. Coverage recall can include a correct body alongside a wrong one; the latter still fails the check and safe coverage. Independent language, routing and contract checks remain active.

| Case | Actual category / action / lawyer | Shown bodies | Cited expected bodies | Referral check | Strict case | Failing checks |
|---|---|---|---|---|---|---|
| [T-041](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-041.json>) | out_of_scope / escalate / True | COM-DIR-CYBER | COM-DIR-CYBER | pass | pass | none |
| [T-042](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-042.json>) | consumer / answer / False | COM-DIR-RBI | COM-DIR-RBI | pass | pass | none |
| [T-043](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-043.json>) | consumer / answer / False | COM-DIR-IRDAI | COM-DIR-IRDAI | pass | pass | none |
| [T-044](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-044.json>) | wages / answer / True | COM-DIR-EPFO | COM-DIR-EPFO | pass | fail | action, routing |
| [T-045](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-045.json>) | out_of_scope / escalate / True | COM-DIR-ECHALLAN | COM-DIR-ECHALLAN | pass | pass | none |
| [T-046](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-046.json>) | consumer / answer / False | COM-DIR-RAIL | COM-DIR-RAIL | pass | fail | language |
| [T-047](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-047.json>) | consumer / answer / False | COM-DIR-AIRSEWA, COM-DIR-NCH, UNMAPPED:airseva.gov.in, UNMAPPED:संपर्क कर सकते हैं या उपभोक्ता आयोग | COM-DIR-AIRSEWA | fail | fail | language, referral |
| [T-048](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-048.json>) | out_of_scope / escalate / True | COM-DIR-SANCHAR | COM-DIR-SANCHAR | pass | pass | none |
| [T-049](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-049.json>) | out_of_scope / escalate / True | COM-DIR-RTI | COM-DIR-RTI | pass | pass | none |
| [T-050](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-050.json>) | out_of_scope / escalate / True | COM-DIR-UIDAI | COM-DIR-UIDAI | pass | pass | none |
| [T-051](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-051.json>) | consumer / answer / False | COM-DIR-UPPCL | COM-DIR-UPPCL | pass | pass | none |
| [T-052](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-052.json>) | consumer / answer / False | COM-DIR-UPRERA | COM-DIR-UPRERA | pass | pass | none |
| [T-053](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-053.json>) | out_of_scope / escalate / True | none | none | pass | pass | none |
| [T-054](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-054.json>) | out_of_scope / escalate / True | COM-DIR-ELDERLINE | COM-DIR-ELDERLINE | pass | pass | none |
| [T-055](<C:/E drive/KuKu Technologies/ai-lawyer/outputs/runs/real-20261106T150609.600967Z/raw/T-055.json>) | consumer / answer / False | COM-DIR-FSSAI, COM-DIR-NCH | COM-DIR-FSSAI | fail | fail | referral |
