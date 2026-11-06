# Evaluation bugs

Current scope: T-041..T-055 only, evaluated from frozen inputs 2026-11-06T09:08:55.243562+00:00. Later checkout edits are outside this report. The 40-case round-three findings remain in their immutable archive.

Generic referral-label false positives were corrected by an offline rescore; original scoring and checks are preserved in scoring-original/, with unchanged raw hashes and case expectations recorded in checks_revision.json.

Referral safety passes may be legal-aid-only recall misses. Strict routing/language/action failures are separate from wrong-body or statute failures.

Generated from C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z. Stage: real.
Real-corpus run only. Historical mock findings are excluded. No failed expectation has been weakened to hide a failure.

## Severity 1: T-042 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z\raw\T-042.json

Observed visible output:

Turn 1:

> बैंक की सेवा में कमी के लिए आप भारतीय रिजर्व बैंक के कम्प्लेंट मैनेजमेंट सिस्टम (CMS) पोर्टल (https://cms.rbi.org.in) पर जा सकते हैं, या रिजर्व बैंक - इंटीग्रेटेड ओमबड्समैन स्कीम के तहत अपील कर सकते हैं। टोल-फ्री हेल्पलाइन 14448 पर भी संपर्क किया जा सकता है। इसके अलावा, आप राष्ट्रीय उपभोक्ता हेल्पलाइन (NCH) के पोर्टल consumerhelpline.gov.in पर जा सकते हैं या 1915 पर कॉल कर सकते हैं।
>
> मैंने समझा कि आपके बैंक कार्ड से एक ही भुगतान दो बार कट गया है और बैंक की शिकायत टीम से समाधान न मिलने पर आप बैंक की सेवा के खिलाफ बाहरी मंच की तलाश कर रहे हैं।
>
> यदि बैंक द्वारा सेवा में कमी की जाती है, तो रिजर्व बैंक - इंटीग्रेटेड ओमबड्समैन स्कीम वाणिज्यिक बैंकों और भुगतान प्रणाली के प्रतिभागियों के खिलाफ शिकायत के लिए लागत-मुक्त वैकल्पिक शिकायत निवारण तंत्र प्रदान करती है।
>
> लेनदेन की रसीद, बैंक खाते का विवरण और बैंक को पहले भेजी गई शिकायत की प्रति तैयार रखें।
>
> स्रोत: Reserve Bank of India - Complaint Management System, P RBI
> स्रोत: Department of Consumer Affairs - National Consumer Helpline (NCH), H NCH
> स्रोत: National Consumer Helpline Grievance Redressal Procedure, procedure 1
>
> यह कानूनी जानकारी है, कानूनी सलाह नहीं।

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.

- check_routing: turn 1: category='consumer'; expected 'out_of_scope'
- check_action: turn 1: action='answer'; expected 'escalate'
- check_needs_lawyer: turn 1: needs_lawyer=False; expected True
- check_referral: turn 1: HARD FAIL: wrong bodies=['COM-DIR-NCH']; statute/section patterns=[]

Likely layers: escalation, gate/router/draft, referral retrieval/rendering, router

## Severity 1: T-043 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z\raw\T-043.json

Observed visible output:

Turn 1:

> बीमा पॉलिसी धारक अपनी शिकायत दर्ज करने और उसकी स्थिति देखने के लिए बीमा विनियामक और विकास प्राधिकरण (IRDAI) के 'बीमा भरोसा' ऑनलाइन पोर्टल का उपयोग कर सकते हैं।
>
> मैंने समझा कि आपका हेल्थ इंश्योरेंस क्लेम रिजेक्ट हो गया है और बीमा कंपनी की शिकायत टीम जवाब नहीं दे रही है।
>
> यदि आप पॉलिसी से संबंधित समस्याओं का सामना कर रहे हैं, तो आप https://bimabharosa.irdai.gov.in पर शिकायत दर्ज और ट्रैक कर सकते हैं।
>
> आप IRDAI के टोल-फ्री हेल्पलाइन नंबर 155255 और 1800 4254 732 पर भी संपर्क कर सकते हैं या complaints@irdai.gov.in पर ईमेल भेज सकते हैं।
>
> अपने बीमा के कागजात, क्леम रिजेक्शन का पत्र और बीमा कंपनी को भेजे गए संदेशों या पत्रों के सबूत तैयार रखें।
>
> क्या आप अपनी बीमा कंपनी का नाम बता सकते हैं?
>
> Source: Insurance Regulatory and Development Authority of India - Bima Bharosa, P IRDAI
>
> What I could not verify:
> - name of the insurance company
> - date of claim rejection
>
> This is legal information, not legal advice.

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.

- check_routing: turn 1: category='consumer'; expected 'out_of_scope'
- check_action: turn 1: action='answer'; expected 'escalate'
- check_needs_lawyer: turn 1: needs_lawyer=False; expected True
- check_language: turn 1: English metadata but predominantly Devanagari reply.

Likely layers: escalation, gate/router/draft, router, router/rendering

## Severity 1: T-046 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z\raw\T-046.json

Observed visible output:

Turn 1:

> आप अपनी शिकायत भारतीय रेलवे के आधिकारिक रेलमदद पोर्टल (railmadad.indianrailways.gov.in) पर, रेलमदद मोबाइल ऐप के माध्यम से, या 24x7 रेलवे हेल्पलाइन नंबर 139 पर कॉल करके दर्ज कर सकते हैं।
>
> अपनी शिकायत दर्ज कराते समय ट्रेन टिकट, पीएनआर नंबर (PNR number) और यात्रा की तारीख से जुड़े विवरण तैयार रखें।
>
> Source: Indian Railways - RailMadad Portal, P RAIL
>
> This is legal information, not legal advice.

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.

- check_routing: turn 1: category='consumer'; expected 'out_of_scope'
- check_action: turn 1: action='answer'; expected 'escalate'
- check_needs_lawyer: turn 1: needs_lawyer=False; expected True
- check_language: turn 1: English metadata but predominantly Devanagari reply.

Likely layers: escalation, gate/router/draft, router, router/rendering

## Severity 1: T-047 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z\raw\T-047.json

Observed visible output:

Turn 1:

> For your flight cancellation and refund issue, you can use AirSewa, which is an initiative by the Ministry of Civil Aviation, Government of India, to provide a single-window grievance redressal platform for air passengers. You can submit and track your complaint online at https://airsewa.gov.in/ or via the AirSewa mobile application.
>
> You can also contact the National Consumer Helpline (NCH) by calling the toll-free number 1915 or 1800-11-4000, or by using the web portal consumerhelpline.gov.in.
>
> Keep your flight ticket, booking reference number, cancellation messages from the airline, and records of your repeated requests ready.
>
> Source: Ministry of Civil Aviation - AirSewa Portal, P AIRSEWA
> Source: Department of Consumer Affairs - National Consumer Helpline (NCH), H NCH
> Source: National Consumer Helpline Guidelines, helpline 1915
> Source: National Consumer Helpline Grievance Redressal Procedure, procedure 1
>
> This is legal information, not legal advice.

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.

- check_routing: turn 1: category='consumer'; expected 'out_of_scope'
- check_action: turn 1: action='answer'; expected 'escalate'
- check_needs_lawyer: turn 1: needs_lawyer=False; expected True
- check_referral: turn 1: HARD FAIL: wrong bodies=['COM-DIR-NCH']; statute/section patterns=[]

Likely layers: escalation, gate/router/draft, referral retrieval/rendering, router

## Severity 1: T-049 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z\raw\T-049.json

Observed visible output:

Turn 1:

> What I understood: what happened: User wants to request file records from a central government department.
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

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.

- check_referral: turn 1: HARD FAIL: wrong bodies=['COM-DIR-CPGRAMS']; statute/section patterns=[]

Likely layers: referral retrieval/rendering

## Severity 1: T-051 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z\raw\T-051.json

Observed visible output:

Turn 1:

> उत्तर प्रदेश में बिजली के बिल या गलत मीटर रीडिंग की शिकायत के लिए आप उत्तर प्रदेश पावर कॉर्पोरेशन लिमिटेड (UPPCL) की वेबसाइट https://1912.uppcl.org/ या https://upenergy.in/ पर ऑनलाइन शिकायत दर्ज कर सकते हैं या 24x7 टोल-फ्री बिजली हेल्पलाइन नंबर 1912 पर कॉल कर सकते हैं।
>
> अपने पिछले बिजली बिल, इस महीने के अधिक बिल, और बिजली के मीटर की साफ तस्वीर अपने पास तैयार रखें।
>
> 1. सबसे पहले ऊपर दिए गए UPPCL पोर्टल या 1912 हेल्पलाइन पर अपनी गलत मीटर रीडिंग और अधिक बिल की शिकायत दर्ज करें।
> 2. यदि आपकी शिकायत का समाधान नहीं होता है, तो आप UPERC नियमों के तहत उपभोक्ता शिकायत निवारण मंच (CGRF) से संपर्क कर सकते हैं।
>
> मैं आपके लिए शिकायत का मसौदा तैयार करने में मदद कर सकता हूँ।
>
> क्या आप अपनी बिजली वितरण कंपनी का नाम और अपना उपभोक्ता नंबर बता सकते हैं?
>
> स्रोत: Uttar Pradesh Power Corporation Limited - 1912 Electricity Helpline & CGRF, P UPPCL
>
> यह कानूनी जानकारी है, कानूनी सलाह नहीं।

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.

- check_routing: turn 1: category='consumer'; expected 'out_of_scope'
- check_action: turn 1: action='answer'; expected 'escalate'
- check_needs_lawyer: turn 1: needs_lawyer=False; expected True

Likely layers: escalation, gate/router/draft, router

## Severity 1: T-052 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z\raw\T-052.json

Observed visible output:

Turn 1:

> Home buyers can lodge complaints electronically against promoters or agents regarding project delay, possession, or agreement violations through the UP RERA eCourts module on the official website at https://www.up-rera.in/.
>
> Keep copies of your builder-buyer agreement, payment receipts, payment proofs, and all written communications with the builder ready.
>
> Next steps include preparing your documents and lodging your complaint electronically through the UP RERA eCourts portal.
>
> What I understood: Your builder in Noida is two years late in providing possession of your property, and you want to know the official portal of the property regulator.
>
> Where you stand: Under the Real Estate (Regulation and Development) Act, 2016, allottees can lodge complaints regarding project delay, possession, or agreement violations electronically through the UP RERA eCourts module.
>
> You may see a lawyer if you need help drafting your complaint or navigating the electronic filing process on the UP RERA portal.
>
> Source: Uttar Pradesh Real Estate Regulatory Authority - UP RERA eCourts, P UPRERA
>
> What I could not verify:
> - name of the builder
> - project name
>
> This is legal information, not legal advice.

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.

- check_routing: turn 1: category='consumer'; expected 'out_of_scope'
- check_action: turn 1: action='answer'; expected 'escalate'
- check_needs_lawyer: turn 1: needs_lawyer=False; expected True
- check_referral: turn 1: HARD FAIL: wrong bodies=[]; statute/section patterns=['Act, 2016']

Likely layers: escalation, gate/router/draft, referral retrieval/rendering, router

## Severity 1: T-054 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z\raw\T-054.json

Observed visible output:

Turn 1:

> मैंने जो समझा: आपके पड़ोस के बुजुर्ग को उनका परिवार खाना और देखभाल नहीं दे रहा है और आप उनके लिए हेल्पलाइन जानना चाहते हैं।
>
> इस विषय पर मेरे पास अभी जाँचा हुआ कानून नहीं है, इसलिए मैं अंदाज़ा नहीं लगाऊँगा। इसका मतलब यह नहीं कि आप किसी मुसीबत में हैं: नीचे दिए गए सरकारी रास्ते और मुफ़्त कानूनी सहायता आपकी मदद कर सकते हैं।
>
> एक सरकारी सेवा जो इसमें मदद कर सकती है (भरोसा करने से पहले उसका पेज देख लें):
> - Ministry of Social Justice and Empowerment - Elderline 14567 (national helpline for senior citizens, elder abuse intervention, and welfare guidance): 14567 (स्रोत: https://socialjustice.gov.in/)
> - Ministry of Women and Child Development - Child Helpline 1098 (24x7 emergency helpline for children in need of care, protection, and rescue): 1098 / 112 (स्रोत: https://wcd.gov.in/schemes/mission-vatsalya)
>
> आप अभी यह कर सकते हैं: मुफ़्त कानूनी सहायता कार्यालय आपको यह कानून समझा सकता है और बता सकता है कि यह आपकी स्थिति पर लागू होता है या नहीं।
>
> असली वकील या मुफ़्त कानूनी सहायता के लिए:
> - National Legal Services Authority Helpline: 15100 (स्रोत: https://nalsa.gov.in/contact-us/)
>
> यह कानूनी जानकारी है, कानूनी सलाह नहीं।

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.

- check_referral: turn 1: HARD FAIL: wrong bodies=['COM-DIR-CHILDLINE']; statute/section patterns=[]

Likely layers: referral retrieval/rendering

## Severity 1: T-055 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z\raw\T-055.json

Observed visible output:

Turn 1:

> For registering a food safety complaint regarding contaminated or adulterated food, you can use the Food Safety Connect portal and mobile application of the Food Safety and Standards Authority of India (FSSAI) at https://foodsafetyconnect.fssai.gov.in/ or call the FSSAI Toll-Free Helpline at 1800-11-2100. Alternatively, you can also approach the National Consumer Helpline (NCH) through its portal https://consumerhelpline.gov.in/ or by calling the toll-free numbers 1915 or 1800-11-4000.
>
> Keep your packaged milk batch details, purchase receipts, and any photographs or packaging ready as proof.
>
> Source: Food Safety and Standards Authority of India - Food Safety Connect, P FSSAI
> Source: Department of Consumer Affairs - National Consumer Helpline (NCH), H NCH
>
> This is legal information, not legal advice.

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.

- check_routing: turn 1: category='consumer'; expected 'out_of_scope'
- check_action: turn 1: action='answer'; expected 'escalate'
- check_needs_lawyer: turn 1: needs_lawyer=False; expected True
- check_referral: turn 1: HARD FAIL: wrong bodies=['COM-DIR-NCH']; statute/section patterns=[]

Likely layers: escalation, gate/router/draft, referral retrieval/rendering, router

## Severity 2: T-044 (repeat 1)

Raw evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\real-20261106T090855.555013Z\raw\T-044.json

Observed visible output:

Turn 1:

> You can register and track your provident fund grievance online through the EPFiGMS (EPF i-Grievance Management System) portal at https://epfigms.gov.in/. You may also contact the EPFO Multilingual Helpline at 14470 or the Toll-Free Help Desk for UAN and member services at 1800-118-005.
>
> Keep a record of your UAN, the date you submitted your withdrawal request, and any reference numbers provided by the portal. Take screenshots of the current pending status to support your grievance.
>
> What is your PF account number (UAN)?
>
> What is the name of the regional PF office where your claim is currently pending?
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

Expected: category=out_of_scope; action=escalate; needs_lawyer=True. Referral safety is scored independently: an expected body or legal-aid-only fallback passes; any other body or statute/section pattern hard fails. No referral is a recall miss, not a precision failure. Targets are agent-mapped, pending human confirmation.

- check_routing: turn 1: category='wages'; expected 'out_of_scope'
- check_action: turn 1: action='answer'; expected 'escalate'

Likely layers: gate/router/draft, router

## Infrastructure and incomplete coverage

Infrastructure errors: 0; unattempted case-runs: 0.

## Findings requiring review
