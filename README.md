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

## Deploy (Streamlit Community Cloud)
1. Push the repo to GitHub (never commit `.env`).
2. On share.streamlit.io choose the repo, main file `app/ui.py`.
3. In Advanced settings -> Secrets add `GEMINI_API_KEY = "..."` (and `SARVAM_API_KEY` once voice exists).
4. Make sure `config.yaml` points `corpus.path` to `data/corpus`.

## Not built yet
Voice (Sarvam STT/TTS), the consumer and salary draft types, and practice mode. See the report.
