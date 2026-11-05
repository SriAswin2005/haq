# Corpus Extraction Failures, Gaps, and Blockers Log

**Agent:** Antigravity (Corpus Collector)  
**Date:** 2026-11-05 (Updated Round 2)

This document logs every source URL, fetch attempt, or statutory instrument that failed, was blocked, was unavailable, or lacked an official statutory publication.

---

### 1. Step 0 Capability Test: India Code Single-Page Application (SPA) & SSL Verification
- **Target URL:** `https://www.indiacode.nic.in` and `https://indiacode.gov.in`
- **Attempted Action:** Direct HTML fetch and page scraping for statutory text.
- **What Failed:**
  1. `https://www.indiacode.nic.in` issued an HTTP refresh header `<meta http-equiv="refresh" content="3;url=https://indiacode.gov.in">`, redirecting to a new portal.
  2. The new portal at `https://indiacode.gov.in` is built as an Angular/DSpace SPA frontend. Direct HTTP GET requests returned only an empty shell (`<ds-app></ds-app>`) with no readable statutory section text.
  3. Python's default SSL certificate store (`certifi`) rejected connections to several Indian NIC servers (`legislative.gov.in`, `labour.gov.in`) with error `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate` because the Indian Controller of Certifying Authorities (CCA) root chain is not distributed in default Python wheels.
- **Resolution / Workaround:**
  Reverse-engineered the frontend JavaScript bundle (`main.993087688882fc35.js`) to uncover the official backend HAL/REST API at `https://indiacode.gov.in/server/api/`. By querying the API directly with an unverified SSL context, verbatim official section metadata and text were successfully retrieved under `dc.identifier.section_page_note`.

---

### 2. Statutory Gap: Official Central Guidance on "How to Send a Legal Notice"
- **Target Subject:** Formal government guidelines for ordinary citizens on drafting and dispatching a private legal notice for money recovery.
- **Attempted Sources:** Department of Justice (`doj.gov.in`), e-Courts (`ecourts.gov.in`), NALSA (`nalsa.gov.in`), Legislative Department (`legislative.gov.in`).
- **Reason for Failure / Gap:** 
  In Indian law, sending a pre-litigation legal notice for private money/deposit recovery is a customary common-law practice based on the Law of Contract and Specific Relief; there is no standalone Central or State statute or official government circular titled "How to Send a Legal Notice" for private disputes (unlike statutory notices under Section 80 CPC for government suits or Section 138 NI Act for cheques).
- **Compliance Action:** 
  Per the non-negotiable instruction in Brief Section 2 ("If no official source exists, do not write one yourself. Log the gap"), no fabricated or secondary-source guidance was written into the corpus. Instead, statutory notice provisions under substantive law (Section 106 Transfer of Property Act, Section 18 Limitation Act on acknowledgment) were included, and the general guidance gap is logged here.

---

### 3. Model Tenancy Act, 2021
- **Target Subject:** Model Tenancy Act, 2021 (Ministry of Housing and Urban Affairs).
- **Reason for Skipping:**
  The brief explicitly notes: "Model Tenancy Act, 2021: mark status: model_only. UP passed its own Act instead of adopting the model text, so UP users are answered from UP's Act. Collect the model Act only if time allows (P2)."
- **Decision:**
  Excluded from P0/P1 corpus to prioritize the legally binding and verified Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021. This prevents the model from conflating non-binding central model suggestions with actual enforceable UP state law.

---

### 4. Direct Court Judgment Quotes (P2 Stretch Goal)
- **Target Subject:** Supreme Court and High Court judgment extracts on security deposit refund and wage delay.
- **Reason for Skipping:**
  Per Brief Section 8 Rule 8 and Priority order: "Judgments (optional, lowest priority, maximum 5 in total). If there is any doubt, skip. If time is short, skip all of them."
- **Decision:**
  Skipped. The statutory text of the Consumer Protection Act, 2019, the UP Tenancy Act, 2021, and the Code on Wages, 2019 provides complete, unambiguous, and enforceable black-letter law. Omitting judgment extracts eliminates any risk of citation distortion or out-of-context judicial quotes.

---

### 5. Round 2 Deletion: e-Daakhil Portal Filing Procedure (`CONS-EDAAKHIL-P1`)
- **Target Subject:** Procedure for online filing of consumer complaints on e-Daakhil (`https://edaakhil.nic.in`).
- **Attempted Sources:** `https://edaakhil.nic.in`, `https://e-jagriti.gov.in`, `https://consumeraffairs.gov.in/pages/e-daakhil`.
- **Reason for Deletion:** 
  1. DNS resolution for `edaakhil.nic.in` failed (`Errno 11001 getaddrinfo failed`). The Ministry of Consumer Affairs formally transitioned and consolidated e-Daakhil, OCMS, and CONFONET into the unified **e-Jagriti** platform (`https://e-jagriti.gov.in`) on January 1, 2025.
  2. The successor platform `https://e-jagriti.gov.in` is built as an interactive React SPA with authenticated workflows; it does not publish static, verbatim statutory procedure text.
  3. The earlier chunk text was an agent-written procedural summary, which violated the non-negotiable verbatim official text contract.
- **Compliance Action:** 
  Per the explicit Round 2 directive ("If no official page states the text, delete the chunk and log it in FAILURES.md. Don't paraphrase"), chunk `CONS-EDAAKHIL-P1` has been permanently deleted from `data/corpus/consumer.jsonl`.

---

### 6. Round 2 Deletion: Ministry of Labour Samadhan Portal Procedure (`WAGE-SAMADHAN-P1`)
- **Target Subject:** Online dispute and conciliation process on Ministry of Labour Samadhan Portal (`https://samadhan.labour.gov.in`).
- **Attempted Sources:** `https://samadhan.labour.gov.in`, Ministry of Labour and Employment (`labour.gov.in`).
- **Reason for Deletion:**
  1. The Samadhan portal's conciliation procedure was originally framed under the Industrial Disputes Act, 1947. The Industrial Disputes Act, 1947 was formally repealed when the Industrial Relations Code, 2020 came into effect on **21 November 2025**.
  2. The Samadhan web portal hosts an interactive web application rather than an official, static, verbatim statutory administrative order or procedural code.
  3. The previous chunk contained agent-synthesized explanatory text.
- **Compliance Action:** 
  Per the Round 2 directive, chunk `WAGE-SAMADHAN-P1` has been permanently deleted from `data/corpus/wages.jsonl`.

---

### 7. Round 2 Deletion: UP Labour Department Wage Grievance Procedure (`WAGE-UPLABOUR-P1`)
- **Target Subject:** Uttar Pradesh Labour Department complaint procedure for unpaid salary and terminal dues (`https://uplabour.gov.in`).
- **Attempted Sources:** `https://uplabour.gov.in`, `https://uplabour.gov.in/Pages/SOP.aspx`, UP Jansunwai (`jansunwai.up.nic.in`).
- **Reason for Deletion:**
  1. The UP Labour Department website does not publish a static, verbatim Standard Operating Procedure (SOP) or statutory regulation governing citizen complaint filing for unpaid wages under the UP Shops and Commercial Establishments Act, 1962.
  2. The previous chunk synthesized generalized administrative guidance spanning Jansunwai / IGRS portal filing and District Labour Commissioner summons, which constituted an agent-authored paraphrase.
- **Compliance Action:** 
  Per the Round 2 directive, chunk `WAGE-UPLABOUR-P1` has been permanently deleted from `data/corpus/wages.jsonl`.


---

### 8. Round 3 Audit: e-Daakhil and NCH Procedure Text Re-collection
- **Target Subject:** Verbatim official step-by-step procedure text for e-Daakhil online consumer complaint filing and National Consumer Helpline grievance lodging.
- **Attempted Sources:** `edaakhil.nic.in`, `consumerhelpline.gov.in`, `consumeraffairs.gov.in`, `e-jagriti.gov.in`.
- **Findings & Actions:**
  1. **e-Daakhil Portal Steps:** The legacy domain `edaakhil.nic.in` remains decommissioned / unresolvable following the transition to the unified **e-Jagriti** portal (`e-jagriti.gov.in`). e-Jagriti is implemented as an interactive, authenticated React application; it does not publish a static, verbatim statutory procedure code or open official PDF manual directly extractable as verbatim legal text. In compliance with the non-negotiable instruction ("Only if verbatim official text exists; otherwise log it in FAILURES.md. Never invent"), no synthetic procedural steps were fabricated.
  2. **National Consumer Helpline Grievance Steps:** The official, authoritative verbatim text from the Department of Consumer Affairs portal (`https://consumeraffairs.gov.in/pages/nch`) is retained in `CONS-NCH-P1`. Detailed secondary portal UI walkthroughs from legal blogs were excluded to protect corpus purity and prevent paraphrasing.
