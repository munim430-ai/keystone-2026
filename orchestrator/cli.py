"""Keystone CEO Orchestrator — CLI.

    python -m orchestrator.cli intake --name "Sania Akter" --phone 01711000000 [--file a.pdf ...]
    python -m orchestrator.cli run --student sania-akter        # match→audit→instruct
    python -m orchestrator.cli board                            # pipeline + survival banner
    python -m orchestrator.cli drafts [--status pending]        # approval queue
    python -m orchestrator.cli approve --draft <id>
    python -m orchestrator.cli scrape [--mode b2b]
    python -m orchestrator.cli demo                             # end-to-end, $0, no keys
"""
from __future__ import annotations

import argparse
import json
import sys

from . import ceo
from .config import CFG
from .models import Job
from .tools import db, fs, wa_draft


def _p(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def cmd_intake(a) -> int:
    slug = fs.slugify(a.name)
    meta = {"name": a.name, "phone": a.phone, "source": a.source, "stage": "intake"}
    fs.create_student(slug, meta)
    for path in a.file or []:
        import pathlib
        p = pathlib.Path(path)
        if p.exists():
            fs.save_upload(slug, p.name, p.read_bytes())
    db.upsert_student(slug, stage="intake", name=a.name, phone=a.phone)
    print(f"created student '{slug}'. Run:  python -m orchestrator.cli run --student {slug}")
    return 0


def cmd_run(a) -> int:
    if not fs.exists(a.student):
        print(f"no such student '{a.student}'", file=sys.stderr); return 1
    log = ceo.process_new_student(a.student)
    for l in log:
        print(f"  [{l['kind']}] {l.get('summary') or l.get('error') or l.get('data','ok')}")
    print(f"\nboard + drafts updated. Survival: {ceo.CEO().survival()['banner']}")
    return 0


def cmd_board(a) -> int:
    surv = ceo.CEO().survival()
    print(f"=== SURVIVAL: {surv['banner']}\n    rule: {surv['rule']}\n")
    rows = db.board()
    if not rows:
        print("(no students yet)"); return 0
    for s in rows:
        print(f"  {s.get('student_id',''):24s} {s.get('stage',''):14s} "
              f"{s.get('audit_verdict','') or ''} "
              f"{('❌'+str(s.get('audit_missing'))) if s.get('audit_missing') else ''} "
              f"→ {s.get('match_top','') or ''}")
    return 0


def cmd_drafts(a) -> int:
    rows = db.drafts(a.status if a.status != "all" else None)
    if not rows:
        print(f"(no {a.status} drafts)"); return 0
    for d in rows:
        print(f"--- draft {d.get('id')} [{d.get('status')}] {d.get('type')} "
              f"student={d.get('student') or '—'}")
        print(d.get("body_bn", "")[:400])
        print()
    print(f"{len(rows)} draft(s). Approve with:  python -m orchestrator.cli approve --draft <id>")
    return 0


def cmd_approve(a) -> int:
    wa_draft.approve(a.draft)
    print(f"draft {a.draft} → approved. (n8n/Evolution API performs the actual send.)")
    return 0


def cmd_scrape(a) -> int:
    _p(ceo.run_job(Job("scrape", "", {"mode": a.mode})))
    return 0


def cmd_demo(a) -> int:
    from .demo import run_demo
    return run_demo()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="orchestrator", description="Keystone CEO Orchestrator")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("intake"); pi.add_argument("--name", required=True)
    pi.add_argument("--phone", default=""); pi.add_argument("--source", default="whatsapp")
    pi.add_argument("--file", action="append")

    pr = sub.add_parser("run"); pr.add_argument("--student", required=True)
    sub.add_parser("board")
    pd = sub.add_parser("drafts"); pd.add_argument("--status", default="pending")
    pa = sub.add_parser("approve"); pa.add_argument("--draft", required=True)
    ps = sub.add_parser("scrape"); ps.add_argument("--mode", default="b2b")
    sub.add_parser("demo")
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return {"intake": cmd_intake, "run": cmd_run, "board": cmd_board, "drafts": cmd_drafts,
            "approve": cmd_approve, "scrape": cmd_scrape, "demo": cmd_demo}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
