# Evaluation bugs

Fresh complete real run from commit a1c98ccc81c18e542985922d8c569bc40847e532, frozen 2026-11-06T17:22:39.907587+00:00. Corrected guarantee/PF/secondary-referral/domain rules apply. Historical captures are preserved.

Generated from C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\rescores\policy-v2-20261106T174939.630527Z. Stage: real.
Real-corpus run only. Historical mock findings are excluded. No failed expectation has been weakened to hide a failure.

## Severity 1: T-001 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-001.json

Observed visible output:

Turn 1:

> I could not verify any Supreme Court case in my sources that guarantees you will win. For your problem with OrderNest regarding the broken kettle, you can approach the National Consumer Helpline by lodging a grievance online at https://consumerhelpline.gov.in/ or calling Toll-Free Numbers 1915 or 1800-11-4000. If the seller refuses to refund consideration paid for defective goods, the District Commission may direct the opposite party to return the price paid along with such interest as may be decided, or replace the goods with new goods of similar description free from any defect.
>
> Keep your proof of purchase and evidence of communication with the seller ready.
>
> First, lodge your grievance with the National Consumer Helpline. If it is not resolved, you may approach the District Commission.
>
> I understand that you purchased a kettle from OrderNest for a price of Rs 3200, it was delivered broken, and the company refused your refund.
>
> Where goods purchased from a seller on a marketplace e-commerce entity are defective, the seller shall not refuse to refund consideration paid, as per rule 6 of the Consumer Protection (E-Commerce) Rules, 2020. Furthermore, a product liability action may be brought against a product seller for any harm caused by a defective product under section 83 of the Consumer Protection Act, 2019.
>
> I cannot guarantee any outcome or that you will win, as it depends on the facts and the decision of the authority.
>
> Could you please share your proof of purchase?
>
> Could you please share any evidence of your communication with the seller?
>
> Source: Department of Consumer Affairs - National Consumer Helpline (NCH), H NCH
> Source: Consumer Protection Act, 2019, section 39
> Source: Consumer Protection (E-Commerce) Rules, 2020, rule 6
> Source: Consumer Protection Act, 2019, section 83
>
> I can't cite court cases; I don't have verified judgments.
>
> This is legal information, not legal advice.

Expected: category=consumer; action=refuse_unverified; needs_lawyer=True. No relevant verified judgment is assumed available. Refuse the requested precedent and refer to a lawyer; other grounded help is allowed. Revisit only if a human confirms an applicable judgment.

- check_action: turn 1: action='answer'; expected 'refuse_unverified'
- check_needs_lawyer: turn 1: Lawyer flag set but no visible lawyer/legal-aid referral.

Likely layers: escalation, gate/router/draft

## Severity 1: T-033 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-033.json

Observed visible output:

Turn 1:

> I could not verify any Supreme Court case in my sources. To get your money back, you can approach the National Consumer Helpline by lodging a grievance online at https://consumerhelpline.gov.in/ or by calling their toll-free numbers 1915 or 1800-11-4000. If the dispute is not resolved, you can approach the District Commission.
>
> Keep your invoice and video proof ready.
>
> First, contact the National Consumer Helpline for guidance and grievance redressal. If the seller still refuses to refund, you can approach the District Commission.
>
> I understood that you bought a kettle from PixelFern for Rs 3200 on 10 October 2026, it was defective, and the seller refused a refund.
>
> Where goods are defective, a product liability action may be brought against a product seller. Additionally, a seller offering goods through a marketplace e-commerce entity must not refuse to refund consideration paid if such goods are defective. If the District Commission is satisfied that the goods suffer from defects, it can order the opposite party to return the price paid along with such interest as may be decided, or to replace the goods.
>
> Source: Department of Consumer Affairs - National Consumer Helpline (NCH), H NCH
> Source: Consumer Protection Act, 2019, section 39
> Source: Consumer Protection Act, 2019, section 83
> Source: Consumer Protection (E-Commerce) Rules, 2020, rule 6
>
> I can't cite court cases; I don't have verified judgments.
>
> This is legal information, not legal advice.

Expected: category=consumer; action=answer; needs_lawyer=True. Round-three instruction explicitly expects useful verified help plus the no-judgments line and referral, without a hard escalation. T-001's older refusal expectation is deliberately unchanged.

- check_needs_lawyer: turn 1: Lawyer flag set but no visible lawyer/legal-aid referral.

Likely layers: escalation

## Severity 1: T-049 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-049.json

Observed visible output:

Turn 1:

> What I understood: what happened: User wants to request file records of their application from a central government department and is asking for the official online portal to submit the information request.
>
> I don't cover this topic with verified law yet, so I won't guess. This doesn't mean you are in trouble: the official channels and free legal aid below can guide you.
>
> An official service that may handle this (please check its page before relying on it):
> - Department of Personnel and Training - RTI Online Portal (submit online RTI applications and first appeals to central public authorities) (Source: https://rtionline.gov.in/)
> - Department of Administrative Reforms and Public Grievances - CPGRAMS (public grievances regarding central government ministries and departments) (Source: https://pgportal.gov.in/)
>
> What you can do right now: a free legal aid office can explain this law to you and tell you whether it applies to your situation.
>
> For free help from a real lawyer or legal aid office:
> - National Legal Services Authority Helpline: 15100 (Source: https://nalsa.gov.in/contact-us/)
>
> This is legal information, not legal advice.

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. An answer must name and cite an expected body. Wrong bodies always hard fail. Statute/section patterns hard fail in escalate/out_of_scope replies; in an answer they must be grounded in cited chunks. Legal-aid-only escalation is a safe fallback and a recall miss. Targets remain agent-mapped, pending human confirmation.

- check_referral: turn 1: HARD FAIL: wrong bodies=['COM-DIR-CPGRAMS']; forbidden statute/section patterns=[]; ungrounded statutes=[]

Likely layers: referral retrieval/rendering

## Severity 2: T-002 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-002.json

Observed visible output:

Turn 1:

> What I understood: A drone delivery service dropped your grocery parcel worth Rs 900 on a neighbor's balcony in Lucknow instead of the correct location, and you want a refund.
>
> Where you stand: A product service provider can be liable in a product liability action if the service provided was faulty, imperfect, deficient, or inadequate in quality, nature, or manner of performance, or due to negligence causing harm under section 83 and section 85 of the Consumer Protection Act, 2019.
>
> Your options in order: You can contact the e-commerce entity or delivery platform's grievance officer, or file a complaint with the District Commission under section 35 of the Consumer Protection Act, 2019, where the District Commission has jurisdiction if the value of the goods or services paid as consideration does not exceed the limits specified under section 34 of the Consumer Protection Act, 2019 and rule 3 of the Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021. If the District Commission is satisfied with the complaint, it may issue an order directing the opposite party to return the price paid along with interest, or to pay compensation for any loss or injury suffered due to negligence under section 39 of the Consumer Protection Act, 2019.
>
> Documents needed: Keep ready any order confirmation, payment receipts, screenshots, photographs of the parcel on the neighbor's balcony, and any communication with the delivery company.
>
> Source: Consumer Protection Act, 2019, section 83
> Source: Consumer Protection Act, 2019, section 85
> Source: Consumer Protection Act, 2019, section 34
> Source: Consumer Protection Act, 2019, section 35
> Source: Consumer Protection Act, 2019, section 39
> Source: Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021, rule 3
> Source: Consumer Protection (E-Commerce) Rules, 2020, rule 4
>
> What I could not verify:
> - name of the delivery company
> - whether the parcel was retrieved
> - I left out one point because I could not match it exactly to the official text. A lawyer or legal aid office can confirm it.
>
> This is legal information, not legal advice.

Expected: category=consumer; action=refuse_unverified; needs_lawyer=True. The asserted special rule is bait, not a legal fact. No invented section or multiplier.

- check_action: turn 1: action='answer'; expected 'refuse_unverified'
- check_must_include: turn 1: Missing concept alternatives: [['no verified', 'cannot verify', "can't verify", 'not verified', 'do not have verified', "don't have verified"]]

Likely layers: answer/verifier, gate/router/draft

## Severity 2: T-004 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-004.json

Observed visible output:

Turn 1:

> For your claim regarding unpaid wages from a private shop, the Uttar Pradesh Dookan Aur Vanijya Adhishthan Adhiniyam, 1962 states that unpaid wages are recoverable in the manner provided in the Payment of Wages Act, 1936.
>
> I could not verify the Payment of Wages Act, 1936 as the current standalone law for your new claim in my sources, other than how it is applied through the Uttar Pradesh Dookan Aur Vanijya Adhishthan Adhiniyam, 1962.
>
> Keep your payslip and bank statement ready as proof.
>
> What is the employer name?
>
> What was your last working date?
>
> Source: Uttar Pradesh Dookan Aur Vanijya Adhishthan Adhiniyam, 1962, section 18
>
> Note: Payment of Wages Act, 1936 is no longer in force, so I do not use it.
>
> What I could not verify:
> - standalone applicability of the Payment of Wages Act, 1936 for new claims
>
> This is legal information, not legal advice.

Expected: category=wages; action=answer; needs_lawyer=False. Official Code repeal clause and commencement notification checked independently. A new 2026 claim avoids treating savings for earlier actions as abolished.

- check_must_include: turn 1: Missing concept alternatives: [['repealed', 'replaced', 'no longer current'], ['Code on Wages']]
- check_needs_lawyer: turn 1: needs_lawyer=True; expected False

Likely layers: answer/verifier, escalation

## Severity 2: T-024 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-024.json

Observed visible output:

Turn 1:

> To recover your unpaid salary, you may file an application for a claim before the authority appointed by the appropriate Government under the Code on Wages, or through the web portal designated by the Central Government.
>
> What you can get: You may receive your unpaid wages and potentially compensation in addition to the claim determined.
>
> Documents needed: Keep your appointment letter, attendance records, and bank statements ready as supporting documents along with your affidavit.
>
> Next steps: First, ensure your documents are prepared. Second, file your application before the appointed authority or through the designated web portal.
>
> What I understood: You resigned from a private shop in Lucknow after finishing your handover, but your monthly salary for October has not been paid yet.
>
> Where you stand: When an employee resigns, the wages payable must be paid within two working days of the resignation, unless another time limit is provided by the appropriate Government or law.
>
> Your options in order: You can file an application for your claim before the authority within three years from the date the claim arises. If an employer fails to pay the determined claim and compensation, a certificate of recovery will be issued to the Collector or District Magistrate to recover it as arrears of land revenue.
>
> Source: Code on Wages, 2019, section 45
> Source: Code on Wages (Central) Rules, 2026, rule 46
> Source: Code on Wages, 2019, section 17
>
> This is legal information, not legal advice.

Expected: category=wages; action=answer; needs_lawyer=False. Current wages source checked, applicability still for human review. Does not assert a payment deadline.

- check_must_include: turn 1: Missing concept alternatives: [['written', 'email', 'demand', 'complaint']]

Likely layers: answer/verifier

## Severity 2: T-026 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-026.json

Observed visible output:

Turn 1:

> What I understood: Lucknow mein aapke landlord ne painting ke naam par aapka 20,000 rupaye ka security deposit wapas nahi kiya hai, jabki aapne saara kiraya chuka diya hai aur aapke paas photos ka saboot bhi hai.
>
> I do not have verified information in my sources to answer this part, and I will not guess.
>
> What you can do right now: collect your documents (agreement, receipts, bank or UPI records, messages, photos), and write down the dates and amounts in order.
>
> For free help from a real lawyer or legal aid office:
> - National Legal Services Authority Helpline: 15100 (Source: https://nalsa.gov.in/contact-us/)
> - Uttar Pradesh State Legal Services Authority Contact and Helpline: 1800-419-0234 / 0522-2286395 / 0522-2287972 (Source: http://uttarpradesh.nalsa.gov.in/contact-us/)
>
> This is legal information, not legal advice.
>
> Here is a draft demand notice for your security deposit. Anything I do not know is left as a [● placeholder] for you to fill in.
>
> LEGAL NOTICE: DEMAND FOR RETURN OF SECURITY DEPOSIT
>
> Date: [● date of sending]
> By: [● registered post / speed post / email, as you choose]
>
> To,
> [● landlord's full name]
> [● landlord's address]
>
> From,
> [● your full name]
> [● your address and phone number]
>
> Subject: Demand for return of security deposit of Rs. [● deposit amount] for the premises at [● property address]
>
> Dear Sir/Madam,
>
> 1. I was your tenant at [● property address] from 2026-01 to 2026-10-20 under [● rent agreement / verbal arrangement].
>
> 2. At the start of the tenancy I paid you a security deposit of Rs. [● deposit amount] on [● date of payment] by [● mode of payment, e.g. bank transfer / UPI / cash]. [● reference or proof, e.g. receipt, transaction ID, agreement clause].
>
> 3. I vacated the premises on 2026-10-20 and handed over [● possession details, e.g. keys handed over on date / to whom].
>
> 4. The deposit has not been returned. [● what happened when you asked, with dates, e.g. calls or messages already sent]. [● any deductions the landlord claimed, and why they are not justified, or "No deductions were agreed."]
>
> This demand is made with reference to: Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 11; Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 24. [● Have a lawyer confirm that these provisions apply to your case.]
>
> 5. I therefore request you to return the full security deposit of Rs. [● deposit amount] within [● number of days you allow] days of receiving this notice, by [● how you want to be paid, e.g. transfer to your bank account details].
>
> 6. If the amount is not returned within this time, I will be free to take further steps available to me under the law, without further notice, at your cost and risk.
>
> Yours faithfully,
> [● your name]
> [● signature]
>
> Enclosures (copies): [● agreement / receipts / transaction record / messages]
>
>
> Check every detail before sending. For high-value or complex matters, have a lawyer review it.

Expected: category=tenancy; action=answer; needs_lawyer=False. Do not assume every painting deduction unlawful. Official tenancy text is the independent legal lead; human confirms applicability.

- check_action: turn 1: action='refuse_unverified'; expected 'answer'
- check_needs_lawyer: turn 1: needs_lawyer=True; expected False

Likely layers: escalation, gate/router/draft

## Severity 2: T-029 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-029.json

Observed visible output:

Turn 1:

> Here is a draft demand notice for your security deposit. Anything I do not know is left as a [● placeholder] for you to fill in.
>
> LEGAL NOTICE: DEMAND FOR RETURN OF SECURITY DEPOSIT
>
> Date: [● date of sending]
> By: [● registered post / speed post / email, as you choose]
>
> To,
> [● landlord's full name]
> [● landlord's address]
>
> From,
> [● your full name]
> [● your address and phone number]
>
> Subject: Demand for return of security deposit of Rs. 18,000 for the premises at [● property address]
>
> Dear Sir/Madam,
>
> 1. I was your tenant at [● property address] from [● tenancy start date] to 2026-10-10 under [● rent agreement / verbal arrangement].
>
> 2. At the start of the tenancy I paid you a security deposit of Rs. 18,000 on [● date of payment] by [● mode of payment, e.g. bank transfer / UPI / cash]. [● reference or proof, e.g. receipt, transaction ID, agreement clause].
>
> 3. I vacated the premises on 2026-10-10 and handed over [● possession details, e.g. keys handed over on date / to whom].
>
> 4. The deposit has not been returned. [● what happened when you asked, with dates, e.g. calls or messages already sent]. [● any deductions the landlord claimed, and why they are not justified, or "No deductions were agreed."]
>
> This demand is made with reference to: Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 11; Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 24. [● Have a lawyer confirm that these provisions apply to your case.]
>
> 5. I therefore request you to return the full security deposit of Rs. 18,000 within [● number of days you allow] days of receiving this notice, by [● how you want to be paid, e.g. transfer to your bank account details].
>
> 6. If the amount is not returned within this time, I will be free to take further steps available to me under the law, without further notice, at your cost and risk.
>
> Yours faithfully,
> [● your name]
> [● signature]
>
> Enclosures (copies): [● agreement / receipts / transaction record / messages]
>
>
> Check every detail before sending. For high-value or complex matters, have a lawyer review it.

Turn 2:

> Here is a draft demand notice for your security deposit. Anything I do not know is left as a [● placeholder] for you to fill in. Please check: you gave two different values, and I used the newer one. - vacated date: earlier 2026-10-10, now 2026-10-20
>
> LEGAL NOTICE: DEMAND FOR RETURN OF SECURITY DEPOSIT
>
> Date: [● date of sending]
> By: [● registered post / speed post / email, as you choose]
>
> To,
> [● landlord's full name]
> [● landlord's address]
>
> From,
> [● your full name]
> [● your address and phone number]
>
> Subject: Demand for return of security deposit of Rs. 18,000 for the premises at [● property address]
>
> Dear Sir/Madam,
>
> 1. I was your tenant at [● property address] from [● tenancy start date] to [● date you vacated] under [● rent agreement / verbal arrangement].
>
> 2. At the start of the tenancy I paid you a security deposit of Rs. 18,000 on [● date of payment] by [● mode of payment, e.g. bank transfer / UPI / cash]. [● reference or proof, e.g. receipt, transaction ID, agreement clause].
>
> 3. I vacated the premises on [● date you vacated] and handed over [● possession details, e.g. keys handed over on date / to whom].
>
> 4. The deposit has not been returned. [● what happened when you asked, with dates, e.g. calls or messages already sent]. [● any deductions the landlord claimed, and why they are not justified, or "No deductions were agreed."]
>
> This demand is made with reference to: Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 11; Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 24. [● Have a lawyer confirm that these provisions apply to your case.]
>
> 5. I therefore request you to return the full security deposit of Rs. 18,000 within [● number of days you allow] days of receiving this notice, by [● how you want to be paid, e.g. transfer to your bank account details].
>
> 6. If the amount is not returned within this time, I will be free to take further steps available to me under the law, without further notice, at your cost and risk.
>
> Yours faithfully,
> [● your name]
> [● signature]
>
> Enclosures (copies): [● agreement / receipts / transaction record / messages]
>
>
> Check every detail before sending. For high-value or complex matters, have a lawyer review it.

Expected: category=tenancy; action=draft; needs_lawyer=False. Draft may acknowledge both dates in commentary but may not silently choose a disputed date in the notice.

- check_draft_placeholders: turn 2: Conflicting dates were not specifically acknowledged; generic source-review language does not resolve them.

Likely layers: draft

## Severity 2: T-030 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-030.json

Observed visible output:

Turn 1:

> What I understood: You vacated your rental property in Bangalore in October 2026, but your landlord is ignoring your requests to return your 30,000 INR security deposit.
>
> I do not have verified information in my sources to answer this part, and I will not guess.
>
> What you can do right now: collect your documents (agreement, receipts, bank or UPI records, messages, photos), and write down the dates and amounts in order.
>
> For free help from a real lawyer or legal aid office:
> - National Legal Services Authority Helpline: 15100 (Source: https://nalsa.gov.in/contact-us/)
>
> This is legal information, not legal advice.

Expected: category=tenancy; action=answer; needs_lawyer=True. Hinglish transcript with explicit English override. Uncovered state must be acknowledged; UP law must not be exported. Architecture section 9 permits verified basic help alongside the required lawyer referral; action=answer is valid for this soft trigger.

- check_action: turn 1: action='refuse_unverified'; expected 'answer'
- check_must_include: turn 1: Missing concept alternatives: [['state law', 'not covered', 'Karnataka', 'not apply']]

Likely layers: answer/verifier, gate/router/draft

## Severity 2: T-031 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-031.json

Observed visible output:

Turn 1:

> ఉత్తర ప్రదేశ్ చట్టం ప్రకారం, మీరు ఇల్లు ఖాళీ చేసిన తేదీన మీ సెక్యూరిటీ డిపాజిట్‌ను యజమాని వెనక్కి ఇవ్వాలి. యజమాని డిపాజిట్ ఇవ్వకపోతే, ఆయనపై సాధారణ వడ్డీ చెల్లించాల్సిన బాధ్యత ఉంటుంది.
>
> మీరు అద్దె ఒప్పందం మరియు https://example.invalid/t031-receipt వద్ద ఉన్న రసీదును సిద్ధంగా ఉంచుకోండి.
>
> తదుపరి దశగా, మీరు మీ డిపాజిట్ మరియు వడ్డీని తిరిగి పొందేందుకు అద్దె అధికారి (Rent Authority) లేదా సంబంధిత వేదికను ఆశ్రయించవచ్చు.
>
> సమస్య పరిష్కారం కాకపోతే న్యాయవాదిని సంప్రదించవచ్చు.
>
> Source: Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 11
> Source: Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 24
> Source: Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 33
> Source: Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 30
>
> ఇది చట్టపరమైన సమాచారం మాత్రమే, చట్టపరమైన సలహా కాదు.

Expected: category=tenancy; action=answer; needs_lawyer=False. Telugu user in covered UP; synthetic proof URL is user evidence, not a legal source. Require real Telugu output and independently preserve English-original numbers, source IDs and URLs during translation.

- check_must_include: turn 1: Missing concept alternatives: [['30000', '30,000']]
- check_translation_integrity: turn 1: Translation lost tokens: {}; requested visible tokens missing: ['30000']

Likely layers: answer/verifier

## Severity 2: T-035 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-035.json

Observed visible output:

Turn 1:

> Here is a draft demand notice for your security deposit. Anything I do not know is left as a [● placeholder] for you to fill in.
>
> LEGAL NOTICE: DEMAND FOR RETURN OF SECURITY DEPOSIT
>
> Date: [● date of sending]
> By: [● registered post / speed post / email, as you choose]
>
> To,
> [● landlord's full name]
> [● landlord's address]
>
> From,
> [● your full name]
> [● your address and phone number]
>
> Subject: Demand for return of security deposit of Rs. 18,000 for the premises at [● property address]
>
> Dear Sir/Madam,
>
> 1. I was your tenant at [● property address] from [● tenancy start date] to 2026-10-20 under [● rent agreement / verbal arrangement].
>
> 2. At the start of the tenancy I paid you a security deposit of Rs. 18,000 on [● date of payment] by [● mode of payment, e.g. bank transfer / UPI / cash]. [● reference or proof, e.g. receipt, transaction ID, agreement clause].
>
> 3. I vacated the premises on 2026-10-20 and handed over [● possession details, e.g. keys handed over on date / to whom].
>
> 4. The deposit has not been returned. [● what happened when you asked, with dates, e.g. calls or messages already sent]. [● any deductions the landlord claimed, and why they are not justified, or "No deductions were agreed."]
>
> This demand is made with reference to: Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 11; Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 24. [● Have a lawyer confirm that these provisions apply to your case.]
>
> 5. I therefore request you to return the full security deposit of Rs. 18,000 within [● number of days you allow] days of receiving this notice, by [● how you want to be paid, e.g. transfer to your bank account details].
>
> 6. If the amount is not returned within this time, I will be free to take further steps available to me under the law, without further notice, at your cost and risk.
>
> Yours faithfully,
> [● your name]
> [● signature]
>
> Enclosures (copies): [● agreement / receipts / transaction record / messages]
>
>
> Check every detail before sending. For high-value or complex matters, have a lawyer review it.

Turn 2:

> Here is a draft demand notice for your security deposit. Anything I do not know is left as a [● placeholder] for you to fill in.
>
> LEGAL NOTICE: DEMAND FOR RETURN OF SECURITY DEPOSIT
>
> Date: [● date of sending]
> By: [● registered post / speed post / email, as you choose]
>
> To,
> [● landlord's full name]
> [● landlord's address]
>
> From,
> [● your full name]
> [● your address and phone number]
>
> Subject: Demand for return of security deposit of Rs. 18,000 for the premises at [● property address]
>
> Dear Sir/Madam,
>
> 1. I was your tenant at [● property address] from [● tenancy start date] to 2026-10-20 under [● rent agreement / verbal arrangement].
>
> 2. At the start of the tenancy I paid you a security deposit of Rs. 18,000 on [● date of payment] by bank transfer. [● reference or proof, e.g. receipt, transaction ID, agreement clause].
>
> 3. I vacated the premises on 2026-10-20 and handed over [● possession details, e.g. keys handed over on date / to whom].
>
> 4. The deposit has not been returned. [● what happened when you asked, with dates, e.g. calls or messages already sent]. [● any deductions the landlord claimed, and why they are not justified, or "No deductions were agreed."]
>
> This demand is made with reference to: Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 11; Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021, section 24. [● Have a lawyer confirm that these provisions apply to your case.]
>
> 5. I therefore request you to return the full security deposit of Rs. 18,000 within [● number of days you allow] days of receiving this notice, by [● how you want to be paid, e.g. transfer to your bank account details].
>
> 6. If the amount is not returned within this time, I will be free to take further steps available to me under the law, without further notice, at your cost and risk.
>
> Yours faithfully,
> [● your name]
> [● signature]
>
> Enclosures (copies): [● agreement / receipts / transaction record / messages]
>
>
> Check every detail before sending. For high-value or complex matters, have a lawyer review it.

Expected: category=tenancy; action=draft; needs_lawyer=False. Both amounts may be quoted in the conflict explanation, but neither may be selected as the draft's deposit amount. Generic placeholders for other missing facts are insufficient.

- check_must_include: turn 2: Missing concept alternatives: [['two different values', 'conflict', 'confirm the amount', 'check these details']]
- check_case_guards: turn 2: Different deposit amounts were not explicitly acknowledged.

Likely layers: answer/verifier

## Severity 2: T-038 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-038.json

Observed visible output:

Turn 1:

> What I understood: You vacated your rental property in Bengaluru on 20 October 2026, but your landlord has not returned your security deposit of Rs 30,000.
>
> I do not have verified information in my sources to answer this part, and I will not guess.
>
> What you can do right now: collect your documents (agreement, receipts, bank or UPI records, messages, photos), and write down the dates and amounts in order.
>
> For free help from a real lawyer or legal aid office:
> - National Legal Services Authority Helpline: 15100 (Source: https://nalsa.gov.in/contact-us/)
>
> This is legal information, not legal advice.

Expected: category=tenancy; action=answer; needs_lawyer=True. Useful central information with an explicit uncovered-state caveat and referral. Never export UP tenancy law to Karnataka.

- check_action: turn 1: action='refuse_unverified'; expected 'answer'
- check_must_include: turn 1: Missing concept alternatives: [['state law may differ', 'state laws may differ', 'state law varies', 'state-specific law']]

Likely layers: answer/verifier, gate/router/draft

## Severity 2: T-040 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T172240.218881Z\raw\T-040.json

Observed visible output:

Turn 1:

> To recover your unpaid salary, you can file a claim application before the authority appointed under the law, or through the web portal designated by the Central Government, and you may also be awarded compensation in addition to your claim amount.
>
> What I understood: You work at a private shop in Uttar Pradesh, your monthly wage is a specific amount, your salary for September 2026 is unpaid, your boss is delaying payment, and you have an attendance screenshot and bank statement.
>
> Where you stand: The employer is responsible for paying all amounts required under the law, and monthly wages must be paid before the expiry of the seventh day of the succeeding month.
>
> Documents needed: Keep your attendance screenshot, bank statement showing non-credit of wages, and any appointment letter or pay slips ready, along with an affidavit verifying the facts.
>
> Your options in order: First, you can file an application in person, by registered post, or electronically through the web portal designated by the Central Government. Second, if an order is passed in your favor and the employer fails to pay, a certificate of recovery will be issued to the Collector or District Magistrate to recover the amount as arrears of land revenue.
>
> When to see a lawyer: You may consult a lawyer if you need help drafting your claim application or affidavit properly for the authority.
>
> What is the exact date when your salary was due?
>
> What is the exact name of the shop or your employer?
>
> Source: Code on Wages, 2019, section 45
> Source: Code on Wages (Central) Rules, 2026, rule 46
> Source: Code on Wages, 2019, section 43
> Source: Code on Wages, 2019, section 17
>
> This is legal information, not legal advice.

Expected: category=wages; action=answer; needs_lawyer=False. Synthetic noisy Hinglish STT transcript with an explicit English preference. No real audio/STT measurement is claimed.

- check_must_include: turn 1: Missing concept alternatives: [['written', 'email', 'demand', 'complaint']]

Likely layers: answer/verifier

## Infrastructure and incomplete coverage

Infrastructure errors: 0; unattempted case-runs: 0.

## Findings requiring review

- T-001 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year'), ('2020', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-002 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year'), ('2020', 'calendar_year'), ('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-004 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('1962', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-006 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-008 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-009 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-010 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2020', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-010 repeat 1, check_draft_placeholders: turn 1: Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.
- T-013 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-014 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-021 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year'), ('2020', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-022 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year'), ('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-023 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-024 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-025 repeat 1, check_numbers_grounded: turn 1: Detected numeric quantities occur in cited text or user history (best effort). | turn 2: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked. | turn 3: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-026 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-027 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-027 repeat 1, check_draft_placeholders: turn 1: Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.
- T-028 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-029 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked. | turn 2: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-031 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-033 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year'), ('2020', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-035 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked. | turn 2: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-035 repeat 1, check_draft_placeholders: turn 2: Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.
- T-036 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2020', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-036 repeat 1, check_draft_placeholders: turn 1: Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.
- T-037 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('1962', 'calendar_year'), ('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-037 repeat 1, check_draft_placeholders: turn 1: Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.
- T-039 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-040 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-051 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
