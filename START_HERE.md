# Start here (for the human)

1. Open this `ai-lawyer` folder as the workspace in each tool. Never open the parent folder: the Kuku screenplays and the assignment PDF are confidential and must not get into the repo.
2. Run `git init` in this folder once.
3. Paste one of these prompts into each agent:

**Claude Code**
> Read `00_ARCHITECTURE.md` fully, then `01_CLAUDE_CODE_BUILD.md`. Build P0 completely before anything else, in the step order given. Don't ask me questions; log assumptions in `docs/ASSUMPTIONS.md`. Commit after each step. Finish with `docs/claude_code_report.md`.

**Antigravity**
> Read `00_ARCHITECTURE.md` fully, then `02_ANTIGRAVITY_CORPUS.md`. Do the Step 0 capability test first and report it. Then collect in the priority order given, validating each category file as you finish it. Verbatim official text only; log every failure. Finish with `docs/antigravity_report.md`.

**Codex**
> Read `00_ARCHITECTURE.md` fully, then `03_CODEX_TESTS.md`. Write the 30 priority cases and `tests/checks.py` first, then `run_eval.py`, and test it in mock mode. Run the real eval only when `docs/claude_code_report.md` exists. Finish with `docs/codex_report.md`.

4. Your own checkpoints:
   - After about 20 min, check Antigravity's capability test. If it can't fetch India Code, download the PDFs yourself into `data/raw_pdfs/` and tell it to parse them.
   - When `data/verification_sheet.csv` appears, check every number, deadline, helpline and non-in-force status.
   - Pick `retrieval.min_score` from `outputs/calibration.md`.
   - Record 2 or 3 voice clips (Hindi and English).
