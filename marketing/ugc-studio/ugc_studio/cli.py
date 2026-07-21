"""Keystone UGC Studio CLI."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from .brandkit import BrandKit
from .config import Config
from .guardrails import check
from .pipeline import load_scripts, render_script

STUDIO = Path(__file__).resolve().parent.parent
DEFAULT_SCRIPTS = STUDIO / "scripts.yaml"


def cmd_doctor(args) -> int:
    cfg = Config.load()
    print("Keystone UGC Studio — environment check\n")
    print(f"  ffmpeg:        {'OK ' + (shutil.which('ffmpeg') or '') if shutil.which('ffmpeg') else 'MISSING (apt install ffmpeg)'}")
    try:
        from PIL import ImageFont
        brand = BrandKit.load()
        ImageFont.truetype(brand.fonts["bengali_bold"], 40)
        print(f"  bengali font:  OK  ({brand.fonts['bengali_bold']})")
    except Exception as e:
        print(f"  bengali font:  MISSING ({e})")
    print(f"  TTS provider:  {cfg.tts_provider}  (sarvam key: {'set' if cfg.sarvam_api_key else 'not set → silent voiceover'})")
    print(f"  avatar:        {cfg.avatar_provider}")
    brand = BrandKit.load()
    for k in ("logo", "founder_photo", "marina_photo"):
        print(f"  asset {k:13s}{'OK' if brand.asset(k) else 'missing'}")
    print(f"\n  scripts file:  {DEFAULT_SCRIPTS}  ({'found' if DEFAULT_SCRIPTS.exists() else 'MISSING'})")
    print(f"  out dir:       {cfg.out_dir}")
    return 0


def cmd_list(args) -> int:
    brand = BrandKit.load()
    scripts = load_scripts(args.scripts or DEFAULT_SCRIPTS)
    print(f"{len(scripts)} scripts in {args.scripts or DEFAULT_SCRIPTS}\n")
    for s in scripts:
        errs, warns = check(s, brand)
        flag = "✗" if errs else ("!" if warns else "✓")
        print(f"  {flag} {s.id:22s} [{s.persona:7s}] {s.total_seconds:>4}s  {s.angle}")
        for e in errs:
            print(f"       ERROR: {e}")
    return 0


def cmd_lint(args) -> int:
    brand = BrandKit.load()
    scripts = load_scripts(args.scripts or DEFAULT_SCRIPTS)
    total_err = 0
    for s in scripts:
        errs, warns = check(s, brand)
        total_err += len(errs)
        for e in errs:
            print(f"ERROR {s.id}: {e}")
        for w in warns:
            print(f"warn  {s.id}: {w}")
    print(f"\n{total_err} error(s) across {len(scripts)} scripts")
    return 1 if total_err else 0


def cmd_render(args) -> int:
    cfg = Config.load()
    brand = BrandKit.load()
    scripts = load_scripts(args.scripts or DEFAULT_SCRIPTS)
    if args.id:
        scripts = [s for s in scripts if s.id == args.id]
        if not scripts:
            print(f"no script with id '{args.id}'", file=sys.stderr)
            return 1
    if args.limit:
        scripts = scripts[: args.limit]
    ok = fail = 0
    for s in scripts:
        res = render_script(s, brand, cfg, strict=not args.no_strict)
        if res.ok:
            ok += 1
            mb = res.meta.get("bytes", 0) / 1e6
            print(f"✓ {s.id:22s} → {res.video}  ({res.meta.get('seconds','?')}s, "
                  f"{res.engine}, {mb:.2f} MB)")
            for w in res.warnings:
                print(f"    warn: {w}")
        else:
            fail += 1
            print(f"✗ {s.id:22s} BLOCKED")
            for e in res.errors:
                print(f"    {e}")
    print(f"\nrendered {ok}, blocked {fail}")
    return 1 if fail and args.id else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ugc-studio",
                                description="Keystone Bangla UGC video studio")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="check environment (ffmpeg, fonts, assets, keys)")
    pl = sub.add_parser("list", help="list scripts with guardrail status")
    pl.add_argument("--scripts")
    pli = sub.add_parser("lint", help="run compliance guardrails on all scripts")
    pli.add_argument("--scripts")
    pr = sub.add_parser("render", help="render one or all scripts to .mp4 + caption")
    pr.add_argument("--id", help="render just this script id")
    pr.add_argument("--limit", type=int, help="render at most N scripts")
    pr.add_argument("--scripts")
    pr.add_argument("--no-strict", action="store_true",
                    help="render even if guardrails flag errors (for local preview only)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return {"doctor": cmd_doctor, "list": cmd_list, "lint": cmd_lint,
            "render": cmd_render}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
