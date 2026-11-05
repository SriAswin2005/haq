# Brief for Claude Code: Build the AI Lawyer application

**First, read `00_ARCHITECTURE.md` completely. It is the contract. It wins any conflict with this file.**

You own: `app/`, `config.yaml`, `requirements.txt`, `.env.example`, `README.md`. Do not touch `data/corpus/`, `tests/` or `outputs/`. Other agents are writing the real corpus and the tests at the same time, so you build against the contract, not against their progress.

## Your mission

Build a working, resilient, free-tier-runnable app that follows the pipeline in Section 6 of the architecture, exposes exactly the interface in Section 7, and implements every anti-hallucination layer in Section 8. Fast and correct beats big. A simple version that works and refuses honestly beats a fancy one that guesses.

## Tech choices (decided, do not revisit)

- Python 3.10+ (the human's machine has 3.10), **Streamlit** UI (hostable free on Streamlit Community Cloud or Hugging Face Spaces).
- Default LLM: **Gemini free tier**, called only through `llm.py`. Model names live in `config.yaml`, never in code. Support separate roles (`router`, `main`, `judge`) so each can point to a different model.
- `llm.py` adapters: `gemini` (default), `openai_compatible` (base_url + key, covers many providers), `anthropic`. Swapping the model must be a config edit only. Provide `generate(messages, role, json_schema=None, temperature=0)` and `embed(texts)`.
- Embeddings: a **multilingual** embedding model behind `embed()`. Check the current provider docs for the model name and do not guess. Cache embeddings to `data/index/` keyed by chunk id plus a hash of the text, so only changed chunks are re-embedded.
- Vector search: in-memory numpy cosine similarity over a few hundred chunks. No external DB. Keep it behind `retrieval.py` so one could be swapped in later.
- Voice: **Sarvam AI** for STT and TTS. Read Sarvam's current official docs for endpoints, models, language codes and input limits; do not rely on memory. Fallback for STT: Gemini audio input. Use `st.audio_input` (or the current Streamlit equivalent) for the mic.
- All keys from environment variables, `.env.example` provided. Never print or commit keys.

## Build order (do it in this order; commit after each step)

**Tiers (Section 0 of the architecture):** Steps 0 to 5, Step 5b, and Step 7 for the deposit notice only are **P0**. Step 6 (voice) and the other two draft types are **P1**. Step 8 (practice) is **P2**. Finish P0 completely, with a written note in your report, before you start P1.

**Step 0: Skeleton and sample data.**
Create the repo layout from Section 4. Write `data/sample/sample_chunks.jsonl` with 6 to 8 chunks that follow the contract schema exactly, each with id prefix `SAMPLE-` and text beginning `[SAMPLE, NOT REAL LAW]`. They exist only so you can develop before the real corpus arrives. The app must show a visible red banner if any `SAMPLE-` chunk is loaded. `config.yaml` has `corpus.path` so one switch moves from sample to real.

**Step 1: `llm.py`, `retrieval.py`, config loader.**
- Corpus loader validates the schema (skip and loudly log bad lines; never crash).
- Index builder with caching.
- `search(query_en, categories, jurisdictions, k)` returning `[{id, score, chunk}]`, applying the metadata filters from Section 6. Repealed or superseded chunks are searched separately and used only for old-law detection.
- Confidence gate reads `retrieval.min_score` from config.

**Step 2: `router.py`.**
One LLM call, JSON output: category, language, state_or_city, case_file_update, missing_facts, escalation_flags, english_retrieval_query. Output must tolerate noisy voice transcripts and Hinglish. Validate the JSON; on a parse failure retry once, then fall back to `category: unclear`.
Deterministic escalation rules (Section 9) are in code plus keyword lists in `config.yaml` (English and Hindi), merged with the LLM flags.

**Step 3: `pipeline.py` advice mode, text only.**
Implement `new_session` and `handle_turn` exactly per Section 7. Answer generation prompt rules (put in `app/prompts/answer.md`):
- Use ONLY the provided source chunks. Never use outside knowledge of law, even if sure.
- Output the JSON block structure from Section 7.
- Every `legal` block cites chunk ids. Do not state any section number, rule, deadline, amount, fee or case name that is not in a cited chunk.
- If the chunks do not cover the question, say so in `gaps` and do not fill the gap.
- Plain words, Class 8 level, short sentences, answer in the user's language.
- Never promise outcomes. Never say "you will win". Say what the law says and what the options are.
- Reply structure: what I understood, where you stand (cited), your options in order, what I can prepare for you now, when to see a lawyer.
- One-line reminder: this is legal information, not legal advice.
Include the SAFE RESPONSE path (Section 10) and the clarify path (max 2 questions).

**Step 4: `verifier.py`.**
Implement every item in Section 8, point 5 (code checks) and point 6 (LLM faithfulness judge, config toggle). The regex list is a starting point: extend it and keep it in one place. Regenerate once with the issue list, then fall back to SAFE RESPONSE. Fill `TurnResult.verifier`. When you test, deliberately make the model cite a fake section and confirm the verifier catches it.

**Step 5: `ui.py`.**
Chat UI, text box plus mic button, language picker (default auto-detect, overridable), mode selector (Advice / Draft / Practice), and a collapsible "How I got this answer" panel showing: category, retrieved chunks with scores, each citation with `doc_title`, unit, `fetched_on`, `source_url`, `verified` status, and the verifier result. A persistent footer: "Legal information, not legal advice." Show a clear banner when escalation is triggered. Show the red banner if sample data is loaded.

**Step 5b: `app/cli.py` (P0).**
`python -m app.cli "mera deposit wapas nahi mila" [--lang hi-IN] [--mode advice|draft] [--mock] [--json]` prints the reply, then (with `--json`) the full `TurnResult`. `--interactive` keeps one session for multi-turn chat. This is how the human runs a new input in the interview, and how they show a model swap: edit `config.yaml`, rerun the same command.

**Step 6: `voice.py`.**
STT in, TTS out, language-aware. Chunk TTS text to the provider limit. If voice fails, degrade to text with a visible message. Test with at least Hindi and English.

**Step 7: `drafts.py` and templates.**
Section 12. Missing facts remain `[● placeholder]`. Never invent a date, name, amount or section. Offer a download.

**Step 8: `practice.py`.**
Section 12. Keep it simple: a roleplay prompt, a difficulty setting and an end-of-session coaching call that goes through the verifier. If time is short, ship this last and ship it small.

**Step 9: README.**
Setup, env vars, how to run locally, how to deploy to Streamlit Community Cloud, how to swap the model (the exact config lines), and how to run Codex's tests.

## Config (`config.yaml`) must expose at least

```yaml
models:
  router: {provider: gemini, model: "<from provider docs>"}
  main:   {provider: gemini, model: "<from provider docs>"}
  judge:  {provider: gemini, model: "<from provider docs>"}
embeddings: {provider: gemini, model: "<multilingual model from docs>"}
corpus: {path: data/corpus}          # sample path for dev: data/sample
retrieval: {top_k: 6, min_score: 0.0}   # min_score is calibrated later from Codex's calibration.md
verifier: {llm_judge: true, max_regenerations: 1}
escalation:
  high_amount_inr: 500000
  limitation_warn_months: 30
  keywords_en: [...]
  keywords_hi: [...]
# Interview swap example (one block, no code change):
#   main: {provider: openai_compatible, model: "<their model>", base_url: "<their url>", api_key_env: "KUKU_API_KEY"}
llm: {min_interval_s: 4, max_retries: 3}
mock: false
languages: [en-IN, hi-IN]
covered_states: [UP]
voice: {stt: sarvam, tts: sarvam, stt_fallback: gemini}
```

## Rules

- No prompts hardcoded in `.py` files; they live in `app/prompts/*.md`.
- Never crash on a bad API response: retry once, then degrade gracefully with an honest message.
- Every turn writes one JSON trace line to `outputs/live_trace.jsonl` (router JSON, retrieved ids and scores, verifier result, models used). Create the file if absent, and do not read the other agents' files.
- Add a `--mock` mode to `llm.py` (fixed canned outputs) so tests can run without keys. Keep it clearly separate from real behaviour. Mock `embed()` too (a deterministic hash-based vector), so the **whole** pipeline, including retrieval and the verifier, runs with no keys at all. Expose it as `config.yaml: mock: true` and as an environment variable `AI_LAWYER_MOCK=1`, so Codex's harness can switch it on.
- Rate limits: one shared client per provider, a minimum gap between calls (`config.yaml: llm.min_interval_s`), and exponential backoff on 429 or 5xx (max 3 tries). Record call counts and latency in `trace`.
- Write a `.gitignore` (`.env`, `data/index/`, `__pycache__/`, `outputs/live_trace.jsonl`).
- Do not hardcode helpline numbers, fees, limits or legal rules anywhere in code or prompts. All such facts come from the corpus.
- Log every AI mistake you notice (including your own) in `docs/ai_mistakes.md`.

## Definition of done

- `streamlit run app/ui.py` works on the sample data, then on the real corpus with only a config change.
- `handle_turn` matches the Section 7 interface exactly (Codex's tests depend on it).
- A fake citation injected into the model output is caught and never shown to the user.
- A question outside the corpus returns the SAFE RESPONSE, not an answer.
- Hindi text and a Hindi voice clip both work end to end.
- Model swap demonstrated by changing only `config.yaml`.

## Final report (write to `docs/claude_code_report.md`)

What works, what does not, known weaknesses, the exact commands to run, the config values the human should tune (especially `min_score`), and anything you assumed.
