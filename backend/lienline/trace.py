"""The tracing engine: how much of the victim's money is in each account now.

The ledger of every participating bank is replayed as one chronological stream. Each
account keeps one *taint pool* per tracing rule. A debit asks the pool how much of the
outgoing amount is the victim's money; that share is credited to the next account's pool,
so taint propagates hop by hop. Rules:

FIFO      Clayton's case. Credits form a queue (opening balance first); a debit spends the
          oldest money first.
LIFO      Credits form a stack; a debit spends the newest money first.
PRO_RATA  Rolling charge. Every debit carries taint in proportion to the tainted share of
          the balance at that moment.
LIBR      Lowest intermediate balance rule, with the account holder's own money deemed spent
          first (Re Hallett's Estate). The traceable amount can never exceed the lowest
          balance since it arrived, and later clean credits never replenish it.

A credit that a lot-based rule (FIFO/LIFO) later splits keeps its own tainted fraction: a
partial spend of one credit takes taint pro rata within that credit. All arithmetic is in
integer paise; shares are floored, so a pool never pays out more taint than it holds and the
total taint is conserved exactly.

Money leaving to ``CASH`` is cashed out; money leaving to ``EXT`` (an account outside the
traced banks) is untraced. Conservation: held + cashed_out + untraced == lost, per rule.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Protocol

from lienline.models import (
    CASH,
    EXTERNAL,
    POLICY_RULE,
    RULES,
    AccountTrace,
    Conservation,
    Edge,
    Outflow,
    Rule,
    RuleAmounts,
    Scenario,
    SeriesPoint,
    Trace,
    Txn,
)


class LedgerError(ValueError):
    """The ledger cannot be replayed (unknown account, overdraft, taint returned to the victim)."""


class TaintPool(Protocol):
    """One account's money under one tracing rule."""

    @property
    def tainted(self) -> int: ...

    def credit(self, amount: int, tainted: int) -> None: ...

    def debit(self, amount: int) -> int:
        """Remove ``amount`` and return how many of those paise are tainted."""
        ...


@dataclass
class _Lot:
    amount: int
    tainted: int


class LotPool:
    """FIFO (spend oldest lot first) or LIFO (spend newest lot first)."""

    def __init__(self, opening: int, newest_first: bool) -> None:
        self._lots: deque[_Lot] = deque([_Lot(opening, 0)] if opening else [])
        self._newest_first = newest_first

    @property
    def tainted(self) -> int:
        return sum(lot.tainted for lot in self._lots)

    def credit(self, amount: int, tainted: int) -> None:
        self._lots.append(_Lot(amount, tainted))

    def debit(self, amount: int) -> int:
        out = 0
        while amount:
            lot = self._lots[-1] if self._newest_first else self._lots[0]
            take = min(amount, lot.amount)
            share = lot.tainted * take // lot.amount  # exact when the whole lot is taken
            lot.amount -= take
            lot.tainted -= share
            out += share
            amount -= take
            if lot.amount == 0:
                self._lots.pop() if self._newest_first else self._lots.popleft()
        return out


class ProRataPool:
    """Rolling charge: each debit is tainted in proportion to the balance's tainted share."""

    def __init__(self, opening: int) -> None:
        self._balance = opening
        self._tainted = 0

    @property
    def tainted(self) -> int:
        return self._tainted

    def credit(self, amount: int, tainted: int) -> None:
        self._balance += amount
        self._tainted += tainted

    def debit(self, amount: int) -> int:
        share = self._tainted * amount // self._balance
        self._balance -= amount
        self._tainted -= share
        return share


class LibrPool:
    """Lowest intermediate balance: own money goes first; taint is capped by the balance."""

    def __init__(self, opening: int) -> None:
        self._balance = opening
        self._tainted = 0

    @property
    def tainted(self) -> int:
        return self._tainted

    def credit(self, amount: int, tainted: int) -> None:
        self._balance += amount
        self._tainted += tainted

    def debit(self, amount: int) -> int:
        self._balance -= amount
        share = max(0, self._tainted - self._balance)
        self._tainted -= share
        return share


def new_pool(rule: Rule, opening: int) -> TaintPool:
    match rule:
        case "FIFO":
            return LotPool(opening, newest_first=False)
        case "LIFO":
            return LotPool(opening, newest_first=True)
        case "PRO_RATA":
            return ProRataPool(opening)
        case "LIBR":
            return LibrPool(opening)


def chronological(txns: list[Txn]) -> list[Txn]:
    """Ledger order: by timestamp; ties keep the order the banks reported them in."""
    return sorted(txns, key=lambda t: t.ts)


def trace(scenario: Scenario, rules: tuple[Rule, ...] = RULES, policy_rule: Rule = POLICY_RULE) -> Trace:
    """Replay every ledger and attribute the victim's money to accounts under each rule."""
    victim = scenario.complaint.victim.account_id
    accounts = {a.id: a for a in scenario.accounts}
    txns = chronological(scenario.transactions)
    if not txns:
        raise LedgerError("no transactions to trace")

    traced = [a.id for a in scenario.accounts if a.id != victim]
    balance = {a.id: a.opening_balance for a in scenario.accounts}
    pools = {acc: {r: new_pool(r, accounts[acc].opening_balance) for r in rules} for acc in traced}
    series = {acc: [SeriesPoint(ts=txns[0].ts, txn=None, balance=balance[acc], tainted={r: 0 for r in rules})]
              for acc in traced}
    outflows: dict[str, list[Outflow]] = {acc: [] for acc in traced}
    edges: list[Edge] = []
    lost = 0
    sunk = {sink: {r: 0 for r in rules} for sink in (CASH, EXTERNAL)}

    for t in txns:
        for end in (t.from_, t.to):
            if end not in accounts and end not in sunk:
                raise LedgerError(f"{t.id}: unknown endpoint {end}")
        if t.tainted_origin and t.from_ != victim:
            raise LedgerError(f"{t.id}: only the victim's own debits can originate taint")

        if t.from_ in balance and balance[t.from_] < t.amount:
            raise LedgerError(f"{t.id}: {t.from_} would be overdrawn")

        # How much of this transfer is the victim's money, per rule.
        if t.tainted_origin:
            share = {r: t.amount for r in rules}
            lost += t.amount
        elif t.from_ in pools:
            share = {r: pools[t.from_][r].debit(t.amount) for r in rules}
        else:
            share = {r: 0 for r in rules}

        if t.from_ in balance:
            balance[t.from_] -= t.amount
        if t.to in balance:
            balance[t.to] += t.amount

        if t.to in pools:
            for r in rules:
                pools[t.to][r].credit(t.amount, share[r])
        elif t.to in sunk:
            for r in rules:
                sunk[t.to][r] += share[r]
        elif any(share.values()):
            raise LedgerError(f"{t.id}: taint returned to the victim is not modelled")

        edges.append(Edge(txn=t.id, from_=t.from_, to=t.to, amount=t.amount, tainted=share))
        if t.from_ in pools:
            outflows[t.from_].append(Outflow(txn=t.id, to=t.to, amount=t.amount, tainted=share))
        for acc in {t.from_, t.to} & pools.keys():
            series[acc].append(SeriesPoint(ts=t.ts, txn=t.id, balance=balance[acc],
                                           tainted={r: pools[acc][r].tainted for r in rules}))

    held = {r: sum(pools[acc][r].tainted for acc in traced) for r in rules}
    by_rule_conservation = {
        r: Conservation(lost=lost, held=held[r], cashed_out=sunk[CASH][r], untraced=sunk[EXTERNAL][r]) for r in rules
    }
    account_traces = {
        acc: AccountTrace(
            by_rule=_held(pools[acc], rules), balance_now=balance[acc], series=series[acc], outflows=outflows[acc],
        )
        for acc in traced
    }
    return Trace(
        as_of=scenario.as_of, rules=list(rules), policy_rule=policy_rule, accounts=account_traces, edges=edges,
        conservation=by_rule_conservation[policy_rule], conservation_by_rule=by_rule_conservation,
    )


def _held(pools: dict[Rule, TaintPool], rules: tuple[Rule, ...]) -> RuleAmounts:
    return {r: pools[r].tainted for r in rules}
