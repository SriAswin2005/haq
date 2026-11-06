"""Independent referral safety, display detection and metric-denominator tests."""
import unittest

from tests.checks import CheckResult, check_referral, referral_observation, check_routing, check_action, check_needs_lawyer, check_no_invented_law
from tests.reporting import referral_metrics
from tests.round4_reports import append_section, START, END


def directory(cid, title, url):
    return {"id": cid, "doc_title": title, "source_url": url, "text": "Fixture directory text.",
            "doc_type": "portal_procedure", "category": "common"}


class ReferralChecks(unittest.TestCase):
    def setUp(self):
        self.case = {"expected_referral_any": ["COM-DIR-CYBER"], "turns": ["UPI fraud"]}
        self.corpus = {c["id"]: c for c in [
            directory("COM-DIR-CYBER", "National Cyber Crime Reporting Portal", "https://cybercrime.gov.in/"),
            directory("COM-DIR-RBI", "Reserve Bank of India - Complaint Management System", "https://www.rbi.org.in/Scripts/Complaints.aspx"),
            directory("COM-DIR-IRDAI", "Insurance Regulatory and Development Authority of India - Bima Bharosa", "https://bimabharosa.irdai.gov.in/"),
            directory("COM-DIR-EPFO", "Employees' Provident Fund Organisation - EPFiGMS Portal", "https://epfigms.gov.in/"),
            directory("COM-DIR-RAIL", "Indian Railways - RailMadad Portal", "https://railmadad.indianrailways.gov.in/"),
            directory("COM-DIR-FSSAI", "Food Safety and Standards Authority of India - Food Safety Connect", "https://foodsafetyconnect.fssai.gov.in/"),
            directory("COM-DIR-SANCHAR", "Department of Telecommunications - Sanchar Saathi Portal", "https://sancharsaathi.gov.in/"),
            directory("COM-DIR-TELECOM", "Department of Telecommunications - Public Grievance Division", "https://dot.gov.in/"),
            directory("COM-NALSA-H15100", "National Legal Services Authority Helpline", "https://nalsa.gov.in/contact-us/"),
        ]}

    def check(self, text, **fields):
        return check_referral({"reply_text": text, **fields}, self.case, self.corpus)

    def test_legal_aid_only_passes_but_earns_no_referral_credit(self):
        result = self.check("For free legal aid: National Legal Services Authority Helpline, 15100 (https://nalsa.gov.in/contact-us/).")
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.details["shown"], [])
        self.assertEqual(result.details["correct"], [])

    def test_expected_body_or_hindi_alias_passes_and_aliases_deduplicate(self):
        for text in ("National Cyber Crime Reporting Portal (https://cybercrime.gov.in/).",
                     "राष्ट्रीय साइबर अपराध रिपोर्टिंग पोर्टल पर शिकायत करें।"):
            with self.subTest(text=text):
                result = self.check(text)
                self.assertEqual(result.status, "pass")
                self.assertEqual(result.details["correct"], ["COM-DIR-CYBER"])

    def test_correct_plus_wrong_body_is_hard_failure(self):
        result = self.check("National Cyber Crime Reporting Portal; also contact RBI.")
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.details["correct"], ["COM-DIR-CYBER"])
        self.assertEqual(result.details["wrong"], ["COM-DIR-RBI"])

    def test_retrieved_and_cited_but_unshown_expected_body_gets_no_credit(self):
        result = self.check("Please ask a lawyer or legal aid office.", citations=["COM-DIR-CYBER"],
                            retrieved=[{"id": "COM-DIR-CYBER", "score": .9}])
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.details["shown"], [])

    def test_wrong_url_and_unknown_body_cannot_disappear_from_precision(self):
        for text in ("Use https://www.rbi.org.in/Scripts/Complaints.aspx", "Contact the Imaginary Relief Board.",
                     "Imaginary Relief Board may help.", "काल्पनिक राहत आयोग में शिकायत करें।", "Apply at https://wrong-office.example/complaint"):
            with self.subTest(text=text):
                result = self.check(text)
                self.assertEqual(result.status, "fail")
                self.assertTrue(result.details["wrong"])

    def test_statute_or_section_is_hard_failure_even_with_correct_referral(self):
        for law in ("Section 35", "Sec. 12", "s. 420", "धारा ४२०", "Rule 6", "RTI Act",
                    "Consumer Protection Act, 2019", "consumer protection act, 2019", "SECTION-35", "IPC", "सूचना का अधिकार अधिनियम"):
            with self.subTest(law=law):
                result = self.check("National Cyber Crime Reporting Portal. " + law)
                self.assertEqual(result.status, "fail")
                self.assertTrue(result.details["statute_patterns"])

    def test_answer_requires_expected_body_to_be_visible_and_cited(self):
        for text, citations, expected in [
            ("National Cyber Crime Reporting Portal.", ["COM-DIR-CYBER"], "pass"),
            ("National Cyber Crime Reporting Portal.", [], "fail"),
            ("Please ask a lawyer or legal aid office.", ["COM-DIR-CYBER"], "fail"),
            ("National Cyber Crime Reporting Portal.", ["COM-DIR-RBI"], "fail")]:
            with self.subTest(text=text, citations=citations):
                result = self.check(text, category="consumer", action="answer", citations=citations)
                self.assertEqual(result.status, expected)

    def test_grounded_answer_statute_is_allowed_but_out_of_scope_or_escalation_still_fails(self):
        self.corpus["COM-DIR-CYBER"]["text"] = "Fixture Remedy Act, 2024. Section 35 describes the fixture."
        text = "National Cyber Crime Reporting Portal. Fixture Remedy Act, 2024; Section 35."
        for category, action, expected in [("consumer", "answer", "pass"), ("out_of_scope", "answer", "fail"),
                                           ("consumer", "escalate", "fail"), ("out_of_scope", "escalate", "fail")]:
            with self.subTest(category=category, action=action):
                result = self.check(text, category=category, action=action, citations=["COM-DIR-CYBER"])
                self.assertEqual(result.status, expected)
                self.assertEqual(result.details["ungrounded_statutes"], [])

    def test_retrieved_but_uncited_law_does_not_ground_an_answer(self):
        self.corpus["COM-DIR-RBI"]["text"] = "Fixture Remedy Act, 2024. Section 35."
        result = {"reply_text": "National Cyber Crime Reporting Portal. Section 35.", "action": "answer", "category": "consumer",
                  "citations": ["COM-DIR-CYBER"], "retrieved": [{"id": "COM-DIR-RBI"}]}
        self.assertEqual(check_referral(result, self.case, self.corpus).status, "fail")
        self.assertEqual(check_no_invented_law(result, self.case, self.corpus).status, "fail")

    def test_grounded_law_cannot_hide_a_wrong_body(self):
        self.corpus["COM-DIR-CYBER"]["text"] = "Fixture Remedy Act, 2024."
        result = self.check("National Cyber Crime Reporting Portal; RBI. Fixture Remedy Act, 2024.",
                            category="consumer", action="answer", citations=["COM-DIR-CYBER"])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.details["wrong"], ["COM-DIR-RBI"])

    def test_cited_statute_url_in_answer_is_a_source_not_an_extra_body(self):
        self.corpus["LAW"] = {"id": "LAW", "doc_type": "statute", "source_url": "https://legislation.example/act1",
                              "text": "Fixture Remedy Act, 2024."}
        result = self.check("National Cyber Crime Reporting Portal. Fixture Remedy Act, 2024 (https://legislation.example/act1).",
            category="consumer", action="answer", citations=["COM-DIR-CYBER", "LAW"])
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.details["shown"], ["COM-DIR-CYBER"])

    def test_allowed_routes_require_coherent_category_action_and_lawyer_tuples(self):
        self.case.update(category_expected="consumer", expected_action="answer", expect_needs_lawyer=False,
            expected_outcomes=[{"category": "consumer", "action": "answer", "needs_lawyer": False},
                               {"category": "out_of_scope", "action": "escalate", "needs_lawyer": True}])
        for category, action, lawyer, expected in [("consumer", "answer", False, True), ("out_of_scope", "escalate", True, True),
            ("consumer", "escalate", False, False), ("consumer", "answer", True, False), ("out_of_scope", "answer", False, False)]:
            with self.subTest(category=category, action=action, lawyer=lawyer):
                result = {"category": category, "action": action, "needs_lawyer": lawyer, "reply_text": "A lawyer or legal aid office can help."}
                passed = all(f(result, self.case).status == "pass" for f in [check_routing, check_action, check_needs_lawyer])
                self.assertEqual(passed, expected)

    def test_generic_legal_disclaimer_and_phone_numbers_are_not_statutes(self):
        result = self.check("National Cyber Crime Reporting Portal: 1930. This is legal information, not legal advice.")
        self.assertEqual(result.status, "pass")

    def test_generic_portal_and_helpline_descriptors_are_not_additional_bodies(self):
        for text in ("National Cyber Crime Reporting Portal. Online Portal. Multilingual Helpline.",
                     "National Cyber Crime Reporting Portal के पोर्टल पर जाएं। टोल-फ्री हेल्पलाइन पर फोन करें।",
                     "National Cyber Crime Reporting Portal. आपको फ्री बिजली हेल्पलाइन नहीं, सही पोर्टल चाहिए।"):
            with self.subTest(text=text):
                result = self.check(text)
                self.assertEqual(result.status, "pass")
                self.assertEqual(result.details["shown"], ["COM-DIR-CYBER"])

    def test_known_body_removed_from_sentence_does_not_create_a_new_portal_body(self):
        self.case["expected_referral_any"] = ["COM-DIR-EPFO"]
        result = self.check("You may contact EPFO by calling its helpline or by using the web portal.")
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.details["shown"], ["COM-DIR-EPFO"])

    def test_official_name_without_portal_suffix_is_the_same_food_body(self):
        self.case["expected_referral_any"] = ["COM-DIR-FSSAI"]
        result = self.check("Contact Food Safety and Standards Authority of India (FSSAI) through its portal.")
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.details["shown"], ["COM-DIR-FSSAI"])

    def test_translated_regulator_and_railway_helpline_names_are_canonical_bodies(self):
        for body, text in [("IRDAI", "बीमा विनियामक और विकास प्राधिकरण (IRDAI) के बीमा भरोसा ऑनलाइन पोर्टल पर जाएं।"),
                           ("RAIL", "भारतीय रेलवे के रेलमदद पोर्टल या रेलवे हेल्पलाइन पर शिकायत करें।")]:
            with self.subTest(body=body):
                self.case["expected_referral_any"] = ["COM-DIR-" + body]
                result = self.check(text)
                self.assertEqual(result.status, "pass")
                self.assertEqual(result.details["shown"], ["COM-DIR-" + body])

    def test_draft_text_is_also_scanned(self):
        result = self.check("National Cyber Crime Reporting Portal.", draft_text="Section 35 applies.")
        self.assertEqual(result.status, "fail")

    def test_full_title_does_not_count_parent_department_twice(self):
        self.case["expected_referral_any"] = ["COM-DIR-SANCHAR"]
        result = self.check("Department of Telecommunications - Sanchar Saathi Portal (https://sancharsaathi.gov.in/)")
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.details["shown"], ["COM-DIR-SANCHAR"])

    def test_old_cases_are_not_reinterpreted(self):
        self.assertEqual(check_referral({"reply_text": "Section 35"}, {}, self.corpus).status, "skip")

    def test_partial_proper_name_inside_known_full_title_is_not_an_extra_body(self):
        self.case["expected_referral_any"] = ["COM-DIR-IRDAI"]
        result = self.check("Insurance Regulatory and Development Authority of India - Bima Bharosa (https://bimabharosa.irdai.gov.in/)")
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.details["shown"], ["COM-DIR-IRDAI"])

    def test_regulator_name_without_portal_suffix_and_full_footer_are_one_body(self):
        self.case["expected_referral_any"] = ["COM-DIR-IRDAI"]
        result = self.check("The Insurance Regulatory and Development Authority of India (IRDAI) operates Bima Bharosa.\n"
            "Source: Insurance Regulatory and Development Authority of India - Bima Bharosa.",
            category="consumer", action="answer", citations=["COM-DIR-IRDAI"])
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.details["shown"], ["COM-DIR-IRDAI"])

    def metric_item(self, text):
        outcome = self.check(text)
        return {"status": "fail" if outcome.status == "fail" else "pass", "case": self.case,
                "turn_checks": [{"check_referral": outcome}], "checks": {"check_referral": outcome}}

    def test_precision_and_recall_use_visible_bodies_and_expected_cases_separately(self):
        metrics = referral_metrics([self.metric_item("National Cyber Crime Reporting Portal."),
                                    self.metric_item("National Cyber Crime Reporting Portal and RBI."),
                                    self.metric_item("Please ask a lawyer or legal aid office.")])
        self.assertEqual(metrics["correct_bodies"], 2)
        self.assertEqual(metrics["shown_bodies"], 3)
        self.assertEqual(metrics["correct_cases"], 2)
        self.assertEqual(metrics["expected_cases"], 3)
        self.assertEqual(metrics["safe_correct_cases"], 1)
        self.assertEqual(metrics["referral_check_passes"], 2)

    def test_two_acceptable_bodies_earn_one_case_of_recall(self):
        self.case["expected_referral_any"] = ["COM-DIR-CYBER", "COM-DIR-RBI"]
        metrics = referral_metrics([self.metric_item("National Cyber Crime Reporting Portal and RBI.")])
        self.assertEqual(metrics["correct_bodies"], 2)
        self.assertEqual(metrics["shown_bodies"], 2)
        self.assertEqual(metrics["correct_cases"], 1)
        self.assertEqual(metrics["expected_cases"], 1)


class ReferralReportTests(unittest.TestCase):
    def test_append_preserves_old_comparison_and_does_not_duplicate_the_section(self):
        before = "# Before / after\n\nBaseline 12/30; after 17/30.\n"
        first = append_section(before, "## New referrals\nOld numbers\n")
        second = append_section(first, "## New referrals\nNew numbers\n")
        self.assertTrue(second.startswith(before.rstrip()))
        self.assertEqual(second.count(START), 1)
        self.assertEqual(second.count(END), 1)
        self.assertNotIn("Old numbers", second)

    def test_rescoring_preserves_unrelated_text_after_the_generated_section(self):
        before = "Prefix\n" + START + "\nOld\n" + END + "\nUser-added note\n"
        after = append_section(before, "Replacement\n")
        self.assertTrue(after.startswith("Prefix\n"))
        self.assertTrue(after.endswith("\nUser-added note\n"))


if __name__ == "__main__":
    unittest.main()
