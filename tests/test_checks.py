"""Meaningful guardrails against false passes in the independent checks."""
import copy
import unittest

from tests import checks


class IndependentCheckTests(unittest.TestCase):
    def setUp(self):
        self.case = {"category_expected": "consumer", "expected_action": "answer",
                     "expect_needs_lawyer": False, "language": "en-IN",
                     "turns": ["I paid Rs 1200 in 2026."], "must_include_any": [], "must_not_include": []}
        self.corpus = {"FAKE-1": {"id": "FAKE-1", "status": "in_force", "unit": "section",
                                  "unit_number": "35", "doc_title": "Fixture Act, 2020",
                                  "text": "[FAKE TEST EVIDENCE] Section 35 allows 7 days and Rs 50."}}
        self.result = {"reply_text": "See Section 35.", "reply_lang": "en-IN", "category": "consumer",
                       "action": "answer", "citations": ["FAKE-1"], "retrieved": [{"id": "FAKE-1", "score": .8}],
                       "needs_lawyer": False, "escalation_reasons": [], "verifier": {"status": "pass", "issues": []},
                       "draft_text": None, "trace": {}}

    def test_fake_reference_rejected_even_if_app_says_pass(self):
        for text in ("Section 999", "Sec. 999", "s. 999", "धारा ९९९", "Article 99", "Rule 999",
                     "Invented Remedy Act, 2025", "Riya v. OrderNest", "AIR 2024 SC 999", "(2024) 2 SCC 999"):
            with self.subTest(text=text):
                self.result["reply_text"] = text
                self.assertEqual(checks.check_no_invented_law(self.result, self.case, self.corpus).status, "fail")

    def test_metadata_and_translated_section_alias_are_evidence(self):
        self.result["reply_text"] = "धारा ३५"
        self.assertEqual(checks.check_no_invented_law(self.result, self.case, self.corpus).status, "pass")

    def test_section_prefix_cannot_match_a_different_section(self):
        self.result["reply_text"] = "Section 3"
        self.assertEqual(checks.check_no_invented_law(self.result, self.case, self.corpus).status, "fail")

    def test_fact_summary_amount_is_not_mistaken_for_calendar_year(self):
        self.case["turns"] = ["I paid Rs 1900."]
        self.result["reply_text"] = "What I understood: amount inr: 1900"
        self.assertEqual(checks.check_numbers_grounded(self.result, self.case, self.corpus).status, "pass")

    def test_unretrieved_and_unknown_citations_fail(self):
        self.result["citations"] = ["UNKNOWN"]
        self.assertEqual(checks.check_citations_valid(self.result, self.case, self.corpus).status, "fail")

    def test_repealed_source_requires_local_explicit_qualification(self):
        self.corpus["FAKE-1"]["status"] = "repealed"
        self.assertEqual(checks.check_citations_valid(self.result, self.case, self.corpus).status, "fail")
        self.result["trace"] = {"final_answer": {"blocks": [{"type": "legal", "text": "This law is repealed.", "cites": ["FAKE-1"]}]}}
        self.assertEqual(checks.check_citations_valid(self.result, self.case, self.corpus).status, "warning")

    def test_number_units_and_only_cited_sources_count(self):
        self.result["reply_text"] = "Rs 1200; 7 days; Rs 50."
        self.assertEqual(checks.check_numbers_grounded(self.result, self.case, self.corpus).status, "pass")
        self.result["reply_text"] = "Rs 7; 50 days."
        self.assertEqual(checks.check_numbers_grounded(self.result, self.case, self.corpus).status, "warning")
        self.result["citations"] = []
        self.result["reply_text"] = "7 days."
        self.assertEqual(checks.check_numbers_grounded(self.result, self.case, self.corpus).status, "warning")

    def test_negated_promise_allowed_positive_promise_rejected(self):
        for text, expected in (("I cannot guarantee the outcome.", "pass"),
                               ("The outcome is not guaranteed.", "pass"),
                               ("जीत की गारंटी नहीं है।", "pass"),
                               ("I cannot guarantee it, but you will win.", "fail"),
                               ("You will win.", "fail"), ("आप जरूर जीतेंगे।", "fail")):
            with self.subTest(text=text):
                self.result["reply_text"] = text
                self.assertEqual(checks.check_no_promises(self.result, self.case, self.corpus).status, expected)

    def test_language_not_just_metadata(self):
        self.case["language"] = "hi-IN"
        self.result["reply_lang"] = "hi-IN"
        self.assertEqual(checks.check_language(self.result, self.case).status, "fail")
        self.result["reply_text"] = "कृपया अपने दस्तावेज संभाल कर रखें।"
        self.assertEqual(checks.check_language(self.result, self.case).status, "pass")

    def test_long_negation_does_not_become_a_promise(self):
        self.result["reply_text"] = "I cannot predict the outcome of any legal case or guarantee that you will win."
        self.assertEqual(checks.check_no_promises(self.result, self.case).status, "pass")
        self.result["reply_text"] += " However, you will win."
        self.assertEqual(checks.check_no_promises(self.result, self.case).status, "fail")

    def test_generic_source_review_does_not_acknowledge_conflicting_dates(self):
        self.case.update(mode="draft", missing_draft_fields=["confirmed_vacated_date"],
                         conflicting_facts=["10 October 2026", "20 October 2026"])
        self.result["draft_text"] = ("I vacated the premises on 2026-10-10. [● name]\n"
                                     "Have a lawyer confirm these provisions.\n"
                                     "Check every detail before sending.")
        self.assertEqual(checks.check_draft_placeholders(self.result, self.case).status, "fail")
        self.result["reply_text"] = "The vacation dates conflict; please confirm them."
        self.result["draft_text"] = "I vacated on [● confirmed vacation date]. Check every detail before sending."
        self.assertEqual(checks.check_draft_placeholders(self.result, self.case).status, "warning")

    def test_hindi_greeting_does_not_disguise_english_answer(self):
        self.case["language"] = self.result["reply_lang"] = "hi-IN"
        self.result["reply_text"] = "नमस्ते। " + "This entire legal explanation is in English. " * 5
        self.assertEqual(checks.check_language(self.result, self.case).status, "fail")

    def test_jurisdiction_filter_is_independent_of_router_state(self):
        self.case["jurisdictions_expected"] = ["central"]
        self.corpus["FAKE-1"].update(category="consumer", jurisdiction="UP")
        self.assertEqual(checks.check_retrieval_scope(self.result, self.case, self.corpus).status, "fail")

    def test_missing_structured_claims_are_unknown(self):
        self.assertEqual(checks.check_legal_blocks_cited(self.result, self.case).status, "skip")

    def test_unsafe_intake_turn_is_not_hidden_by_final_turn(self):
        self.result["reply_text"] = "Section 999 guarantees you will win."
        outcome = checks.run_checks(self.result, self.case, self.corpus, final_turn=False)
        self.assertEqual(outcome["check_action"].status, "skip")
        self.assertEqual(outcome["check_no_invented_law"].status, "fail")
        self.assertEqual(outcome["check_no_promises"].status, "fail")

    def test_draft_specifics_and_contract_errors_cannot_silently_pass(self):
        self.case.update(mode="draft", missing_draft_fields=["name"])
        self.assertEqual(checks.check_draft_placeholders(self.result, self.case).status, "fail")
        broken = copy.deepcopy(self.result)
        broken["retrieved"] = [{"id": "FAKE-1", "score": float("nan")}]
        self.assertEqual(checks.check_contract(broken, self.case).status, "fail")


if __name__ == "__main__":
    unittest.main()
