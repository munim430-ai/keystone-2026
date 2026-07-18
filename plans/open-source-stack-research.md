# Keystone Open-Source Stack — GitHub Research & Recommendations

**Compiled:** 18 July 2026 | All stars/licenses/activity verified live on GitHub that day

## Context
Keystone Education (2–3 people, one part-time developer — Fahim) wants a full operational system: student tracking, B2B partner tracking, CRM, OCR, document audit (the zero-silent-error auditor discussed), and money management. Before building anything, the founder asked for a hard-researched list of genuinely beneficial free/open-source GitHub tools across every category. This plan compiles verified candidates (star counts, licenses, maintenance, deployability) and recommends a minimal stack — biased against deploying software the team can't maintain.

## Already verified (earlier session research, 2026-07-18 live GitHub data)
| Category | Repo | Stars | License | Verdict |
|---|---|---|---|---|
| System of record (Sheets replacement) | nocodb/nocodb | 64k | AGPL-3.0 | ✅ PRIMARY — Airtable-like, forms, attachments, Kanban, webhooks; 1 dev-day to deploy |
| CRM (cPanel fallback) | espocrm/espocrm | 3.1k | AGPL-3.0 | ✅ Fallback if only shared hosting |
| WhatsApp shared inbox | chatwoot/chatwoot | 34.5k | MIT core | Later, when volume outgrows the bot |
| WhatsApp API layer | evolution-foundation/evolution-api | 9k | Apache-2.0 | Later; upgrade path for wa_bot_marina.js |
| Existing bot libs | wwebjs/whatsapp-web.js (22k), WhiskeySockets/Baileys (10k) | | Apache/MIT | Keep short-term; ban risk noted |
| Intake forms | OpnForm/OpnForm | 3.5k | AGPL-3.0 | Optional; NocoDB forms may suffice |
| Guided doc interviews | jhpyle/docassemble | ~1k | MIT | ❌ Avoid — needs retained developer |
| Trendy CRM | twentyhq/twenty | 53k | AGPL dual | ❌ Avoid — fast-moving, needs dev support |
| Doc→skill converter | virgiliojr94/book-to-skill | — | — | ✅ Already installed & used |

## Verified — OCR, parsing, DMS, rules, e-sign (Agent A, live GitHub data 2026-07-18)

### OCR (the Bangla question)
| Repo | Stars | License | Bangla verdict |
|---|---|---|---|
| tesseract-ocr/tesseract | 75.4k | Apache-2.0 | ✅ deploy (it's inside Paperless anyway) — but Bangla output = "searchable hint," weak on juktakkhor/noisy scans |
| JaidedAI/EasyOCR | 29.8k | Apache-2.0 | ✅ **best practical Bangla**: BRAC Univ benchmark ~91% char / ~78% word accuracy on real Bengali docs, beats Tesseract on noise; CPU-ok; stale (last release 2024) — pin versions |
| PaddlePaddle/PaddleOCR | 85.7k | Apache-2.0 | ❌ Bengali only via new VL model (GPU); painful install |
| datalab-to/surya | 21.1k | OpenRail-M weights | ❌ best modern Bangla quality but 650M-param GPU model — too heavy for part-time dev |
| mindee/doctr | 6.2k | Apache-2.0 | ❌ no Bengali vocab |

### Parsing / field extraction
- **docling-project/docling** — 63.4k★, MIT, very active. ✅ Layout/tables from PDFs on CPU; pluggable OCR. Produces structured *text*, not named fields — date/amount/name extraction stays custom regex/rules.
- marker (GPL+restricted weights, GPU) ❌; unstructured (15.2k★, superseded by Docling for this use) ❌.
- **No open-source "extract fields from Bangladeshi bank statement/NID" model exists** — field extraction is custom code, period.

### Document management
- **paperless-ngx/paperless-ngx** — 43.2k★, GPL-3.0, very active. ✅ **THE pick**: Tesseract under the hood with confirmed Bengali (`PAPERLESS_OCR_LANGUAGE=ben+eng`), tags/custom-fields/REST API, Docker on a cheap VPS. One student = one correspondent; doc-type tags map to audit checklist.
- Mayan EDMS (overkill), Teedy (dormant, no Bengali) ❌.

### Validation / rules engines
- **Honest answer confirmed: YAML manifest + ~200 lines of Python beats every framework at this scale.** Great Expectations = wrong shape (tabular pipelines); json-rules-engine adds nothing.
- Only framework worth using: **python-jsonschema** (MIT) to validate the manifest files themselves so rule typos fail loudly.

### E-signature
- **docusealco/docuseal** — 18k★, AGPL-3.0, single Docker container w/ SQLite — easiest self-host in the whole report. ✅ Pick. (Documenso 14k★ = good second choice, heavier stack.)

## Verified — money, ERP, referrals, automation, portals (Agent B, live GitHub data 2026-07-18)

### Accounting / money
- **bigcapitalhq/bigcapital** — 3.8k★, AGPL-3.0, active. ✅ **Pick**: double-entry, A/R+A/P, P&L, multi-currency with BDT base (invoice universities in USD/KRW). QuickBooks-like UI a non-accountant can use; single Docker Compose. Milestones = invoices; university commissions = A/R; partner payouts = bills.
- Invoice Ninja (9.9k★, Elastic License — free self-host, invoicing-first + real client portal) = runner-up.
- ❌ **Akaunting**: confirmed trap — phones home for plan validation, essentials paywalled. ❌ Firefly III (personal finance, no A/R). ❌ Crater (abandoned 2022). ❌ ERPNext-for-accounting-only (too heavy unless adopted wholesale).

### Education-agency ERP
- **Honest verdict: nothing open-source models the AGENCY workflow** (lead → foreign-university application → visa → arrival). frappe/education (572★), Gibbon (618★), OpenEduCat (843★) all model running-a-school (attendance, grades, admission INTO your institution). ➡ Model the pipeline in NocoDB kanban / EspoCRM stages — that IS the state of the art without SaaS.

### B2B partner/referral tracking
- **Honest verdict: a NocoDB table, not new software.** dub (24k★) is online link-attribution, wrong shape for "Coaching Center X referred student Y, owes ৳20,000 after visa." Partners table + link to Students + rollup for commission owed, paired with Bigcapital bills.

### Automation glue
- **n8n-io/n8n** — 196.9k★, Sustainable Use License — ✅ **Pick**; the license caveat doesn't bite (self-hosting for internal business ops incl. commercial is explicitly free; only reselling n8n is barred). The "doc uploaded → checklist update → WhatsApp reminder" flow is a stock 3-node pattern. Activepieces (23.3k★, MIT core) = cleaner-license second choice.

### Family-facing portal
- **Honest verdict: none exists open-source.** Order of attack: (1) skip portal, push status via WhatsApp (n8n + Evolution API) — culturally right for BD; (2) NocoDB shared views (fragile >50 students); (3) Invoice Ninja's client portal if adopted; (4) tiny custom portal = v2 project only.

---

## FINAL RECOMMENDED STACK

### Adopt now (Phase 1 — audit system core, ~2-3 dev-days)
| Tool | Role |
|---|---|
| **Paperless-ngx** (`PAPERLESS_OCR_LANGUAGE=ben+eng`) | Per-student document vault; OCR search; tags = doc types; REST API feeds the auditor |
| **YAML manifests + ~200-line Python auditor + python-jsonschema** | The zero-silent-error audit engine (3-state: VERIFIED/FLAGGED/MISSING); manifests generated from the korea-student-visa-sop skill |
| **EasyOCR sidecar** (`['bn','en']`, CPU) | Better Bangla extraction where Tesseract fails (best benchmarked practical accuracy) |
| **NocoDB** | System of record: students, pipeline kanban, B2B partners table, audit-status columns |

### Adopt next (Phase 2 — operations, when Phase 1 sticks)
| Tool | Role |
|---|---|
| **Bigcapital** | Books: milestone invoices, commission A/R, partner payout bills, BDT base + USD/KRW |
| **n8n** | Glue: doc-uploaded → checklist → WhatsApp reminder; status pushes to families |
| **Docling** | Table extraction from bank statements/transcripts feeding property rules |
| **DocuSeal** | Service-agreement signing with families (single container) |

### Later / only if outgrown
Chatwoot + Evolution API (WhatsApp inbox at volume) · Invoice Ninja portal (if families need logins)

### Explicitly avoid (with reasons on file)
Akaunting (phone-home paywall) · Crater (dead) · Twenty CRM/docassemble (needs retained dev) · Surya/marker/PaddleOCR-VL (GPU) · Mayan EDMS (overkill) · any education ERP (wrong workflow shape) · all 0-star "visa CRM" repos

### Architecture in one line
OpnForm/NocoDB intake → Paperless-ngx vault (ben+eng OCR) → Python auditor (YAML manifests per country/university, EasyOCR/Docling extraction, 3-state report) → NocoDB status columns → n8n → WhatsApp reminders → human sign-off gate → Bigcapital records the money.

Everything runs CPU-only on one 4–8GB VPS. Total license cost: $0 (n8n fair-code is free for this use).

## Verification
- This plan's deliverable is the research document itself + (on approval) committing it to the repo as `plans/open-source-stack-research.md`.
- Each recommended repo was verified live (stars/license/last-push, 2026-07-18) by research agents; Bangla OCR claims traced to a real BRAC University benchmark and paperless-ngx docs.
- Practical verification after any adoption: deploy Paperless-ngx with `ben+eng`, feed it 3 real student documents (1 clean English, 1 noisy Bangla NID, 1 bank statement), confirm OCR searchability and API retrieval before building the auditor on top.
