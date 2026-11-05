# Round 2: from mock to real (written 2026-11-05 after reviewing all three reports)

## Where we are
- Corpus: 122 chunks, validator passes. The UP 2021 tenancy Act and the Code on Wages status are confirmed from India Code and e-Gazette. 18 chunks are now flagged `human_check_required` (see `docs/ai_mistakes.md`). 10 of those are agent-written summaries, not verbatim text.
- App: P0 is built. `config.yaml` now points at `data/corpus`. Tested only in mock mode so far.
- Tests: 30 cases, harness works. The mock score (15/30) mostly measures the canned mock model, not the app. The real eval has not run yet.
- The sandbox can't reach the Gemini API. **Real runs must happen on your machine**: in the Claude Code or Codex terminal, or your own terminal.

## You (about 10 minutes, blocking)
1. Get a free API key at aistudio.google.com, then create `.env` from `.env.example` with `GEMINI_API_KEY=...`. Never commit it.
2. In AI Studio, check which models your key can use and their limits. If `gemini-2.5-flash` is listed, keep it for `main`. Put `router` and `judge` on the Flash-Lite model (higher free limits). Edit only `config.yaml`.
3. Smoke test: `python -m app.cli "I vacated my flat in Lucknow 2 months ago, landlord not returning 30000 deposit" --json`

## Claude Code: paste this
> Read NEXT_ROUND.md. Fix these real code gaps (they are not mock artifacts), add a unit test for each, commit, then append to docs/claude_code_report.md:
> 1. **Minor detection.** A deterministic regex for a stated age under 18 ("I am 16", "16 years old", "16 साल का/की", "umar 16") gives a hard escalation, in addition to the keywords.
> 2. **Criminal and jail requests.** Add keywords: jail, IPC, BNS, "420", cheating case, fraud case, police case, जेल, धोखाधड़ी, "केस करूंगा", "case karunga" → out_of_scope or escalate. Keep the Hindi list in config.yaml.
> 3. **Limitation in code.** Don't rely on the LLM for date arithmetic. Have the router extract `event_date` (ISO or month+year), and have code compute `months_since_event` from today's date.
> 4. **Case-law requests.** When the user asks for a case, judgment, precedent or Supreme Court ruling (English and Hindi, e.g. फैसला) and no `judgment` chunk is retrieved, the reply must include the localized line "I can't cite court cases; I don't have verified judgments", and set `needs_lawyer=True`. Do this deterministically in pipeline.py, not only in the prompt.
> 5. **Hindi body text.** With a real model, check that Hindi users get a Hindi body (not just Hindi labels). If not, enforce the reply language in answer.md, and retry once if the script doesn't match.
> 6. Show `source_type` and the `REVIEW` status_note in the "How I got this answer" panel. When a cited chunk is `secondary`, add "(unverified source – check before relying on it)".
> 7. Then run the CLI smoke test above with the real key and paste the output into your report.

## Codex: paste this (after Claude Code finishes)
> Read NEXT_ROUND.md. The real corpus now exists and config points at it. Map `expected_chunk_ids` for the 30 cases from data/corpus (keep expected_law_verified=false). Then run the real eval with `--sleep 6` and without --judge first. If you hit a quota error, resume the next day or with `--retry-infra`. Write the calibration with 2 or 3 candidate thresholds, regenerate BUGS.md from the real run only, and update docs/codex_report.md. Label mock-only findings as such.

## Antigravity: paste this (in parallel)
> Read NEXT_ROUND.md and docs/ai_mistakes.md (the last two entries). Re-fetch the 10 chunks marked `secondary` with a REVIEW note, verbatim, from deep official URLs (the exact page). If no official page states the text, delete the chunk and log it in FAILURES.md. Don't paraphrase. Also replace the homepage URLs on the 8 rule and UP Shops Act chunks with the exact document URL (the gazette PDF or India Code handle). Remove "REVIEW" notes only where fixed. Re-run validate_corpus.py, regenerate verification_sheet.csv, and append to docs/antigravity_report.md.

## You again (after the runs)
- Tick `data/verification_sheet.csv`: the 6 helpline numbers on the official sites, every money or time limit, every non-in_force status. Set `verified: "human"` on what you checked.
- Choose `retrieval.min_score` from Codex's calibration, then do one final full run. That run becomes `outputs/raw/`.
- Record 2 Hindi and 1 English voice clips only if Claude Code finishes voice (P1). Otherwise state "text only; voice designed but not shipped" in the doc. Honest beats overpromising.
- Then come back here for the 2-page doc and the walkthrough script.
