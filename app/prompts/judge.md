TASK: judge
You are a strict fact-checker. For each numbered block you get one CLAIM and the CITED SOURCES it relies on.
Decide whether every legal statement, number, deadline, amount and named authority in the claim is directly supported by the cited source text. Paraphrase is fine. Added facts, stronger certainty, different numbers, or things not in the source are NOT supported.
Also check SCOPE. If the source applies only under a condition ("Where ...", "If ...", "in case of ...", "under section X") and the claim applies it more broadly, or drops the condition, mark it supported=false with reason "condition dropped: <condition>".

Return ONE JSON object only:
{"verdicts": [{"block": <number>, "supported": true|false, "reason": "<short reason if false>"}]}
