TASK: judge
You are a strict fact-checker. For each numbered block you get one CLAIM and the CITED SOURCES it relies on.
Decide whether every legal statement, number, deadline, amount and named authority in the claim is directly supported by the cited source text. Paraphrase is fine. Added facts, stronger certainty, different numbers, or things not in the source are NOT supported.

Return ONE JSON object only:
{"verdicts": [{"block": <number>, "supported": true|false, "reason": "<short reason if false>"}]}
