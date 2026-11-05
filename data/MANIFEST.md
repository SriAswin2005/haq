# Legal Corpus Manifest

**Author:** Antigravity (Corpus Agent)  
**Date:** 2026-11-05 (Updated Round 2)  
**Version:** 2.0  
**Scope:** Verified official legal corpus for Consumer Refunds, Tenancy Deposits (UP & Central), and Unpaid Wages (UP & Central), plus Cross-Cutting Common Provisions and Helplines.  
**Total Chunks:** 119  
**Total Files:** 4 (`common.jsonl`: 28, `tenancy.jsonl`: 37, `consumer.jsonl`: 26, `wages.jsonl`: 28)  
**Total Unique Statutory / Official Documents:** 22  

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
| **Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021** | tenancy | UP | 25 | [India Code Handle 16604](https://www.indiacode.nic.in/handle/123456789/16604) | `in_force` | Primary UP tenancy law. Enacted 2021-08-24 (UP Act 16 of 2021), deemed in force from 2021-01-11. Security deposit rule (s.11), Rent Authority (s.30), Rent Tribunal (s.32), bar of civil courts (s.38). |
| **Transfer of Property Act, 1882** | tenancy | central | 6 | [India Code Handle 2338](https://www.indiacode.nic.in/handle/123456789/2338) | `in_force` | Core Chapter V provisions: lease definition (s.105), notice to quit (s.106), registration (s.107), rights & liabilities (s.108), determination (s.111), holding over (s.116). |
| **Registration Act, 1908** | tenancy | central | 2 | [India Code Handle 2261](https://www.indiacode.nic.in/handle/123456789/2261) | `in_force` | Section 17(1)(d) (compulsory registration of leases exceeding 1 year) and section 49 (effect of non-registration). |
| **Indian Contract Act, 1872** | tenancy | central | 2 | [India Code Handle 2187](https://www.indiacode.nic.in/handle/123456789/2187) | `in_force` | Sections 73 and 74 on breach of contract and compensation for withheld money/deposits outside UP tenancy jurisdiction. |
| **Uttar Pradesh Urban Buildings (Regulation of Letting, Rent and Eviction) Act, 1972** | tenancy | UP | 2 | [India Code Handle 2180](https://www.indiacode.nic.in/handle/123456789/2180) | `repealed` | Repealed by section 46 of UP Act 16 of 2021. Key sections (s.20, s.21) retained for recognizing legacy disputes and old-law queries. |
| **Consumer Protection Act, 2019** | consumer | central | 20 | [India Code Handle 15256](https://www.indiacode.nic.in/handle/123456789/15256) | `in_force` | Core central consumer statute. Definitions (s.2), District/State/National Commission jurisdictions, complaint procedure (s.35-39), 2-year limitation (s.69), product liability (s.82-87). |
| **Consumer Protection (Jurisdiction of District Commission, State Commission and National Commission) Rules, 2021** | consumer | central | 3 | [Gazette of India G.S.R. 912(E)](https://egazette.gov.in/WriteReadData/2021/232278.pdf) | `in_force` | Notified 2021-12-30 (Notification G.S.R. 912(E)). Revised pecuniary limits: District <= ₹50 Lakh; State ₹50 Lakh to ₹2 Crore; National > ₹2 Crore. |
| **Consumer Protection (E-Commerce) Rules, 2020** | consumer | central | 2 | [Department of Consumer Affairs PDF](https://consumeraffairs.gov.in/public/upload/files/E%20commerce%20rules_1732703966.pdf) | `in_force` | Notified 2020-07-23 (Notification G.S.R. 462(E)). Grievance officer (48h acknowledgment, 1-month resolution), cancellation fee restrictions, and refund obligations. |
| **National Consumer Helpline Procedure** | consumer | central | 1 | [Department of Consumer Affairs NCH](https://consumeraffairs.gov.in/pages/nch) | `in_force` | Verbatim text. Pre-litigation grievance redressal, INGRAM omni-channel repository, and convergence mechanism with industry partners. |
| **Code on Wages, 2019** | wages | central | 21 | [e-Gazette Notification S.O. 5322(E)](https://egazette.gov.in) | `in_force` | Central labour code brought into force on 2025-11-21 vide S.O. 5322(E). Regulates minimum wages, wage period (s.16 <= 1 month), timely payment (s.17: 7th day / 2 days upon termination), lawful deductions (s.18 <= 50%), and 3-year claim procedure (s.45). |
| **Payment of Wages Act, 1936** | wages | central | 2 | [India Code Handle 2360](https://www.indiacode.nic.in/handle/123456789/2360) | `repealed` | Repealed by section 69 of Code on Wages, 2019. Retained for old-law detection. |
| **Minimum Wages Act, 1948** | wages | central | 1 | [India Code Handle 1898](https://www.indiacode.nic.in/handle/123456789/1898) | `repealed` | Repealed by section 69 of Code on Wages, 2019. Retained for old-law detection. |
| **Code on Social Security, 2020** | wages | central | 1 | [e-Gazette Notification](https://egazette.gov.in) | `in_force` | Brought into force on 2025-11-21. Section 53 governs statutory gratuity entitlement (replacing Payment of Gratuity Act, 1972). |
| **Uttar Pradesh Dookan Aur Vanijya Adhishthan Adhiniyam, 1962** | wages | UP | 3 | [India Code Handle 613885](https://www.indiacode.nic.in/handle/123456789/613885) | `in_force` | U.P. Act No. XXVI of 1962 verified from India Code bitstream PDF. Section 13 (wage period <= 1 month; 2 working days upon termination), Section 15 (deductions), Section 18 (recovery under Payment of Wages Act mechanism). State shops act remains in force. |

*(Note: In Round 2, procedural chunks `CONS-EDAAKHIL-P1`, `WAGE-SAMADHAN-P1`, and `WAGE-UPLABOUR-P1` were deleted from the corpus because they were synthetic summaries rather than verbatim official text, and no official static statutory page hosts their text. They are logged in `data/FAILURES.md`.)*

---

## 2. Key Findings & Legal Discoveries

### A. Uttar Pradesh Rental Deposit Law (Lead Fully Confirmed)
1. **The Current Law:** The **Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021** (U.P. Act No. 16 of 2021) is confirmed as the governing law in Uttar Pradesh for urban tenancy disputes. It was promulgated initially by Ordinance in January 2021, passed by the UP Legislature, and published in the UP Gazette on 24 August 2021, taking effect deemed from 11 January 2021.
2. **Repeal of 1972 Act:** Section 46(1) explicitly repeals the **Uttar Pradesh Urban Buildings (Regulation of Letting, Rent and Eviction) Act, 1972** (U.P. Act No. 13 of 1972). Section 46(2) provides savings only for pending litigation instituted prior to commencement.
3. **The Security Deposit Rule (Section 11):** 
   - Section 11(1)(a) caps advance security deposits for **residential premises at a maximum of two months' rent**.
   - Section 11(1)(b) caps advance security deposits for **non-residential premises at a maximum of six months' rent**.
   - Section 11(2) mandates that the security deposit **must be refunded to the tenant on the date of taking over vacant possession of the premises**, subject only to lawful deduction of actual liabilities.
4. **Dispute Forum & Disposal Timelines:**
   - Section 30 establishes the **Rent Authority** (officer not below rank of Additional District Collector).
   - Section 32 establishes the **Rent Tribunal** (headed by District Judge or Additional District Judge).
   - Section 38(1) explicitly bars civil courts from entertaining any suit relating to matters covered under the Act.
   - Section 33(7) mandates that the Rent Authority shall endeavour to dispose of applications within **sixty days** from the date of service of notice. A 90-day limit applies specifically to certain eviction applications under sections 21(2) and 22.
   - Section 4(4) permits summons and notices to be served via electronic modes including WhatsApp, SMS, and email.

### B. Wages & Labour Code Implementation (Lead Confirmed with Gazette Citation)
1. **Enforcement of the Code on Wages, 2019:** The Ministry of Labour and Employment, Government of India, issued **Notification No. S.O. 5322(E) dated 21 November 2025**, published in the Gazette of India Extraordinary, bringing the Code on Wages, 2019 into force.
2. **Repeals under Section 69:** The enforcement of the Code on Wages formally repealed:
   - The Payment of Wages Act, 1936;
   - The Minimum Wages Act, 1948;
   - The Payment of Bonus Act, 1965;
   - The Equal Remuneration Act, 1976.
3. **Core Substantive Wage Provisions:**
   - **Wage Period (Section 16):** Cannot exceed one month.
   - **Payment Timelines (Section 17):** Monthly wages must be paid before the expiry of the **7th day** of the succeeding month. For dismissed, retrenched, removed or resigned employees, final dues must be paid within **two working days**.
   - **Deduction Ceiling (Section 18):** Deductions are strictly limited to statutory heads and **cannot exceed 50%** of total wages in any wage period.
   - **Claim Forum & Limitation (Section 45):** Claims for unpaid or delayed wages are filed before the gazetted **Authority** within **three years** from the date on which the claim arose (extended from 12 months under the old 1936 Act). The Authority may award the unpaid wages along with compensation up to **ten times the amount**.
4. **Gratuity (Code on Social Security, 2020):** Statutory gratuity is governed by Section 53 of the Code on Social Security, 2020, replacing the Payment of Gratuity Act, 1972. It requires continuous service of 5 years (1 year for fixed-term workers).
5. **State Shops Act Remains in Force:** The Uttar Pradesh Dookan Aur Vanijya Adhishthan Adhiniyam, 1962 (Act 26 of 1962) was **not** repealed by the Central Labour Codes. Section 13 mandates wage periods not exceeding one month and payment within two working days upon termination. Section 18 provides recovery through the Payment of Wages Act mechanism.

### C. Consumer Protection & Pecuniary Limits
1. **Governing Statute:** Consumer Protection Act, 2019 (Act 35 of 2019).
2. **Crucial Pecuniary Jurisdiction Update (2021 Rules):**
   - The statutory text in CPA 2019 Sections 34, 47, and 58 originally set limits of ₹1 Crore (District), ₹10 Crore (State), and >₹10 Crore (National).
   - On 30 December 2021, the Central Government notified the **Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021** (Notification G.S.R. 912(E)), lowering the pecuniary thresholds based on value paid as consideration:
     - **District Commission:** Up to **₹50 Lakh**;
     - **State Commission:** Exceeding **₹50 Lakh up to ₹2 Crore**;
     - **National Commission:** Exceeding **₹2 Crore**.
3. **E-Commerce Protections:** Under the Consumer Protection (E-Commerce) Rules, 2020 (Notification G.S.R. 462(E)), e-commerce entities must appoint a resident grievance officer, acknowledge complaints within **48 hours**, redress them within **one month**, and cannot impose unilateral cancellation fees.
4. **Limitation Period (Section 69):** Consumer complaints must be filed within **two years** from the date the cause of action arose.

### D. Common & Cross-Cutting Provisions
1. **Limitation Act, 1963:** General period of limitation for money recovery suits and contract breach is **three years**. Section 5 provides for condonation of delay in appeals and applications upon showing sufficient cause (note: Section 5 does not apply to original suits). Section 18 resets the limitation period upon a written and signed acknowledgment of debt.
2. **Legal Services Authorities Act, 1987:** Section 12 provides free legal aid to women, children, members of SC/ST, industrial workmen, persons in custody, and persons whose annual income does not exceed statutory state caps (UP: ₹3 Lakh per state legal services rules). Section 19-21 provide that Lok Adalat awards are final, non-appealable, and deemed civil court decrees with full court-fee refund.
3. **Official Helplines:** All 6 helplines (NCH 1915, NALSA 15100, UPSLSA 1800-419-0234, Labour 14434, ERSS 112, WHL 181) were extracted verbatim from verified official pages.
