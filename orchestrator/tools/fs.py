"""Per-student folder CRUD. Extends the existing audit-system/students/<slug>/
convention so the auditor reads what we write with zero migration.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import yaml

from ..config import STUDENTS_DIR, TEMPLATE_METADATA

SUBDIRS = ("docs_in", "files", "chats", "audits", "instructions")


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "student"


def student_root(slug: str) -> Path:
    return STUDENTS_DIR / slug


def exists(slug: str) -> bool:
    return student_root(slug).is_dir()


def create_student(slug: str, meta: dict) -> Path:
    """Create the folder tree + meta.json + a metadata.yaml seeded from the
    template (blanks stay blank → the auditor FLAGs them, never silently passes)."""
    root = student_root(slug)
    for d in SUBDIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    md = root / "metadata.yaml"
    if not md.exists():
        if TEMPLATE_METADATA.exists():
            shutil.copy(TEMPLATE_METADATA, md)
        else:
            md.write_text("student_name: \"\"\nhuman_signoffs: []\n", encoding="utf-8")
        # seed the student_name so the auditor's report is labelled
        if meta.get("name"):
            set_metadata_field(slug, "student_name", meta["name"])
    return root


def read_meta(slug: str) -> dict:
    p = student_root(slug) / "meta.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def write_meta(slug: str, meta: dict) -> None:
    (student_root(slug) / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def read_metadata_yaml(slug: str) -> dict:
    p = student_root(slug) / "metadata.yaml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def set_metadata_field(slug: str, field: str, value) -> None:
    p = student_root(slug) / "metadata.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
    data = data or {}
    data[field] = value
    p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def save_upload(slug: str, filename: str, content: bytes) -> Path:
    dest = student_root(slug) / "docs_in" / Path(filename).name
    dest.write_bytes(content)
    return dest


def write_report(slug: str, stem: str, md: str, js: dict | None = None) -> Path:
    adir = student_root(slug) / "audits"
    adir.mkdir(parents=True, exist_ok=True)
    (adir / f"{stem}.md").write_text(md, encoding="utf-8")
    if js is not None:
        (adir / f"{stem}.json").write_text(
            json.dumps(js, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return adir / f"{stem}.md"


def latest_audit_json(slug: str) -> dict | None:
    adir = student_root(slug) / "audits"
    if not adir.is_dir():
        return None
    jsons = sorted(adir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jsons:
        return None
    return json.loads(jsons[0].read_text(encoding="utf-8"))


def write_match(slug: str, match: dict) -> None:
    (student_root(slug) / "match.json").write_text(
        json.dumps(match, ensure_ascii=False, indent=2), encoding="utf-8")


def read_match(slug: str) -> dict | None:
    p = student_root(slug) / "match.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def save_instruction(slug: str, draft_id: str, body_bn: str) -> Path:
    idir = student_root(slug) / "instructions"
    idir.mkdir(parents=True, exist_ok=True)
    p = idir / f"{draft_id}.txt"
    p.write_text(body_bn, encoding="utf-8")
    return p


def write_context(slug: str, md: str) -> None:
    (student_root(slug) / "context.md").write_text(md, encoding="utf-8")


def list_students() -> list[str]:
    if not STUDENTS_DIR.is_dir():
        return []
    return sorted(p.name for p in STUDENTS_DIR.iterdir()
                  if p.is_dir() and not p.name.startswith("_"))
