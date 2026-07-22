"""AuditAgent — wraps the existing audit-system/audit.py (imported, not shelled).

Runs the 3-state auditor against the student's matched manifest, writes the
report into the student folder, and returns the JSON verdict for the board.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from ..config import AUDIT_DIR, MANIFEST_DIR
from ..tools import fs

# import audit.py as a module without polluting sys.path permanently
_spec = importlib.util.spec_from_file_location("keystone_audit", AUDIT_DIR / "audit.py")
audit_mod = importlib.util.module_from_spec(_spec)
sys.modules["keystone_audit"] = audit_mod
_spec.loader.exec_module(audit_mod)


def default_manifest(slug: str) -> Path:
    """Use the student's match if present, else fall back to the KUAC manifest
    (KDU/KUAC is the founder's live corridor)."""
    match = fs.read_match(slug)
    if match and match.get("top") and match["top"][0].get("manifest_path"):
        return Path(match["top"][0]["manifest_path"])
    return MANIFEST_DIR / "korea" / "kdu-global-kuac.yaml"


def run(slug: str, manifest_path: str | None = None) -> dict:
    student_dir = fs.student_root(slug)
    mpath = Path(manifest_path) if manifest_path else default_manifest(slug)

    manifest = audit_mod.load_manifest(str(mpath))
    meta, present = audit_mod.load_student(str(student_dir))
    results, consistency = audit_mod.audit(manifest, meta, present)
    report_md, ready, counts = audit_mod.render_report(manifest, results, consistency, meta)

    js = {"ready": ready, "counts": counts, "documents": results,
          "consistency": consistency, "manifest": manifest["id"]}
    stem = f"{meta.get('student_name', slug).replace(' ', '_')}_{manifest['id']}"
    fs.write_report(slug, stem, report_md, js)
    return js
