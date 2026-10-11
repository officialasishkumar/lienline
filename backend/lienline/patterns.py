"""Mule signals: features computed by code from the ledger, one set per account.

The pattern analyst agent only *explains* these; it never decides whether one is present.
Thresholds live here as data so the decision letter can quote them.
"""

from __future__ import annotations

from datetime import timedelta

from lienline.models import SINKS, Account, Scenario, Signal, Txn
from lienline.trace import chronological

NEW_ACCOUNT_DAYS = 180
LINKED_COMPLAINTS = 3
PASS_THROUGH_RATIO = 0.9
RAPID_WINDOW = timedelta(minutes=30)
RAPID_SHARE = 0.5
RAPID_MIN_CREDIT = 10_000_00  # ignore small credits: ₹10,000 in paise


def signals_for(scenario: Scenario, account: Account) -> list[Signal]:
    """Every signal for one account, present or not, with the transactions that show it."""
    txns = chronological(scenario.transactions)
    ins = [t for t in txns if t.to == account.id]
    outs = [t for t in txns if t.from_ == account.id]
    return [
        Signal(id="registry_hit", label="On the I4C suspect registry", present=account.registry_hit,
               value=account.registry_hit, threshold="listed", refs=[account.id]),
        Signal(id="linked_complaints", label=f"{account.complaints_linked} linked NCRP complaints",
               present=account.complaints_linked >= LINKED_COMPLAINTS, value=account.complaints_linked,
               threshold=f">= {LINKED_COMPLAINTS}", refs=[account.id]),
        Signal(id="new_account", label=f"Account opened {account.kyc_age_days} days ago",
               present=account.kyc_age_days < NEW_ACCOUNT_DAYS, value=account.kyc_age_days,
               threshold=f"< {NEW_ACCOUNT_DAYS} days", refs=[account.id]),
        _pass_through(account, ins, outs),
        _rapid(account, ins, outs),
        _round_trip(account, ins, outs),
    ]


def _pass_through(account: Account, ins: list[Txn], outs: list[Txn]) -> Signal:
    """Share of all money available in the window (opening + credits) that left again."""
    available = account.opening_balance + sum(t.amount for t in ins)
    ratio = round(sum(t.amount for t in outs) / available, 3) if available else 0.0
    return Signal(id="pass_through", label=f"{ratio:.0%} of available funds passed straight through",
                  present=ratio >= PASS_THROUGH_RATIO, value=ratio, threshold=f">= {PASS_THROUGH_RATIO:.0%}",
                  refs=[account.id, *(t.id for t in outs)][:6])


def _rapid(account: Account, ins: list[Txn], outs: list[Txn]) -> Signal:
    """A large credit of which at least half leaves within 30 minutes."""
    for credit in ins:
        if credit.amount < RAPID_MIN_CREDIT:
            continue
        window = [t for t in outs if credit.ts <= t.ts <= credit.ts + RAPID_WINDOW]
        if sum(t.amount for t in window) >= credit.amount * RAPID_SHARE:
            minutes = int((window[-1].ts - credit.ts).total_seconds() // 60)
            return Signal(id="rapid_movement", label=f"Half of {credit.id} moved on within {minutes} minutes",
                          present=True, value=minutes, threshold=f">= {RAPID_SHARE:.0%} out within 30 min",
                          refs=[credit.id, *(t.id for t in window)])
    return Signal(id="rapid_movement", label="No large credit moved on within 30 minutes", present=False,
                  value=False, threshold=f">= {RAPID_SHARE:.0%} out within 30 min", refs=[account.id])


def _round_trip(account: Account, ins: list[Txn], outs: list[Txn]) -> Signal:
    """Money sent to a traced account and received back from it (layering)."""
    sent_to = {t.to: t for t in outs}
    for t in ins:
        if t.from_ in sent_to and t.from_ not in SINKS:
            back = sent_to[t.from_]
            return Signal(id="round_trip", label=f"Round trip with {t.from_}", present=True, value=True,
                          threshold="money sent to and received from the same account", refs=[back.id, t.id])
    return Signal(id="round_trip", label="No round trips", present=False, value=False,
                  threshold="money sent to and received from the same account", refs=[account.id])


def present(signals: list[Signal]) -> list[Signal]:
    return [s for s in signals if s.present]


def full_freeze_justified(signals: list[Signal]) -> bool:
    """Policy: at least two signals, one of which is a registry hit or >= 3 linked complaints."""
    found = {s.id for s in present(signals)}
    return len(found) >= 2 and bool(found & {"registry_hit", "linked_complaints"})
