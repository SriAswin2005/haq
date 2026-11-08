# Haq: an AI lawyer for everyday problems in India

<p class="by">Kantipudi Sri Aswin · Roll no. 230527 · BS (MTH), IIT Kanpur · aswinkantipudi2004@gmail.com · Kuku AI Generalist assignment, Problem 2 · November 2026</p>

## Problem and scope

Haq ("your right") lets an ordinary person describe a legal problem in their own words and language, by text or voice, and get back three things: what the law says, what they can expect from it, and what to do next. I chose Problem 2 because its central risk, an AI inventing law, can be measured and engineered against.

| What the user gets | Covers |
| --- | --- |
| **The law, explained with its section**, plus a case file and, for money disputes, a notice to send | 431 passages from about 45 Acts and rules: rent and deposits (UP, Karnataka, Maharashtra, Delhi, Tamil Nadu, central law elsewhere), salary and gratuity, consumer refunds, police, FIR, arrest and bail (BNS, BNSS and the old IPC/CrPC), domestic violence, marriage, divorce, maintenance, dowry, inheritance, RTI, traffic, cyber fraud, POSH, cheque bounce, the Constitution, limitation |
| **Where to go** | 40 official offices and helplines: RBI, IRDAI, EPFO, cyber crime 1930, Rail Madad, AirSewa, UIDAI, RTI, NCW and more |
| **A live, cited web answer** when the library lacks the law | Any Indian legal question: Google Search through Gemini, keeping only sentences backed by a page the user can open |
| **Refusal** | Help to commit or hide a crime. A lawyer note (with free legal aid, NALSA 15100) is added, not substituted, for arrests, large sums, minors and near deadlines; danger puts 112 first |

**Assumptions.** Users are individuals on a phone, often not English-first, and many prefer to speak. Haq gives legal information, not representation: no guaranteed outcomes and no court judgments. Free tiers only; law as of November 2026.

## How it works, and how it avoids invented law

Every legal point shown is tied to a source the user can open: a law passage retrieved for that turn, or a web page Google Search returned for it. With neither, Haq says so and gives only labelled general guidance, with no sections or numbers.

<svg viewBox="0 0 760 132" xmlns="http://www.w3.org/2000/svg" font-family="Inter,Arial,sans-serif" font-size="11" style="width:100%;margin:0.5mm 0 1.5mm"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#6b7286"/></marker></defs><g fill="none" stroke="#6b7286" stroke-width="1.1"><path d="M104 30H126" marker-end="url(#a)"/><path d="M234 30H256" marker-end="url(#a)"/><path d="M364 30H386" marker-end="url(#a)"/><path d="M494 30H516" marker-end="url(#a)"/><path d="M624 30H646" marker-end="url(#a)"/><path d="M180 50V82" marker-end="url(#a)"/><path d="M310 50V82" marker-end="url(#a)"/><path d="M570 50V82" marker-end="url(#a)"/></g><g stroke="#2e3a8c" stroke-width="1.1" fill="#eef0f8"><rect x="6" y="10" width="98" height="40" rx="6"/><rect x="126" y="10" width="108" height="40" rx="6"/><rect x="256" y="10" width="108" height="40" rx="6"/><rect x="386" y="10" width="108" height="40" rx="6"/><rect x="516" y="10" width="108" height="40" rx="6"/><rect x="646" y="10" width="108" height="40" rx="6" fill="#e3f0e8" stroke="#2c6a4e"/></g><g stroke="#b3261e" stroke-width="1" fill="#fbeeec"><rect x="116" y="84" width="128" height="40" rx="6"/><rect x="246" y="84" width="128" height="40" rx="6"/><rect x="496" y="84" width="148" height="40" rx="6"/></g><g fill="#1d2331" text-anchor="middle"><text x="55" y="27" font-weight="600">Message</text><text x="55" y="41" fill="#4b5368">text or voice</text><text x="180" y="27" font-weight="600">Understand</text><text x="180" y="41" fill="#4b5368">topic, facts, danger</text><text x="310" y="27" font-weight="600">Find the law</text><text x="310" y="41" fill="#4b5368">431 official passages</text><text x="440" y="27" font-weight="600">Write answer</text><text x="440" y="41" fill="#4b5368">each claim cites one</text><text x="570" y="27" font-weight="600">Check claims</text><text x="570" y="41" fill="#4b5368">code + judge model</text><text x="700" y="27" font-weight="600">Reply</text><text x="700" y="41" fill="#4b5368">+ sources, notice</text><text x="180" y="101">Small talk or crime:</text><text x="180" y="115" fill="#4b5368">chat, or refuse</text><text x="310" y="101">Law not in library:</text><text x="310" y="115" fill="#4b5368">live search, cited pages</text><text x="570" y="101">Claim fails: rewrite once,</text><text x="570" y="115" fill="#4b5368">then drop only that claim</text></g></svg>

- **A law library, not memory.** 431 passages copied word for word from official sources (India Code, state gazettes, ministry sites), each with URL, jurisdiction and in-force status; 46 are marked repealed so old law (IPC, CrPC, Payment of Wages Act) is named as replaced. Search mixes Gemini Embedding 2 vectors with keyword matching, filtered by state.
- **Understand first.** A router model separates small talk, legal questions and requests for harm; detects the language (including Romanised Telugu or Hindi), state, danger and missing facts; and writes an English search query.
- **Two-layer check on library answers.** Code checks that each cited section was retrieved and is in force, and that every number, date, website and email appears in the cited text or the user's words. A judge model from another family (Gemma) checks each claim and its conditions. A failed claim gets one rewrite and is then dropped, keeping the rest.
- **Live web search when the library lacks the law.** Gemini answers with Google Search grounding. Code keeps only sentences that Google's grounding marks as supported by a returned page, numbers them to those pages, and drops forums and social media. Under two supported sentences, nothing is shown from search.
- **Last resort.** A short answer labelled "not checked against a law text", from which code removes section numbers, case names, Act years, unknown numbers, websites and promises.
- **Language and voice.** Replies in English, Hindi and 10 more Indian languages; a translation is rejected if it loses a number, section or link, or comes back in the wrong script. Voice uses Google speech models, with Sarvam as a paid backup the user can choose in settings.

## How I know it's good, and where it fails

**Live test of the final design** (27 questions, 29 turns, real models; questions and every raw reply in `tests/live_questions.jsonl` and `outputs/live/`). The questions mix my own failed chats (Tamil, Telugu, Romanised Telugu, a request to help commit murder, a Dubai payment) with everyday ones (FIR refused, cheque bounce, Bengaluru deposit, helmet fine, daughters' inheritance, POSH, arrest, senior-citizen maintenance). I read every reply:

| Result (29 turns) | Count |
| --- | --- |
| Answered with the law, what you can get and what to do, every point cited | 15 |
| Correct but thin (e.g. right that the Domestic Violence Act protects only women, with little else) | 4 |
| Library had nothing useful and said so (Bengaluru deposit, same-sex marriage, Dubai payment) | 3 |
| Web search refused by Google (free-tier search quota), so labelled general information | 3 |
| Small talk answered normally; murder request refused in Telugu with a 112 line | 4 |

Replies came in the language asked (English, Hindi, Telugu, Tamil) in 29/29 turns, and no reply cited a section outside the library. Median time 27 s; the three web-search turns took 90–120 s before falling back, which is now cut to seconds.

**Earlier version, 55-case evaluation.** A separate agent (Codex) wrote 55 cases (messy Hindi, Telugu and Hinglish, other states, prompt injection, a fake Supreme Court case) and scored each reply with about 18 automatic checks (raw replies in `outputs/raw`): 42/55 passed, with 142/142 citations to a retrieved in-force section, 73/73 websites matching a source and 94.7% / 93.3% office precision / recall.

**Where it fails.** That version was safe but too cautious: it sent most questions outside three topics to "see a lawyer" with no law, which is what the redesign fixes. Live web search is built and tested offline, but this free API key's Google Search quota was refused in the live run, so it needs a key with search enabled; and a supported sentence is only as right as its page. About 200 passages with numbers still await a human check against the official page, there is no lawyer reviewing answers, and it has not been tested with real users.

## Scale and cost

- **Cost.** A library answer takes about 5 model calls and 2 embedding calls, roughly 20K input and 2K output tokens: about $0.011 (₹1) at Gemini Flash-Lite paid prices, or $1,100 per 100,000 answers. Web answers add one grounded search call. The free tier covers a few hundred answers a day.
- **Serving.** One CPU container (about 90 MB of memory, no GPU or database) on Azure Container Apps' free grant, scaling to zero when idle. The browser keeps the chat and sends the case state each turn, so scaling means more copies. Each model client paces itself to its rate limits and falls through to the next model on errors.
- **Swapping models is config only.** Each role (route, answer, search, judge, translate, speech) is a fallback chain in `config.yaml`; adapters for OpenAI-compatible APIs and Anthropic exist. Coverage grows through data: a new state or Act is passages plus one index rebuild.

## AI tools, and where they got it wrong

**Claude** designed the architecture and wrote a brief for each agent; **Claude Code** built the app; **Antigravity (Gemini)** collected the law passages and office directory from official sites; **Codex** wrote the tests and ran every evaluation, without touching the app. Inside Haq: Gemini Flash-Lite and Flash, Gemma, Gemini Embedding 2 and Google speech models, with Sarvam as a voice backup.

**A wrong website.** One answer sent the user to "airseva.gov.in"; the source says "airsewa.gov.in". The model had re-spelt a government site, which could lead someone to a fake one, and the judge model passed it. Codex's evaluation caught it, and the fix was code: every website and email must appear in a cited source. Anything a user might copy is now checked by code, never by another model.

**A wrong design.** To avoid inventing law, the AI-built first version refused too much: keyword rules sent anything mentioning police, family or harassment to a lawyer, and a Telugu question got an English helpline list. Testing it myself, I judged it useless to an ordinary person. The redesign keeps the source rule but widens what counts as a source: a larger library and live, cited web pages. `docs/ai_mistakes.md` logs about 15 more mistakes.

**Links.** Prototype: RENDER_LINK · Code, tests and raw outputs: GITHUB_LINK
