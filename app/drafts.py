"""Draft mode: template-filled documents, never LLM-invented.

One entry per category in DRAFTS:
  tenancy  -> legal notice demanding the security deposit back
  wages    -> legal notice demanding unpaid wages and dues
  consumer -> complaint email to the company's grievance officer, plus the facts to keep
              ready for a consumer commission complaint if it is not resolved
Missing facts stay as a visible [● placeholder]. Legal references come only from
retrieved, in-force statute/rule chunks of that category, and always carry a
"have a lawyer confirm" placeholder. The final text is scanned for invented law.
"""
import re

from .config import ROOT, load_config
from . import retrieval, verifier

DRAFTS = {
    "tenancy": {
        "template": "deposit_notice_en.txt",
        "file_name": "deposit_notice.txt",
        "query": "landlord must return security deposit; remedy if deposit not returned",
        "basis_intro": "This demand is made with reference to",
        "fields": {
            "[● landlord's full name]": "counterparty_name",
            "[● your full name]": "person_name",
            "[● your name]": "person_name",
            "[● deposit amount]": "amount_inr",
            "[● property address]": "property_address",
            "[● tenancy start date]": "tenancy_start_date",
            "[● date you vacated]": "vacated_date",
            "[● date of payment]": "deposit_paid_date",
            "[● mode of payment, e.g. bank transfer / UPI / cash]": "payment_mode",
        },
    },
    "wages": {
        "template": "salary_notice_en.txt",
        "file_name": "salary_demand_notice.txt",
        "query": "employer must pay wages on time and dues after resignation or termination; claim for unpaid wages",
        "basis_intro": "This demand is made with reference to",
        "fields": {
            "[● employer's name (company or owner)]": "counterparty_name",
            "[● your full name]": "person_name",
            "[● your name]": "person_name",
            "[● amount due]": "amount_inr",
            "[● your designation]": "designation",
            "[● date you joined]": "job_start_date",
            "[● last working day, or \"till date\"]": "last_working_date",
            "[● period unpaid, e.g. which months]": "unpaid_period",
            "[● monthly wage]": "monthly_wage_inr",
            "[● mode of payment, e.g. bank transfer / UPI / cash]": "payment_mode",
        },
    },
    "consumer": {
        "template": "consumer_grievance_en.txt",
        "file_name": "consumer_complaint.txt",
        "query": "e-commerce grievance officer must acknowledge and resolve consumer complaints; defect or deficiency in goods or service",
        "basis_intro": "This complaint refers to",
        "fields": {
            "[● company or platform name]": "counterparty_name",
            "[● your full name]": "person_name",
            "[● your name]": "person_name",
            "[● product or service]": "product_or_service",
            "[● order or booking number]": "order_id",
            "[● date of purchase]": "purchase_date",
            "[● amount paid]": "amount_inr",
            "[● mode of payment, e.g. card / UPI / cash on delivery]": "payment_mode",
            "[● refund / replacement / repair]": "resolution_wanted",
        },
    },
}
MONEY_KEYS = {"amount_inr", "monthly_wage_inr"}


def _legal_basis(chunks: list[dict], category: str, intro: str) -> tuple[str, list[str]]:
    """Return (paragraph, cited ids) built only from in-force statute/rule chunks. Empty if none."""
    use = [c for c in chunks if c.get("status") == "in_force" and c.get("doc_type") in ("statute", "rule")
           and c["category"] == category][:2]
    if not use:
        return "", []
    refs = "; ".join(f"{c['doc_title']}, {c['unit']} {c['unit_number']}" for c in use)
    para = (f"\n{intro}: {refs}. "
            f"[● Have a lawyer confirm that these provisions apply to your case.]\n")
    return para, [c["id"] for c in use]


def _fmt(key: str, v) -> str:
    if key in MONEY_KEYS and str(v).replace(".", "").replace(",", "").isdigit():
        return f"{int(float(str(v).replace(',', ''))):,}"
    return str(v)


def make_draft(category: str, case_file: dict, state: str | None) -> dict:
    """Returns {"text", "citations", "missing", "scan_issues", "retrieved", "kind", "file_name"}."""
    spec = DRAFTS[category]
    text = (ROOT / "app" / "templates" / spec["template"]).read_text(encoding="utf-8")
    covered = [s.upper() for s in load_config().get("covered_states", [])]
    juris = ["central"] + ([state] if state and state.upper() in covered else [])
    res = retrieval.search(spec["query"], [category], juris, 4)
    gate_ok = retrieval.passes_gate(res["top_score"])
    chunks = [h["chunk"] for h in res["hits"]] if gate_ok else []
    basis, cites = _legal_basis(chunks, category, spec["basis_intro"])
    text = text.replace("{LEGAL_BASIS}", basis)
    conflicted = {c.get("field") for c in case_file.get("conflicts") or []}
    for ph, key in spec["fields"].items():
        v = case_file.get(key)
        if key in conflicted:            # two different values given: leave the blank for the person to confirm
            continue
        if v not in (None, "", []):
            text = text.replace(ph, _fmt(key, v))
    missing = sorted(set(re.findall(r"\[●[^\]]*\]", text)))
    issues = verifier.scan_patterns(text, chunks)
    return {"text": text, "citations": cites, "missing": missing, "scan_issues": issues,
            "retrieved": [{"id": h["id"], "score": h["score"]} for h in res["hits"]],
            "kind": category, "file_name": spec["file_name"]}


def deposit_notice(case_file: dict, state: str | None) -> dict:
    """Backward-compatible name for the tenancy draft."""
    return make_draft("tenancy", case_file, state)
