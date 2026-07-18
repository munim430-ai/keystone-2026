# KUAC / KDU Global — Process Playbook

Distilled from the real Skylentra↔KUAC WhatsApp thread + the KDU Global Required
Documents list. This is the human process around the auditor: the auditor checks
the *documents*; this playbook covers the *choreography* (what to send when, and
the traps that cost days of back-and-forth).

## Who / where
- **KUAC** = Korean Universities Admission Center — the admissions intermediary for KDU Global (Kyungdong University).
- **Originals go by DHL** to: KUAC, 2002-ho Jungdong Benesta, 252 Gilju-ro, Bucheon-si, Gyeonggi-do 14548, Republic of Korea · +82 10 7599 9627.
- **TB clinic (nominated):** PRAAVA HEALTH, Plot 9, Road 17, Block C, Banani, Dhaka-1213.

## The lifecycle (each step = a NocoDB pipeline stage)
1. **Final interview** — KUAC schedules a Zoom with the KDU professor; join ~10 min early, others may run first.
2. **Offer letter** — KUAC emails it. Student pays fees, then **send the payment receipt (SWIFT)**.
3. **Bank payment trap** — the student **must carry the "KDU Global – KUAC Confirmation Letter" to the bank**, or the bank may refuse to process the tuition payment.
4. **Documents to KUAC** — run **[AUDIT GATE]** first (`audit.py`), then send. Originals by DHL; scans by **email as SEPARATE files — never one combined PDF** (KUAC organizes them individually).
5. **KUAC review** — they check and list anything missing/wrong (this is the loop the auditor removes).
6. **Regional vs normal visa** — KUAC may select the student for the **regional visa**, which triggers a second DHL round + the **Regional Visa Pledge Statement**.
7. **DHL originals** — send the tracking number as soon as it ships.
8. **Final admission letter** — up to ~10 days after documents received.
9. **VIN issued** — KUAC applies for the VIN (visa issuance number) and emails the release.
10. **Embassy visa** — apply at the Korean Embassy Dhaka with the VIN + documents (see the MoFA page KUAC links); **send the application receipt**.
11. **Visa granted → fly.**

## The traps the auditor exists to prevent (all real, from the thread)
- ❌ **Bank statement "almost expired"** → auditor `max_age_days: 30` on `bank_statement_date`. Time the bank certificate LAST.
- ❌ **Father's translated NID typo (ID numbers didn't match)** → auditor `father_name_match` consistency rule; and any ID-number field mismatch should be entered and checked.
- ❌ **Name English spelling differs across documents** → auditor auto-requires the **Affidavit of Same Name Declaration** (KUAC's own hard rule; red text on their checklist).
- ❌ **TB report sent as a copy for a regional-visa student** → `kdu-global-kuac-regional` requires `tb_test_is_original: true`.
- ❌ **Documents sent as one combined PDF** → process rule: split into separate named files (Phase-2 splitter automates this).
- ❌ **Wrong-format death certificate** → KUAC sends a sample; match their template (situational, per student).

## Money notes (for Bigcapital later)
- Application fee: **USD 250 is non-refundable if the visa is denied** (stated in the KUAC invoice, red text).
- Tuition paid by SWIFT after the offer; keep both SWIFT message copies as the receipt.

## How to run the gate
```bash
cd audit-system
python3 audit.py --manifest manifests/korea/kdu-global-kuac.yaml --student students/<name>/
#   normal visa; use kdu-global-kuac-regional.yaml once KUAC selects regional
```
Exit 0 = send it. Exit 2 = fix the listed items first. Never email KUAC on a red verdict.
