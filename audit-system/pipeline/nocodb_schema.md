# NocoDB base schema — "Keystone Ops"

Create these four tables in NocoDB (Airtable-style). Column types in parentheses.
The audit sync (`nocodb_sync.py`) writes into the **Students** audit columns.

## Table: Students
| Column | Type | Notes |
|---|---|---|
| student_id | Single line text (primary) | e.g. `kuac-demo` — matches the students/ folder name |
| student_name | Single line text | as on passport |
| target_university | Single line text | from the master list |
| manifest | Single line text | e.g. `kdu-global-kuac` |
| stage | Single select | the `pipeline` stages from stages.yaml |
| referred_by | Link → Partners | which B2B partner referred them |
| **audit_verdict** | Single select | `READY` / `NOT READY` (written by nocodb_sync) |
| **audit_verified** | Number | count (written by sync) |
| **audit_flagged** | Number | count (written by sync) |
| **audit_missing** | Number | count (written by sync) |
| **audit_blockers** | Long text | the MISSING/FLAGGED item list (written by sync) |
| **audit_updated** | Date | last audit run (written by sync) |
| dhl_tracking | Single line text | |
| vin_number | Single line text | |
| notes | Long text | |

## Table: Documents  *(optional — the auditor already tracks per-doc state)*
| Column | Type |
|---|---|
| doc_id | Single line text (primary) |
| student | Link → Students |
| doc_type | Single select (passport, bank_statement, …) |
| state | Single select (VERIFIED / FLAGGED / MISSING) |
| received_date | Date |

## Table: Partners  (B2B referral tracking — replaces a separate CRM)
| Column | Type | Notes |
|---|---|---|
| partner_name | Single line text (primary) | IELTS/coaching center, or aggregator (KUAC, WeBring) |
| type | Single select | IELTS center / coaching / aggregator / settlement |
| contact | Single line text | |
| students | Link → Students | rollup: count |
| commission_per_student | Currency (BDT) | |
| commission_owed | Formula | count(students at fee_paid+) × commission_per_student |

## Table: Payments  (mirrors Bigcapital; see money_model.md)
| Column | Type |
|---|---|
| student | Link → Students |
| milestone | Single select (registration / application / offer / visa / final) |
| amount | Currency |
| currency | Single select (BDT / USD / KRW) |
| date | Date |
| swift_ref | Single line text |

## Getting an API token
NocoDB → account menu → **Tokens** → create. Use it as `xc-token` in `nocodb_sync.py`
and the n8n HTTP nodes. The base + table ids are in the URL / API snippet panel.
