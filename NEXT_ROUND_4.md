# Round 4 (6 Nov 2026): broad coverage, the "where to go" directory

**Why.** Most everyday legal questions are really "who handles this and how do I reach them?". India has an official body for nearly every everyday grievance, and each one is a single official page to verify, not a web of statutes. So Haq gets broad coverage at low risk:

| Tier | What Haq gives | Coverage |
|---|---|---|
| 1. Where to go | an official body, portal and helpline, quoted from its own page | every directory topic (this round) |
| 2. What the law says | verbatim statutes, cited | covered topics only |
| 3. Help with my case | drafts, case file, follow-ups | rental deposit, salary, consumer refund |

**Engine (done).** Out-of-scope questions show at most 2 referrals, and only:
- verified `official` directory, procedure or helpline chunks,
- scoring at least `retrieval.referral_min_score` (0.70, stricter than the 0.66 answer gate),
- worded as "an official service that **may** handle this (please check its page)".

Helpline numbers are copied from the chunk text, never typed by a model. Covered-topic answers can also cite directory chunks, because they live in `common`. Tests: `app/tests/test_referrals.py`. Precision over recall: a wrong office misleads, a missing one only falls back to legal aid.

## Antigravity: paste this
> Read NEXT_ROUND_4.md and 02_ANTIGRAVITY_CORPUS.md. The same non-negotiable rules apply: verbatim official text only, deep URLs, never construct a URL, log failures, never invent.
> Build **data/corpus/directory.jsonl**: one chunk per official grievance body. Use the existing contract (no new fields):
> - `category: common`, `doc_type: portal_procedure` (or `helpline` if it is mainly a phone line), `id: COM-DIR-<SHORTNAME>`, `unit: P`, `unit_number: <SHORTNAME>`
> - `jurisdiction: central` (or `UP`), `status: in_force`, `source_type: official`, `human_check_required: true`, `fetched_on: today`
> - `doc_title`: the body's official name. `heading`: what it handles, in the page's own words (a short phrase).
> - `text`: VERBATIM paragraphs from that body's own official page saying what complaints it handles, how to file (portal, app, helpline), and its contact numbers. If the page does not say what it handles, skip the entry and log it.
> - `source_url`: the exact page you copied from. Official domains only (.gov.in, .nic.in, or the regulator's own domain such as rbi.org.in, sebi.gov.in, irdai.gov.in).
>
> Candidates. Find each one's official page yourself, and skip any you cannot verify:
> - **Money:** RBI Complaint Management System / Integrated Ombudsman (banks, NBFCs, digital payments); SEBI SCORES; IRDAI Bima Bharosa; EPFO grievance (EPFiGMS); ESIC grievance.
> - **Cyber:** National Cyber Crime Reporting Portal and helpline 1930; Sanchar Saathi (lost or stolen phone, suspected fraud communication).
> - **Transport:** Parivahan e-Challan (pay or check a challan); Virtual Courts (traffic challans); RailMadad; AirSewa.
> - **Government services:** CPGRAMS (central grievances); UP IGRS / Jansunwai; RTI Online; Passport Seva grievance; UIDAI (Aadhaar) grievance.
> - **Consumer:** e-Daakhil (online consumer complaints); FSSAI consumer complaint (FoSCoS).
> - **Work:** e-Shram; UP Labour Department complaint.
> - **Housing and utilities:** UP RERA complaint; UPPCL electricity complaint / consumer grievance forum.
> - **Safety and rights:** UP Police citizen services / online complaint; National Commission for Women complaint; Childline 1098; NCPCR complaint; Elderline 14567; NHRC complaint.
> - **Legal help:** Tele-Law (Department of Justice); Lok Adalat (NALSA pages).
>
> Aim for 35 to 45 verified entries; fewer is fine if the rest cannot be verified. Run validate_corpus.py, add every entry to verification_sheet.csv (all have numbers), and append a "Directory" section to MANIFEST.md and docs/antigravity_report.md listing which bodies were verified and which were skipped, with the reason.

## Codex: paste this (after the directory exists)
> Read NEXT_ROUND_4.md. Do not edit app/ or data/.
> Write 15 cases (T-041..T-055), each an everyday out-of-scope question in English, Hindi or Hinglish: UPI fraud, bank card charge, insurance claim rejected, PF withdrawal stuck, traffic challan, train refund, flight refund, lost phone, RTI request, Aadhaar update problem, electricity bill dispute, builder delay, harassment by a loan recovery agent, a senior citizen neglected, a food adulteration complaint.
> For each, set `expected_referral_any` (list of acceptable directory ids) and add `check_referral` in tests/checks.py:
> - **PASS** if the reply names one of the expected bodies, or names no referral at all (legal aid only).
> - **HARD FAIL** if it names a different body, or contains any statute or section pattern.
> - Report referral precision (correct / shown) and recall (correct / expected) separately.
> Then run these cases in the real eval and add the numbers to outputs/BEFORE_AFTER.md.

## You (human)
- Check every directory row in verification_sheet.csv (about 1 hour for ~40 rows). Each row is one official page: open it, confirm the name, what it handles and the number.
- Next code step (Claude, after the deadline): make topics configuration-driven, so a new deep topic (e.g. traffic challans) is just data, config and tests.
