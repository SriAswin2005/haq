# Antigravity brief: build the everyday law library (round 5)

Paste this whole file into Antigravity.

## Why

Haq answers only what it can quote. Today the library has 169 passages, and almost all of them cover three topics. So for most real questions (an FIR, a spouse who beats you, an RTI request, a cheque that bounced, same-sex marriage, a challan) it has nothing to quote, and it falls back to "contact legal aid". This round gives it the bare Acts that ordinary people's questions actually need.

## What to collect

Verbatim text of the sections listed below, from official sources only:

- India Code (`indiacode.nic.in`)
- `legislative.gov.in`
- the Gazette (`egazette.gov.in`)
- state government law department sites, for state Acts

Use the current, amended text. Where a list below says "find the sections on X", find them yourself in the Act; don't guess numbers. Section numbers in this brief are pointers I believe are right: **check every one against the official text**, and log any that are wrong in `docs/antigravity_report.md`.

Aim for 400 to 700 passages. Completeness on the listed questions matters more than volume.

### Category `rights`: Constitution of India (`RGT-COI-A<n>`, unit `article`)

Articles 14, 15, 16, 17, 19, 21, 21A, 22, 23, 24, 25, 32, 39A, 226, 300A.

### Category `criminal`: criminal law and procedure

- **Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS).** In force from 1 July 2024; check the commencement.
  - FIR, including a zero FIR and refusal to register (around s.173)
  - arrest without warrant, and the arrested person's rights (grounds of arrest, informing a relative, meeting a lawyer, production before a magistrate within 24 hours, medical examination)
  - bail for bailable and non-bailable offences, and anticipatory bail
  - maintenance of wives, children and parents (around s.144)
  - complaints to a Magistrate
- **Bharatiya Nyaya Sanhita, 2023 (BNS).** Find the sections on:
  - cruelty by husband or relatives
  - dowry death
  - hurt and grievous hurt
  - criminal intimidation
  - cheating
  - theft
  - defamation
  - stalking
  - sexual harassment
  - wrongful restraint
  - insult to the modesty of a woman
  - attempt to murder
  - punishment for murder: the user's harmful-intent questions need the plain law, never steps
- **Bharatiya Sakshya Adhiniyam, 2023.** Only the sections on electronic records as evidence.
- **Indian Penal Code, 1860 and Code of Criminal Procedure, 1973.** Only the sections that correspond to the above, with `status: "repealed"` and a `status_note` naming the BNS/BNSS replacement, so Haq can recognise people who quote the old numbers.

### Category `family`

- **Hindu Marriage Act, 1955:** conditions for a valid marriage, registration, divorce grounds, divorce by mutual consent, maintenance pending the case, permanent alimony, custody.
- **Special Marriage Act, 1954:** conditions, notice of intended marriage, objections, divorce, and divorce by mutual consent. This Act answers inter-faith marriage questions.
- **Protection of Women from Domestic Violence Act, 2005:** definitions (including "aggrieved person" and "domestic relationship"), the meaning of domestic violence, the Protection Officer, the application to the Magistrate, the right to reside, protection, residence, monetary and custody orders.
- **Dowry Prohibition Act, 1961:** definition, penalty for giving or taking dowry, penalty for demanding dowry.
- **Maintenance and Welfare of Parents and Senior Citizens Act, 2007:** maintenance of parents and senior citizens, the application, tribunals, and transfer of property being void.
- **Prohibition of Child Marriage Act, 2006:** the definition of a child, child marriage being voidable, punishment.

### Category `civic`

- **Right to Information Act, 2005:** the definition of public authority, the right to information, the request for information (s.6), the disposal of a request and its time limits (s.7), exemptions (s.8), first and second appeal (s.19), and penalties (s.20).
- **Motor Vehicles Act, 1988:** driving licence required, the helmet requirement, offences and penalties for driving without a licence or insurance, drunk driving, and not wearing a helmet or seat belt, plus the power to seize documents and vehicles. Use the amended text as of 2019.
- **Information Technology Act, 2000:** compensation for damage to a computer (s.43), identity theft (s.66C), cheating by personation using a computer (s.66D), publishing obscene material (s.67), and intermediary liability (s.79).
- **Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013:** definitions, the Internal Committee, the Local Committee, the complaint and its time limit, inquiry, and interim relief.

### Category `money`

- **Negotiable Instruments Act, 1881:** dishonour of cheque (s.138), the presumption (s.139), cognizance and the notice period (s.142), and interim compensation (s.143A).
- **Indian Contract Act, 1872:** compensation for breach (s.73, s.74), the liability of a guarantor, money paid by mistake (s.72), and partnership-related sections if present.
- **Indian Partnership Act, 1932:** the mutual rights and duties of partners, sharing of profits and losses, and dissolution plus settlement of accounts. This answers "my partner won't pay his share".
- **Limitation Act, 1963:** the sections on the effect of the period expiring and on condonation of delay (s.3, s.5), plus the Schedule articles for suits to recover money lent, on contracts, and for rent.
- **Code of Civil Procedure, 1908:** summary suits (Order XXXVII), and the pecuniary jurisdiction rule (s.15).

### Category `wages`: additions

- **Payment of Gratuity Act, 1972:** payment of gratuity (s.4), the determination of the amount (s.7).
- **Code on Social Security, 2020:** the gratuity chapter, if the gratuity provisions are now in force there. Check the commencement and say which Act is current.
- **Sexual harassment at work:** already covered under `civic`.

### Category `tenancy`: other states

- **Karnataka Rent Act, 1999:** the deposit or advance limit, receipts for rent, eviction grounds, and the Rent Court or Rent Controller.
- **Maharashtra Rent Control Act, 1999:** the deposit or premium provisions, receipts, eviction grounds, and the Rent Controller.
- **Delhi Rent Control Act, 1958:** the same topics.
- **Tamil Nadu Regulation of Rights and Responsibilities of Landlords and Tenants Act, 2017:** the security deposit limit and refund, plus the Rent Authority. One passage already exists; complete the set.
- **Model Tenancy Act, 2021:** the security deposit limit only, with `status: "model_only"`, so Haq can say "the central model law suggests X, but your state's own law applies".
- **Transfer of Property Act, 1882:** s.105, s.106 and s.108, the rights and liabilities of lessor and lessee. These are the central fallback.

### Category `property`

- **Hindu Succession Act, 1956:** the general rules of succession for males and females, daughters' coparcenary rights (s.6), and the Class I heirs.
- **Indian Succession Act, 1925:** the sections on wills (who may make a will, execution of an unprivileged will).
- **Registration Act, 1908:** documents of which registration is compulsory.

### Category `common`: free legal help (extend)

- **Legal Services Authorities Act, 1987:** the criteria for free legal services (s.12) and Lok Adalat awards (s.21), if they're not already present.

## Format

Use the same contract as before (`00_ARCHITECTURE.md` section 5), with these changes:

- **Categories:**
  - new: `rights`, `criminal`, `family`, `civic`, `money`, `property`
  - existing: `consumer`, `wages`, `tenancy`, `common`
- **One file per category:** `data/corpus/<category>.jsonl`. Append to the existing files for `wages`, `tenancy` and `common`.
- **IDs:** `{CAT}-{ACTCODE}-{UNITLETTER}{NUMBER}`, where CAT is one of `RGT`, `CRM`, `FAM`, `CIV`, `MON`, `PRP`, `WAGE`, `TEN`, `COM`.
  - Articles use unit letter `A`, as in `RGT-COI-A21`.
  - Schedule articles of the Limitation Act use `L`, as in `MON-LA1963-L113`.
- **Jurisdiction:** `central`, or the state code: `KA`, `MH`, `DL`, `TN`, `UP`.
- **`text`:** must be VERBATIM. Split a long section into `-a`, `-b` parts at sub-section boundaries. Keep each part under about 2,500 characters.
- **`heading`:** the official marginal heading.
- **Any passage with a money limit, fine, time limit, age or deadline:** set `human_check_required: true`, and add a row to `data/verification_sheet.csv`.
- **`status`:** must be right.
  - IPC and CrPC: `repealed`.
  - BNS and BNSS: `in_force`, with `effective_from`.
  - If you cannot confirm a commencement, use `unclear` and say why in `status_note`.

## Before you finish

1. Update `data/validate_corpus.py` so it accepts the new categories, CAT codes and unit letters (`A`, `L`), and then run it until it passes.
2. Append a "Round 5: everyday law library" section to `data/MANIFEST.md` and `docs/antigravity_report.md` covering:
   - each Act and the source URL you used
   - how many passages you took from it
   - every section number from this brief that turned out to be wrong
   - anything you could not find
3. Do not edit anything under `app/`, and do not touch `data/index/`.
