"""One LienLine run: the agents in order, emitting the event stream the UI replays.

``stream`` is a generator: it yields each ``Event`` as it happens (the server forwards them
over SSE) and returns the finished ``Run``. Event times ``t`` are honest: code steps add the
wall time they took, model steps add the seconds the model call took when it was made (so a
replay from the cache keeps the original pacing).
"""

from __future__ import annotations

import json
from collections.abc import Generator, Iterable
from datetime import datetime
from pathlib import Path
from time import perf_counter

from lienline import agents
from lienline.agents import Gate
from lienline.clocks import clocks_for
from lienline.decide import decide
from lienline.letters import plan_letters
from lienline.models import (
    SINKS,
    AgentName,
    Event,
    EventKind,
    EventType,
    IndexEntry,
    Letter,
    ModelInfo,
    Run,
    Scenario,
    Verification,
)
from lienline.money import from_rupees, inr
from lienline.patterns import present, signals_for
from lienline.simulate import IST
from lienline.trace import trace
from lienline.verify import allowed_amounts, verify


class Recorder:
    """Stamps events with a run-relative time and keeps them in order."""

    def __init__(self) -> None:
        self.t = 0.0
        self.events: list[Event] = []
        self._mark = perf_counter()

    def model_time(self, seconds: float) -> None:
        """Count a model step by the model's own seconds, not the wall time (which may be a cache hit)."""
        self._mark = perf_counter()
        self.t += seconds

    def emit(self, agent: AgentName, kind: EventKind, type_: EventType, text: str, *,
             refs: Iterable[str] = (), data: dict | None = None, ok: bool = True) -> Event:
        now = perf_counter()
        self.t += now - self._mark
        self._mark = now
        event = Event(t=round(self.t, 3), agent=agent, kind=kind, type=type_, text=text,
                      refs=list(dict.fromkeys(refs)), data=data or {}, ok=ok)
        self.events.append(event)
        return event


def stream(scenario: Scenario, gate: Gate) -> Generator[Event, None, Run]:
    """Run every agent on one case, yielding events as they happen; returns the verified run."""
    rec = Recorder()
    model_kind: EventKind = "model" if gate.enabled else "code"
    known = {a.id for a in scenario.accounts} | {t.id for t in scenario.transactions} | SINKS

    # 1. Intake: the model reads the paperwork, code checks every UTR and account against the ledgers.
    yield rec.emit("Intake", model_kind, "start", f"Reading the Section {scenario.notice.section} notice "
                   f"({len(scenario.notice.flagged)} accounts) and the victim's complaint.")
    extraction, source, seconds = agents.intake(gate, scenario)
    rec.model_time(seconds)
    yield rec.emit("Intake", source, "message",
                   f"Extracted {len(extraction.notice_lines)} notice lines, {len(extraction.victim_utrs)} victim UTRs "
                   f"and a stated loss of {inr(from_rupees(extraction.amount_lost_rupees))}.",
                   data=extraction.model_dump())
    for f in agents.cross_check_intake(scenario, extraction):
        yield rec.emit("Intake", "code", "check", f.detail, refs=f.refs, ok=f.ok, data={"item": f.item})

    # 2. Tracer: all four rules over every bank's ledger, hop by hop.
    yield rec.emit("Tracer", "code", "start", f"Replaying {len(scenario.transactions)} transactions across "
                   f"{len(scenario.banks)} banks in time order under FIFO, LIFO, PRO_RATA and LIBR.")
    tr = trace(scenario)
    for acc_id, at in tr.accounts.items():
        if not any(at.by_rule.values()) and acc_id not in scenario.flagged_ids():
            continue
        credits = [e.txn for e in tr.edges if e.to == acc_id and any(e.tainted.values())]
        spread = ", ".join(f"{r} {inr(v)}" for r, v in at.by_rule.items() if r != tr.policy_rule)
        yield rec.emit("Tracer", "code", "result", f"{acc_id} {scenario.account(acc_id).holder}: balance "
                       f"{inr(at.balance_now)}; traceable {inr(at.by_rule[tr.policy_rule])} under {tr.policy_rule} "
                       f"({spread}).", refs=[acc_id, *credits], data={"by_rule": at.by_rule})
    c = tr.conservation
    balanced = c.held + c.cashed_out + c.untraced == c.lost
    yield rec.emit("Tracer", "code", "check", f"Conservation under {tr.policy_rule}: held {inr(c.held)} + cashed out "
                   f"{inr(c.cashed_out)} + untraced {inr(c.untraced)} = lost {inr(c.lost)}.", ok=balanced,
                   data=c.model_dump())

    # 3. Pattern analyst: code computes the signals, the model explains them.
    signals = {acc_id: signals_for(scenario, scenario.account(acc_id)) for acc_id in tr.accounts}
    for acc_id, sigs in signals.items():
        found = present(sigs)
        if found:
            yield rec.emit("Pattern analyst", "code", "tool", f"{acc_id}: " + "; ".join(s.label for s in found) + ".",
                           refs=[acc_id, *(r for s in found for r in s.refs)],
                           data={"signals": [s.model_dump() for s in sigs]})
    explained, findings, source, seconds = agents.explain_patterns(gate, scenario, signals, known)
    rec.model_time(seconds)
    for f in findings:
        yield rec.emit("Pattern analyst", "code", "check", f"{f.item} {f.detail}.", ok=False)
    for e in explained:
        if present(signals[e.account_id]):
            yield rec.emit("Pattern analyst", source, "message", f"{e.account_id}: {e.explanation}",
                           refs=[e.account_id, *e.refs])

    # 4. Advocates argue; code rejects bad citations and numbers. The decider is code policy.
    decisions = decide(scenario, tr, signals)
    by_acc = {d.account_id: d for d in decisions}
    for side, agent in (("victim", "Victim's advocate"), ("holder", "Account holder's advocate")):
        yield rec.emit(agent, model_kind, "start", f"Arguing the hold on {len(decisions)} contested accounts.")
        args, source, seconds = agents.advocate(gate, side, scenario, tr, decisions, signals)
        rec.model_time(seconds)
        for claim in args.claims:
            ruling = agents.judge(side, claim, tr, by_acc, signals, known)
            ask = "release" if claim.action == "release" else f"{claim.action.replace('_', ' ')} of " \
                  f"{inr(ruling.as_data()['amount'])}" + (f" ({claim.rule})" if claim.rule else "")
            refs = claim.refs if ruling.status != "rejected" else [r for r in (claim.account_id,) if r in known]
            yield rec.emit(agent, source, "debate", f"{claim.account_id}: asks for {ask}. {claim.argument} "
                           f"[{ruling.status}: {ruling.detail}]", refs=refs, ok=ruling.status != "rejected",
                           data={"claims": [ruling.as_data()]})

    for d in decisions:
        yield rec.emit("Decider", "code", "result", f"{d.account_id}: {d.action.replace('_', ' ')} {inr(d.amount)}; "
                       f"current hold {inr(d.current_hold)}, released {inr(d.released_by_change)} "
                       f"({d.confidence} confidence).", refs=[d.account_id, *(r for x in d.reasons for r in x.refs)],
                       data=d.model_dump())

    # 5. Clock keeper.
    clocks = clocks_for(scenario, decisions)
    for ck in clocks:
        if ck.status != "met":
            yield rec.emit("Clock keeper", "code", "result", f"{ck.account_id}: {ck.label} — due {ck.due:%d %b %Y}, "
                           f"{ck.status}. ({ck.rule})", refs=[ck.account_id, ck.id], ok=ck.status != "breached")

    # 6. Drafter: every figure in every letter is checked against the decision.
    letters: list[Letter] = []
    utrs, masked = {t.utr for t in scenario.transactions}, {a.masked for a in scenario.accounts}
    for spec in plan_letters(scenario, tr, decisions, signals):
        allowed = allowed_amounts(spec.decision, tr.accounts[spec.account_id], tr.edges, scenario.notice.flagged,
                                  scenario.complaint.amount_lost)
        drafted = agents.draft_letter(gate, spec, allowed, utrs, masked)
        rec.model_time(drafted.seconds)
        for problems in drafted.rejected:
            yield rec.emit("Drafter", "code", "check", f"Draft {spec.id} rejected by the number checker: "
                           + "; ".join(problems), refs=[spec.account_id], ok=False)
        letters.append(Letter(id=spec.id, account_id=spec.account_id, kind=spec.kind, to=spec.to,
                              subject=drafted.subject, body=drafted.body, verified=True,
                              numbers_checked=drafted.numbers_checked))
        yield rec.emit("Drafter", drafted.source, "letter", f"{spec.id} {spec.kind.replace('_', ' ')} to {spec.to}: "
                       f"{drafted.numbers_checked} figures checked.", refs=[spec.account_id, spec.id])

    # 7. Verifier: an independent replay of everything above.
    yield rec.emit("Verifier", "code", "start", "Replaying the ledgers independently and re-checking every figure.")
    calls = gate.calls
    backend = gate.backend()
    run = Run(
        case_id=scenario.case_id, title=scenario.title, summary=scenario.summary,
        generated_at=datetime.now(IST).replace(microsecond=0),
        model=ModelInfo(backend=backend["backend"], chat_model=backend.get("chat_model", ""), calls=len(calls),
                        tokens=sum(x.tokens for x in calls)),
        complaint=scenario.complaint, notice=scenario.notice, banks=scenario.banks, accounts=scenario.accounts,
        transactions=scenario.transactions, grievances=scenario.grievances, trace=tr, decisions=decisions,
        clocks=clocks, events=[], letters=letters, verification=Verification(passed=False, checks=[]),
    )
    run.events = list(rec.events)  # the citation check covers every event emitted so far
    run.verification = verify(run)
    for ck in run.verification.checks:
        yield rec.emit("Verifier", "code", "check", f"{ck.name}: {ck.detail}", ok=ck.ok)
    yield rec.emit("Verifier", "code", "result", "All checks passed." if run.verification.passed else
                   "Verification FAILED: do not act on this run.", ok=run.verification.passed)

    # 8. The nodal officer approves or edits each decision in the UI (POST /api/decision).
    released = sum(max(0, d.released_by_change) for d in decisions)
    yield rec.emit("Nodal officer", "human", "approval", f"Awaiting approval of {len(decisions)} decisions "
                   f"({inr(released)} to be released).", refs=[d.account_id for d in decisions])
    run.events = rec.events
    return run


def run_case(scenario: Scenario, gate: Gate) -> Run:
    """Run to completion without streaming."""
    gen = stream(scenario, gate)
    while True:
        try:
            next(gen)
        except StopIteration as done:
            return done.value


# ---------------------------------------------------------------- files the web app reads


def save(run: Run, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run.case_id}.json"
    path.write_text(json.dumps(run.to_json(), ensure_ascii=False, indent=1) + "\n")
    return path


def index_entry(run: Run) -> IndexEntry:
    return IndexEntry(
        case_id=run.case_id, title=run.title, summary=run.summary, accounts=len(run.accounts), banks=len(run.banks),
        lost=run.complaint.amount_lost, held_before=sum(d.current_hold for d in run.decisions),
        held_after=sum(d.amount for d in run.decisions),
        status="verified" if run.verification.passed else "failed", model_calls=run.model.calls,
    )


def rebuild_index(out_dir: Path, order: Iterable[str]) -> Path:
    """index.json from the run files present, in the given case order."""
    entries = []
    for case_id in order:
        path = out_dir / f"{case_id}.json"
        if path.exists():
            entries.append(index_entry(Run.model_validate(json.loads(path.read_text()))).model_dump())
    index = out_dir / "index.json"
    index.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n")
    return index
