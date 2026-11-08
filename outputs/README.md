# Raw outputs (unedited)

Everything here was produced by running Haq; nothing was edited by hand.

| Folder / file | What it is |
| --- | --- |
| `live/20261108-190709.md` and `.json` | **Final design.** 27 test questions (29 turns) run on real models on 8 Nov 2026. The `.md` shows each question, the reply, which path answered it (law library, web search, general information, small talk, refusal), the reply language, time and models used. The `.json` is the same run, machine-readable. Questions: `../tests/live_questions.jsonl`. |
| `raw/T-001.json` ... `raw/T-055.json` | **Earlier version** (before the November redesign). 55 test cases written by a separate agent (Codex), one file per case with the full reply, citations, verifier result and trace. Cases: `../tests/cases.jsonl`. |
| `summary.md`, `results.csv`, `rescore_summary.md`, `BEFORE_AFTER.md` | Automatic scoring of the 55-case run (42/55 passed) and how it changed across rounds. |
| `referrals.md`, `referrals.csv`, `calibration.md`, `perf.md`, `server_api.md` | Office-referral precision and recall, confidence-gate calibration, latency, API checks. |
| `runs/` | Every earlier evaluation run (mock and real), kept for the record. |

In the final live run, three questions needed live web search, which Google refused on the free API key (search quota), so they fell back to labelled general information. This is reported, not hidden, in the solution doc.
