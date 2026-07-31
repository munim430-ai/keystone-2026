#!/bin/bash
# Installs the runtime dependencies this repo's scripts actually need, so they
# work the first time in a fresh Claude Code on the web session instead of
# failing halfway through with a missing-package error.
#
# Scope: web sessions only (see the CLAUDE_CODE_REMOTE check below). The repo
# has no package.json/requirements.txt/CI/linter config of its own -- this
# hook exists to cover the real imports found across scrapers/, bots/, and
# audit-system/ (requests, pillow, pyyaml, jsonschema, pypdf, pytesseract,
# pdf2image) plus the system packages pdf2image/pypdf need (poppler-utils,
# tesseract-ocr with the Bengali+English language packs).
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

if command -v apt-get >/dev/null 2>&1; then
  sudo -n apt-get update -qq
  sudo -n apt-get install -y -qq \
    tesseract-ocr tesseract-ocr-ben tesseract-ocr-eng poppler-utils
fi

pip install --quiet \
  requests pillow pyyaml jsonschema pypdf pytesseract pdf2image

# Debian's system `cryptography` package can end up mismatched with the pip-
# installed `cffi` it depends on, which breaks `pypdf` (used by
# audit-system/split.py) with "ModuleNotFoundError: _cffi_backend" even
# though both packages report as installed. --ignore-installed shadows the
# broken debian package with a clean pip-managed pair without trying (and
# failing) to uninstall it first -- --force-reinstall fails here because the
# debian package has no pip RECORD file to uninstall from.
pip install --quiet --ignore-installed cffi cryptography
