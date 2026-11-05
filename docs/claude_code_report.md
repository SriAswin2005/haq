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

## Update 2026-11-05 (from the review chat): model routing and fallback
- `app/llm.py` was rewritten. Each role (router, main, judge) is now an ordered chain in `config.yaml`, with per-model `rpm`/`tpm`/`rpd`. The client paces itself to those limits. On a 429 it reads `retryDelay`, cools that model and switches to the next. A per-day 429 marks the model exhausted until midnight Pacific. A 5xx gets one retry, then a switch. A 401/403/404 marks the model unavailable. An empty or blocked answer moves to the next model.
- The daily budget is shared across processes in `data/index/quota_state.json`.
- Gemma models get no systemInstruction and no JSON mode; the prompt is folded into the user turn. Any model that rejects JSON mode with a 400 is retried once without it, and the client remembers that.
- Model ids are resolved against the key's model list (`python -m app.models`). An id with a missing suffix (e.g. `-preview`) resolves automatically.
- `trace.llm.fallbacks` records every switch and its reason. `trace.llm.models` records which model served each role.
- Embeddings are paced to 100 texts and 30K tokens per minute, and never switch models.
- Interface unchanged: `generate()`, `embed()`, `parse_json()`, `LLMError`, `reset_stats()`, `snapshot_stats()`.
- Offline test: `python -m app.selfcheck_fallback` (13 checks, no network).
- Note: the largest corpus chunk is ~24K characters, which is over the embedding model's input limit (truncated). Ask Antigravity to split it at sub-sections.

---
# Round 2 (2026-11-05): code gaps from NEXT_ROUND.md

Unit tests: `python -m unittest discover -s app/tests -t .` -> 18 tests, all pass (mock model, date pinned with `AI_LAWYER_TODAY`). Codex's `tests/` suite still passes in mock mode (23 tests). Streamlit AppTest: no exceptions.

| # | Gap | What changed | Test |
|---|---|---|---|
| 1 | Minor detection | `app/guards.py:minor_flags` - regexes for "I am 16", "16 years old", "16-year-old", "umar 16", "16 saal ka hoon", "16 साल का/की", "उम्र 16", Devanagari digits. Age 1-17 = hard escalation `minor_age`, kept for the whole session. | `MinorDetection` (positives, false-positive guards like "3 months", "5 साल का किराया", pipeline + persistence) |
| 2 | Criminal / jail | Added to `config.yaml`: jail, ipc, bns, "420", "cheating case", "fraud case", "police case", "case karunga", "case kar dunga", जेल, धोखाधड़ी, केस करूंगा/करूँगा, केस कर दूंगा. Matching is NFC-normalised (nukta forms). | `CriminalKeywords` ("Rs 4200" is not flagged) |
| 3 | Limitation in code | Router now gives `event_date` only (prompt gets `TODAY`). Code computes `months_since_event` (`guards.months_since`), ignores any LLM-supplied number, and also resolves "2 months ago" / "3 साल पहले" / "mahine pehle" itself. `limitation_risk` then fires from `escalation.limitation_warn_months`. | `LimitationInCode` (LLM's bogus `1` ignored, March 2023 flags, 2 months ago does not) |
| 4 | Case-law requests | `pipeline._case_law_line`, applied to every path (answer, clarify, refuse, escalate, draft): if the user asks for a case/judgment/precedent/Supreme Court ruling/फैसला and no `judgment` chunk is in the retrieved or cited set, the localized line "I can't cite court cases; I don't have verified judgments." is inserted before the disclaimer and `needs_lawyer=True`. | `CaseLaw` (en, hi, escalation path, not added when not asked) |
| 5 | Hindi body | `answer.md` rule 9 now demands the body in the reply language's own script. Code check `guards.script_ok` (>=50% Devanagari for hi); one retry with `prompts/language_retry.md`; if it still fails, `trace.language_warning` is set and the verified answer is still shown. | `HindiBody` (retry fires exactly once, uses the Hindi result). **Not yet checked with a real model** (see item 7). |
| 6 | Source info in panel | "How I got this answer" shows `source_type`, the `REVIEW` status_note (as a warning) and "(unverified source - check before relying on it)" for `secondary` chunks, via `guards.source_notes`. | `SourceNotes` |

## Item 7: real-key smoke test - NOT DONE
The sandbox I run in cannot reach `generativelanguage.googleapis.com` (curl returns 000, `ProxyError` on every model in the chain; same as NEXT_ROUND.md warned). With the key in `.env` the CLI correctly fell through all five router models and degraded to the honest service-error reply instead of crashing, but no real model output exists to paste. So I have no evidence yet that the real model (a) returns valid router JSON with `event_date`, (b) writes a Hindi body, or (c) passes the verifier without false positives.

Please run this in your own terminal and paste the output here (or into this section):
```
python -m app.cli "I vacated my flat in Lucknow 2 months ago, landlord not returning 30000 deposit" --json
python -m app.cli "मैंने 2 महीने पहले लखनऊ में फ्लैट खाली किया, मकान मालिक 30000 की डिपॉज़िट नहीं लौटा रहा" --lang hi-IN --json
```
What to look at in the JSON: `trace.router.case_file_update.event_date`, `case_file.months_since_event` (about 2.0), `trace.language_retry` / `trace.language_warning` for the Hindi run, `verifier.status`, and `trace.verifier_history` for false positives.

## Not changed / still open
Voice, the other two draft types and practice mode are still unbuilt. `retrieval.min_score` is still 0.0 pending Codex's calibration. The llm.py rewrite with model fallback chains and the config model list came from outside this round; I did not review them beyond running the mock suites.

## Update 2026-11-05 evening (review chat): P1 built
- **Voice** (`app/voice.py`): Sarvam STT (`saaras:v4` → `saaras:v3`), with Gemini audio input as the fallback, and recordings split into ≤28 s pieces. Sarvam TTS (`bulbul:v3` → `bulbul:v2`): text cleaned for speech (amounts with Indian commas, helplines read digit by digit, no URLs or source lines), chunked, WAVs joined, first 1800 chars spoken. Sarvam's docs disagree on the TTS language field name, so the client retries with the other name. UI: mic recorder plus a "Read answers aloud" setting. CLI: `--audio in.wav`, `--speak out.wav`. Offline: `python -m app.selfcheck_voice` (14 checks). **Not yet run against the live Sarvam API.**
- **Drafts** (`app/drafts.py`): `DRAFTS` registry with tenancy deposit notice, wages salary demand notice, and consumer grievance email plus commission fact sheet. `deposit_notice()` is kept as an alias. New router case-file keys: designation, job_start_date, last_working_date, unpaid_period, monthly_wage_inr, product_or_service, order_id, purchase_date, resolution_wanted.
- **Answer quality**: CONDITIONS and WHERE-TO-GO rules in answer.md, a SCOPE check in judge.md, and per-category forum queries in retrieval (`retrieval.forum_queries`).
- **Hosting**: st.secrets is bridged to env vars in ui.py, the embedding cache is committed, and README deploy steps are updated.
- Streamlit AppTest (mock): load, text turn and salary draft run with no exceptions. All suites pass: app/tests 18, fallback 13, voice 14, tests.test_checks, corpus validator.
- Still open: practice mode (P2), live voice test, and "where to complain" still a gap in one live deposit answer (forum chunks retrieved; the prompt may need a nudge).
- **Fixes from the first real eval** (`outputs/runs/real-20261105T155525…`, 12/30): helplines are rendered as "name: numbers", with the numbers copied verbatim from the chunk (long English text no longer swamps Hindi replies). The old-law note appears only when the user mentions that law, and the chunk is recorded in `retrieved`. Aid-search citations are always listed in `retrieved`. answer.md rules 13 (say "I could not verify" for laws the user claims) and 14 (no guarantees).
