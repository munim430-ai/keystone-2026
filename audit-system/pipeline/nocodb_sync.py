#!/usr/bin/env python3
"""
Sync an audit verdict into the NocoDB Students row.

Reads the JSON report that `audit.py --json` writes, distills it to the
audit_* columns defined in nocodb_schema.md, and PATCHes the student's record
(or prints the payload with --dry-run). This is what makes the audit visible in
the pipeline board and lets n8n react to a red verdict.

Usage:
    # produce the JSON first:
    python3 audit.py --manifest manifests/korea/kdu-global-kuac.yaml \
                     --student students/kuac-demo/ --report-dir out/ --json
    # then sync it:
    python3 pipeline/nocodb_sync.py --report out/DEMO_STUDENT..._kdu-global-kuac.json \
        --student-id kuac-demo --dry-run
    # live:
    python3 pipeline/nocodb_sync.py --report <json> --student-id kuac-demo \
        --base-url https://nocodb.your-vps --table-id <tbl> --token <xc-token>
"""
import argparse
import datetime as dt
import json
import sys
import urllib.request


def build_payload(report, student_id):
    c = report.get("counts", {})
    blockers = []
    for d in report.get("documents", []):
        if d["state"] in ("MISSING", "FLAGGED"):
            blockers.append(f"[{d['state']}] {d['name']}: {'; '.join(d.get('messages', []))}")
    for r in report.get("consistency", []):
        if r["state"] in ("MISSING", "FLAGGED"):
            blockers.append(f"[{r['state']}] {r['rule']}: {r['message']}")
    return {
        "student_id": student_id,
        "audit_verdict": "READY" if report.get("ready") else "NOT READY",
        "audit_verified": c.get("VERIFIED", 0),
        "audit_flagged": c.get("FLAGGED", 0),
        "audit_missing": c.get("MISSING", 0),
        "audit_blockers": "\n".join(blockers) if blockers else "(none — ready to submit)",
        "audit_updated": dt.date.today().isoformat(),
    }


def patch_nocodb(base_url, table_id, token, payload):
    # NocoDB v2 records API: PATCH /api/v2/tables/{tableId}/records
    url = f"{base_url.rstrip('/')}/api/v2/tables/{table_id}/records"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="PATCH",
                                 headers={"xc-token": token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode()


def main():
    ap = argparse.ArgumentParser(description="Sync an audit verdict into NocoDB")
    ap.add_argument("--report", required=True, help="the JSON from audit.py --json")
    ap.add_argument("--student-id", required=True)
    ap.add_argument("--base-url"); ap.add_argument("--table-id"); ap.add_argument("--token")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    report = json.load(open(args.report, encoding="utf-8"))
    payload = build_payload(report, args.student_id)

    if args.dry_run or not all([args.base_url, args.table_id, args.token]):
        print("DRY RUN — payload that would be sent to NocoDB:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        if not args.dry_run:
            print("\n(need --base-url, --table-id, --token to send live)", file=sys.stderr)
        return
    status, resp = patch_nocodb(args.base_url, args.table_id, args.token, payload)
    print(f"NocoDB responded {status}: {resp[:200]}")


if __name__ == "__main__":
    main()
