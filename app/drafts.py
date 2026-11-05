"""Draft mode (P0: security-deposit demand notice only). Template-filled, never LLM-invented.
Missing facts stay as visible [● placeholder]. Legal references only from retrieved, in-force chunks."""
import re

from .config import ROOT, load_config
from . import retrieval, verifier

FIELDS = {  # placeholder text in the template -> case_file key
    "[● landlord's full name]": "counterparty_name",
    "[● your full name]": "person_name",
    "[● your name]": "person_name",
    "[● deposit amount]": "amount_inr",
    "[● property address]": "property_address",
    "[● tenancy start date]": "tenancy_start_date",
    "[● date you vacated]": "vacated_date",
    "[● date of payment]": "deposit_paid_date",
    "[● mode of payment, e.g. bank transfer / UPI / cash]": "payment_mode",
}


def _legal_basis(chunks: list[dict]) -> tuple[str, list[str]]:
    """Return (paragraph, cited ids) built only from in-force statute/rule chunks. Empty if none."""
    use = [c for c in chunks if c.get("status") == "in_force" and c.get("doc_type") in ("statute", "rule")
           and c["category"] == "tenancy"][:2]
    if not use:
        return "", []
    refs = "; ".join(f"{c['doc_title']}, {c['unit']} {c['unit_number']}" for c in use)
    para = (f"\nThis demand is made with reference to: {refs}. "
            f"[● Have a lawyer confirm that these provisions apply to your case.]\n")
    return para, [c["id"] for c in use]


def deposit_notice(case_file: dict, state: str | None) -> dict:
    """Returns {"text": str, "citations": [ids], "missing": [placeholders left], "scan_issues": [...]}."""
    text = (ROOT / "app" / "templates" / "deposit_notice_en.txt").read_text(encoding="utf-8")
    cats, juris = ["tenancy"], ["central"] + ([state] if state and state.upper() in
                                               [s.upper() for s in load_config().get("covered_states", [])] else [])
    res = retrieval.search("landlord must return security deposit; remedy if deposit not returned", cats, juris, 4)
    gate_ok = retrieval.passes_gate(res["top_score"])
    chunks = [h["chunk"] for h in res["hits"]] if gate_ok else []
    basis, cites = _legal_basis(chunks)
    text = text.replace("{LEGAL_BASIS}", basis)
    for ph, key in FIELDS.items():
        v = case_file.get(key)
        if v not in (None, "", []):
            val = f"{int(v):,}" if key == "amount_inr" and str(v).replace(".", "").isdigit() else str(v)
            text = text.replace(ph, val)
    missing = sorted(set(re.findall(r"\[●[^\]]*\]", text)))
    issues = verifier.scan_patterns(text, chunks)
    return {"text": text, "citations": cites, "missing": missing, "scan_issues": issues,
            "retrieved": [{"id": h["id"], "score": h["score"]} for h in res["hits"]]}
