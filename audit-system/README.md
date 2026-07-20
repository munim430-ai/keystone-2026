# Keystone Document Audit System

Automated, **zero-silent-error** document auditing for student visa applications —
Bangladesh → Korea today, other countries by adding manifests.

## The core promise
No automated system can promise literal zero error (OCR misreads, stamps hide text,
seal authenticity can't be machine-verified). What this system guarantees instead is
**zero *silent* error**: it never says PASS on anything it couldn't mechanically verify.
Every required item lands in one of three states —

| | meaning |
|---|---|
| ✅ **VERIFIED** | present AND every machine check passed (evidence attached) |
| ⚠️ **FLAGGED** | present but needs a human (subjective check, or a fact not supplied) |
| ❌ **MISSING** | absent, or a definitive rule failure |

A file is **submit-ready only when Flagged = 0 and Missing = 0**. The machine
guarantees nothing is forgotten (the #1 human failure mode); a human resolves the
small flagged pile and records a sign-off. That combination is how you approach
zero real-world error.

## The end-to-end flow
```
one combined scan
      │  split.py  (page-map → separate named PDFs, the format KUAC demands)
      ▼
students/<name>/files/  +  metadata.yaml  (facts, from OCR + human confirm)
      │  audit.py  (manifest per university → 3-state report, exit 0/2)
      ▼
  ┌── READY ──▶ generate.py (draft affidavit/NOC/cover/SOP) ──▶ submit to KUAC
  │
  └── NOT READY ──▶ nocodb_sync.py writes the verdict + blockers to the pipeline
                    board ──▶ n8n alerts staff / reminds the family (WhatsApp)
```
The **AUDIT GATE** (`pipeline/stages.yaml`) is the rule: nothing is sent while the
verdict is red.

## Layout
```
audit-system/
  audit.py                     # the engine (3-state auditor + consistency rules)
  generate.py                  # Phase 2: draft affidavit / NOC / cover letter / SOP
  split.py                     # Phase 2: one combined scan → separate named PDFs
  manifests/
    schema.json                # JSON schema every manifest must pass (typos fail loudly)
    korea/
      _core-korea.yaml         # shared Korean document set (all others extend it)
      kdu-global-kuac.yaml  kdu-global-kuac-regional.yaml  KUAC-process-playbook.md
      kyungsung-*.yaml  sejong-*.yaml  gachon-masters.yaml  dongshin-masters.yaml  assist-masters.yaml
  templates/                   # document templates the generator fills
  students/
    _TEMPLATE/metadata.yaml    # copy per student; blanks become ⚠️ FLAGGED
    ariful-demo/  kuac-demo/   # fabricated fixtures (safe to keep in git)
  pipeline/                    # Phase 3
    stages.yaml                # the student lifecycle (Kanban stages + the AUDIT GATE)
    nocodb_schema.md           # NocoDB tables (Students / Documents / Partners / Payments)
    nocodb_sync.py             # audit JSON → NocoDB Students row (verdict + blockers)
    money_model.md             # Bigcapital chart of accounts + milestone→invoice ladder
  sidecar/easyocr_extract.py   # Bangla+English OCR sidecar (run on the VPS)
  deploy/                      # docker-compose stack + runbook + n8n workflows
```

## Generate derived documents (Phase 2)
```bash
python3 generate.py --student students/kuac-demo/ --manifest manifests/korea/kdu-global-kuac.yaml
# auto-drafts NOC, cover letter, SOP — and the Same-Name Affidavit ONLY when names diverge.
# Missing facts appear as visible [FILL: field] markers; nothing is invented.
```

## Split one combined scan (Phase 2)
```bash
python3 split.py --pdf raw_scan.pdf --map students/<name>/pagemap.yaml --out students/<name>/files/
# pagemap.yaml: document_id: "page-range"  (ids match the manifests, so output feeds the auditor)
```

## Sync a verdict to the pipeline board (Phase 3)
```bash
python3 audit.py --manifest ... --student ... --report-dir out/ --json
python3 pipeline/nocodb_sync.py --report out/<report>.json --student-id <id> --dry-run
# live: add --base-url --table-id --token  (see pipeline/nocodb_schema.md)
```

## Run an audit
```bash
python3 audit.py \
  --manifest manifests/korea/kyungsung-bachelor.yaml \
  --student  students/ariful-demo/ \
  --report-dir out/ --json
```
Exit code `0` = submit-ready, `2` = not ready — so it can gate a pre-submit hook.
Prints a Markdown report and (with `--report-dir`) writes `.md` + `.json`.

Requirements: `pip install pyyaml jsonschema` (the auditor itself is pure-Python;
OCR/extraction is the separate sidecar).

## Adding a new country
1. Write `manifests/<country>/_core-<country>.yaml` (shared docs) — it must pass `schema.json`.
2. Add per-university manifests that `extends:` the core and override docs by id.
3. Because the shared visa-document core barely differs between destinations, this
   is a data task, not a code change — the engine is country-agnostic.

## How manifests were built
The Korean manifests were generated from the `korea-student-visa-sop` skill
(`.claude/skills/korea-student-visa-sop/`), itself built from the 16-document
WeCare pack. Figures are 2025–26 agency data — **re-verify per intake before
quoting families**; the auditor flags processing chains and human-judgment items
rather than trusting them.
```
