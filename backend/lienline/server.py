"""Local API for live runs. The deployed site replays the recorded JSON instead.

    uv run lienline            # http://localhost:8300

GET  /api/health            backend + model status
GET  /api/cases             the scenarios that can be run
POST /api/run/{case_id}     Server-Sent Events: one `data:` line per pipeline event, then
                            `event: run` carrying the full run JSON, then `event: done`
POST /api/decision          the nodal officer approves or edits one decision
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, NonNegativeInt

from lienline import llm
from lienline.agents import Gate
from lienline.models import Event, Run
from lienline.money import inr
from lienline.patterns import full_freeze_justified, signals_for
from lienline.pipeline import stream
from lienline.simulate import IST, SCENARIOS, load

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT.parent / "web" / "public" / "runs"
APPROVALS = Path(os.environ.get("LIENLINE_APPROVALS", ROOT / "data" / "approvals.json"))

app = FastAPI(title="LienLine")
app.add_middleware(CORSMiddleware, allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
                   allow_methods=["GET", "POST"], allow_headers=["content-type"])
_lock = threading.Lock()


@app.get("/api/health")
def health() -> dict:
    gate = Gate.auto()
    return {"ok": True, "model": gate.backend(), "live_model": gate.enabled}


@app.get("/api/cases")
def cases() -> list[dict]:
    out = []
    for case_id in SCENARIOS:
        s = load(case_id)
        out.append({"case_id": case_id, "title": s.title, "summary": s.summary})
    return out


@app.post("/api/run/{case_id}")
def run_live(case_id: str) -> StreamingResponse:
    if case_id not in SCENARIOS:
        raise HTTPException(404, f"unknown case {case_id}")
    return StreamingResponse(_sse(case_id), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _sse(case_id: str) -> Iterator[str]:
    gen = stream(load(case_id), Gate.auto())
    while True:
        try:
            event = next(gen)
        except StopIteration as done:
            run: Run = done.value
            break
        yield f"data: {json.dumps(event.model_dump(mode='json'), ensure_ascii=False)}\n\n"
    yield f"event: run\ndata: {json.dumps(run.to_json(), ensure_ascii=False)}\n\n"
    yield "event: done\ndata: {}\n\n"


class Approval(BaseModel):
    case_id: str
    account_id: str
    verdict: Literal["approve", "edit"]
    action: Literal["lien", "full_freeze", "release"] | None = None  # required for an edit
    amount: NonNegativeInt | None = None  # paise; required for an edit
    officer: str = Field(min_length=2, max_length=80)
    note: str = Field(default="", max_length=1000)


@app.post("/api/decision")
def approve(req: Approval) -> dict:
    """Record the nodal officer's call. An edit must stay within what the ledgers and policy allow."""
    path = RUNS / f"{req.case_id}.json"
    if req.case_id not in SCENARIOS or not path.exists():
        raise HTTPException(404, f"no recorded run for {req.case_id}")
    run = Run.model_validate(json.loads(path.read_text()))
    decision = next((d for d in run.decisions if d.account_id == req.account_id), None)
    if decision is None:
        raise HTTPException(404, f"no decision for {req.account_id}")

    action, amount = decision.action, decision.amount
    if req.verdict == "edit":
        if req.action is None or req.amount is None:
            raise HTTPException(422, "an edit needs an action and an amount")
        action, amount = req.action, req.amount
        _check_edit(run, req, action, amount)

    record = {"case_id": req.case_id, "account_id": req.account_id, "verdict": req.verdict, "action": action,
              "amount": amount, "officer": req.officer, "note": req.note,
              "at": datetime.now(IST).replace(microsecond=0).isoformat()}
    with _lock:
        APPROVALS.parent.mkdir(parents=True, exist_ok=True)
        log = json.loads(APPROVALS.read_text()) if APPROVALS.exists() else []
        log.append(record)
        APPROVALS.write_text(json.dumps(log, ensure_ascii=False, indent=1))

    verb = "approved" if req.verdict == "approve" else "edited to"
    event = Event(t=run.events[-1].t if run.events else 0.0, agent="Nodal officer", kind="human", type="approval",
                  text=f"{req.officer} {verb} {action.replace('_', ' ')} {inr(amount)} on {req.account_id}."
                       + (f" Note: {req.note}" if req.note else ""), refs=[req.account_id])
    return {"record": record, "event": event.model_dump(mode="json")}


def _check_edit(run: Run, req: Approval, action: str, amount: int) -> None:
    at = run.trace.accounts[req.account_id]
    traceable = at.by_rule[run.trace.policy_rule]
    if amount > at.balance_now:
        raise HTTPException(422, f"{inr(amount)} exceeds the balance of {inr(at.balance_now)}")
    if action == "release" and amount != 0:
        raise HTTPException(422, "a release holds nothing; amount must be 0")
    if action == "full_freeze":
        signals = signals_for(load(req.case_id), next(a for a in run.accounts if a.id == req.account_id))
        if not full_freeze_justified(signals) and not req.note.strip():
            raise HTTPException(422, "full freeze without the policy's mule signals needs a recorded reason (note)")
        if amount != at.balance_now:
            raise HTTPException(422, f"a full freeze holds the whole balance of {inr(at.balance_now)}")
    if action == "lien" and amount > traceable and not req.note.strip():
        raise HTTPException(422, f"a lien above the traceable {inr(traceable)} needs a recorded reason (note)")


def run() -> None:
    import uvicorn

    print(f"LienLine API on http://localhost:8300 (model: {llm.describe_backend().get('backend')})")
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8300")))
