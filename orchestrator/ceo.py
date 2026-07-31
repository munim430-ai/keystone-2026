"""The CEO orchestrator — a small dispatcher, not a framework.

It owns a job queue, runs each job by spawning the matching ephemeral sub-agent
(a function call that returns and is discarded), writes results to the student
folder + board, and chains the natural next step. The whole "multi-agent"
behaviour is this ~120 lines; per the repo's own stack research, a custom
dispatcher beats CrewAI/AutoGen at this scale.

Nothing here can send/post/spend — sub-agents only draft, and the board sync is
dry-run unless the founder wired NocoDB.
"""
from __future__ import annotations

import datetime as dt

from . import guardrails
from .agents import audit_agent, matcher_agent, instruct_agent, scraper_agent, content_agent
from .config import CFG
from .models import Job
from .tools import db, fs


def build_context(slug: str) -> None:
    """Write the per-student AI bundle (full detail — stays in the folder)."""
    meta = fs.read_meta(slug)
    audit_js = fs.latest_audit_json(slug) or {}
    match = fs.read_match(slug) or {}
    top = match.get("top", [])
    lines = [f"# AI context — {meta.get('name', slug)}", "",
             f"- slug: {slug}", f"- stage: {meta.get('stage')}",
             f"- source: {meta.get('source')}", ""]
    if audit_js:
        c = audit_js.get("counts", {})
        lines += [f"## Audit ({audit_js.get('manifest')})",
                  f"verdict: {'READY' if audit_js.get('ready') else 'NOT READY'} — "
                  f"✅{c.get('VERIFIED',0)} ⚠️{c.get('FLAGGED',0)} ❌{c.get('MISSING',0)}", ""]
    if top:
        lines += ["## Top matches"]
        lines += [f"- {t['university']} — {t['eligibility']} (visa-likelihood {t['visa_likelihood']})"
                  for t in top[:3]]
    fs.write_context(slug, "\n".join(lines))


def run_job(job: Job) -> dict:
    """Dispatch a single job to its ephemeral agent. Returns a result dict and
    enqueues any natural follow-on job (returned in result['next'])."""
    kind, slug = job.kind, job.student
    result: dict = {"job": job.id, "kind": kind, "student": slug, "next": []}

    if kind == "match":
        m = matcher_agent.run(slug)
        top = m["top"][0] if m["top"] else None
        db.upsert_student(slug, stage="counselling",
                          match_top=top["university"] if top else "")
        result["summary"] = f"{len(m['top'])} matches; top={top['university'] if top else '—'}"
        result["next"] = [Job("audit", slug)]

    elif kind == "audit":
        js = audit_agent.run(slug)
        c = js["counts"]
        db.upsert_student(
            slug, stage="audit_gate",
            audit_verdict="READY" if js["ready"] else "NOT READY",
            audit_missing=c.get("MISSING", 0), audit_flagged=c.get("FLAGGED", 0))
        result["summary"] = (f"audit {'READY' if js['ready'] else 'NOT READY'} — "
                             f"❌{c.get('MISSING',0)} ⚠️{c.get('FLAGGED',0)}")
        if not js["ready"]:
            result["next"] = [Job("instruct", slug, {"audit": js})]

    elif kind == "instruct":
        r = instruct_agent.run(slug, job.payload.get("audit"))
        result["summary"] = f"draft {r['draft_id']} queued (pending): {len(r['missing'])} missing"

    elif kind == "scrape":
        result["data"] = scraper_agent.run(job.payload.get("mode", "b2b"),
                                            job.payload.get("urls"))

    elif kind == "content":
        r = content_agent.run(job.payload.get("insight", ""),
                              job.payload.get("name_hint", ""))
        result["summary"] = f"post draft {r['draft_id']} queued (pending)"

    else:
        result["error"] = f"unknown job kind: {kind}"

    if slug:
        build_context(slug)
    return result


class CEO:
    """Synchronous dispatcher (a queue + a drain loop). Deterministic and
    trivially testable; cron-able. An async server variant wraps this."""

    def __init__(self):
        self.queue: list[Job] = []
        self.log: list[dict] = []

    def submit(self, job: Job) -> None:
        self.queue.append(job)

    def drain(self, max_jobs: int = 100) -> list[dict]:
        done = 0
        while self.queue and done < max_jobs:
            job = self.queue.pop(0)
            res = run_job(job)
            self.log.append(res)
            for nxt in res.get("next", []):
                self.queue.append(nxt)
            done += 1
        return self.log

    def survival(self) -> dict:
        enrolled = sum(1 for s in db.board() if s.get("stage") in ("departed", "visa_granted"))
        return guardrails.survival_status(enrolled)


def process_new_student(slug: str) -> list[dict]:
    """Standard intake chain: match → audit → (if not ready) instruct."""
    ceo = CEO()
    ceo.submit(Job("match", slug))
    return ceo.drain()
