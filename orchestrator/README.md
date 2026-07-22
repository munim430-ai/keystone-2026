# Keystone CEO Orchestrator 🧭

One thin dispatcher that wires the pieces this repo already has — the
`audit-system/` auditor, the manifests, the IELTS scraper, the bots — into a
single **draft-first, Bangla-first** pipeline. A messy student upload becomes a
folder, an audit verdict, a ranked university match, and a **warm Bangla
missing-document message waiting for your approval** — while the survival clock
stares back at you.

It coordinates ephemeral sub-agents (audit, matcher, instruct, scraper, content)
but **nothing here sends, posts, or spends.** The only outbound paths are
human-approved queues. Runs **$0, offline, with no API keys** by design.

> Respects `plans/60-day-war-plan.md` rule #5 ("no building until 2 students/mo"):
> this is glue around finished parts so your hours move from ops → selling, not a
> new product to maintain.

---

## Quick start ($0, no keys)

```bash
cd orchestrator
pip install -r requirements.txt        # PyYAML, Jinja2, openpyxl (+ fastapi if you serve)

make demo          # end-to-end on a fabricated messy student — see the whole machine
make board         # the pipeline + the survival banner
make drafts        # the Bangla approval queue (nothing is sent)
make test          # 14 tests
```

`make demo` walks intake → match → audit → Bangla draft on a half-complete student
and prints the pending draft. Nothing is sent, posted, or paid for.

## What it does (per student)

```
messy upload / WhatsApp
   │  intake  → audit-system/students/<slug>/ (meta.json, metadata.yaml, docs_in/, files/…)
   ▼
CEO loop  → spawns ephemeral sub-agents, chains the next step
   ├─ MatcherAgent   profile vs the 10 manifests + master list → ranked eligible unis (match.json)
   ├─ AuditAgent     runs the existing audit.py → 3-state verdict → audits/ + board
   ├─ InstructAgent  audit verdict → warm Bangla missing-doc DRAFT → approval queue
   ├─ ScraperAgent   859-center B2B list summary + public competitor snapshots
   └─ ContentAgent   competitor insight → DRAFT Bangla whistleblower post (anonymized)
   ▼
NocoDB board + Drafts queue  →  you approve  →  n8n → Evolution API sends
```

Your daily surface is the **board** and the **drafts queue** — about 15 minutes.

## Commands

```
python -m orchestrator.cli intake --name "Sania Akter" --phone 01711000000 --file scan.pdf
python -m orchestrator.cli run --student sania-akter     # match → audit → instruct
python -m orchestrator.cli board                         # pipeline + survival clock
python -m orchestrator.cli drafts [--status pending]     # approval queue
python -m orchestrator.cli approve --draft <id>          # flip to approved (n8n sends)
python -m orchestrator.cli scrape --mode b2b             # 859-center district coverage
python -m orchestrator.cli demo
uvicorn orchestrator.intake:app --port 8090              # webhook: POST /intake, GET /board /drafts
```

## Guardrails (enforced in `guardrails.py`, covered by tests)

1. **Draft-first** — no agent has a send/post/spend tool; the registry asserts it
   at import. `wa_draft.py` writes drafts and has no `send()`.
2. **PII firewall** — anything reaching the marketing/content agent is anonymized
   (name → initials, phone/passport/NID stripped); a leak raises.
3. **Brand honesty** — banned claims ("100%", "গ্যারান্টি", "98%", "1500 universities",
   "escrow") are blocked before any draft is queued.
4. **No AI visa/bank advice** — instruction scope is document-checklist status only;
   an LLM that strays falls back to the safe template.
5. **Survival clock** — every run prints enrolled-vs-kill-date from the reality plan.
6. **Open-source / zero-spend** — LLM endpoints are allow-listed (Groq free / Ollama /
   mock); no payment-capable tool exists. Default is the mock → truly $0.

## How it reuses what exists (no rebuild)

| Uses | From |
|------|------|
| 3-state auditor (imported, not shelled) | `audit-system/audit.py` |
| University requirements + eligibility gates | `audit-system/manifests/korea/*.yaml` |
| Visa-likelihood ranking | `data/Korea_Master_University_List.xlsx` |
| Student folder convention | `audit-system/students/<slug>/` |
| Board sync payload shape | `audit-system/pipeline/nocodb_sync.py` |
| B2B ammunition | `data/IELTS_Partners_Tier2.csv` (859 centers) |
| Downstream send + posting | n8n + Evolution API + Postiz (`marketing/`, `bots/`) |

## Wiring real services (optional, still free)

- **NocoDB board**: set `NOCODB_BASE_URL`, `NOCODB_TOKEN`, `NOCODB_STUDENTS_TABLE`
  (+ `NOCODB_DRAFTS_TABLE`). Until then the board writes a local mirror so the CLI works.
- **Better Bangla phrasing**: `GROQ_API_KEY` (free tier) or run Ollama locally.
  With neither, deterministic Bangla templates are used — always correct, always $0.
- **Actual WhatsApp send**: an n8n flow polls `status=approved` drafts and calls
  Evolution API. The orchestrator never sends directly.
```
