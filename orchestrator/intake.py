"""FastAPI intake webhook — a messy upload becomes a student folder + a board
card, and kicks the CEO chain (match → audit → instruct-draft).

Runnable with `uvicorn orchestrator.intake:app`. Optional: with no NocoDB
configured, the board writes to the local mirror so everything still works.
"""
from __future__ import annotations

import re

from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import JSONResponse

from . import ceo
from .models import Job
from .tools import db, fs

app = FastAPI(title="Keystone CEO Orchestrator — Intake")


def _normalize_bd(phone: str) -> str:
    digits = re.sub(r"[^\d]", "", phone or "")
    if digits.startswith("880"):
        digits = digits[3:]
    if digits.startswith("0"):
        digits = digits[1:]
    return "+880" + digits if len(digits) == 10 and digits.startswith("1") else (phone or "")


@app.get("/health")
async def health():
    surv = ceo.CEO().survival()
    return {"ok": True, "survival": surv["banner"]}


@app.post("/intake")
async def intake(name: str = Form(...), phone: str = Form(""),
                 source: str = Form("whatsapp"),
                 files: list[UploadFile] = File(default=[])):
    slug = fs.slugify(name)
    meta = {"name": name, "phone": _normalize_bd(phone), "source": source,
            "stage": "intake"}
    fs.create_student(slug, meta)
    for f in files:
        fs.save_upload(slug, f.filename, await f.read())
    db.upsert_student(slug, stage="intake", name=name, phone=meta["phone"])
    # run the chain synchronously (fast: no external calls in mock mode)
    log = ceo.process_new_student(slug)
    return JSONResponse({"student": slug, "status": "created",
                         "jobs": [l.get("summary") or l.get("kind") for l in log]})


@app.get("/board")
async def board():
    return {"students": db.board(), "survival": ceo.CEO().survival()}


@app.get("/drafts")
async def drafts(status: str = "pending"):
    return {"drafts": db.drafts(status)}
