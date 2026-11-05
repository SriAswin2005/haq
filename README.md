# AI Lawyer for India (prototype)

A chat assistant that helps ordinary people with three everyday legal problems (consumer refunds, unpaid salary, rental security deposits), in English and Hindi. It gives legal **information, not legal advice**, and is built so it never invents law: every legal statement must cite a verified source chunk or it is not shown.

Design contract: `00_ARCHITECTURE.md`. Build brief: `01_CLAUDE_CODE_BUILD.md`. Status and tuning notes: `docs/claude_code_report.md`.

## Setup
```
pip install -r requirements.txt
cp .env.example .env        # then put your GEMINI_API_KEY in .env
```
Python 3.10+. Keys are read from environment variables only and never printed.

## Run
Web UI: `streamlit run app/ui.py`

CLI (also the interview demo):
```
python -m app.cli "mera deposit wapas nahi mila, Lucknow, 20000 rupees" --lang hi-IN --json
python -m app.cli --interactive
python -m app.cli "message" --mode draft      # deposit demand notice
```
**No keys needed:** add `--mock`, or set `AI_LAWYER_MOCK=1`, or `mock: true` in `config.yaml`. Mock mode uses a canned model and hash embeddings, so retrieval, the verifier and the whole pipeline still run. It is not real model behaviour.

## Corpus: sample vs real
`config.yaml` -> `corpus.path`. `data/sample` holds FAKE chunks (ids start `SAMPLE-`); the UI shows a red banner when any are loaded. Switch to `data/corpus` once the real corpus passes `data/validate_corpus.py`. The embedding cache in `data/index/` rebuilds only changed chunks.

## Swap the model (config only)
Edit `config.yaml`. Each role (`router`, `main`, `judge`) can differ:
```yaml
models:
  main: {provider: openai_compatible, model: "<their model>", base_url: "<their url>", api_key_env: "KUKU_API_KEY"}
```
Providers: `gemini`, `openai_compatible`, `anthropic`. Set the matching key in `.env`, rerun the same command. Embeddings are configured separately under `embeddings:`; if you change the embedding model, the cache keys on the model name so it re-embeds automatically.

## Tune
`retrieval.min_score` (confidence gate) should be set from `outputs/calibration.md`. `escalation.*` holds the amount threshold, the limitation warning and the English/Hindi keyword lists.

## Tests
Codex's harness lives in `tests/` and calls only `app.pipeline.handle_turn`. Run with `AI_LAWYER_MOCK=1` for keyless runs (see `tests/` for the exact command).

## Voice
- UI: the mic recorder sits above the text box. The sidebar setting "Read answers aloud" (When I speak / Always / Never) controls speech output.
- CLI: `python -m app.cli --audio question.wav --speak answer.wav`
- Speech to text: Google first (`gemini-3.5-transcribe`, then Flash-Lite audio input, free tier), with Sarvam (`saaras`) only if every Google model fails. Gemini takes the whole recording; for Sarvam, recordings over ~28 s are split.
- Text to speech: Google first (Gemini TTS models, free tier), with Sarvam (`bulbul`) only if every Google model fails. Only the first ~1800 characters are spoken; the full answer stays on screen.
- The `trace` records which model served each step (`tts.provider` / `tts.model`). The CLI prints `[heard via ...]`.
- Offline checks: `python -m app.selfcheck_voice`

## Drafts
Draft mode builds the document for the routed category: a deposit demand notice (tenancy), a salary demand notice (wages), or a grievance-officer complaint plus the facts for a consumer commission complaint (consumer). Unknown facts stay as `[● placeholder]`. Legal references come only from retrieved, in-force chunks.

## Model routing
Each role in `config.yaml` is an ordered fallback chain with per-model rpm/tpm/rpd. `python -m app.models --probe` checks them. `python -m app.selfcheck_fallback` tests the switching offline. Every switch is recorded in `trace.llm.fallbacks`.

## Deploy (Streamlit Community Cloud, free)
1. Push the repo to GitHub. `.env` is git-ignored; check `git status` shows no keys. Kuku's input pack is outside this folder and must never be added.
2. On share.streamlit.io: New app -> pick the repo and branch, main file `app/ui.py`. In Advanced settings choose Python 3.11.
3. In Advanced settings -> Secrets paste:
   ```
   GEMINI_API_KEY = "..."
   SARVAM_API_KEY = "..."
   ```
4. Deploy. The embedding cache (`data/index/embeddings_gemini-embedding-001.json`) is committed, so a cold start does not re-embed the corpus. A changed chunk is re-embedded automatically.
5. Daily model budgets are tracked per container. If the app restarts it starts counting from zero, and Google's own 429s are still handled by the fallback chain.

## Not built yet
Practice mode (roleplay against the other side). Languages beyond English and Hindi are untested.
