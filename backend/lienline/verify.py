"""The verifier: an independent replay of a finished run.

It deliberately shares no code with ``trace.py`` or ``decide.py``. It replays the raw ledgers
itself and recomputes the policy rule (LIBR) with a closed form instead of the tracer's
step-by-step pool. For an account with cumulative tainted credits ``D`` and, at each debit k,
balance-after ``B_k`` and cumulative tainted credits ``D_k``:

    held = D + min(0, min_k (B_k - D_k))

which is the unrolled form of "taint never exceeds the lowest balance since it arrived, own
money is spent first". The other rules are checked by invariants (bounds, per-account flow
balance and conservation) rather than recomputed.

Run it on recorded files:  ``uv run python -m lienline.verify ../web/public/runs/*.json``
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from lienline.models import CASH, EXTERNAL, Account, AccountTrace, Check, Decision, Edge, Flag, Run, Txn, Verification
from lienline.money import inr

_AMOUNT = re.compile(r"(?:₹|\bRs\.?|\bINR)\s*([0-9][0-9,]*(?:\.[0-9]+)?)(\s*(?:crores?|lakhs?|lacs?)\b)?", re.I)
_UTR = re.compile(r"(?<!\d)\d{12}(?!\d)")
_MASKED = re.compile(r"XXXX\d{4}")
_SCALE = {"crore": 10**7, "lakh": 10**5, "lac": 10**5}


def verify(run: Run) -> Verification:
    """Every check over the run; ``passed`` only if all pass."""
    libr = replay_libr(run.accounts, run.transactions, run.complaint.victim.account_id)
    checks = [
        _ledger_replay(run),
        _policy_replay(run, libr),
        _taint_bounds(run),
        _flow_balance(run),
        _conservation(run, libr),
        _decisions(run, libr),
        _letters(run),
        _citations(run),
        _clocks(run),
    ]
    return Verification(passed=all(c.ok for c in checks), checks=checks)


# ---------------------------------------------------------------- independent replay


def _balances(run: Run) -> tuple[dict[str, int], list[str]]:
    bal = {a.id: a.opening_balance for a in run.accounts}
    problems = []
    for t in sorted(run.transactions, key=lambda t: t.ts):
        if t.from_ in bal:
            bal[t.from_] -= t.amount
            if bal[t.from_] < 0:
                problems.append(f"{t.from_} overdrawn by {t.id}")
        if t.to in bal:
            bal[t.to] += t.amount
    return bal, problems


class _Libr:
    """Closed-form LIBR state for one account (see module docstring)."""

    def __init__(self, opening: int) -> None:
        self.balance = opening
        self.credited = 0  # D: cumulative tainted credits
        self.low: int | None = None  # min over debits of (balance after - D at that time)

    @property
    def held(self) -> int:
        return self.credited + min(0, self.low if self.low is not None else 0)

    def credit(self, amount: int, tainted: int) -> None:
        self.balance += amount
        self.credited += tainted

    def debit(self, amount: int) -> int:
        before = self.held
        self.balance -= amount
        gap = self.balance - self.credited
        self.low = gap if self.low is None else min(self.low, gap)
        return before - self.held


@dataclass
class LibrReplay:
    held: dict[str, int]  # account -> traceable paise now
    edge: dict[str, int]  # txn -> tainted paise it carried
    sink: dict[str, int]  # CASH / EXT -> tainted paise that left
    lost: int


def replay_libr(accounts: list[Account], transactions: list[Txn], victim: str) -> LibrReplay:
    """LIBR over the raw ledgers, hop by hop, using the closed form."""
    ids = {a.id for a in accounts}
    state = {a.id: _Libr(a.opening_balance) for a in accounts if a.id != victim}
    edge: dict[str, int] = {}
    sink: dict[str, int] = defaultdict(int)
    lost = 0
    for t in sorted(transactions, key=lambda t: t.ts):
        if t.tainted_origin:
            share = t.amount
            lost += t.amount
        elif t.from_ in state:
            share = state[t.from_].debit(t.amount)
        else:
            share = 0
        if t.to in state:
            state[t.to].credit(t.amount, share)
        elif t.to not in ids:
            sink[t.to] += share
        edge[t.id] = share
    return LibrReplay({k: s.held for k, s in state.items()}, edge, dict(sink), lost)


# ---------------------------------------------------------------- checks


def _check(name: str, problems: list[str], ok_detail: str) -> Check:
    if problems:
        shown = "; ".join(problems[:4]) + (f" (+{len(problems) - 4} more)" if len(problems) > 4 else "")
        return Check(name=name, ok=False, detail=shown)
    return Check(name=name, ok=True, detail=ok_detail)


def _ledger_replay(run: Run) -> Check:
    bal, problems = _balances(run)
    txns = {t.id: t for t in run.transactions}
    for e in run.trace.edges:
        t = txns.get(e.txn)
        if t is None or (t.from_, t.to, t.amount) != (e.from_, e.to, e.amount):
            problems.append(f"edge {e.txn} does not match the ledger")
    if len(run.trace.edges) != len(txns):
        problems.append(f"{len(run.trace.edges)} edges for {len(txns)} transactions")
    for acc, at in run.trace.accounts.items():
        if bal.get(acc) != at.balance_now:
            problems.append(f"{acc} balance {at.balance_now} but ledger replays to {bal.get(acc)}")
        if at.series and at.series[-1].balance != at.balance_now:
            problems.append(f"{acc} series ends at {at.series[-1].balance}, not {at.balance_now}")
    return _check("ledger_replay", problems,
                  f"{len(run.transactions)} transactions replayed; no overdrafts; every balance matches")


def _policy_replay(run: Run, libr: LibrReplay) -> Check:
    rule = run.trace.policy_rule
    problems = []
    if rule != "LIBR":
        problems.append(f"policy rule is {rule}, verifier replays LIBR")
    for e in run.trace.edges:
        if e.tainted.get("LIBR") != libr.edge.get(e.txn):
            problems.append(f"{e.txn} carries {e.tainted.get('LIBR')} but replay gives {libr.edge.get(e.txn)}")
    for acc, at in run.trace.accounts.items():
        if at.by_rule.get("LIBR") != libr.held.get(acc):
            problems.append(f"{acc} holds {at.by_rule.get('LIBR')} but replay gives {libr.held.get(acc)}")
    return _check("policy_rule_replay", problems,
                  f"LIBR recomputed in closed form for {len(libr.held)} accounts and {len(libr.edge)} hops")


def _taint_bounds(run: Run) -> Check:
    problems = []
    for acc, at in run.trace.accounts.items():
        for p in at.series:
            for r, v in p.tainted.items():
                if not 0 <= v <= p.balance:
                    problems.append(f"{acc} {r} tainted {v} outside [0, {p.balance}] at {p.txn}")
        if at.series and at.series[-1].tainted != at.by_rule:
            problems.append(f"{acc} final series point differs from by_rule")
    return _check("taint_bounds", problems, "0 <= tainted <= balance at every point, under every rule")


def _flow_balance(run: Run) -> Check:
    problems = []
    net: dict[tuple[str, str], int] = defaultdict(int)
    for e in run.trace.edges:
        for r, v in e.tainted.items():
            net[(e.to, r)] += v
            net[(e.from_, r)] -= v
    for acc, at in run.trace.accounts.items():
        for r, held in at.by_rule.items():
            if net[(acc, r)] != held:
                problems.append(f"{acc} {r}: taint in - out = {net[(acc, r)]}, but holds {held}")
    return _check("flow_balance", problems, "for every account and rule, tainted in - tainted out = held")


def _conservation(run: Run, libr: LibrReplay) -> Check:
    problems = []
    lost = run.complaint.amount_lost
    if libr.lost != lost:
        problems.append(f"ledger shows {libr.lost} leaving the victim, complaint says {lost}")
    for r, c in run.trace.conservation_by_rule.items():
        if c.held + c.cashed_out + c.untraced != c.lost or c.lost != lost:
            problems.append(f"{r}: {c.held} + {c.cashed_out} + {c.untraced} != {lost}")
        if c.held != sum(at.by_rule[r] for at in run.trace.accounts.values()):
            problems.append(f"{r}: held total differs from the per-account amounts")
    c = run.trace.conservation
    replay = (sum(libr.held.values()), libr.sink.get(CASH, 0), libr.sink.get(EXTERNAL, 0))
    if (c.held, c.cashed_out, c.untraced) != replay:
        problems.append(f"policy conservation {c.held}/{c.cashed_out}/{c.untraced} but replay gives {replay}")
    return _check("conservation", problems,
                  f"held {c.held} + cashed out {c.cashed_out} + untraced {c.untraced} = lost {lost} paise")


def _decisions(run: Run, libr: LibrReplay) -> Check:
    problems = []
    accounts = {a.id: a for a in run.accounts}
    decided = {d.account_id for d in run.decisions}
    for f in run.notice.flagged:
        if f.account_id not in decided:
            problems.append(f"flagged account {f.account_id} has no decision")
    for d in run.decisions:
        at = run.trace.accounts.get(d.account_id)
        if at is None:
            problems.append(f"decision for untraced account {d.account_id}")
            continue
        traceable = libr.held[d.account_id]
        if d.amount > at.balance_now or d.current_hold > at.balance_now:
            problems.append(f"{d.account_id}: amount or hold exceeds balance {at.balance_now}")
        if d.released_by_change != d.current_hold - d.amount:
            problems.append(f"{d.account_id}: released_by_change is not current_hold - amount")
        if (d.range.min, d.range.max) != (min(at.by_rule.values()), max(at.by_rule.values())):
            problems.append(f"{d.account_id}: range does not span the four rules")
        if d.action == "lien" and not 0 < d.amount == traceable:
            problems.append(f"{d.account_id}: lien {d.amount} but traceable is {traceable}")
        if d.action == "release" and (d.amount != 0 or traceable != 0):
            problems.append(f"{d.account_id}: release with {traceable} still traceable")
        if d.action == "full_freeze":
            acc = accounts[d.account_id]
            if d.amount != at.balance_now:
                problems.append(f"{d.account_id}: full freeze must hold the whole balance")
            if not (acc.registry_hit or acc.complaints_linked >= 3):
                problems.append(f"{d.account_id}: full freeze without a registry hit or 3 linked complaints")
    return _check("decisions", problems,
                  f"{len(run.decisions)} decisions: liens equal replayed LIBR, none exceeds its balance")


def amounts_in(text: str) -> list[int]:
    """Every rupee figure in a text, in paise ("₹2.51 crore" -> 2510000000)."""
    out = []
    for num, scale in _AMOUNT.findall(text):
        value = Decimal(num.replace(",", ""))
        if scale:
            word = scale.strip().lower().rstrip("s")
            value *= _SCALE[word]
        out.append(int(value * 100))
    return out


def allowed_amounts(d: Decision, at: AccountTrace, edges: list[Edge], flags: list[Flag], lost: int) -> set[int]:
    """The only rupee figures a letter about this decision may state: the decision's own numbers, the
    account's traced amounts, the notice's flagged amount, the loss, and the transfers its reasons cite."""
    allowed = {d.amount, d.current_hold, abs(d.released_by_change), at.balance_now, d.range.min, d.range.max, lost,
               *at.by_rule.values()}
    allowed |= {f.amount for f in flags if f.account_id == d.account_id}
    cited = {ref for reason in d.reasons for ref in reason.refs}
    for e in edges:
        if e.txn in cited:
            allowed |= {e.amount, *e.tainted.values()}
    return allowed


def figure_problems(text: str, allowed: set[int], utrs: set[str], masked: set[str]) -> tuple[list[str], int]:
    """Problems with the figures in one letter, and how many figures were checked."""
    problems, n = [], 0
    for paise in amounts_in(text):
        n += 1
        if paise not in allowed:
            problems.append(f"₹ figure {inr(paise)} matches no decision or traced amount")
    for utr in _UTR.findall(text):
        n += 1
        if utr not in utrs:
            problems.append(f"UTR {utr} is not in any ledger")
    for m in _MASKED.findall(text):
        n += 1
        if m not in masked:
            problems.append(f"account {m} is not in the case")
    return problems, n


def _letters(run: Run) -> Check:
    problems = []
    decided = {d.account_id for d in run.decisions}
    utrs = {t.utr for t in run.transactions}
    masked = {a.masked for a in run.accounts}
    for letter in run.letters:
        if letter.account_id not in decided:
            problems.append(f"{letter.id} is about {letter.account_id}, which has no decision")
            continue
        d = next(x for x in run.decisions if x.account_id == letter.account_id)
        allowed = allowed_amounts(d, run.trace.accounts[d.account_id], run.trace.edges, run.notice.flagged,
                                  run.complaint.amount_lost)
        found, n = figure_problems(f"{letter.subject}\n{letter.body}", allowed, utrs, masked)
        problems += [f"{letter.id}: {p}" for p in found]
        if letter.verified and n != letter.numbers_checked:
            problems.append(f"{letter.id}: claims {letter.numbers_checked} figures checked, found {n}")
    total = sum(x.numbers_checked for x in run.letters)
    return _check("letters", problems, f"{total} figures in {len(run.letters)} letters match the decisions")


def _citations(run: Run) -> Check:
    known = ({a.id for a in run.accounts} | {t.id for t in run.transactions} | {x.id for x in run.letters}
             | {c.id for c in run.clocks} | {CASH, EXTERNAL})
    problems = []

    def need(where: str, refs: Iterable[str]) -> None:
        problems.extend(f"{where} cites unknown {r}" for r in refs if r not in known)

    for i, ev in enumerate(run.events):
        need(f"event {i} ({ev.agent})", ev.refs)
        for claim in ev.data.get("claims", []):
            if claim.get("accepted"):
                need(f"accepted claim in event {i}", claim.get("refs", []))
    for d in run.decisions:
        for reason in d.reasons:
            need(f"decision {d.account_id}", reason.refs)
    n = sum(len(ev.refs) for ev in run.events) + sum(len(r.refs) for d in run.decisions for r in d.reasons)
    return _check("citations", problems, f"{n} citations in events and reasons all resolve to the case")


def _clocks(run: Run) -> Check:
    problems = []
    holds = {d.account_id: d for d in run.decisions}
    for c in run.clocks:
        if c.due < c.start:
            problems.append(f"{c.id} is due before it starts")
        if c.due > c.start:
            if c.status == "running" and run.trace.as_of > c.due:
                problems.append(f"{c.id} is past due but marked running")
            if c.status == "breached" and run.trace.as_of <= c.due:
                problems.append(f"{c.id} is marked breached before its due date")
        elif c.account_id in holds:
            d = holds[c.account_id]
            if (c.status == "met") != (d.current_hold <= d.amount):
                problems.append(f"{c.id} status does not match the hold")
    return _check("clocks", problems, f"{len(run.clocks)} clocks consistent with their dates and holds")


def main(paths: list[str]) -> int:
    failed = 0
    for p in paths:
        run = Run.model_validate(json.loads(Path(p).read_text()))
        result = verify(run)
        failed += not result.passed
        print(f"{'PASS' if result.passed else 'FAIL'} {p}")
        for c in result.checks:
            print(f"  {'ok ' if c.ok else 'BAD'} {c.name}: {c.detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
