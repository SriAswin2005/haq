# Brief for Antigravity: Build the verified legal corpus

**First, read `00_ARCHITECTURE.md` completely, especially Section 5 (the data contract). It wins any conflict with this file.**

You own: everything inside `data/` except `data/sample/` and `data/index/` (Claude Code's). Do not touch `app/`, `tests/` or `outputs/`.

## Your mission

Collect, from **official sources only**, the legal text that an AI will rely on to answer everyday problems about **consumer refunds, unpaid salary and rental deposits** in India (Uttar Pradesh as the one covered state), and deliver it as clean JSONL chunks in exactly the contract format.

Be careful about this. The whole project exists to avoid invented law. **A small, correct corpus is far better than a large, doubtful one.** If you cannot verify something, leave it out and log it.

## The non-negotiable rules

1. **Verbatim only.** `text` is copied word for word from the official source. No summaries, no paraphrase, no "cleaned up" wording, nothing from memory or from your own model knowledge. Fixing OCR errors or removing page numbers and headers is fine. Rewording is not.
2. **Official sources first.** Government and court sites only: India Code (indiacode.nic.in), e-Gazette (egazette.gov.in), Legislative Department (legislative.gov.in), Department of Consumer Affairs (consumeraffairs.nic.in), e-Daakhil (edaakhil.nic.in), Ministry of Labour and Employment (labour.gov.in), UP Labour Department and UP government sites, NALSA (nalsa.gov.in), Supreme Court and High Court sites. These are starting points, so check each URL actually resolves. Never construct a URL from memory and assume it works.
3. **Secondary sources** (law blogs, aggregators, news) may be used only to *find out what to look for*, never as chunk text. If you must use one as the only available text, mark `source_type: secondary` and `human_check_required: true`.
4. **Every chunk has the exact `source_url` it was copied from and `fetched_on`** (today's date).
5. **Status is the hard part. Check it properly.** India has been replacing and consolidating many old laws (criminal laws, labour laws and others). For every Act and rule you collect, find out whether it is currently in force, repealed, superseded or only partly in force, and what replaced it. Record the evidence URL in `STATUS_REGISTER.csv`. If you cannot establish status from an official source, set `status: unclear`. Do not guess. This matters most for the wages category.
6. **If you cannot fetch it, log it.** Add it to `data/FAILURES.md` with the URL and the reason. Do not fill the gap from memory.
7. **Do not translate.** The corpus is English in v1.

## Step 0: Capability test (do this first, report it)

Before any collection, fetch one small official page (for example one section of an Act from India Code) and confirm you can read and extract its text. If you cannot browse or fetch, or sites block you, write that in `data/FAILURES.md` and stop. The human will then download PDFs manually, and you will parse them. Do not pretend you fetched something.

## Priority order (deliver in this order; the corpus is usable at every stop)

Validate and save each category file as soon as it is done, so Claude Code can switch from sample data early.

1. **P0 `common`**: NALSA / legal aid provisions, and the helplines (small, but the app needs them for every refusal).
2. **P0 `tenancy`**: the UP 2021 tenancy Act's deposit, Rent Authority and repeal sections (see the lead below), plus the core Transfer of Property Act lease provisions.
3. **P0 `consumer`**: the Consumer Protection Act, 2019 core sections, the current pecuniary-jurisdiction rule, and the e-Daakhil and National Consumer Helpline procedures.
4. **P1 `wages`**: the Code on Wages core sections, status evidence, and 2 or 3 sections of the old Acts marked as repealed.
5. **P1** everything else on the list.

Target **60 to 100 chunks in total**. 150 is a ceiling, not a goal.

## What to collect (candidate list; verify each one, find the exact current titles yourself)

These are topics to *look for*, not facts to trust. Section numbers and exact names must come from what you actually read.

**consumer**
- Consumer Protection Act, 2019: definitions (consumer, defect, deficiency, unfair trade practice), consumer rights, who can file, where to file (District, State, National Commission), pecuniary jurisdiction, how a complaint is made, limitation period, product liability basics.
- Rules under the Act: jurisdiction and pecuniary limits, complaint fees, the e-commerce rules (grievance officer, refund obligations), the consumer commission procedure rules. Find the current versions.
- Official procedure pages: how to file on e-Daakhil, the National Consumer Helpline (how to lodge a grievance), what documents are needed.

**wages**
- The current central wage law and its status. India's wage laws were consolidated into new labour codes. *Lead, verify it yourself:* law-firm summaries and SCC Online report that the four codes (Code on Wages, 2019; Industrial Relations Code, 2020; Code on Social Security, 2020; OSH Code, 2020) were brought into force by Ministry of Labour notifications dated **21 November 2025**, repealing among others the Payment of Wages Act, 1936, the Minimum Wages Act, 1948, the Payment of Bonus Act, 1965 and the Equal Remuneration Act, 1976. The Payment of Gratuity Act, 1972 is reported as repealed by the Social Security Code. Rules under the codes (central and UP) were notified later and in pieces, so record the status of the **rules** separately from the **codes**. Use the e-Gazette notifications as the `evidence_url`. State shops-and-establishments Acts were reportedly **not** repealed by the codes. Establish which Act(s) are in force today, which are repealed, and since when. Collect the provisions on timely payment of wages, deductions, unpaid wages claim procedure, authority and forum, time limits. Also collect the old Acts as `repealed` or `superseded` chunks (a few key sections), so the system can recognise a user citing the old law.
- Gratuity and final-settlement dues: find which law governs now.
- Uttar Pradesh: the state shops-and-establishments law, UP Labour Department complaint or grievance process for unpaid wages, any official portal procedure.
- Official labour-complaint portal procedures (central and UP).

**tenancy**
- Transfer of Property Act, 1882: the lease provisions relevant to rent, notice and possession.
- Model Tenancy Act, 2021: mark `status: model_only`. UP passed its own Act (below) instead of adopting the model text, so UP users are answered from UP's Act. Collect the model Act only if time allows (P2).
- **Uttar Pradesh rent law.** *Lead, verify it yourself:* the UP Urban Buildings (Regulation of Letting, Rent and Eviction) Act, 1972 appears to have been **replaced** by the **Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021** (UP Act No. 16 of 2021, enacted 24 August 2021 per India Code, after ordinances from January 2021). Secondary sources say it has a security-deposit section (a cap on the deposit, and a refund when vacant possession is handed back, after lawful deductions), a Rent Authority, Rent Court and Rent Tribunal structure, and a bar on civil courts for matters it covers. From the **official text** (India Code, or the UP Housing department or gazette), collect: the deposit section, the sections on applying to the Rent Authority and its time limits, the definitions they depend on, the repeal-and-savings section, and the applicability or extent section (which areas it covers). Check whether UP has notified rules or forms under it. Also collect 2 or 3 key sections of the 1972 Act **only** if the official source shows its status, marked `repealed` or `superseded`, for old-law detection.
- Registration and stamp requirements for rent agreements (Registration Act, Indian Stamp Act as applied in UP).
- The general money-recovery route, for users outside UP or outside the 2021 Act's area: legal notice, civil recovery suit, summary procedure. Collect the official text of the relevant Code of Civil Procedure provisions and the Indian Contract Act provisions on breach and compensation, if they are the correct source. (P1.)
- Whatever you find about UP deposits, **including if the lead above turns out to be wrong**, state it in `MANIFEST.md` with the evidence URL. Do not manufacture a rule.

**common**
- Limitation Act, 1963: the general limitation provisions for money recovery and how limitation works.
- Legal Services Authorities Act, 1987: free legal aid eligibility, NALSA and State Legal Services Authority, Lok Adalat.
- How to send a legal notice: any official guidance. If no official source exists, do not write one yourself. Log the gap.
- **Helplines (`unit` = `H`)**: National Consumer Helpline, NALSA legal aid helpline, UP legal services authority contact, labour helpline, emergency and women's helplines. Copy from official pages only, with the URL. These are the only source the app uses for phone numbers, so wrong numbers here are dangerous. Mark every one `human_check_required: true`.

**Judgments (optional, lowest priority, maximum 5 in total).** Only if the full judgment is available on an official court site and you can quote an exact passage verbatim, with the case name, court, date and exact URL. Use `doc_type: judgment`, `unit: J`. If there is any doubt, skip. If time is short, skip all of them.

## Size and chunking

- Aim for roughly **15 to 40 chunks per category**, under about 150 in total. Choose the provisions that a real person with these problems needs: their rights, where to complain, how, the time limit, the fee, the documents required, the deadlines.
- One chunk = one section or one self-contained provision or procedure step. If a section is very long, split it at sub-section boundaries, with ids like `...-S35-a`, `...-S35-b`.
- Include the **heading** and, where a section depends on a definition, make sure the definition chunk is included too.

## Deliverables (all inside `data/`)

1. `corpus/consumer.jsonl`, `corpus/wages.jsonl`, `corpus/tenancy.jsonl`, `corpus/common.jsonl`. Contract schema exactly, ids unique and stable.
2. `validate_corpus.py`: checks every line against the schema and rules in Section 5 (required fields, allowed enum values, unique ids, non-empty `text`, `source_url` present, `human_check_required` true for any chunk containing digits followed by words like days, months, years, rupees, lakh, crore, or `%`, or for any `helpline` chunk or `secondary` source). Prints a pass/fail summary and exits non-zero on failure. Run it on your own output and fix everything until it passes.
3. `STATUS_REGISTER.csv`: one row per Act or rule collected (columns in Section 5).
4. `MANIFEST.md`: a table of every document (title, category, jurisdiction, number of chunks, source URL, status, issues) plus **findings**: for example "no direct UP deposit provision found" or "old wage Acts repealed on X per source Y".
5. `FAILURES.md`: everything you could not fetch or verify, with the reason.
6. `verification_sheet.csv`: for the human. Include **all** chunks where `human_check_required` is true, all chunks whose status is not `in_force`, plus a **random 20% sample** of the rest. Columns: `id, doc_title, unit_number, source_url, status, why_flagged, human_verdict (blank), human_notes (blank)`.

## Self-check before you finish

- Pick 10 random chunks and re-open the source URL. Does the chunk text match the source exactly? Fix or delete any that do not. Say what you checked in your report.
- Search your own corpus for any chunk whose text you did not directly copy from a fetched page. Delete it.
- Confirm `validate_corpus.py` passes.
- Confirm there is no text written by you in any `text` field.

## Rules

- Do not touch other agents' folders. Do not set `verified: "human"` (only the human does).
- Never invent a URL, section, rule number, fee, limit or date. If unsure, `status: unclear` or leave it out.
- Log every mistake you or an AI tool made while collecting (wrong section, dead link, wrong status, hallucinated source) in `docs/ai_mistakes.md`: `date | antigravity | what went wrong | how caught | fix`. Real examples are valuable to the human.
- Do not ask the human questions mid-task; assume, write the assumption to `docs/ASSUMPTIONS.md`, move on.

## Final report (write to `docs/antigravity_report.md`)

What you collected, per category counts, what failed, what you could not establish, every status finding with evidence, and the specific items the human must personally verify (all numbers, deadlines, helplines, and every non-`in_force` status).
