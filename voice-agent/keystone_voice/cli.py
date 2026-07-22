"""Command-line entry point for the Keystone Voice Agent."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .config import Config
from .db import Database

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CSV = BASE_DIR.parent / "data" / "IELTS_Partners_Tier2.csv"


def _print_status(cfg: Config, db: Database) -> None:
    s = db.stats()
    print(f"demo_mode={cfg.demo_mode}  dialer={cfg.dialer_mode}  kill_switch={s['kill_switch']}")
    print(f"centers by status: {s['funnel']}")
    print(f"calls today: {s['calls_today']}  total: {s['calls_total']}  "
          f"answered: {s['answered_total']}")
    missing = cfg.missing_for_live()
    if missing:
        print(f"missing for LIVE calls: {', '.join(missing)}")
    else:
        print("ready for live calls (set DEMO_MODE=0 to enable)")


def cmd_init_db(cfg: Config, args) -> int:
    Database(cfg.db_path)
    print(f"initialized DB at {cfg.db_path}")
    return 0


def cmd_import(cfg: Config, args) -> int:
    db = Database(cfg.db_path)
    path = args.csv or str(DEFAULT_CSV)
    if not Path(path).exists():
        print(f"CSV not found: {path}", file=sys.stderr)
        return 1
    result = db.import_centers_csv(path)
    print(f"imported from {path}: {result}")
    total = db.one("SELECT COUNT(*) AS n FROM centers WHERE phone LIKE '+8801%'")
    print(f"dialable centers now: {total['n']}")
    return 0


def cmd_status(cfg: Config, args) -> int:
    _print_status(cfg, Database(cfg.db_path))
    return 0


def cmd_serve(cfg: Config, args) -> int:
    import uvicorn
    from .app import create_app
    app = create_app(cfg)
    print(f"dashboard: http://{cfg.host}:{cfg.port}/   (demo_mode={cfg.demo_mode})")
    uvicorn.run(app, host=cfg.host, port=cfg.port, log_level="info")
    return 0


def cmd_console(cfg: Config, args) -> int:
    from .console_sim import run_console
    asyncio.run(run_console(cfg, args.center))
    return 0


def cmd_pregen(cfg: Config, args) -> int:
    from .pregen import main as pregen_main
    pregen_main(cfg)
    return 0


def cmd_kill(cfg: Config, args) -> int:
    db = Database(cfg.db_path)
    db.set_killed(not args.resume)
    print("kill switch:", "OFF (resumed)" if args.resume else "ON (all calls stopping)")
    return 0


def cmd_test_call(cfg: Config, args) -> int:
    """Place a single self-test call to OPERATOR_PHONE (Test 1)."""
    if cfg.demo_mode:
        print("DEMO_MODE=1 — no real call placed. Use 'console' to rehearse the brain, "
              "or set DEMO_MODE=0 with Twilio configured.")
        return 0
    missing = cfg.missing_for_live()
    if missing:
        print(f"cannot place live call, missing: {', '.join(missing)}", file=sys.stderr)
        return 1
    if not cfg.operator_phone:
        print("set OPERATOR_PHONE in .env for the self-test", file=sys.stderr)
        return 1

    async def _go() -> None:
        from .app import Runtime
        rt = Runtime(cfg)
        db = rt.db
        # ensure a scratch "operator self-test" center exists
        row = db.one("SELECT * FROM centers WHERE phone=?", (cfg.operator_phone,))
        if not row:
            db._exec("INSERT OR IGNORE INTO centers(name,district,category,phone,priority,notes)"
                     " VALUES(?,?,?,?,?,?)",
                     ("SELF TEST", "test", "korean", cfg.operator_phone, 9, "operator self-test"))
            row = db.one("SELECT * FROM centers WHERE phone=?", (cfg.operator_phone,))
        sid = await rt.dial_center(row)
        print(f"placed self-test call to {cfg.operator_phone} (ref {sid}). "
              f"Answer and role-play a center owner. Watch the dashboard for the transcript.")
        await rt.close()

    asyncio.run(_go())
    return 0


def cmd_export(cfg: Config, args) -> int:
    from .export import export_calls, export_centers
    db = Database(cfg.db_path)
    if args.what == "calls":
        n = export_calls(db, args.out)
    else:
        n = export_centers(db, args.out)
    if args.out:
        print(f"exported {n} {args.what} rows -> {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="keystone-voice",
                                description="Autonomous Bangla AI sales caller for Keystone")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-db", help="create the SQLite database")

    pi = sub.add_parser("import-centers", help="import the scraped centers CSV")
    pi.add_argument("--csv", help=f"path to CSV (default: {DEFAULT_CSV})")

    sub.add_parser("status", help="show funnel + readiness")
    sub.add_parser("serve", help="run the web server + dashboard")

    pc = sub.add_parser("console", help="text simulator of a call (no telephony)")
    pc.add_argument("--center", type=int, help="center id to role-play")

    sub.add_parser("pregen", help="pre-generate cached audio clips")

    pk = sub.add_parser("kill", help="engage the kill switch (stop all calls)")
    pk.add_argument("--resume", action="store_true", help="release the kill switch")

    sub.add_parser("test-call", help="place a single self-test call to OPERATOR_PHONE")

    pe = sub.add_parser("export", help="export data to CSV")
    pe.add_argument("what", choices=["centers", "calls"])
    pe.add_argument("--out", help="output file (default: stdout)")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = Config.load()
    handlers = {
        "init-db": cmd_init_db, "import-centers": cmd_import, "status": cmd_status,
        "serve": cmd_serve, "console": cmd_console, "pregen": cmd_pregen,
        "kill": cmd_kill, "test-call": cmd_test_call, "export": cmd_export,
    }
    return handlers[args.cmd](cfg, args)


if __name__ == "__main__":
    raise SystemExit(main())
