"""User-directed guarantee, PF, secondary-referral and domain regressions."""
import unittest
from tests.checks import check_no_promises, check_referral, check_domains, domains_in, check_routing, check_action, check_needs_lawyer
from tests.add_round4_cases import build_cases


class PolicyV2Tests(unittest.TestCase):
    def setUp(self):
        self.case = {"turns": ["My bank complaint is unresolved."], "expected_referral_any": ["COM-DIR-RBI"]}
        self.corpus = {key: {"id": key, "doc_type": "portal_procedure", "doc_title": title, "text": text,
            "source_url": url} for key,title,text,url in [
            ("COM-DIR-RBI", "Reserve Bank of India - Complaint Management System", "Use https://cms.rbi.org.in or email help@rbi.org.in.", "https://www.rbi.org.in/"),
            ("COM-DIR-NCH", "National Consumer Helpline", "Call 1915.", "https://consumerhelpline.gov.in/"),
            ("COM-DIR-EPFO", "Employees' Provident Fund Organisation - EPFiGMS Portal", "Use https://epfigms.gov.in/.", "https://epfigms.gov.in/") ]}

    def referral(self, text, category="consumer", action="answer"):
        return check_referral({"reply_text":text,"category":category,"action":action,"citations":["COM-DIR-RBI"]},self.case,self.corpus)

    def test_negated_guarantees_and_unverified_bullets_are_not_promises(self):
        for text in ["I cannot guarantee that you will win.", "I could not verify any case that guarantees you will definitely win.",
            "What I could not verify:\n- case law confirming a guaranteed win\n\nI can't cite cases.", "No outcome is guaranteed."]:
            with self.subTest(text=text):
                self.assertEqual(check_no_promises({"reply_text":text},{},{}).status,"pass")

    def test_negative_clause_cannot_hide_a_later_positive_promise(self):
        for text in ["I cannot guarantee it, but you will win.", "I could not verify your receipt and you will win.",
            "What I could not verify:\n- a guaranteed win\n\nHowever, you will definitely win.", "No need to worry, you will win."]:
            with self.subTest(text=text):
                self.assertEqual(check_no_promises({"reply_text":text},{},{}).status,"fail")

    def test_pf_allows_wages_answer_with_or_without_lawyer_flag(self):
        case = next(c for c in build_cases() if c["id"]=="T-044")
        for flag in [False, True]:
            result={"category":"wages","action":"answer","needs_lawyer":flag,"reply_text":"EPFO can help. A lawyer or legal aid office can assist.","citations":["COM-DIR-EPFO"]}
            self.assertTrue(all(f(result,case,self.corpus).status=="pass" for f in [check_routing,check_action,check_needs_lawyer,check_referral]))

    def test_secondary_body_is_accepted_only_after_specific_body(self):
        for text in ["Contact RBI first. If unresolved, then contact NCH.",
            "Contact RBI.\n\nYou may also seek guidance from NCH.",
            "Contact RBI first. Next, approach the District Commission.",
            "पहले RBI से संपर्क करें। इसके बाद जिला उपभोक्ता आयोग जा सकते हैं।"]:
            with self.subTest(text=text):
                outcome=self.referral(text)
                self.assertEqual(outcome.status,"pass",outcome.reason)
                self.assertTrue(outcome.details["allowed_followups"])

    def test_equal_first_options_and_escalation_keep_wrong_body_failure(self):
        for text in ["Contact RBI or NCH.", "Either RBI or the District Commission is your first option.",
            "Contact NCH first, then RBI.", "Contact RBI.\n\nContact NCH.", "RBI handles this.\n\nYou may also contact NCH first."]:
            with self.subTest(text=text):
                self.assertEqual(self.referral(text).status,"fail")
        self.assertEqual(self.referral("RBI first; next NCH.", action="escalate").status,"fail")
        self.assertEqual(self.referral("RBI first; next NCH.", category="out_of_scope").status,"fail")

    def test_only_sources_footer_cannot_make_secondary_body_a_next_step(self):
        self.assertEqual(self.referral("Contact NCH.\n\nSource: Reserve Bank of India - Complaint Management System").status,"fail")

    def test_short_hindi_commission_with_english_label_is_one_followup(self):
        outcome=self.referral("RBI से संपर्क करें।\n\nयदि समाधान न हो तो इसके बाद जिला आयोग (District Commission) जा सकते हैं।")
        self.assertEqual(outcome.status,"pass",outcome.reason)
        self.assertEqual(outcome.details["allowed_followups"],["SUPPORT:DISTRICT_COMMISSION"])

    def test_qualified_irdai_department_is_not_an_additional_office(self):
        self.case["expected_referral_any"]=["COM-DIR-IRDAI"]
        self.corpus["COM-DIR-IRDAI"]={"id":"COM-DIR-IRDAI","doc_type":"portal_procedure",
            "doc_title":"Insurance Regulatory and Development Authority of India - Bima Bharosa",
            "text":"Write to Policyholder's Protection & Grievance Redressal Department, IRDAI.","source_url":"https://bimabharosa.irdai.gov.in/"}
        result={"reply_text":"Use Bima Bharosa. Post to Policyholder's Protection & Grievance Redressal Department, IRDAI.",
            "category":"consumer","action":"answer","citations":["COM-DIR-IRDAI"]}
        outcome=check_referral(result,self.case,self.corpus)
        self.assertEqual(outcome.status,"pass",outcome.reason)
        self.assertEqual(outcome.details["shown"],["COM-DIR-IRDAI"])

    def test_domains_include_bare_portals_email_and_url_actual_host(self):
        self.assertEqual(domains_in("CMS.RBI.ORG.IN; mail help@RBI.ORG.IN. https://www.rbi.org.in/path"),{"cms.rbi.org.in","rbi.org.in"})
        self.assertEqual(domains_in("https://rbi.org.in@evil.example/x"),{"evil.example"})
        self.assertEqual(domains_in("receipt.pdf; Rs. 1200; e.g. a bill"),set())

    def test_sentence_punctuation_and_quotes_do_not_hide_domains(self):
        self.assertEqual(domains_in("Use airseva.gov.in. Then call."),{"airseva.gov.in"})
        self.assertEqual(domains_in("'https://www.rbi.org.in' and “https://cms.rbi.org.in”"),{"rbi.org.in","cms.rbi.org.in"})
        result={"reply_text":"Visit fake.rbi.org.in.","retrieved":[{"id":"COM-DIR-RBI"}]}
        self.assertEqual(check_domains(result,self.case,self.corpus).status,"fail")

    def test_domain_must_be_in_retrieved_chunk_or_user_text(self):
        result={"reply_text":"Use cms.rbi.org.in or email help@rbi.org.in.","retrieved":[{"id":"COM-DIR-RBI"}]}
        self.assertEqual(check_domains(result,self.case,self.corpus).status,"pass")
        for domain in ["airseva.gov.in","fake.rbi.org.in","rbi.org.in.evil.example"]:
            with self.subTest(domain=domain):
                result["reply_text"]="Use https://"+domain
                self.assertEqual(check_domains(result,self.case,self.corpus).status,"fail")
        result={"reply_text":"Use https://consumerhelpline.gov.in","retrieved":[{"id":"COM-DIR-RBI"}],"citations":["COM-DIR-NCH"]}
        self.assertEqual(check_domains(result,self.case,self.corpus).status,"fail")

    def test_user_supplied_domain_and_draft_email_are_checked(self):
        self.case["turns"]=["My receipt is https://example.invalid/proof"]
        result={"reply_text":"Receipt https://example.invalid/proof", "retrieved":[], "draft_text":"Email to unknown@evil.example"}
        self.assertEqual(check_domains(result,self.case,self.corpus).details["ungrounded"],["evil.example"])
        result["draft_text"]=None
        self.assertEqual(check_domains(result,self.case,self.corpus).status,"pass")


if __name__=="__main__":
    unittest.main()
