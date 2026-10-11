"""The decider: one proportionate action per account, by code policy.

Policy (SPEC):
* lien        the traceable amount under the policy rule (LIBR, the legal tracing standard);
* full_freeze only with >= 2 mule signals including a registry hit or >= 3 linked complaints;
* release     when nothing is traceable under the policy rule and a full freeze is not justified.

Every reason cites the transaction and account ids it rests on.
"""

from __future__ import annotations

from itertools import pairwise

from lienline.clocks import MP_HC, RAJ_HC
from lienline.models import (
    RULES,
    AccountTrace,
    Action,
    AmountRange,
    Confidence,
    Decision,
    Reason,
    Rule,
    Scenario,
    SeriesPoint,
    Signal,
    Trace,
)
from lienline.money import inr
from lienline.patterns import full_freeze_justified, present


def decide(scenario: Scenario, trace: Trace, signals: dict[str, list[Signal]]) -> list[Decision]:
    """Decisions for every account that is on hold or holds traceable money."""
    flagged = scenario.flagged_ids()
    out = []
    for acc_id, at in trace.accounts.items():
        if acc_id not in flagged and not any(at.by_rule.values()):
            continue
        out.append(_decide_one(acc_id, at, trace, signals[acc_id], hold=at.balance_now if acc_id in flagged else 0))
    return out


def _decide_one(acc_id: str, at: AccountTrace, trace: Trace, sigs: list[Signal], hold: int) -> Decision:
    rule = trace.policy_rule
    traceable = at.by_rule[rule]
    action: Action
    if full_freeze_justified(sigs):
        action, amount = "full_freeze", at.balance_now
    elif traceable > 0:
        action, amount = "lien", traceable
    else:
        action, amount = "release", 0

    reasons = [_trail_reason(acc_id, at, trace, rule, action)]
    if action == "full_freeze":
        reasons.append(_freeze_reason(acc_id, sigs, traceable, rule))
    else:
        reasons += _signal_reasons(acc_id, sigs)
    if hold > amount:
        reasons.append(Reason(
            text=f"The current hold of {inr(hold)} covers the whole balance. {MP_HC} and {RAJ_HC} limit a hold to "
                 f"the identifiable disputed amount, so {inr(hold - amount)} is released.",
            refs=[acc_id]))
    reasons.append(_rules_reason(acc_id, at, rule))

    lo, hi = min(at.by_rule.values()), max(at.by_rule.values())
    return Decision(account_id=acc_id, action=action, amount=amount, current_hold=hold,
                    released_by_change=hold - amount, reasons=reasons,
                    confidence=_confidence(action, sigs, lo, hi), range=AmountRange(min=lo, max=hi))


def _trail_reason(acc_id: str, at: AccountTrace, trace: Trace, rule: Rule, action: Action) -> Reason:
    """Where the victim's money came in, and what (under the policy rule) is still here."""
    inflows = [e for e in trace.edges if e.to == acc_id and any(e.tainted.values())]
    came = ", ".join(f"{e.txn} ({inr(e.tainted[rule])} of {inr(e.amount)} from {e.from_})" for e in inflows)
    refs = [*(e.txn for e in inflows), *(e.from_ for e in inflows), acc_id]
    traceable = at.by_rule[rule]
    if traceable == 0:
        return Reason(text=f"Nothing is traceable here under {rule}: {came or 'no tainted credit'} carried "
                           f"{inr(0)} of the victim's money because the payer's own funds covered each payment.",
                      refs=refs)
    received = sum(e.tainted[rule] for e in inflows)
    if traceable == received:
        return Reason(text=f"{inr(traceable)} of the victim's money is identifiable here under {rule}: it arrived via "
                           f"{came}, and the balance never fell below it afterwards.", refs=refs)
    cap = _last_cap(at, rule)
    cap_txt = f" fell to {inr(cap.balance)} after {cap.txn}, which caps" if cap and cap.txn else " caps"
    if cap and cap.txn:
        refs.append(cap.txn)
    return Reason(text=f"The victim's money arrived via {came}. The balance{cap_txt} what can still be traced: "
                       f"{inr(traceable)} under {rule} (lowest intermediate balance).", refs=refs)


def _last_cap(at: AccountTrace, rule: Rule) -> SeriesPoint | None:
    """The last point where the policy rule's tainted amount went down: the binding low balance."""
    last = None
    for prev, point in pairwise(at.series):
        if point.tainted[rule] < prev.tainted[rule]:
            last = point
    return last


def _freeze_reason(acc_id: str, sigs: list[Signal], traceable: int, rule: Rule) -> Reason:
    found = present(sigs)
    return Reason(
        text=f"Full freeze justified by {len(found)} mule signals: {'; '.join(s.label for s in found)}. The amount "
             f"traceable from this complaint alone is {inr(traceable)} under {rule}; the whole balance is held "
             f"because of these signals, not this complaint's amount.",
        refs=sorted({acc_id, *(r for s in found for r in s.refs)}))


def _signal_reasons(acc_id: str, sigs: list[Signal]) -> list[Reason]:
    found = present(sigs)
    if not found:
        return []
    return [Reason(
        text=f"Mule signals present ({'; '.join(s.label for s in found)}), but no registry hit and fewer than 3 "
             f"linked complaints, so a full freeze is not justified.",
        refs=sorted({acc_id, *(r for s in found for r in s.refs)}))]


def _rules_reason(acc_id: str, at: AccountTrace, rule: Rule) -> Reason:
    others = ", ".join(f"{r} {inr(at.by_rule[r])}" for r in RULES if r != rule)
    if len(set(at.by_rule.values())) == 1:
        return Reason(text=f"All four tracing rules agree on {inr(at.by_rule[rule])}.", refs=[acc_id])
    return Reason(
        text=f"Other tracing rules give {others}. {rule} is used because it is the accepted standard for mixed "
             "funds: it never counts the holder's later, clean credits as the victim's money.",
        refs=[acc_id])


def _confidence(action: Action, sigs: list[Signal], lo: int, hi: int) -> Confidence:
    if action == "full_freeze":
        return "high" if len(present(sigs)) >= 3 else "medium"
    spread = hi - lo
    if spread * 100 <= hi:  # rules agree to within 1%
        return "high"
    return "medium" if spread * 4 <= hi else "low"
