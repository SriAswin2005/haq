# AI Lawyer for India: Architecture and Shared Contract

**Version:** v1.1 (2026-11-05 review: added Section 0 cut line, corrected the UP tenancy-law lead, added `app/cli.py`, rate-limit and confidentiality rules). **Status: FROZEN.** Only the project owner (the human) may change Sections 4, 5, 7 and 8. If you think something is wrong, write it in `docs/CONTRACT_CHANGE_REQUESTS.md` and carry on with the contract as written.

Three agents work in parallel from this one document:

| Agent | Owns (only edit here) | Brief |
|---|---|---|
| Claude Code | `app/`, `config.yaml`, `requirements.txt`, `.env.example`, `README.md` | `01_CLAUDE_CODE_BUILD.md` |
| Antigravity | `data/` | `02_ANTIGRAVITY_CORPUS.md` |
| Codex | `tests/`, `outputs/` | `03_CODEX_TESTS.md` |

All three work in one repo, each inside its own folders. Never edit another agent's folder. Shared files, which anyone may append to but never rewrite: `docs/ai_mistakes.md`, `docs/ASSUMPTIONS.md`.

---

## 0. Time box and cut line (read this first)

The assignment asks for about 2 to 3 hours of human time. It is judged on a prototype that runs on real inputs, honest quality checks and a clear 2-page doc. Polish and size earn nothing. So every feature has a tier, and agents build strictly in tier order. If time runs short, stop at the end of a tier and report. Do not half-build the next tier.

| Tier | What must work | Owner |
|---|---|---|
| **P0** (ship this even if nothing else ships) | Text chat in English and Hindi; router; filtered retrieval; confidence gate; code verifier (Section 8, point 5); SAFE RESPONSE; citations panel; one draft type (deposit demand notice); `app/cli.py`; `--mock` mode with no API keys; P0 corpus (see the corpus brief); 30 test cases, harness and raw outputs | all |
| **P1** | Voice in and out (Sarvam). The problem statement asks for text **or voice**, so treat this as close to required. Also all three draft types, the LLM faithfulness judge, `calibration.md`, hosting on Streamlit Community Cloud | Claude Code, Codex |
| **P2** (stretch) | Practice mode, languages beyond en/hi, judgments in the corpus, `--runs N` flakiness checks | anyone with spare time |

**Interview readiness.** If shortlisted, the human runs the solution on a new input during the interview, possibly with a stronger model through an API key Kuku provides. So P0 includes `app/cli.py` (one command: a message in, the reply and the full `TurnResult` out) and a model swap done in `config.yaml` alone, including an `openai_compatible` provider.

## 1. Goal

A conversational AI that an ordinary person in India can talk to, by text or voice, in the language they are comfortable with, about an everyday legal problem. It helps them: (a) turn a messy story into a structured case (what happened, when, how much, what proof), (b) understand where they stand and their options in plain language, (c) prepare the paperwork (legal notice, complaint), (d) practise against the other side.

**The overriding design rule: it must never invent law.** Every legal statement must be traceable to a verified source chunk, or it must not be said. When the system does not know, it says so and points to a real lawyer or free legal aid.

## 2. Scope (v1)

Covered, in depth:

1. **Consumer refunds and defective goods or services** (`consumer`)
2. **Unpaid or withheld salary and dues** (`wages`)
3. **Rental security deposit not returned** (`tenancy`)

Plus a small cross-cutting set (`common`): limitation periods, how to send a legal notice, free legal aid, Lok Adalat, verified helpline numbers, how to find a lawyer.

**Jurisdiction.** Central laws, plus **Uttar Pradesh** as the one state covered in depth for tenancy and wages (state rent and shops-and-establishments laws vary). *Lead, to be confirmed by the corpus agent from official text:* India Code lists the **Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021** (UP Act 16 of 2021), which appears to have replaced the 1972 UP rent Act. Secondary sources say it caps and governs the security deposit and sends tenancy disputes to a **Rent Authority** instead of the civil court. If that is confirmed, UP deposit answers and the UP deposit draft route to the Rent Authority. For any other state, the system gives only central-law information and says clearly that state law may differ and is not covered. Other states are a stretch goal and must not be added unless fully verified.

Explicitly NOT covered (must trigger the out-of-scope / see-a-lawyer path): criminal matters, FIRs, arrests and bail, family law (divorce, custody, maintenance), property title or ownership disputes, inheritance, tax notices, immigration, cheque-bounce, company or IP law, anything involving violence or threats, and anything outside the three categories.

## 3. Assumptions made (the brief was silent)

- The user is a layperson with a smartphone; reading level about Class 8.
- Corpus is English. User input and output can be in other languages. Retrieval queries are translated to English.
- Free tiers only. The model is swappable. A paid or stronger model is a config change, not a code change.
- The product gives **legal information, not legal advice**, and says so.
- Free tiers limit requests per minute and per day. `llm.py` throttles, and retries with backoff on HTTP 429. The eval runs sequentially and can resume.
- Free-tier model providers may keep prompts. Test cases use invented people and details, never real personal data.

## 4. Repo layout (FROZEN)

```
ai-lawyer/
  .gitignore                # .env, data/index/, __pycache__, outputs/live_trace.jsonl
  config.yaml
  .env.example              # GEMINI_API_KEY, SARVAM_API_KEY (never commit real keys)
  requirements.txt
  README.md                 # run steps, hosting steps
  app/
    ui.py                   # Streamlit UI (text + mic + language picker)
    pipeline.py             # handle_turn() -- the ONLY entry point tests use
    cli.py                  # python -m app.cli "message" -> reply + TurnResult JSON (interview demo)
    llm.py                  # generate(), embed() -- provider-swappable
    voice.py                # Sarvam STT / TTS (+ fallback)
    router.py               # category + facts extraction + escalation flags
    retrieval.py            # index build, filtered search, confidence gate
    verifier.py             # citation + claim checks
    drafts.py               # notice / complaint generation
    practice.py             # roleplay opposing party + coach feedback
    prompts/                # *.md prompt files (no prompts hardcoded in .py)
    templates/              # draft templates with [● placeholders]
  data/
    corpus/
      consumer.jsonl
      wages.jsonl
      tenancy.jsonl
      common.jsonl
    sample/sample_chunks.jsonl   # FAKE chunks, written by Claude Code, dev only
    index/                       # built by app (embeddings cache), gitignored
    MANIFEST.md                  # written by Antigravity
    FAILURES.md                  # written by Antigravity
    STATUS_REGISTER.csv          # written by Antigravity
    verification_sheet.csv       # written by Antigravity, ticked by the human
    validate_corpus.py           # written by Antigravity
  tests/
    cases.jsonl
    run_eval.py
    checks.py
    BUGS.md
  outputs/                       # raw unedited eval runs; never hand-edit
    raw/
    results.csv
    summary.md
    calibration.md
  docs/
    ai_mistakes.md               # every agent logs where an AI tool got it wrong
    ASSUMPTIONS.md
    CONTRACT_CHANGE_REQUESTS.md
```

**Confidentiality.** The repo lives in its own folder (`ai-lawyer/`). Kuku's input pack (the screenplays) and the assignment PDF stay outside it and are never copied in or committed. The brief says not to share them, and the GitHub repo will be public.

## 5. Data contract: the corpus (FROZEN)

One JSON object per line (JSONL), one chunk = one legal unit (one section, one rule, one self-contained procedure step, or one government guidance paragraph group). UTF-8.

```json
{
  "id": "CONS-CPA2019-S35",
  "category": "consumer",
  "doc_title": "Consumer Protection Act, 2019",
  "doc_type": "statute",
  "jurisdiction": "central",
  "unit": "section",
  "unit_number": "35",
  "heading": "<official heading if any>",
  "text": "<VERBATIM text copied from the official source>",
  "status": "in_force",
  "status_note": "",
  "effective_from": "YYYY-MM-DD or null",
  "source_url": "https://...",
  "source_type": "official",
  "fetched_on": "YYYY-MM-DD",
  "verified": "agent",
  "human_check_required": false,
  "language": "en"
}
```

The `CONS-CPA2019-S35` id is a **format example only**; do not assume that section is right.

Field rules:

- `id`: `{CAT}-{ACTCODE}-{UNITLETTER}{NUMBER}`, unique and stable, no spaces. `CAT` is one of `CONS`, `WAGE`, `TEN`, `COM`. Unit letters: `S` section, `R` rule, `O` order, `P` procedure or guidance, `J` judgment extract, `H` helpline.
- `category`: exactly one of `consumer`, `wages`, `tenancy`, `common`. (`out_of_scope` exists only as a router label, never in the corpus.)
- `doc_type`: `statute` | `rule` | `govt_guidance` | `portal_procedure` | `helpline` | `judgment`
- `jurisdiction`: `central` or a state code such as `UP`.
- `status`: `in_force` | `repealed` | `superseded` | `not_yet_in_force` | `model_only` | `unclear`. Repealed or superseded chunks may be kept (so the system can recognise questions about old laws) but are never cited as current law.
- `source_type`: `official` (government or court site) | `secondary`. Secondary sources require `human_check_required: true`.
- `verified`: `agent` (agent checked) | `human` (the project owner checked against the source). Only the human sets `human`.
- `text` must be verbatim. No summaries, no paraphrase, no text written from memory. Long sections may be split into labelled sub-chunks, each with its own id suffix (`...-S35-a`).
- Any chunk containing a **money limit, fee, time limit or deadline** has `human_check_required: true`.

`STATUS_REGISTER.csv` columns: `doc_title, category, jurisdiction, current_status, replaced_by, evidence_url, checked_on, notes`.

## 6. Pipeline: what happens in every turn

```
voice/text in
  -> [voice.py] STT (Sarvam) -> text + detected language
  -> [router.py] one LLM call returns JSON:
        category (consumer|wages|tenancy|out_of_scope|unclear),
        language, state_or_city, case_file_update (facts), missing_facts[],
        escalation_flags[], english_retrieval_query
  -> [deterministic] escalation keyword rules (see Section 9), merged with LLM flags
  -> if out_of_scope or hard escalation: skip to SAFE RESPONSE (Section 10)
  -> [retrieval.py] filter chunks: category in {routed, common}
        AND jurisdiction in {central, user_state_if_covered}
        AND status != repealed (repealed/superseded retrieved separately for "old law" detection)
        -> embed query -> top-k by cosine similarity
  -> CONFIDENCE GATE: if top score < config.retrieval.min_score -> SAFE RESPONSE ("no verified information")
  -> [llm.py] answer generation: ONLY from retrieved chunks, structured JSON output (Section 7)
  -> [verifier.py] code checks + optional LLM faithfulness check (Section 8)
        fail -> one regeneration with the issues listed -> fail again -> SAFE RESPONSE
  -> render: user's language, plain words, citations as "Source: <doc_title>, <unit> <number>"
  -> [voice.py] TTS (Sarvam) if the user is in voice mode
```

Modes (same session, switchable): `advice` (default), `draft`, `practice`.

**Intake behaviour.** Be useful with what is known. Ask at most **2** clarifying questions per turn, only for facts that change the answer (state or city, amount, dates, what proof exists, what they already tried). Never interrogate. The `case_file` accumulates across turns.

## 7. Python interface contract (FROZEN)

Tests, UI and everything else go through this and nothing else.

```python
# app/pipeline.py
@dataclass
class Session:
    id: str
    lang: str            # BCP-47, e.g. "hi-IN"
    mode: str            # "advice" | "draft" | "practice"
    case_file: dict      # accumulated facts
    history: list[dict]  # [{"role": "user"|"assistant", "text": str}]

@dataclass
class TurnResult:
    reply_text: str
    reply_lang: str
    category: str                  # consumer|wages|tenancy|out_of_scope|unclear
    action: str                    # "answer" | "clarify" | "refuse_unverified" | "escalate" | "draft" | "practice"
    citations: list[str]           # chunk ids actually shown to the user
    retrieved: list[dict]          # [{"id": str, "score": float}] top-k, in rank order
    needs_lawyer: bool
    escalation_reasons: list[str]
    verifier: dict                 # {"status": "pass"|"fixed"|"failed", "issues": [str]}
    draft_text: str | None
    trace: dict                    # raw router JSON, prompts used, timings, model names

def new_session(lang_hint: str | None = None) -> Session: ...
def handle_turn(session: Session, user_text: str,
                input_mode: str = "text", lang_hint: str | None = None) -> TurnResult: ...
```

Structured answer the model must produce (before rendering):

```json
{
  "blocks": [
    {"text": "...", "type": "legal|practical|question", "cites": ["CHUNK-ID", "..."]}
  ],
  "needs_lawyer": false,
  "gaps": ["what I could not verify"]
}
```

Rules: every `legal` block has at least one cite. Cites must come only from the retrieved set. `practical` blocks (for example "keep the receipt and screenshots") may have no cite but must not state law, numbers or deadlines.

## 8. Anti-hallucination design: layers

1. **Closed-book prohibition.** The prompt forbids using memory for law. Only the retrieved chunks count.
2. **Scoped retrieval.** Category and jurisdiction metadata filters, so a wages question cannot be answered from tenancy law.
3. **Confidence gate.** Weak retrieval means no answer, only an honest "no verified information on this" plus a lawyer or legal aid pointer. Threshold in config, calibrated from test results.
4. **Mandatory citations.** Every legal claim cites chunk ids from this turn's retrieval.
5. **Code verifier** (deterministic):
   - all cited ids exist in the retrieved set;
   - every `legal` block has cites;
   - cited chunks have `status: in_force` (or the block must say the law is not current);
   - regex scan of the final text for statute patterns (`Section|Sec\.|s\.|धारा \d+`, `Article \d+`, `Act, \d{4}`, `Rule \d+`), case patterns (` v. `, ` vs `, `AIR `, `SCC`, `(\d{4}) \d+ SCC`) and any pattern not present in the retrieved chunk text or metadata is flagged, because it was invented;
   - every number, amount, percentage or number of days in a `legal` block must appear in the cited chunk text or the user's own `case_file`.
6. **LLM faithfulness judge** (config toggle, default on): a second call checks "is each claim supported by its cited chunk text?" Different model role allowed (`judge`).
7. **Regenerate once, then fail safe.** One retry with the verifier's issues fed back. Second failure returns the SAFE RESPONSE.
8. **Case law rule.** The assistant may mention a judgment only if a `judgment` chunk is in the retrieved set. Otherwise it must say it cannot cite cases and suggest a lawyer.
9. **Staleness.** Every cited source shows its `fetched_on` date in the UI details panel. Repealed or superseded law is never presented as current.
10. **Human in the loop.** The project owner spot-checks the corpus (Antigravity's `verification_sheet.csv`) and confirms the status of every Act. Numbers and deadlines are checked 100%.

## 9. Escalation rules (always add "see a real lawyer / free legal aid")

Deterministic keyword and fact triggers (English and Hindi lists in `config.yaml`), OR'd with the LLM's flags:

- Arrest, police, FIR, summons, court notice already received, bail
- Violence, threats, harassment, lock-out or forced eviction in progress
- Family matters, property ownership, inheritance, minors involved
- Amount above `config.escalation.high_amount_inr`
- Limitation risk: the event is older than `config.escalation.limitation_warn_months` months
- State not covered, or the user is unsure of the state
- Any other situation the verifier or router marks `unclear`

Escalation never blocks basic help. The system still gives verified general information, then states clearly that a lawyer is needed and why. Free legal aid and helpline numbers come **only from verified `helpline` / `common` chunks**, never from model memory.

## 10. SAFE RESPONSE (the refusal path)

Content, in the user's language: (1) what the system understood, (2) plainly that it has no verified information to answer this part, (3) what the person can still do right now (gather documents, write down dates), (4) the verified legal-aid pointer (from corpus), (5) it never guesses. `action = "refuse_unverified"` or `"escalate"`.

## 11. Voice and language

- STT and TTS via **Sarvam AI** (read its current docs; do not guess endpoints or model names). Fallback: Gemini audio input for STT. If both fail, the UI tells the user to type.
- Languages enabled in `config.yaml`. Default: `en-IN`, `hi-IN`. Others (Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia) are enabled one by one only after a passing test run. Reply language always matches the user's language, and the UI language picker overrides detection.
- Voice transcripts are messy. The router must tolerate fillers, repeats and mixed Hindi-English ("Hinglish").
- TTS inputs are chunked to the provider's length limit.

## 12. Draft mode and practice mode

**Draft** (`drafts.py`): templates for (a) legal notice demanding deposit refund, (b) salary or dues demand notice, (c) consumer complaint: first the company grievance email, then the facts for a consumer commission complaint. Rules: facts come only from `case_file`; anything missing stays a visible `[● placeholder]`, and nothing is ever invented. Legal references in a draft appear only if they come from retrieved, in-force chunks. Every draft ends with: "Check every detail before sending. For high-value or complex matters, have a lawyer review it." Output: text with a copy button and a `.txt` or `.docx` download.

**Practice** (`practice.py`): the AI plays the opposing party (landlord, employer, company support) at an adjustable difficulty. It is clearly labelled a simulation, stays in character, and makes no legal claims of its own. When the user ends the session it gives coaching feedback, and any legal point in the feedback must be cited from the corpus with the same verifier. If it is not supported, the feedback is limited to communication tips.

## 13. Quality metrics (what we report in the solution doc)

Computed by Codex's `run_eval.py` on the test set:

- **Routing accuracy**: correct category or out_of_scope.
- **Citation validity**: share of cited ids that exist in the retrieved set. Target 100%.
- **Unsupported-claim rate**: legal blocks that fail the verifier or judge after the final response. Target 0 in final output.
- **Correct-refusal rate**: out-of-scope and unverifiable cases handled by refuse or escalate.
- **Escalation recall**: the flagged cases that should escalate, did.
- **Trap pass rate**: hallucination bait, repealed-law and injection cases.
- **Language match**: reply language equals user language.
- **Retrieval hit rate**: expected topic present in the top-k.
- Plus a **failure list**: honest, with case ids.

## 14. Scale and cost story (for the solution doc)

- New category = one new `data/corpus/<cat>.jsonl` + one entry in `config.yaml` + test cases. No code change.
- New state = new chunks with `jurisdiction: <state>` + status register entries + tests.
- At v1 size (a few hundred chunks) an in-memory cosine search is enough. At scale (tens of thousands) swap in a vector database behind `retrieval.py`.
- Keeping the law fresh: scheduled re-fetch of source URLs, diff against stored text, flag changed chunks as `unclear` until a human re-verifies. The status register is rechecked monthly.
- Cost per conversation turn is roughly 2 to 4 model calls (router, answer, optional judge, optional regeneration) plus STT or TTS for voice. Free tiers are enough for a demo, and a stronger model is a one-line config swap.
- Human legal reviewer samples a share of live conversations for quality. High-stakes categories get a lawyer review queue.

## 15. Rules for every agent

1. Read this whole document first. In a conflict, this document wins over the agent's own brief.
2. Do not ask the human questions mid-task. Make a sensible assumption, write it in `docs/ASSUMPTIONS.md`, and continue.
3. Never fabricate a source, URL, section number, case name or test result. If you could not do something, say so in your report.
4. Keep secrets out of the repo. Use `.env`.
5. Log **every** place an AI tool (including you) produced something wrong, with how it was caught, in `docs/ai_mistakes.md`: `date | agent | what went wrong | how caught | fix`. The assignment requires at least one real example.
6. Finish with a short written report (what is done, what is not, what the human must check).

## 16. Order of work

1. Human: puts this repo skeleton in place and starts all three agents.
2. Claude Code: skeleton, `llm.py`, `retrieval.py`, `pipeline.py` against `data/sample/` first. Antigravity: capability test, then corpus, category by category. Codex: test cases first.
3. When `data/corpus/*.jsonl` passes `validate_corpus.py`, Claude Code rebuilds the index on the real corpus.
4. Codex runs the full eval. Bugs go to `tests/BUGS.md`. Claude Code fixes. Re-run.
5. Human: spot-check the corpus, confirm the status of each Act, record 2 or 3 voice clips, then write the 2-page solution doc and the walkthrough video.
