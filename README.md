---
title: Haq - AI legal help for everyday problems
emoji: ⚖️
colorFrom: indigo
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

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

## Web app (main UI)
```
python -m app.serve            # opens http://localhost:7860 in your browser
python -m app.serve --mock     # no API keys: canned model
```
A FastAPI backend (`app/server.py`) serves a single-page chat UI (`app/web/`):
- type or speak, in any of 10 Indian languages
- answers with clickable source stamps and a "How I got this answer" panel
- a live case file that fills in as you talk
- draft notices you can copy or download

Chats are saved only in the user's browser (localStorage) and can be exported. Each turn sends the chat's saved state back to the server, so the conversation survives a server restart. The older Streamlit UI (`streamlit run app/ui.py`) still works.

Product features:
- **Live stage streaming** over Server-Sent Events (`/api/turn/stream`), so users see "Finding the law…" and "Checking each claim…" as they happen.
- **Interface in English, Hindi and Telugu.** Answers come in 10 languages.
- **First-run privacy notice**, including "don't type Aadhaar or bank numbers".
- **Feedback.** Thumbs up/down goes to `outputs/feedback.jsonl`. The question and answer text are stored only if the user ticks "share", and the file is git-ignored.
- **Per-IP rate limits**, set with `HAQ_TURNS_PER_10MIN` and `HAQ_VOICE_PER_10MIN`.
- **Security headers** (CSP, nosniff, microphone permission policy).
- **`/api/stats`** shows today's model usage against the free-tier budgets.
- **Installable as a phone or desktop app** (PWA). The service worker caches only the app shell, never legal answers.

Engine safeguards added in this round:
- **Claim-level pruning.** When one claim fails verification, only that claim is dropped and the rest of the verified answer is kept, with a note.
- **Conflict detection.** When two different dates or amounts are given, the user is asked to confirm, and drafts leave a blank.

Offline checks: `python -m app.selfcheck_server` (21 checks, mock mode).

## Deploy (free): Hugging Face Spaces, Docker
1. Create a new Space at huggingface.co/new-space. Choose SDK **Docker** and a blank template, and make it Public.
2. Push this folder to the Space's git repo (or link the GitHub repo). The YAML header at the top of this README configures the Space (port 7860). `.env` and run outputs are excluded by `.gitignore` and `.dockerignore`.
3. In the Space's Settings, under Variables and secrets, add the secrets `GEMINI_API_KEY` and `SARVAM_API_KEY`.
4. The Space builds the Dockerfile and starts. The embedding cache is committed, so a cold start does not re-embed the corpus.
5. A public Space uses your free-tier quota for every visitor. The model fallback chain handles 429s, but share the link only with reviewers.

The same Dockerfile runs on Render or Railway (they set `PORT`). The Streamlit Community Cloud route also still works with `app/ui.py`.

## Not built yet
Practice mode (roleplay against the other side). Languages beyond English and Hindi are untested.
