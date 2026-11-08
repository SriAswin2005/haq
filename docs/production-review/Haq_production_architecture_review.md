# Haq Production Architecture Review

7 November 2026 | Product and engineering review | Kuku assignment Problem 2

## Decision and purpose

Haq needs a redesigned answer and evidence pipeline before it is suitable for a public service. Keep the useful interface, provider integrations, source records, and reproducible evaluation tooling. Replace the narrow routing contract, inconsistent verification states, and scattered language handling. Add source maintenance, session isolation, privacy controls, and operational limits as product requirements.

The goal is an application that helps an ordinary person understand a legal problem and take a sensible next step in their own language. A response that passes a citation check but leaves the question unanswered is a product failure. A fluent answer without reliable support is also a failure.

This report proposes the architecture and implementation sequence. The work completed in this review consists of removing five obsolete or empty files, inspecting the repository, and running isolated offline checks. Application code, configuration, legal content, and existing uncommitted work have not been changed.

## Main findings

- The supplied chat export contains 10 completed replies: seven escalations, one unverified fallback, and two answers. Eight replies did not reach the answer-writing model in that captured version.
- The current working tree is newer than the export. It already adds general guidance, one shared Google or Sarvam preference, and a migration separating interface language from reply language. These changes must not be mistaken for verified production improvements.
- The collection contains 169 passages, including 40 directory entries. It contains no judgment passages or textbook commentaries. All 169 records are marked agent-verified; 65 require human checking.
- A focused probe showed that an empty judge response is accepted. Another showed that unchanged English can be labelled a successful Telugu translation.
- Server traces contain user text despite the interface saying chats are saved only in the browser. Session lookup also lacks a separate ownership check.
- The latest stored evaluation reports 42 of 55 passes, but independent semantic accuracy is unavailable. The stored results do not validate the newer guidance changes.

## Proposed product standard

Answer the question directly when evidence supports an answer. Ask a material clarification when facts are missing. Explain precisely what remains uncertain. Recommend professional assistance according to the situation, without using that recommendation as a substitute for useful information. Handle immediate danger and requests to cause harm separately.

Do not impose the original prototype's three-topic ceiling on the production product. Expand coverage through maintained sources and measured quality, while showing honest boundaries for each jurisdiction, topic, and task.

<!-- PAGEBREAK -->

## Assignment requirements and product interpretation

Problem 2 asks for a conversational AI for ordinary people in India, accepting text or voice in a comfortable language and helping them act on legal problems. It suggests building a case, explaining options, preparing documents, and practising arguments. These are possible directions, not a requirement that every feature be built immediately. It permits one problem in depth or many in breadth. It requires honesty about uncertainty, appropriate lawyer referral, protection against invented law, and original test cases with raw outputs. [A1, pages 3 and 6]

The assignment's short build window explains the original restriction. It does not justify retaining a frustrating experience as the permanent product design. The user's current requirement is a complete public-facing application, so this proposal uses a production quality standard. The eventual assignment submission still requires its own concise PDF of at most two pages; this engineering report is a separate planning deliverable. [A1, pages 1 and 4]

| Requirement | Current implementation | Production direction |
| --- | --- | --- |
| Understand a messy story | Router extracts a mutable case file | Preserve facts with their originating message, confirmation state, and separate matter IDs |
| Explain options plainly | Three grounded topics plus new unchecked guidance | Evidence-based answers across a broader topic catalogue |
| Help the user act | Three English document templates and referral directory | Useful next steps, reviewed document workflows, and source-backed procedural guidance |
| Comfortable language | English and Hindi generation; other languages translated | One language policy covering every response path and spoken output |
| Text or voice | Browser recording, Google and Sarvam adapters | Independently chosen STT and TTS providers, transcript correction, predictable fallback |
| Avoid invented law | Pattern checks, model judge, regeneration and pruning | Complete claim evidence, applicability checks, explicit verification states, human review |
| Know when a lawyer is needed | Topic and keyword escalation | Risk and urgency assessed independently of topic coverage |
| Demonstrate quality | 55 cases, preserved raw runs, mock tests | Independent legal review, helpfulness evaluation, real audio and adversarial testing |

## What the user should receive

A basic question should receive a short explanation. A dispute should receive a useful account of the options and next step. A notice should be explainable through an upload workflow, with uncertain OCR fields confirmed before use. A draft should be editable, grounded in confirmed facts, and clear about missing details. Practice mode can follow once these core tasks work reliably; the existing practice module is only a stub.

The principal success measure is whether the person understands a useful next step supported by law.

<!-- PAGEBREAK -->

## Current system and review evidence

The main web path is browser input, FastAPI transport, a globally serialised turn, router, category-filtered vector retrieval, answer generation, verification and optional rewrite, translation, then optional speech synthesis. The newer guidance path can generate general information when normal coverage is unavailable. Browser localStorage holds chats, while server memory also holds sessions and the pipeline appends traces to disk. [C1-C7]

The review covered the application modules, prompts, templates, browser assets, configuration, deployment files, corpus structure, validation tooling, evaluation framework, test inventory, and operational documentation. Historical raw runs were treated as evidence rather than re-audited claim by claim. Dependency directories and Git internals were excluded from source review. No live provider quality benchmark or exhaustive legal audit of the corpus was performed.

| Evidence | Observed result | What it establishes |
| --- | --- | --- |
| Application unit suite | 48 tests passed | Existing deterministic behaviour remains testable |
| Evaluation-tool suites | 73 tests passed | Existing scoring and orchestration checks pass |
| Corpus validator | 169 passages passed schema checks | Required structure passes; legal truth is not established |
| Browser JavaScript | Three files passed syntax checks | Scripts parse; browser usability is not established |
| API test suite | Zero tests ran; setup failed | Installed test client requires missing httpx2 dependency |
| Focused diagnostic probes | Six observations recorded | Concrete verification, language, and session gaps |
| Stored real evaluation | 42 of 55 strict passes | Historical checks passed for a captured revision |
| Stored performance report | Median 10.968 s; p95 43.723 s | Historical response latency, not a current load test |

All review tests ran in an isolated repository copy with outbound requests blocked where model calls could occur. Existing raw outputs, local traces, feedback, and embedding files were preserved. API dependencies were not installed or altered because this task authorises cleanup and reporting, not implementation changes.

## Corpus coverage

The files contain 28 common passages, 29 consumer passages, 40 directory entries, 42 tenancy passages, and 30 wages passages. Their metadata describes 130 central records, 38 Uttar Pradesh records, and one Tamil Nadu record. Types are 115 statutes, seven rules, 36 portal procedures, and 11 helplines. There are no judgment records. Status labels are 164 in force and five repealed; these labels were counted, not independently confirmed in this review.

All 55 evaluation cases have expected_law_verified set to false. The latest summary explicitly reports independent semantic support as unavailable and final structured legal blocks as unobservable. These qualifications must remain attached to the historical pass rate. [E1-E3]

<!-- PAGEBREAK -->

## Answer quality findings

### Coverage is constrained before reasoning begins

The router, retrieval validator, prompt, and pipeline encode the original consumer, wages, and tenancy categories. The router reduces location to UP, other, or unknown. Configuration enables only UP for detailed state retrieval, even though a Tamil Nadu passage exists. Increasing the number of files alone would not make those sources usable across topics and states. [C1, C2]

Replace the hard category barrier with a broad topic taxonomy and explicit jurisdiction fields. Topic selection should guide research; it should not decide that a basic explanation must be refused.

### New general guidance does not solve legal grounding

The uncommitted guidance module asks a model to state general legal positions without the supporting law text. Its cleaner removes certain numbers, citations, domains, and promises, then asks another model to remove misleading lines. An unsupported statement can contain none of those patterns. A synthetic unsupported entitlement sentence survived the cleaner unchanged in an offline probe. The guidance judge also returns no removals when unavailable. [C3, P1]

Retain conversational small talk and appropriate safety responses. Route substantive legal claims through an evidence-backed path. A label saying general information is useful disclosure, but it is not proof that the content is correct. Do not market regex deletion as a legal verification mechanism.

### Verification can report success without complete checking

The verifier accepts an empty JSON object from the judge as an empty list of issues with status ok. It does not require exactly one verdict for every expected legal block. When the judge is unavailable, deterministic checks stand, which can still lead to a final pass status. A separate probe confirmed that a legal-looking sentence labelled practical bypasses semantic judging. [C4, P2-P4]

Require validated verdicts for all material claims, including claims mislabelled by the generator. Record supported, conditional, unsupported, conflicting, and unchecked states separately. If semantic checking fails, provide bounded practical help or an explicitly limited answer rather than presenting full verification success.

### Retrieval scores and document references are insufficient

The current gate uses a single vector similarity floor. It can reject a useful answer or accept a close but inapplicable provision. The ordinary retrieval mask excludes only repealed and superseded records, so unclear or not-yet-in-force records are not excluded at that stage; later checks carry the burden. Drafts attach the first two current statute or rule hits without an applicability decision. [C2, C5]

Use retrieval to find candidates, then check the facts, jurisdiction, effective dates, exceptions, and legal issue. Bind each material claim to exact supporting passages. Treat a failed search as a limitation of the search, not evidence that a legal right does not exist.

<!-- PAGEBREAK -->

## Language voice and conversation findings

### Language can be lost or falsely confirmed

The chat export shows correct Telugu and Tamil detection but English replies with no translation attempt. The newer browser code separates interface and reply language, but still does not send the STT-detected language with the turn request. Romanised Telugu therefore depends on another model inferring the language again. [C6, H1]

Translation checks currently compare token preservation and length. They do not establish that the output is actually in the target language or preserves legal meaning. A probe returning the original English text was accepted with reply_lang te-IN and translation status ok. Names and numbers surviving translation also cannot detect a reversed condition or missing negation. [C1, P5]

The main trace captures timing and model statistics before translation. Translation effort is therefore omitted from those trace totals, although the server's overall timer includes it. English templates can also be appended after translation, and draft_text remains a separate English artifact. [C1, C5]

### Provider selection is partly implemented

The working tree now has one Google or Sarvam setting used for both speech recognition and synthesis. The backend reorders providers but always keeps the other as fallback. There is no separate STT choice, TTS choice, or fallback-off option. This is useful work to retain, but it does not yet implement the proposed settings contract. [C6, C7]

Browser recordings use MediaRecorder formats. The Sarvam adapter only splits PCM WAV recordings, while non-WAV input is sent whole. The product can record up to two minutes, so long-recording behaviour needs real format and provider-limit tests. The Google transcription prompt emphasises Hindi and English. These are coverage risks, not proof that every regional recording fails.

### Case memory and retries need stronger boundaries

The pipeline can restore a previous case by matching its category. Two unrelated consumer disputes can therefore be confused. Out-of-scope topics live in side-topic strings rather than full independent matters. Use explicit matter IDs and facts with provenance; ask before reconnecting an ambiguous follow-up.

The streaming fallback may make a second request after a first request has already started, and retries have no idempotency key. Add a unique client turn ID so reconnection or retry returns the existing result rather than duplicating model calls and conversation entries. Preserve language and voice metadata across retries. [C1, C6]

<!-- PAGEBREAK -->

## Production security privacy and reliability findings

### Privacy claims do not match storage

The browser states that chats are saved only in that browser. However, handle_turn writes traces containing user_text and extracted facts to outputs/live_trace.jsonl. Feedback has an explicit share-text control, but that control does not govern pipeline tracing. Deleting a browser chat does not delete the server trace or in-memory session. [C1, C6, C8]

Before public release, define storage, retention, deletion, export, and provider-sharing behaviour. Default operational logs should contain timings, identifiers, and error classes rather than legal narratives. Store conversation content only according to the declared product policy. Redact sensitive information from research queries and diagnostic events.

### Sessions are not bound to an owner

The API accepts a client-provided session_id and restores arbitrary browser state. A diagnostic probe showed that two callers using the same identifier obtain the same session object without a separate ownership check. This demonstrates missing authorisation binding; it does not show that identifiers are easy to guess or that a real cross-user incident occurred. [C8, P6]

Use server-issued opaque session credentials, ownership checks, expiration, and server-side state validation. Anonymous use can remain available without accepting arbitrary session ownership claims. Treat supplied history and facts as user data, never as trusted instructions or verified evidence.

### Throughput and request limits need redesign

All answer turns in a process share one lock. Voice calls can concurrently mutate module-level provider statistics and quota state outside that lock. File-based quota accounting does not provide a distributed budget across workers. The STT endpoint calls synchronous network code inside an async handler. Request history and TTS text have no comparable tight model-level bounds, and forwarded IP headers are trusted directly. [C7, C8, C9]

Use request-scoped statistics, per-conversation ordering, bounded concurrency, global provider budgets, trusted-proxy configuration, and limits for text, history, files, duration, and tokens. Apply a total request deadline and cancellation, not just independent provider timeouts. Do not simply remove the global lock before isolating its shared state.

### Deployment and evidence need reproducible releases

Dependencies use broad minimum versions. The API suite failed to initialise against the installed dependency combination. Model names and fallback chains are configuration, not proof that models remain available or equivalent in quality. Build a pinned, tested release with a recorded model and corpus manifest. Do not embed on an interactive health request. Separate liveness from readiness. Restrict administrative stats and exclude assignment material, traces, and review artifacts from deployment packaging. [C8-C10]

<!-- PAGEBREAK -->

## Target architecture

Use a modular Python application with one API deployment and separate background workers for ingestion and maintenance. Keep FastAPI and the existing browser interface initially. A frontend framework migration is not a prerequisite for better answers. Avoid a large collection of autonomous agents or microservices until measured needs justify them.

<!-- ARCHITECTURE_DIAGRAM -->

### Interactive path

Resolve session ownership, language, and the user's task. Distinguish conversation, legal explanation, document work, immediate danger, and harmful assistance. Identify relevant facts and research questions. Retrieve evidence, assess applicability, compose the answer, validate every material claim and the final language, then display it and optionally synthesise speech.

If a missing fact changes the answer, ask at most one or two useful questions while offering supported information that does not depend on that fact. Research and verification must have bounded attempts. A source outage must become an honest service limitation rather than invented legal content.

### Background path

Acquire permitted documents from approved sources, preserve originals, extract text and structure, validate provenance and applicability metadata, review high-impact changes, and publish a versioned index. Change detection should create a review task. It should not silently overwrite law already used in previous answers.

### Storage and infrastructure

Use PostgreSQL for users or anonymous sessions, matters, facts, document versions, claims, citations, and review records. PostgreSQL full-text search plus pgvector can support an initial hybrid retrieval implementation; pgvector documents combining lexical and vector rankings. Add a dedicated search system only after relevance or scale measurements justify it. [W1]

Store original documents and generated artifacts in private object storage with access controls and retention rules. Use a worker queue and shared budget store as traffic requires. Keep private case material separate from the public legal collection and never add uploaded notices to the shared index by default.

Recommended module boundaries are api, conversations, policy, knowledge, retrieval, answers, verification, language, voice, documents, providers, and observability. Each boundary should have typed inputs and outputs and independent tests. Preserve the current pipeline entry point temporarily as an adapter while migrating.

<!-- PAGEBREAK -->

## Building a broader legal library

The Constitution belongs in the collection, alongside central and state Acts, subordinate legislation, judgments, and official procedural guidance. The Supreme Court describes this wider structure of Indian law. India Code provides a repository of legislation, and court resources provide judgments and reports. These are starting sources, not a guarantee that every document is current, complete, or ready for unrestricted bulk ingestion. [W4-W6]

Textbooks and commentaries should be added where access and usage rights permit ingestion. Record the edition, publication date, author, publisher, page, and licence. Use commentary to explain and connect legal concepts. Use the applicable primary sources to support statements of law. A commentary's interpretation must not be presented as if it were a statutory passage or court holding.

### Document lifecycle

1. Register the source, acquisition method, permitted use, document identity, and responsible reviewer.
2. Preserve the original bytes and a content hash. Extract headings, sections, tables, footnotes, and paragraph or page anchors. Flag low-quality OCR.
3. Record publication, commencement, amendment, and repeal information separately. Preserve historical versions and provisions with differing commencement dates.
4. Split on meaningful legal boundaries. Retrieve a small relevant unit with links to its parent section, definitions, exceptions, and referenced provisions.
5. Link judgments to court, date, citation, issues, relevant paragraphs, and known later treatment. Do not infer that an old judgment is still controlling merely because it is retrievable.
6. Run validation and expert review for high-impact content, then publish an immutable corpus release. Quarantine uncertain or malformed records rather than silently dropping them.
7. Monitor official updates, stale links, and review dates. Revalidate affected content and invalidate dependent caches before releasing a replacement index.

### Coverage plan

Build broad foundational coverage for constitutional rights, consumer issues, employment, housing, contracts, family matters, property, inheritance, criminal procedure, RTI, and common grievance processes. Provide source-backed general explanations across these areas. Add detailed state-specific procedures and document workflows only when supporting material and evaluation are ready.

Maintain a coverage matrix by topic, state, date, language, and task. A topic can support general explanation while a particular state procedure remains under review. A missing source should trigger targeted research or a precise limitation, rather than an automatic blanket referral.

The existing 169 records are a seed collection. Reuse them after provenance and status review; do not assume that agent verification or a schema pass establishes legal correctness. The existing validator even rejects human verification labels as an agent-authoring rule, so publication validation must be redesigned separately from authoring checks. [C2, C11]

<!-- PAGEBREAK -->

## Retrieval evidence and answer contracts

### Retrieve for the question and its conditions

Preserve the original query and a normalised search version. Identify the actual legal issue, location, relevant dates, and requested task. Split multi-issue questions when necessary; a request for bills and an assertion about RTI may require different evidence and a clarification about the organisation involved.

Combine lexical matching for exact names and provisions with semantic retrieval for everyday language. Fuse rankings and rerank candidates, then expand linked definitions and exceptions. Treat topic labels as relevance hints. Apply jurisdiction, date, source status, and private-document permissions as explicit constraints.

When local evidence is insufficient, run a bounded search of approved official sources. Remove personal details from search terms. Validate the retrieved document and its metadata before use. External pages and uploaded files are untrusted data: RAG does not itself prevent prompt injection. Restrict fetching, redirects, network destinations, file types, and tool permissions. [W1, W3]

### Preserve structured evidence through the whole response

| Record | Essential fields |
| --- | --- |
| SourceDocumentVersion | Identity, original hash, authority, licence, publication and effective dates, status evidence, review state |
| LegalUnit | Document version, heading, section or paragraph, page anchor, text, jurisdiction, relationships and exceptions |
| MatterFact | Matter ID, value, originating turn or document span, confidence, confirmation and conflict state |
| TurnPlan | Task, issues, country and state, relevant date, language, missing facts, risk and research budget |
| EvidenceBundle | Retrieved units, relevance, applicable conditions, conflicts, coverage gaps, corpus version |
| AnswerClaim | Claim text, supporting spans, applicability assessment, claim type and verification state |
| Response | Final blocks, citations, language, professional-help rationale, next actions, draft and voice metadata |

The public response should remain simple. Detailed evidence and model diagnostics belong in source details and internal operations, not in every paragraph of the answer.

### Verification and graceful failure

Validate citations, exact quoted spans, numbers with their meaning, URLs, and applicability. The semantic reviewer must inspect all material legal assertions and return a complete validated verdict set. Missing or malformed verdicts are failures of checking, not proof of support.

Allow at most a bounded repair pass, then keep independently supported content. Do not remove an exception while retaining the rule it qualifies. If the remaining content no longer answers the question, state the limitation and offer a useful next step. An absent search result must never become a confident claim that a law or remedy does not exist.

<!-- PAGEBREAK -->

## Language voice and document experience

### One language decision per turn

Resolve language in this order: an explicit instruction in the current message, an explicit saved reply preference, detected speech language, detected written language, and finally the established conversation language. Keep interface language separate. A language instruction must be recognised as a user preference without allowing it to override evidence or safety rules.

Pass the original text, transcript language, confidence, and user preference through the API. Recognise code-switching and Romanised regional languages. Ask a short clarification if confidence is low. Do not force English merely because the transcript uses Latin letters.

Generate the user-visible answer in the selected language from a structured evidence plan. English sources and internal retrieval queries can remain English. If an intermediate translation is used, validate language, legal meaning, negation, conditions, figures, and named entities after translation. Protect citations and identifiers as structured fields rather than depending only on token sets.

All routes must follow the same contract: answers, clarifications, professional-help messages, safety responses, errors, and drafts. A failed language conversion should produce a short localised status and retry option; English can be an explicit fallback choice. Record the actual rendered language, and include all conversion calls in latency and cost metrics.

### Voice settings and behaviour

| Setting | Proposed choices |
| --- | --- |
| Speech recognition | Google or Sarvam |
| Spoken responses | Google or Sarvam |
| Automatic provider fallback | Enabled or disabled |
| Reply language | Match my language or an explicit language |
| Interface language | Independently selected |

Validate provider availability and language support from a capability registry. Honour the selected provider or disclose the actual fallback. Do not silently incur a paid fallback contrary to the user's setting. Normalise recordings into an accepted format, enforce duration and size limits, and chunk with continuity where required.

Let users correct the transcript before submitting, especially names, amounts, dates, and ambiguous threats. Read validated response content aloud; when only a summary is spoken, label it and preserve qualifications and safety-relevant details. Provide stop, replay, and retry controls. The text answer must remain useful if audio fails.

### Documents that help users act

Introduce private notice upload and OCR with visible extracted text and uncertain-field confirmation. Separate the user's document assertions from authoritative legal sources. Use reviewed templates and confirmed facts for drafts, with applicability checks for legal references. Export the requested language, show unfilled fields, and allow editing. Never invent missing facts or automatically send, file, or serve a document. Practice mode should simulate opposing arguments without inventing precedents or promising outcomes.

<!-- PAGEBREAK -->

## Product behaviour safety and operational design

### Distinct response policies

| Situation | Required behaviour |
| --- | --- |
| Harmless ordinary conversation | Brief natural response without legal-aid escalation |
| General legal question | Direct source-backed explanation; clarify material ambiguity |
| Personal legal dispute | Explain supported options and useful next steps; ask only necessary questions |
| Missing or conflicting evidence | Identify the exact uncertainty and preserve supported help |
| Complex or time-sensitive matter | Explain what can be established and why professional help matters |
| Immediate danger | Prioritise appropriate safety support in the user's language |
| Request to cause harm or evade accountability | Refuse harmful assistance and offer de-escalation or lawful alternatives |
| Non-Indian jurisdiction | Clarify jurisdiction; do not automatically reuse Indian procedures or referrals |

Criminal law, family law, and a user's age are context, not universal reasons to suppress explanation. Safety classification should precede expensive research when necessary, but lawful rights information should remain available. Contact numbers and referral routes need maintained, jurisdiction-specific source records.

### Privacy and access

Offer anonymous use with a secure server-issued session token. Bind each matter and artifact to an owner, and check ownership on every operation. Use database access controls as defence in depth; PostgreSQL row security can restrict records, but owner and privileged-role bypasses must be considered in configuration and tests. [W2]

Make retention and deletion observable. Deleting a matter should cover conversation records, derived documents, cached audio, and retained diagnostic content according to the published retention policy. Use consent-based diagnostic sharing, restricted staff access, encryption, and audit records. Legal-compliance review of the product's actual data flows remains a release workstream; this report does not assert regulatory compliance.

### Reliability and cost

Use request-scoped telemetry and a bounded worker pool. Serialise only turns for the same matter where necessary. Share provider budgets across workers, enforce per-user and deployment limits, and use circuit breakers for unhealthy providers. Process audio and source ingestion away from the interactive event loop.

Define a total time budget for each turn. Return progress immediately and stream only content that has passed the required checks. Support cancellation, idempotent retries, and reconnecting to an existing job. Cache public source retrieval by corpus version and query; avoid cross-user caching of personal answers.

Record cost as model input and output tokens, speech duration or billed text units, retrieval, and infrastructure. Pick models through measured accuracy, latency, language, and cost tests. A free tier can support development, but production availability should not depend on repeatedly exhausting it or switching to untested models.

<!-- PAGEBREAK -->

## Migration and module decisions

The proposed implementation is an incremental replacement of the core, with explicit migration boundaries. It is not authorised as part of this cleanup task.

| Existing area | Decision | Reason |
| --- | --- | --- |
| FastAPI and browser shell | Retain and harden | Useful transport, progress, mobile layout and source presentation |
| pipeline.py and router.py | Replace behind a compatibility adapter | Routing, state, policy, formatting and research are tightly coupled |
| guidance.py | Split conversational support from legal reasoning | Unchecked substantive law must not bypass evidence requirements |
| retrieval.py | Replace search and publication layer | Need broader taxonomy, hybrid search, linked context and date filtering |
| verifier.py and prompts | Redesign contracts and failure states | Incomplete verdicts and unchecked claims can appear successful |
| llm.py | Retain adapters; refactor execution state | Provider interchangeability is useful; globals and quotas limit concurrency |
| voice.py | Retain adapters; extend request contract | Separate STT/TTS preference, format handling and fallback control |
| drafts.py and templates | Retain reviewed templates; add applicability and localisation | Template fields are useful but citations and language need stronger handling |
| guards.py | Retain narrow utilities with tests | Arithmetic and normalisation help; keyword policy should not decide answerability |
| config.yaml | Replace implicit mutable settings with validated configuration | Need versioned capabilities, policy and model releases |
| app/ui.py and requirements-ui.txt | Keep during migration; retire after usage is confirmed | Legacy Streamlit entry point is still documented and executable |
| practice.py | Keep as an explicit unsupported feature until implemented | A stub must not be advertised as a working capability |
| data and evaluation archives | Preserve and revalidate | Provenance, raw failures and reproducibility have continuing value |
| Existing tests | Preserve regression evidence; revise future expectations transparently | Some tests encode the old refusal policy rather than desired usefulness |

### Implementation sequence

Phase 1 establishes trustworthy operation: fix verification state reporting, language detection checks, trace privacy, session ownership, dependency reproducibility, request bounds, and observability. Capture a new baseline for the current working tree before changing behaviour.

Phase 2 introduces the broader source registry, legal document versions, linked units, hybrid retrieval, and the answer/evidence contract. Pilot multiple substantive topics and jurisdictions; professional review decides whether the coverage is useful and accurate.

Phase 3 completes multilingual generation, independent voice settings, real audio testing, matter memory, notice explanation, and reviewed draft workflows. Validate end-to-end on ordinary user tasks, not only scripted demonstrations.

Phase 4 runs controlled release, load tests, legal review, usability sessions, update monitoring, rollback drills, and quality monitoring. Roll back the relevant model, policy, or corpus release when a regression appears. Keep the old engine available only as a temporary technical rollback path, not as evidence of adequate public quality.

<!-- PAGEBREAK -->

## Evaluation and release criteria

Retain the 55-case set as a historical regression suite. Build a separate production evaluation with independently reviewed expectations and hidden holdout cases. Do not alter old raw results or report a larger denominator as if it were the same benchmark. The supplied chat export should become an acceptance set, with paraphrases and new cases that prevent memorising its wording.

Evaluate answer usefulness and legal support together. Reviewers should judge whether the answer addresses the actual question, avoids unsupported assumptions, explains relevant conditions, and provides a usable next step. Citation membership, model confidence, and a judge's agreement are supporting signals, not substitutes for this assessment.

### Proposed release targets

These are initial acceptance targets to validate and refine, not current performance claims or guarantees.

| Dimension | Initial release criterion |
| --- | --- |
| Critical safety and privacy | No observed severe unsafe assistance, cross-user disclosure, or undeclared content retention in the dedicated release suite |
| Material legal claims | At least 98 percent judged supported and applicable in a predeclared expert-reviewed sample; report denominator and uncertainty |
| Useful answers | At least 90 percent of answerable cases rated useful; at most 5 percent unnecessary blanket refusals |
| Language | At least 98 percent correct reply language in each released language cohort, with separate semantic review |
| Provider selection | All preference and fallback contract scenarios pass for STT and TTS |
| Retrieval | Report relevant evidence recall at k, jurisdiction errors, stale-source errors, and coverage gaps by cohort |
| Experience | User progress within one second; target p95 text response within 20 seconds at the declared supported load |
| Degraded operation | Bounded timeouts, clear source or provider failure, idempotent retry, and no silent verification success |

Measure results separately by legal topic, state, language, risk, and task. Set sample sizes and reviewer agreement rules before testing. Aggregate success must not hide failure in Telugu, a particular state, or a sensitive type of question. Finite tests cannot establish zero real-world risk; continue review after release.

### Required test families

Include basic rights questions, multi-issue disputes, wrong premises, unfamiliar legal terms, ambiguous relationships, conflicting dates and amounts, multiple matters, and follow-ups. Include unsupported legal claims without numbers, missing or malformed judge verdicts, incorrect language labelled successful, changed negation in translation, stale law, and missing exceptions.

Use recorded audio in real browser formats with accents, code-switching, noise, names, amounts, and dates. Test both providers, fallback-off behaviour, quota failures, and audio cancellation. Add browser-level checks for transcript correction, keyboard navigation, mobile layout, source links, chat deletion, and downloads.

Test direct and document-borne prompt injection, unauthorised session reuse, forged state, oversized requests, duplicate streaming retries, disconnected clients, concurrent voice/text traffic, worker restart, and unavailable sources. A release should have raw outputs, source versions, model identifiers, review decisions, and a reproducible run manifest.

<!-- PAGEBREAK -->

## Cleanup completed and retained evidence

Only five files were removed. The three round instructions were superseded one-time prompts, not executable dependencies. References to them in historical reports remain historical text. Two editing remnants were empty. Total removed file content was 14,839 bytes.

| Removed file | Bytes | Reason |
| --- | --- | --- |
| NEXT_ROUND.md | 4682 | Superseded iteration instructions |
| NEXT_ROUND_3.md | 4844 | Superseded iteration instructions |
| NEXT_ROUND_4.md | 5313 | Superseded iteration instructions |
| app/tests/test_referrals.py.tmp | 0 | Empty editing remnant |
| app/tests/test_guidance.py.add | 0 | Empty editing remnant |

The original architecture and build briefs were retained because current documentation and validation tooling refer to them. They describe the existing implementation; this report proposes its replacement. The original assignment PDF and the solution-document work were preserved. Nothing was committed, published, or deployed.

Old-looking evaluation files were deliberately retained after checking dependencies. full55_reports.py and policy_v2_reports.py import helpers from round3_reports.py. Current referral tests import round4_reports.py. test_policy_v2.py and revise_round4_expectations.py use add_round4_cases.py. Removing these by filename would break current tests or reproduction of old results.

Raw evaluation archives, expectation revisions, manifests, source verification sheets, and failure reports were preserved. The assignment requires test cases and raw outputs, and the production redesign needs trustworthy before-and-after evidence. Tests should be consolidated later through an explicit migration, not removed to make the repository appear cleaner.

## Code evidence index

| ID | Location | Review focus |
| --- | --- | --- |
| C1 | app/pipeline.py:69, 310, 396, 406, 476 | Translation, guidance, tracing, orchestration and state |
| C2 | app/router.py; app/retrieval.py:128; config.yaml | Topic limits, location handling and retrieval gate |
| C3 | app/guidance.py:67, 95, 108; guidance prompts | General information cleaning and judging |
| C4 | app/verifier.py:119, 172, 199 | Claim types, judge completeness and unavailable checks |
| C5 | app/drafts.py:74; app/templates | Template content, legal basis and language |
| C6 | app/web/app.js; index.html; i18n.js; sw.js | Voice metadata, settings, privacy, retries and display |
| C7 | app/voice.py:203, 353, 376 | Provider state, recording format and fallback |
| C8 | app/server.py:114, 133, 174, 284 | Session ownership, limits, concurrency and transport |
| C9 | app/llm.py:111, 412 | Shared quota state, provider calls and telemetry |
| C10 | requirements files; Dockerfile; render.yaml | Dependency and deployment reproducibility |
| C11 | data/validate_corpus.py; data metadata files | Publication checks and provenance review |

<!-- PAGEBREAK -->

## Evidence and references

### Local evidence

A1. Kuku AI Generalist Assignment PDF supplied in the repository, pages 1, 3, 4, 5 and 6. Problem 2 and submission requirements were reviewed. The assignment was not modified or republished.

H1. User-supplied haq-chats (3).json in Downloads. Ten completed replies were analysed in this conversation. Its traces describe the captured deployment, not necessarily the current uncommitted working tree.

E1. outputs/summary.md and outputs/perf.md. Latest published report identifies real-20261106T172240.218881Z; 42 of 55 strict passes, 59 turns, and semantic support unavailable. These are historical results.

E2. tests/cases.jsonl, tests/checks.py, tests/reporting.py, tests/README.md, and the test inventory. Fifty-five case definitions have no human-confirmed law flag.

E3. data/corpus/*.jsonl, data/MANIFEST.md, data/STATUS_REGISTER.csv, data/verification_sheet.csv, and data/FAILURES.md. Counts and schema validation were checked; the review does not certify every legal assertion in these files.

P1. Synthetic unsupported plain-language entitlement survived guidance.clean unchanged. P2. Empty judge JSON produced no issues and status ok. P3. Simulated judge outage produced no verification issues with an unavailable note. P4. A synthetic legal assertion labelled practical bypassed semantic judging. P5. Unchanged English text was accepted as a Telugu translation. P6. Reusing a session identifier returned the same session object without an ownership check. These were isolated diagnostic probes, not attacks on a deployed service.

The accompanying review_evidence.json records file fingerprints, cleanup, checks and probe outcomes. The separate cleanup manifest identifies removed files. Temporary test copies and render intermediates are not application deliverables.

### External technical and source references

W1. pgvector official documentation, Hybrid Search. Supports combining PostgreSQL full-text search and vector retrieval, with rank fusion or reranking. https://github.com/pgvector/pgvector#hybrid-search

W2. PostgreSQL documentation, Row Security Policies. Describes record-level policies, default-deny behaviour when enabled without policies, and privileged-role exceptions. https://www.postgresql.org/docs/current/ddl-rowsecurity.html

W3. OWASP Gen AI Security Project, LLM01 Prompt Injection. Describes direct and indirect injection, including untrusted retrieved material; RAG does not eliminate this risk. https://genai.owasp.org/llmrisk/llm01-prompt-injection/

W4. Supreme Court of India, Constitution and Sources of Law. Explains the constitutional framework and other sources of Indian law. https://www.sci.gov.in/constitution/

W5. Government of India, description of India Code's legislative repository and modernisation. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2299217&lang=1&reg=3

W6. Supreme Court of India official portal, judgments and Supreme Court Reports access. https://www.sci.gov.in/

External sources were consulted during this review. Provider pricing, model availability, legal commencement dates, and state procedures must be checked for the eventual release; configured names and existing corpus labels are not treated here as current guarantees.
