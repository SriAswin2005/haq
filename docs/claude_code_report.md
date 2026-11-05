# Claude Code report

**Scope delivered: all of P0.** Not started: P1 (voice, the other two draft types) and P2 (practice mode).
Everything below was tested in `--mock` mode on the **sample** corpus only. **Nothing has run against the live Gemini API or the real corpus**, because no keys and no real corpus were available.

## What works (tested in mock mode)
- `handle_turn` / `new_session` match the Section 7 interface exactly (`TurnResult` fields checked by script).
- Router: one call, JSON validated, one retry, then `unclear`. Deterministic English/Hindi escalation keywords from `config.yaml`, merged with LLM flags. Hard triggers go to the SAFE RESPONSE (`action=escalate`); soft ones (high amount, limitation risk, unknown or uncovered state) still answer and add the lawyer/legal-aid message.
- Retrieval: schema-validated loader (bad lines skipped and logged), embedding cache keyed by chunk id + text hash, category and jurisdiction filters, repealed/superseded chunks searched separately for an "old law" note, confidence gate.
- Verifier: cited ids exist in this turn's set, legal blocks have cites, cited law is in force, statute/case regex scan against retrieved text and metadata, numbers/amounts/day counts must appear in the cited chunk or the user's own facts, optional LLM judge, one regeneration, then SAFE RESPONSE. A final scan runs on the rendered reply too.
- **Fake-citation test:** with `AI_LAWYER_MOCK_FAKECITE=1` the mock model cites `FAKE-ID-999`, "Section 420 of the Indian Penal Code" and "5 lakh". The verifier flagged all five issues, the regeneration was clean (`status: fixed`), and none of it reached the reply. With `=always` both attempts fail and the user gets the SAFE RESPONSE (`refuse_unverified`).
- Out-of-corpus or other-state questions: SAFE RESPONSE or, if only the state is missing, a question asking for it.
- Hindi text works end to end in mock mode (Hindi templates for refusals, labels, disclaimer).
- Deposit demand notice (`--mode draft`): facts from `case_file`, everything else a visible `[● placeholder]`, legal basis only from retrieved in-force statute/rule chunks, mandated closing line.
- `app/cli.py` (`--mock --json --interactive --lang --mode`), Streamlit UI (checked with Streamlit's AppTest: no exceptions) with red sample-data banner, escalation warning, "How I got this answer" panel, footer.
- One trace line per turn in `outputs/live_trace.jsonl`; missing key or unreachable model degrades to an honest message, not a crash.

## What does not work / not built
- **Voice** (Sarvam STT/TTS, mic button): not built (P1). The UI says so.
- **Consumer and salary draft types**: not built (P1). Draft mode for other topics says only the deposit notice exists.
- **Practice mode**: not built (P2); selecting it returns a "not available" message.
- Languages beyond en/hi: not enabled.
- Real-model behaviour is unknown: prompts, JSON compliance and the LLM judge have only run against the mock.

## Known weaknesses
- Model ids in `config.yaml` are unverified assumptions (see `docs/ASSUMPTIONS.md`). Check them first.
- The mock model copies chunk text, so it cannot show how a real model paraphrases; the verifier's number and regex checks may be too strict or too loose on real output. Watch false positives (needless SAFE RESPONSES) in Codex's first real run.
- Hindi legal terms inside real answers are not checked by the regex beyond `धारा N`.
- State detection relies on the router; unusual city names may be missed (then the system asks for the state).
- Free-tier rate limits: `llm.min_interval_s` is 4 s, so a turn with router + answer + judge takes about 12 s or more.

## Commands
```
pip install -r requirements.txt
python -m app.cli "my landlord in Lucknow kept my deposit of 20000 rupees" --mock --json
AI_LAWYER_MOCK=1 streamlit run app/ui.py          # or drop the variable and add GEMINI_API_KEY to .env
python -m app.cli "..." --mode draft --mock
AI_LAWYER_MOCK_FAKECITE=1 python -m app.cli "my landlord in Lucknow kept my deposit" --mock --json   # verifier demo
```

## Values the human should set
1. `models.*.model` and `embeddings.model`: confirm against current Gemini docs.
2. `corpus.path`: change `data/sample` to `data/corpus` when `validate_corpus.py` passes.
3. `retrieval.min_score`: currently **0.0** (gate effectively off). Set it from `outputs/calibration.md`; real embeddings will score very differently from the mock.
4. `verifier.llm_judge`: on by default; turn off if free-tier limits bite.
5. `escalation.high_amount_inr` (500000) and `limitation_warn_months` (30): from the contract; keywords in `config.yaml` can be extended.

## Assumptions
See `docs/ASSUMPTIONS.md` (all lines tagged `claude-code`). Mistakes logged in `docs/ai_mistakes.md`.

## For Codex
Entry point `app.pipeline.handle_turn`. Set `AI_LAWYER_MOCK=1` for keyless runs. The harness may switch corpus with `config.yaml: corpus.path`. `TurnResult.trace` carries router JSON, retrieval scores, verifier history and timings.
