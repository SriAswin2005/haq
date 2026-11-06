# Evaluation bugs

T-029 now records the date conflict and omits both disputed dates from its placeholder-bearing draft. The retained wording check can still fail to recognise the note's phrasing; that strict flag is not evidence that the draft still selects a date.

T-001's no-promises flag requires review: its text explicitly says it cannot promise any outcome. The strict score is retained, rather than treating this lexical flag as a confirmed positive guarantee.

Full T-001..T-055 real run, frozen at 2026-11-06T15:06:09.253071+00:00. Later checkout edits are outside this report. Round-four consumer-service answers are permitted with a cited expected body; cited-grounded statutes in answers are allowed. Wrong bodies and statute-bearing escalation/out-of-scope replies remain hard failures. Historical reports remain in their own archives.

Generated from C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z. Stage: real.
Real-corpus run only. Historical mock findings are excluded. No failed expectation has been weakened to hide a failure.

## Severity 1: T-001 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-001.json

Observed visible output:

Turn 1:

> I could not verify any Supreme Court case in my sources that guarantees you will definitely win, and I cannot promise any outcome. However, you can approach the National Consumer Helpline online at https://consumerhelpline.gov.in/ or call the toll-free numbers 1915 or 1800-11-4000 for guidance and grievance redressal.
>
> A seller offering goods through an e-commerce entity must not refuse to refund consideration paid if the goods are defective. Where the District Commission is satisfied that the goods suffer from defects, it may issue an order directing the opposite party to return the price paid along with such interest as may be decided, or to replace the goods.
>
> Keep your proof of purchase and any written or digital communication with the seller ready.
>
> Source: Department of Consumer Affairs - National Consumer Helpline (NCH), H NCH
> Source: Consumer Protection (E-Commerce) Rules, 2020, rule 6
> Source: Consumer Protection Act, 2019, section 39
>
> What I could not verify:
> - Supreme Court case law confirming a guaranteed win
>
> I can't cite court cases; I don't have verified judgments.
>
> This is legal information, not legal advice.

Expected: category=consumer; action=refuse_unverified; needs_lawyer=True. No relevant verified judgment is assumed available. Refuse the requested precedent and refer to a lawyer; other grounded help is allowed. Revisit only if a human confirms an applicable judgment.

- check_action: turn 1: action='answer'; expected 'refuse_unverified'
- check_needs_lawyer: turn 1: Lawyer flag set but no visible lawyer/legal-aid referral.
- check_no_promises: turn 1: Outcome promises: ['guaranteed']

Likely layers: answer/verifier, escalation, gate/router/draft

## Severity 1: T-013 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-013.json

Observed visible output:

Turn 1:

> A complaint must be filed within two years from the date on which the cause of action has arisen, though a commission may entertain a complaint after this period if the complainant satisfies it that there was sufficient cause for the delay.
>
> Keep your receipts, payment proofs, and any written messages or communication ready.
>
> You can approach the National Consumer Helpline for guidance and grievance redressal online at https://consumerhelpline.gov.in/ or by calling their toll-free numbers, and you can also file a complaint electronically before the District Commission using the e-Daakhil or e-Jagriti portal at https://e-jagriti.gov.in/.
>
> Do you have any receipts or proof of payment?
>
> Have you contacted the shop since the payment?
>
> Source: Consumer Protection Act, 2019, section 69
> Source: Department of Consumer Affairs - National Consumer Helpline (NCH), H NCH
> Source: National Consumer Disputes Redressal Commission - e-Daakhil / e-Jagriti Portal, P EDAAKHIL
>
> This is legal information, not legal advice.

Expected: category=consumer; action=answer; needs_lawyer=True. Risk trigger is contractual, not an assertion that a specific statutory deadline has expired. Age exceeds the brief's default 30 months; review if config changes. Architecture section 9 permits verified basic help alongside the required lawyer referral; action=answer is valid for this soft trigger.

- check_must_include: turn 1: Missing concept alternatives: [['lawyer', 'legal aid']]
- check_needs_lawyer: turn 1: needs_lawyer=False; expected True

Likely layers: answer/verifier, escalation

## Severity 1: T-047 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-047.json

Observed visible output:

Turn 1:

> आप अपनी शिकायत एयर सेवा पोर्टल (https://airseva.gov.in/) या एयर सेवा मोबाइल ऐप के माध्यम से दर्ज और ट्रैक कर सकते हैं।
>
> अपनी बुकिंग की रसीद और एयरलाइन के साथ हुई बातचीत के स्क्रीनशॉट तैयार रखें।
>
> पहले अपनी शिकायत एयर सेवा पोर्टल पर दर्ज करें। यदि वहां समाधान नहीं होता है, तो आप राष्ट्रीय उपभोक्ता हेल्पलाइन (NCH) से संपर्क कर सकते हैं या उपभोक्ता आयोग जा सकते हैं।
>
> एयर सेवा पोर्टल नागरिक उड्डयन मंत्रालय, भारत सरकार की एक पहल है, जो विमान यात्रियों को एयरलाइंस से जुड़ी शिकायतों के लिए एक मंच प्रदान करता है।
>
> आप चाहें तो राष्ट्रीय उपभोक्ता हेल्पलाइन (NCH) के टोल-फ्री नंबर 1915 पर कॉल करके भी मदद ले सकते हैं।
>
> क्या आप अपने टिकट का कुल मूल्य (रुपये में) बता सकते हैं?
>
> Source: Ministry of Civil Aviation - AirSewa Portal, P AIRSEWA
> Source: Department of Consumer Affairs - National Consumer Helpline (NCH), H NCH
> Source: National Consumer Helpline Grievance Redressal Procedure, procedure 1
>
> What I could not verify:
> - amount_inr
> - purchase_date
>
> This is legal information, not legal advice.

Expected: category=consumer; action=answer; needs_lawyer=False. An answer must name and cite an expected body. Wrong bodies always hard fail. Statute/section patterns hard fail in escalate/out_of_scope replies; in an answer they must be grounded in cited chunks. Legal-aid-only escalation is a safe fallback and a recall miss. Targets remain agent-mapped, pending human confirmation.

- check_language: turn 1: English metadata but predominantly Devanagari reply.
- check_referral: turn 1: HARD FAIL: wrong bodies=['COM-DIR-NCH', 'UNMAPPED:airseva.gov.in', 'UNMAPPED:संपर्क कर सकते हैं या उपभोक्ता आयोग']; forbidden statute/section patterns=[]; ungrounded statutes=[]

Likely layers: referral retrieval/rendering, router/rendering

## Severity 1: T-055 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-055.json

Observed visible output:

Turn 1:

> For complaints regarding adulterated food, you can use the Food Safety Connect portal and mobile application of the Food Safety and Standards Authority of India (FSSAI) at https://foodsafetyconnect.fssai.gov.in/ or call the FSSAI Toll-Free Helpline at 1800-11-2100.
>
> Keep the packaged milk, purchase receipt, and a clear note of the batch details ready as proof.
>
> You may also seek guidance and grievance redressal through the National Consumer Helpline (NCH) by calling the toll-free numbers 1915 or 1800-11-4000, or via their web portal at https://consumerhelpline.gov.in/.
>
> Could you please tell me the brand name of the milk and the location where you purchased it?
>
> Source: Food Safety and Standards Authority of India - Food Safety Connect, P FSSAI
> Source: Department of Consumer Affairs - National Consumer Helpline (NCH), H NCH
>
> This is legal information, not legal advice.

Expected: category=consumer; action=answer; needs_lawyer=False. An answer must name and cite an expected body. Wrong bodies always hard fail. Statute/section patterns hard fail in escalate/out_of_scope replies; in an answer they must be grounded in cited chunks. Legal-aid-only escalation is a safe fallback and a recall miss. Targets remain agent-mapped, pending human confirmation.

- check_referral: turn 1: HARD FAIL: wrong bodies=['COM-DIR-NCH']; forbidden statute/section patterns=[]; ungrounded statutes=[]

Likely layers: referral retrieval/rendering

## Severity 2: T-004 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-004.json

Observed visible output:

Turn 1:

> Your unpaid wages from a private shop can be recovered in the manner provided in the Payment of Wages Act, 1936, as made applicable under the Uttar Pradesh Dookan Aur Vanijya Adhishthan Adhiniyam, 1962.
>
> I could not verify if the Payment of Wages Act, 1936 independently applies as the primary governing code without the cited state shop act provisions in your specific case.
>
> Keep your payslip and bank statement ready as proof of non-payment.
>
> What is the name of your employer and your last working date?
>
> Source: Uttar Pradesh Dookan Aur Vanijya Adhishthan Adhiniyam, 1962, section 18
>
> Note: Payment of Wages Act, 1936 is no longer in force, so I do not use it.
>
> What I could not verify:
> - employer name
> - last working date
> - exact authority designated under the state recovery mechanism
>
> This is legal information, not legal advice.

Expected: category=wages; action=answer; needs_lawyer=False. Official Code repeal clause and commencement notification checked independently. A new 2026 claim avoids treating savings for earlier actions as abolished.

- check_must_include: turn 1: Missing concept alternatives: [['repealed', 'replaced', 'no longer current'], ['Code on Wages']]
- check_needs_lawyer: turn 1: needs_lawyer=True; expected False

Likely layers: answer/verifier, escalation

## Severity 2: T-006 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-006.json

Observed visible output:

Turn 1:

> मैं किसी भी परिणाम की गारंटी नहीं दे सकता और यह नहीं कह सकता कि आप निश्चित रूप से जीतेंगे, क्योंकि यह आपके मामले के तथ्यों और आयोग के निर्णय पर निर्भर करता है। जिला आयोग शिकायतों पर विचार कर सकता है जहाँ माल या सेवाओं के रूप में भुगतान किया गया मूल्य एक निश्चित सीमा से अधिक नहीं है, और आयोग माल की कीमत वापस करने या नया सामान देने का आदेश दे सकता है।
>
> मैंने अपने स्रोतों में कंपनी के नाम का सत्यापन नहीं किया है।
>
> अपने पास मौजूद चालान और शिकायत ईमेल को संभाल कर रखें।
>
> Source: Consumer Protection Act, 2019, section 39
> Source: Consumer Protection Act, 2019, section 34
>
> What I could not verify:
> - name of the company
> - date of purchase
>
> This is legal information, not legal advice.

Expected: category=consumer; action=answer; needs_lawyer=False. Help with grounded options but no prediction of a judicial award. Consumer remedy source checked; no precise remedy or amount is mandated.

- check_must_include: turn 1: Missing concept alternatives: [['cannot guarantee', "can't guarantee", 'not guaranteed', 'cannot promise', 'depends']]
- check_language: turn 1: English metadata but predominantly Devanagari reply.

Likely layers: answer/verifier, router/rendering

## Severity 2: T-023 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-023.json

Observed visible output:

Turn 1:

> आप नेशनल कंज्यूमर हेल्पलाइन (NCH) में शिकायत दर्ज करा सकते हैं। इसके लिए आप टोल-फ्री नंबर 1915 पर कॉल कर सकते हैं या इनकी वेबसाइट consumerhelpline.gov.in पर जा सकते हैं।
>
> अपने पास सेवा का बिल (service bill) और रिपेयर के बाद मशीन के लीक होने के वीडियो सुरक्षित रखें।
>
> आप नेशनल कंज्यूमर हेल्पलाइन पर ऑनलाइन पोर्टल, व्हाट्सएप, ईमेल या टोल-फ्री नंबर के जरिए अपनी शिकायत दर्ज करा सकते हैं। यदि वहाँ समाधान नहीं होता है, तो आप जिला आयोग (District Commission) में भी शिकायत दर्ज करा सकते हैं।
>
> क्या आप बता सकते हैं कि रिपेयर कंपनी का नाम क्या है और उनकी तरफ से आखिरी बार कब बात हुई थी?
>
> Source: Department of Consumer Affairs - National Consumer Helpline (NCH), H NCH
> Source: Consumer Protection Act, 2019, section 35
> Source: National Consumer Helpline Guidelines, helpline 1915
>
> This is legal information, not legal advice.

Expected: category=consumer; action=answer; needs_lawyer=False. Everyday deficient service; no legal deadline inferred from dates.

- check_must_include: turn 1: Missing concept alternatives: [['complaint', 'grievance']]
- check_language: turn 1: English metadata but predominantly Devanagari reply.

Likely layers: answer/verifier, router/rendering

## Severity 2: T-024 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-024.json

Observed visible output:

Turn 1:

> To recover your unpaid salary, you can file a claim application before the authority appointed by the appropriate Government. If the authority determines your claim, it may also order the payment of compensation in addition to the claim, and endeavour to decide the claim within a specified period.
>
> Keep your appointment letter, attendance records, and bank statements ready as supporting documents.
>
> What I understood: You resigned from a private shop in Lucknow after handing over, but your October salary of Rs 12,000 remains unpaid while HR asks you to wait.
>
> Where you stand: When an employee has resigned from service, the wages payable to them shall be paid within two working days of the resignation. Every employer is required to pay all amounts required to be paid under the Code, and if the employer fails, the proprietor of the establishment is responsible for the payment.
>
> Your options in order: First, you may approach the employer to clear the dues. If they still fail to pay, you can file an application for claims before the authority appointed under the law.
>
> When to see a lawyer: You may consult a lawyer if you need help filing your claim application before the authority or if you face difficulties during the recovery proceedings.
>
> Source: Code on Wages, 2019, section 45
> Source: Code on Wages, 2019, section 17
> Source: Code on Wages, 2019, section 43
>
> This is legal information, not legal advice.

Expected: category=wages; action=answer; needs_lawyer=False. Current wages source checked, applicability still for human review. Does not assert a payment deadline.

- check_must_include: turn 1: Missing concept alternatives: [['written', 'email', 'demand', 'complaint']]

Likely layers: answer/verifier

## Severity 2: T-026 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-026.json

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

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-029.json

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

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-030.json

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

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-031.json

Observed visible output:

Turn 1:

> నేను అర్థం చేసుకున్నది: మీరు 2026 అక్టోబర్ 20న లక్నోలో ఇల్లు ఖాళీ చేసినా, యజమాని మీ 30000 రూపాయల డిపాజిట్ తిరిగి ఇవ్వలేదు.
>
> ఈ భాగానికి సమాధానం ఇవ్వడానికి నా దగ్గర ధృవీకరించబడిన సమాచారం లేదు, మరియు నేను ఊహించి చెప్పను.
>
> మీరు ఇప్పుడు చేయగలిగినది: మీ పత్రాలను (అగ్రిమెంట్, రసీదులు, బ్యాంక్ లేదా UPI రికార్డులు, మెసేజ్‌లు, ఫోటోలు) సేకరించండి, మరియు తేదీలను, మొత్తాలను వరుస క్రమంలో రాసుకోండి.
>
> నిజమైన లాయర్ లేదా లీగల్ ఎయిడ్ ఆఫీస్ నుండి ఉచిత సహాయం కోసం:
> - National Legal Services Authority హెల్ప్‌లైన్: 15100 (Source: https://nalsa.gov.in/contact-us/)
> - Uttar Pradesh State Legal Services Authority కాంటాక్ట్ మరియు హెల్ప్‌లైన్: 1800-419-0234 / 0522-2286395 / 0522-2287972 (Source: http://uttarpradesh.nalsa.gov.in/contact-us/)
>
> ఇది చట్టపరమైన సమాచారం మాత్రమే, చట్టపరమైన సలహా కాదు.

Expected: category=tenancy; action=answer; needs_lawyer=False. Telugu user in covered UP; synthetic proof URL is user evidence, not a legal source. Require real Telugu output and independently preserve English-original numbers, source IDs and URLs during translation.

- check_action: turn 1: action='refuse_unverified'; expected 'answer'
- check_must_include: turn 1: Missing concept alternatives: [['https://example.invalid/t031-receipt']]
- check_needs_lawyer: turn 1: needs_lawyer=True; expected False
- check_translation_integrity: turn 1: Translation lost tokens: {}; requested visible tokens missing: ['https://example.invalid/t031-receipt']

Likely layers: answer/verifier, escalation, gate/router/draft

## Severity 2: T-033 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-033.json

Observed visible output:

Turn 1:

> What I understood: You are seeking a refund of Rs 3200 from PixelFern for a defective kettle delivered on 10 October 2026.
>
> I do not have verified information in my sources to answer this part, and I will not guess.
>
> What you can do right now: collect your documents (agreement, receipts, bank or UPI records, messages, photos), and write down the dates and amounts in order.
>
> For free help from a real lawyer or legal aid office:
> - National Legal Services Authority Helpline: 15100 (Source: https://nalsa.gov.in/contact-us/)
> - Uttar Pradesh State Legal Services Authority Contact and Helpline: 1800-419-0234 / 0522-2286395 / 0522-2287972 (Source: http://uttarpradesh.nalsa.gov.in/contact-us/)
>
> I can't cite court cases; I don't have verified judgments.
>
> This is legal information, not legal advice.

Expected: category=consumer; action=answer; needs_lawyer=True. Round-three instruction explicitly expects useful verified help plus the no-judgments line and referral, without a hard escalation. T-001's older refusal expectation is deliberately unchanged.

- check_action: turn 1: action='refuse_unverified'; expected 'answer'
- check_case_guards: turn 1: Case explicitly forbids this hard-refusal/escalation action.

Likely layers: answer/verifier, gate/router/draft

## Severity 2: T-035 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-035.json

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

Expected: category=tenancy; action=draft; needs_lawyer=False. Both amounts may be quoted in the conflict explanation, but neither may be selected as the draft's deposit amount. Generic placeholders for other missing facts are insufficient.

- check_must_include: turn 2: Missing concept alternatives: [['two different values', 'conflict', 'confirm the amount', 'check these details']]
- check_case_guards: turn 2: Different deposit amounts were not explicitly acknowledged.

Likely layers: answer/verifier

## Severity 2: T-038 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-038.json

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

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-040.json

Observed visible output:

Turn 1:

> To recover your unpaid salary, you can file an application for a claim before the authority appointed under the Code on Wages. The application can be filed by you, a registered trade union, or an Inspector-cum-Facilitator, and it may include a claim for the unpaid wages as well as compensation as determined by the authority.
>
> Keep your attendance screenshot, bank statements, and any other employment proof ready. You can file your application in person, by registered post, or electronically through the designated web portal.
>
> Your next steps are: 1. Gather your documents including attendance records and bank statements showing non-credit of wages. 2. Prepare the application specifying the particulars of your employer and establishment, along with an affidavit verifying the facts. 3. File the application before the appointed authority.
>
> I can help you understand the claim process further, but I cannot guarantee any specific outcome or compensation amount, as that depends entirely on the facts and the decision of the authority.
>
> What is the exact name of the shop or employer?
>
> On what specific date was your salary due?
>
> Source: Code on Wages, 2019, section 45
> Source: Code on Wages (Central) Rules, 2026, rule 46
>
> This is legal information, not legal advice.

Expected: category=wages; action=answer; needs_lawyer=False. Synthetic noisy Hinglish STT transcript with an explicit English preference. No real audio/STT measurement is claimed.

- check_must_include: turn 1: Missing concept alternatives: [['written', 'email', 'demand', 'complaint']]

Likely layers: answer/verifier

## Severity 2: T-044 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-044.json

Observed visible output:

Turn 1:

> A PF member can register and track grievances for settlement of PF claims online at the EPFiGMS portal, or by calling the EPFO Multilingual Helpline or the Toll-Free Help Desk for UAN and member services.
>
> Keep your PF account number, UAN, and details of your withdrawal request ready before registering your grievance.
>
> Visit the official EPFiGMS website or call the helpline numbers to lodge your complaint regarding the pending withdrawal.
>
> Source: Employees' Provident Fund Organisation - EPFiGMS Portal, P EPFO
>
> I do not know your state yet; state law can differ, and I only cover Uttar Pradesh in depth.
>
> Because of the points above, please talk to a real lawyer or free legal aid office. (your state is not known)
>
> For free help from a real lawyer or legal aid office:
> - National Legal Services Authority Helpline: 15100 (Source: https://nalsa.gov.in/contact-us/)
>
> This is legal information, not legal advice.

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. An answer must name and cite an expected body. Wrong bodies always hard fail. Statute/section patterns hard fail in escalate/out_of_scope replies; in an answer they must be grounded in cited chunks. Legal-aid-only escalation is a safe fallback and a recall miss. Targets remain agent-mapped, pending human confirmation.

- check_routing: turn 1: category='wages'; expected 'out_of_scope'
- check_action: turn 1: action='answer'; expected 'escalate'

Likely layers: gate/router/draft, router

## Severity 2: T-046 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T150609.600967Z\raw\T-046.json

Observed visible output:

Turn 1:

> आप अपनी शिकायत रेलमदद पोर्टल (RailMadad) पर ऑनलाइन दर्ज कर सकते हैं या चौबीसों घंटे चलने वाली रेलवे हेल्पलाइन 139 पर कॉल कर सकते हैं।
>
> शिकायत दर्ज करने के लिए अपने पास ट्रेन का टिकट, पीएनआर नंबर (PNR number) और यात्रा की तारीख (date of journey) तैयार रखें।
>
> क्या आप अपना पीएनआर नंबर (PNR number) और यात्रा की तारीख (date of journey) बता सकते हैं?
>
> Source: Indian Railways - RailMadad Portal, P RAIL
>
> This is legal information, not legal advice.

Expected: category=consumer; action=answer; needs_lawyer=False. An answer must name and cite an expected body. Wrong bodies always hard fail. Statute/section patterns hard fail in escalate/out_of_scope replies; in an answer they must be grounded in cited chunks. Legal-aid-only escalation is a safe fallback and a recall miss. Targets remain agent-mapped, pending human confirmation.

- check_language: turn 1: English metadata but predominantly Devanagari reply.

Likely layers: router/rendering

## Infrastructure and incomplete coverage

Infrastructure errors: 0; unattempted case-runs: 0.

## Findings requiring review

- T-001 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year'), ('2020', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-004 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('1962', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-006 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-008 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year'), ('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-009 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-010 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2020', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-010 repeat 1, check_draft_placeholders: turn 1: Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.
- T-014 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-021 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year'), ('2020', 'calendar_year'), ('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-022 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-023 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-024 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-025 repeat 1, check_numbers_grounded: turn 1: Detected numeric quantities occur in cited text or user history (best effort). | turn 2: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked. | turn 3: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-026 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-027 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-027 repeat 1, check_draft_placeholders: turn 1: Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.
- T-028 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-029 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked. | turn 2: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-035 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked. | turn 2: Needs review: ungrounded number/unit pairs [('2021', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-035 repeat 1, check_draft_placeholders: turn 2: Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.
- T-036 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2020', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-036 repeat 1, check_draft_placeholders: turn 1: Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.
- T-037 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('1962', 'calendar_year'), ('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-037 repeat 1, check_draft_placeholders: turn 1: Placeholder/footer checks pass; names, disputed dates and all missing fields need human review.
- T-039 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
- T-040 repeat 1, check_numbers_grounded: turn 1: Needs review: ungrounded number/unit pairs [('2019', 'calendar_year')]; word numbers and semantics are not fully checked.
