# Legal Corpus Manifest

**Author:** Antigravity (Corpus Agent)  
**Date:** 2026-11-06 (Updated Round 3)  
**Version:** 3.0  
**Scope:** Verified official legal corpus for Consumer Refunds, Tenancy Deposits (UP, Central & Tamil Nadu), and Unpaid Wages (UP & Central), plus Cross-Cutting Common Provisions and Helplines.  
**Total Chunks:** 129  
**Total Files:** 4 (`common.jsonl`: 28, `consumer.jsonl`: 29, `tenancy.jsonl`: 42, `wages.jsonl`: 30)  
**Total Unique Statutory / Official Documents:** 24  

---

## 1. Document Inventory

| Document Title | Category | Jurisdiction | Chunks | Source URL | Status | Issues / Notes |
|---|---|---|---|---|---|---|
| **Legal Services Authorities Act, 1987** | common | central | 13 | [India Code Handle 1925](https://www.indiacode.nic.in/handle/123456789/1925) | `in_force` | Complete sections on NALSA, SLSA, DLSA, legal aid eligibility (s.12), and Lok Adalats (s.19-22E). |
| **Limitation Act, 1963** | common | central | 9 | [India Code Handle 1565](https://www.indiacode.nic.in/handle/123456789/1565) | `in_force` | Core sections on bar of limitation (s.3), court closure (s.4), condonation of delay (s.5), exclusion of time (s.12, 14), and written acknowledgment (s.18). |
| **National Consumer Helpline (NCH)** | common | central | 1 | [Department of Consumer Affairs NCH](https://consumeraffairs.gov.in/pages/nch) | `in_force` | Verbatim text. Short code 1915, toll-free 1800-11-4000, WhatsApp 8800001915, 17 languages, 8 AM - 8 PM daily. |
| **National Legal Services Authority Helpline** | common | central | 1 | [NALSA Contact Us](https://nalsa.gov.in/contact-us/) | `in_force` | Verbatim text. Toll-free legal aid helpline 15100 and Jaisalmer House Delhi contact info. |
| **Uttar Pradesh State Legal Services Authority (UPSLSA)** | common | UP | 1 | [UPSLSA Contact Us](http://uttarpradesh.nalsa.gov.in/contact-us/) | `in_force` | Verbatim text. Toll-free 1800-419-0234 and Lucknow Gomti Nagar office numbers (0522-2286395/265). |
| **Ministry of Labour Helpdesk** | common | central | 1 | [eShram Helpdesk](https://eshram.gov.in/helpdesk) | `in_force` | Verbatim text. Toll-free 14434 / 18008896811 (9:00 AM to 6:00 PM daily) in 10 languages. |
| **Emergency Response Support System (ERSS)** | common | central | 1 | [PIB MHA PRID 1594669](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1594669) | `in_force` | Verbatim official text. Pan-India single emergency number 112 with computer-aided dispatch and SHOUT app. |
| **Women Helpline Scheme (WHL 181)** | common | central | 1 | [MWCD WHL Scheme](https://wcd.gov.in/offerings/women--helpline--scheme) | `in_force` | Verbatim text. 24-hour toll-free universal short code 181 integrated with ERSS-112 and One Stop Centres. |
| **Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021** | tenancy | UP | 27 | [India Code Handle 16604](https://www.indiacode.nic.in/handle/123456789/16604) | `in_force` | Primary UP tenancy law (UP Act 16 of 2021). Security deposit cap (s.11), Rent Authority (s.30), Rent Tribunal (s.32), eviction protection (s.21-a, s.21-b), The First Schedule Form for Information of Tenancy (s.4, Sch 1). |
| **Transfer of Property Act, 1882** | tenancy | central | 6 | [India Code Handle 2338](https://www.indiacode.nic.in/handle/123456789/2338) | `in_force` | Core Chapter V provisions: lease definition (s.105), notice to quit (s.106), registration (s.107), rights & liabilities (s.108), determination (s.111), holding over (s.116). |
| **Registration Act, 1908** | tenancy | central | 3 | [India Code Handle 2261](https://www.indiacode.nic.in/handle/123456789/2261) | `in_force` | Section 17 split at subsection (3) into s.17-a (compulsory registration including leases) and s.17-b (exceptions & state amendments). Section 49 retained. |
| **Indian Contract Act, 1872** | tenancy | central | 3 | [India Code Handle 2187](https://www.indiacode.nic.in/handle/123456789/2187) | `in_force` | Section 73 split into s.73-a (section & illustrations a-h) and s.73-b (illustrations i-r, including deposit return). Section 74 retained. |
| **Tamil Nadu Regulation of Rights and Responsibilities of Landlords and Tenants Act, 2017** | tenancy | TN | 1 | [India Code Handle 20507](https://www.indiacode.nic.in/handle/123456789/20507) | `in_force` | Tamil Nadu Act No. 42 of 2017. Section 11 caps security deposits at three times monthly rent and mandates refund within one month of vacating. |
| **Uttar Pradesh Urban Buildings (Regulation of Letting, Rent and Eviction) Act, 1972** | tenancy | UP | 2 | [India Code Handle 2180](https://www.indiacode.nic.in/handle/123456789/2180) | `repealed` | Repealed by section 46 of UP Act 16 of 2021. Key sections (s.20, s.21) retained for recognizing legacy disputes and old-law queries. |
| **Consumer Protection Act, 2019** | consumer | central | 22 | [India Code Handle 15256](https://www.indiacode.nic.in/handle/123456789/15256) | `in_force` | Core central consumer statute. Definitions split into s.2-a and s.2-b; procedure on admission split into s.38-a and s.38-b. District/State/National Commission jurisdictions, 2-year limitation (s.69), product liability (s.82-87). |
| **Consumer Protection (Jurisdiction of District Commission, State Commission and National Commission) Rules, 2021** | consumer | central | 3 | [Gazette of India G.S.R. 912(E)](https://egazette.gov.in/WriteReadData/2021/232278.pdf) | `in_force` | Notified 2021-12-30 (Notification G.S.R. 912(E)). Revised pecuniary limits: District <= ₹50 Lakh; State ₹50 Lakh to ₹2 Crore; National > ₹2 Crore. |
| **Consumer Protection (E-Commerce) Rules, 2020** | consumer | central | 2 | [Department of Consumer Affairs PDF](https://consumeraffairs.gov.in/public/upload/files/E%20commerce%20rules_1732703966.pdf) | `in_force` | Notified 2020-07-23 (Notification G.S.R. 462(E)). Grievance officer (48h acknowledgment, 1-month resolution), cancellation fee restrictions, and refund obligations. |
| **Consumer Protection (Consumer Disputes Redressal Commissions) Rules, 2020** | consumer | central | 1 | [Department of Consumer Affairs GSR 892(E)](https://consumeraffairs.gov.in/public/upload/files/GSR_892.pdf) | `in_force` | Notified 2020-07-15 (G.S.R. 448(E)); amended 2022-12-20 (G.S.R. 892(E)). Rule 7 prescribes complaint fee schedule: Nil up to ₹5 Lakh, tiered fees up to ₹50 Lakh (District), ₹2 Crore (State), >₹2 Crore (National). |
| **National Consumer Helpline Procedure** | consumer | central | 1 | [Department of Consumer Affairs NCH](https://consumeraffairs.gov.in/pages/nch) | `in_force` | Verbatim text. Pre-litigation grievance redressal, INGRAM omni-channel repository, and convergence mechanism with industry partners. |
| **Code on Wages, 2019** | wages | central | 22 | [e-Gazette Notification S.O. 5322(E)](https://egazette.gov.in) | `in_force` | Central labour code brought into force on 2025-11-21 vide S.O. 5322(E). Section 2 split into s.2-a and s.2-b. Minimum wages, wage period (s.16), timely payment (s.17), lawful deductions (s.18 <= 50%), and 3-year claim procedure (s.45). |
| **Code on Wages (Central) Rules, 2026** | wages | central | 1 | [Ministry of Labour & Employment](https://labour.gov.in) | `in_force` | Final rules notified on 2026-05-08 vide Notification G.S.R. 343(E) in Gazette of India Extraordinary. Rule 46 prescribes Form-II claim procedure under Section 45. |
| **Payment of Wages Act, 1936** | wages | central | 2 | [India Code Handle 2360](https://www.indiacode.nic.in/handle/123456789/2360) | `repealed` | Repealed by section 69 of Code on Wages, 2019. Retained for old-law detection. |
| **Minimum Wages Act, 1948** | wages | central | 1 | [India Code Handle 1898](https://www.indiacode.nic.in/handle/123456789/1898) | `repealed` | Repealed by section 69 of Code on Wages, 2019. Retained for old-law detection. |
| **Code on Social Security, 2020** | wages | central | 1 | [e-Gazette Notification](https://egazette.gov.in) | `in_force` | Brought into force on 2025-11-21. Section 53 governs statutory gratuity entitlement (replacing Payment of Gratuity Act, 1972). |
| **Uttar Pradesh Dookan Aur Vanijya Adhishthan Adhiniyam, 1962** | wages | UP | 3 | [India Code Handle 613885](https://www.indiacode.nic.in/handle/123456789/613885) | `in_force` | U.P. Act No. XXVI of 1962 verified from India Code bitstream PDF. Section 13 (wage period <= 1 month; 2 working days upon termination), Section 15 (deductions), Section 18 (recovery under Payment of Wages Act mechanism). State shops act remains in force. |

---

## 2. Key Findings & Legal Discoveries (Round 3 Additions)

### A. Consumer Commission Complaint Fee Schedule (Rule 7)
- Governed by Rule 7 of the **Consumer Protection (Consumer Disputes Redressal Commissions) Rules, 2020**, amended vide Notification G.S.R. 892(E) dated 20 December 2022.
- **Nil Court Fee for Small Claims:** Complaints where the value of goods or services paid as consideration does not exceed **₹5,00,000 (Rupees Five Lakh)** are entirely exempt from any filing fee (Fee: **Nil**).
- **Tiered Fee Slabs:**
  - Above ₹5 Lakh and up to ₹10 Lakh: **₹200**
  - Above ₹10 Lakh and up to ₹20 Lakh: **₹400**
  - Above ₹20 Lakh and up to ₹50 Lakh: **₹1,000**
  - Above ₹50 Lakh and up to ₹1 Crore: **₹2,000**
  - Above ₹1 Crore and up to ₹2 Crore: **₹2,500**
  - Above ₹2 Crore up to ₹4 Crore: **₹3,000** (scaling up to ₹7,500 for claims >₹10 Crore).

### B. Uttar Pradesh Tenancy Agreement Form (The First Schedule)
- Under Section 4(1) of the **Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021**, any tenancy created after commencement must be executed by a written agreement and informed to the Rent Authority within **two months** in the form specified in **THE FIRST SCHEDULE**.
- Residential leases under 12 months (e.g. 11-month agreements) are exempt from mandatory notification to the Rent Authority, but a written contract is required.
- The First Schedule prescribes details of landlord, tenant, property manager, premises description, agreed rent, due dates, enhancement periodicity, and specific terms for the **amount and refund of security deposit**.

### C. Code on Wages Central Rules Claim Procedure
- The Ministry of Labour and Employment published final rules titled the **Code on Wages (Central) Rules, 2026** vide Notification G.S.R. 343(E) dated **8 May 2026**.
- **Rule 46** establishes the claim procedure under Section 45(5) of the Code on Wages, 2019:
  - Application filed before the gazetted Authority in **Form-II**.
  - A single application can be filed for multiple employees in an establishment for unpaid wages in the same wage period.
  - Requires supporting affidavit, proof of employment, pay slips, and bank statements showing non-credit.
- **Rule 50**: Appeals before the Appellate Authority under Section 49(1) are filed in **Form-III**, requiring deposit of 100% of the awarded amount by the employer.

### D. Inter-State Tenancy Comparison: Tamil Nadu Tenancy Act, 2017
- The **Tamil Nadu Regulation of Rights and Responsibilities of Landlords and Tenants Act, 2017** (Tamil Nadu Act No. 42 of 2017, enforced 22 February 2019).
- **Section 11 (Security Deposit):**
  - Section 11(1): Unlawful to charge a security deposit exceeding **three months' rent** (unlike UP's 2-month residential cap under Section 11(1)(a) of UP Act 16 of 2021).
  - Section 11(2): Mandatory refund within **one month** after vacating premises, after lawful deductions.
