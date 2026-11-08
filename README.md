# Haq: an AI lawyer for India (prototype)

**Haq** is a chat assistant that explains everyday legal problems in India to ordinary people, by text or voice, in their own language: what the law says, what they can get and what to do. It gives legal **information, not legal advice**, and is built so it never invents law: every legal point cites a passage from its law library (431 passages from about 45 Acts and rules, plus 40 official offices) or a web page found by live Google Search, or it is not shown.

Solution doc: `docs/solution/`. Test questions and raw outputs: `tests/`, `outputs/`. Mistakes the AI tools made while building it: `docs/ai_mistakes.md`.

Original design contract (before the November redesign below): `00_ARCHITECTURE.md`. Build brief: `01_CLAUDE_CODE_BUILD.md`. Review that led to the redesign: `docs/production-review/`.

## Setup
```
pip install -r requirements.txt
cp .env.example .env        # then put your GEMINI_API_KEY in .env
```
Python 3.10+. Keys are read from environment variables only and never printed.

## Run
Legacy Streamlit UI: `pip install -r requirements-ui.txt` then `streamlit run app/ui.py`

CLI (also the interview demo):
```
python -m app.cli "mera deposit wapas nahi mila, Lucknow, 20000 rupees" --lang hi-IN --json
python -m app.cli --interactive
python -m app.cli "message" --mode draft      # deposit demand notice
```
**No keys needed:** add `--mock`, or set `AI_LAWYER_MOCK=1`, or `mock: true` in `config.yaml`. Mock mode uses a canned model and hash embeddings, so retrieval, the verifier and the whole pipeline still run. It is not real model behaviour.

## How an answer is built (Nov 2026 redesign)
1. **Router** decides the kind of message: small talk (a normal short reply), a request to cause harm (refused, no steps), or a legal question; plus topic, state, country, language and whether anyone is in danger right now.
2. **Law library first.** For a legal question, Haq searches the whole library (vectors plus keywords for exact Act names and section numbers). If a passage matches, the answer quotes and cites it: short answer, what the law says, what you can get, what to do. Every claim is checked by code and by a judge model; claims that fail are removed.
3. **Live web search** when the library has no passage: Gemini with Google Search. Only sentences Google ties to a source are kept, each with its numbered source; forums and social media never count. Google's search-suggestion chip is shown as required.
4. **Labelled general information** only if both fail, with everything specific (sections, fines, deadlines, case names) removed by code.
5. A lawyer is mentioned only when there is a real reason (already in court, arrested, large sums, deadline), as one line under the answer. Real danger puts a 112 line first; the answer still follows.

Useful commands:
```
python -m app.build_index                 # embed new library passages ahead of time (free quota: ~1,000 a day)
python -m app.try_questions               # run tests/live_questions.jsonl on real models -> outputs/live/<time>.md
python -m app.try_questions --text "can police arrest me without a warrant"
```
Diagnostic traces (they contain users' words) are written only when `HAQ_WRITE_TRACES=1`.

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
`retrieval.min_score_by_model` is the confidence gate for each embedding model (below it, Haq goes to live web search instead of the library). `escalation.*` holds the amount and limitation thresholds that add a lawyer note under the answer.

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

## Deploy (main): Azure Container Apps + GitHub Container Registry
Free with Azure for Students (no card): Container Apps has a permanent free monthly grant (180,000 vCPU-seconds,
360,000 GiB-seconds, 2 million requests) and the app scales to zero when idle, waking in seconds.
1. Every push to `main` runs `.github/workflows/container.yml`, which builds the Dockerfile and publishes
   `ghcr.io/<github-user>/haq:latest` (make the package public once in GitHub -> Packages -> haq -> settings).
2. One-time setup (Azure CLI):
   ```
   az group create -n haq-rg -l centralindia
   az containerapp env create -n haq-env -g haq-rg -l centralindia --logs-destination none
   az containerapp create -n haq -g haq-rg --environment haq-env --image ghcr.io/<github-user>/haq:latest \
     --target-port 7860 --ingress external --cpu 0.5 --memory 1.0Gi --min-replicas 0 --max-replicas 1 \
     --secrets gemini-key=<your key> --env-vars GEMINI_API_KEY=secretref:gemini-key
   ```
3. After a new push has built: `az containerapp update -n haq -g haq-rg --image ghcr.io/<github-user>/haq:<commit sha>`.

## Deploy (alternative, free, long-running): Render + GitHub
Why Render: its free web service has no expiry date and no credit card. One service running all month uses about
744 of the 750 free hours each workspace gets, so it is never suspended. (Hugging Face now needs a paid plan for
Docker Spaces; Railway and Fly.io have no lasting free tier.) The catch: after 15 minutes without visitors it sleeps,
and the next visit takes about a minute to wake it.

1. Push this repo to GitHub (public, so reviewers can read it).
2. On render.com, sign in with GitHub, then New -> Blueprint -> pick the repo. `render.yaml` sets up one free Docker
   web service. Paste your `GEMINI_API_KEY` when asked (`SARVAM_API_KEY` is optional).
3. Wait for the first build (about 5 minutes). The app is at `https://haq-ai-lawyer.onrender.com` (or the name Render shows).
4. Every push to GitHub redeploys automatically.
5. Optional, while reviewers are looking: a free cron-job.org job that opens `/api/meta` every 14 minutes keeps it
   awake. That endpoint never calls the AI, so it costs no Gemini quota. Only do this if it is your only free Render service.

What keeps it working for months: the embedding cache is committed (no re-embedding on restart), every AI role has a
fallback chain ending in Google's `gemini-flash-lite-latest` alias (which moves to the newest model when old ones
retire), and the app needs no database. What could still break it: the Gemini key being revoked or the free tier
being withdrawn, or `gemini-embedding-2` being retired (then set a new model under `embeddings:` and run `python -m app.build_index`).
The same Dockerfile runs anywhere that sets `PORT`.

## Not built yet
Practice mode (roleplay against the other side). No lawyer has reviewed the answers, and about 200 library passages with numbers still await a human check against the official page (`data/verification_sheet.csv`).
