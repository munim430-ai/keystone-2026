#!/usr/bin/env python3
"""
Seed the NocoDB `B2B_Partners` table from data/IELTS_Partners_Tier2.csv
(Strategy §6 — the 859-center B2B engine).

Adds the operational columns the raw scrape lacks:
  Priority   — HOME districts first (Narsingdi, Gazipur, Mymensingh, Tangail,
               Kishoreganj, Jamalpur, Sherpur), then the rest.
  Status     — new (default). Owner/Last_contact/Referrals filled in as you work it.

Two modes:
  --dry-run                      (default) print what WOULD be inserted + priority split
  --base-url .. --table-id .. --token ..   live: POST rows to NocoDB v2 API

Usage:
  python seed_b2b_from_csv.py --dry-run
  python seed_b2b_from_csv.py --base-url https://nocodb.your-vps \\
      --table-id m_xxxxxxxx --token <nocodb_api_token>
"""
import argparse
import csv
import json
import os
import sys
import urllib.request

CSV_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "IELTS_Partners_Tier2.csv")

# Work the home turf first — a referrer you can visit in person signs faster.
HOME_DISTRICTS = {
    "narsingdi": 1, "gazipur": 1,
    "mymensingh": 2, "tangail": 2, "kishoreganj": 2, "jamalpur": 2, "sherpur": 2,
}


def priority_for(district: str) -> int:
    return HOME_DISTRICTS.get((district or "").strip().lower(), 3)


def load_rows(csv_path):
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            district = r.get("Location (District)", "").strip()
            yield {
                "Center_Name": r.get("Center Name", "").strip(),
                "District": district,
                "WhatsApp_Mobile": r.get("WhatsApp/Mobile", "").strip(),
                "Source_URL": r.get("Source URL", "").strip(),
                "Priority": priority_for(district),
                "Status": "new",
                "Owner": "",
                "Last_contact": "",
                "Referrals": 0,
                "Commission_due_bdt": 0,
            }


def post_row(base_url, table_id, token, row):
    url = f"{base_url.rstrip('/')}/api/v2/tables/{table_id}/records"
    req = urllib.request.Request(
        url,
        data=json.dumps(row).encode("utf-8"),
        headers={"Content-Type": "application/json", "xc-token": token},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=CSV_DEFAULT)
    ap.add_argument("--base-url")
    ap.add_argument("--table-id")
    ap.add_argument("--token")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = list(load_rows(args.csv))
    split = {1: 0, 2: 0, 3: 0}
    for r in rows:
        split[r["Priority"]] += 1

    print(f"Loaded {len(rows)} centers from {os.path.normpath(args.csv)}")
    print(f"  Priority 1 (Narsingdi/Gazipur): {split[1]}")
    print(f"  Priority 2 (nearby districts):  {split[2]}")
    print(f"  Priority 3 (rest of Bangladesh):{split[3]}")

    live = args.base_url and args.table_id and args.token
    if args.dry_run or not live:
        print("\n[DRY RUN] first 3 records that would be inserted:")
        for r in rows[:3]:
            print("  " + json.dumps(r, ensure_ascii=False))
        if not live:
            print("\nProvide --base-url --table-id --token to write to NocoDB.")
        return 0

    ok = 0
    for i, r in enumerate(rows, 1):
        try:
            post_row(args.base_url, args.table_id, args.token, r)
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ! row {i} ({r['Center_Name']}): {e}", file=sys.stderr)
    print(f"\nInserted {ok}/{len(rows)} records into NocoDB.")
    return 0 if ok == len(rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
