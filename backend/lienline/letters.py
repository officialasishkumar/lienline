"""Which letters a case needs, the facts each may state, and the plain template used when no
model is available (or when the model's draft fails the number check twice).

A letter may state only figures that appear in its facts; ``verify.allowed_amounts`` enforces it.
"""

from __future__ import annotations

from dataclasses import dataclass

from lienline.clocks import MP_HC, RAJ_HC
from lienline.models import Decision, LetterKind, Scenario, Signal, Trace
from lienline.money import inr
from lienline.patterns import present

PURPOSE: dict[LetterKind, str] = {
    "lien_instruction": "Instruct the branch to replace the whole-account freeze with a lien of only the traceable "
                        "amount, and to release the rest.",
    "release_notice": "Instruct the branch to remove the hold completely because nothing is traceable.",
    "full_freeze_justification": "Record why the whole balance stays frozen, citing the mule signals.",
    "grievance_reply": "Reply to the account holder's grievance with the outcome and what happens next.",
}

ACTION_LETTER: dict[str, LetterKind] = {
    "lien": "lien_instruction", "release": "release_notice", "full_freeze": "full_freeze_justification",
}

LEGAL_BASIS = f"{MP_HC}; {RAJ_HC}: a hold is limited to the identifiable disputed amount"


@dataclass(frozen=True)
class LetterSpec:
    id: str
    kind: LetterKind
    to: str
    bank: str
    masked: str
    decision: Decision
    account_line: str
    reference: str
    trail: list[str]  # one line per credit that carried the victim's money
    signals: str | None  # full freeze only
    traceable_alone: str | None  # full freeze only
    grievance_date: str | None  # grievance replies only

    @property
    def account_id(self) -> str:
        return self.decision.account_id

    @property
    def facts(self) -> list[str]:
        """What the drafter model is told, one fact per line."""
        d = self.decision
        hold = f"Current hold: {inr(d.current_hold)} (the whole balance)" if d.current_hold else "Current hold: none"
        decision = {
            "lien": f"Decision: lien of {inr(d.amount)}, the amount traceable under the lowest intermediate balance "
                    f"rule; release {inr(d.released_by_change)} from the hold",
            "release": f"Decision: release the hold of {inr(d.current_hold)} in full; traceable amount is {inr(0)}",
            "full_freeze": f"Decision: keep the full freeze of the balance of {inr(d.amount)}",
        }[d.action]
        lines = [self.account_line, self.reference, hold, *self.trail, decision, self.signals, self.traceable_alone,
                 f"Legal basis: {LEGAL_BASIS}",
                 f"Grievance received on {self.grievance_date}" if self.grievance_date else None]
        return [x for x in lines if x]


def plan_letters(scenario: Scenario, trace: Trace, decisions: list[Decision],
                 signals: dict[str, list[Signal]]) -> list[LetterSpec]:
    """One instruction per decision, plus a reply to every grievance."""
    grievances = {g.account_id: g for g in scenario.grievances}
    utrs = {t.id: t.utr for t in scenario.transactions}
    rule = trace.policy_rule
    specs: list[LetterSpec] = []
    for d in decisions:
        acc = scenario.account(d.account_id)
        bank = scenario.bank(acc.bank).name
        inflows = [e for e in trace.edges if e.to == d.account_id and any(e.tainted.values())]
        freeze = d.action == "full_freeze"
        kinds: list[LetterKind] = [ACTION_LETTER[d.action]]
        if d.account_id in grievances:
            kinds.append("grievance_reply")
        for kind in kinds:
            g = grievances.get(d.account_id) if kind == "grievance_reply" else None
            specs.append(LetterSpec(
                id=f"L{len(specs) + 1}", kind=kind, decision=d, bank=bank, masked=acc.masked,
                to=acc.holder if g else f"Branch Manager, {bank}",
                account_line=f"Account {acc.masked}, {acc.holder}, {bank}",
                reference=f"NCRP acknowledgement {scenario.complaint.ack_no}; notice under Section "
                          f"{scenario.notice.section} dated {scenario.notice.issued_at:%d %b %Y} from "
                          f"{scenario.complaint.io}, {scenario.complaint.police_station}",
                trail=[f"Credit by UTR {utrs[e.txn]}: {inr(e.amount)}, of which {inr(e.tainted[rule])} is "
                       f"traceable to the complaint under {rule}" for e in inflows],
                signals=(f"Mule signals: {'; '.join(s.label for s in present(signals[d.account_id]))}"
                         if freeze else None),
                traceable_alone=(f"Traceable to this complaint alone under {rule}: "
                                 f"{inr(trace.accounts[d.account_id].by_rule[rule])}") if freeze else None,
                grievance_date=f"{g.received_at:%d %b %Y}" if g else None,
            ))
    return specs


def template(spec: LetterSpec) -> tuple[str, str]:
    """(subject, body) stating only the spec's own figures."""
    d = spec.decision
    head = f"Ref: {spec.reference}.\n\n"
    trail = "\n".join(f"- {line}" for line in spec.trail)
    trail = f"The complainant's money reached the account as follows:\n{trail}\n\n" if trail else ""
    sign = f"\n\nNodal Officer, {spec.bank}"
    match spec.kind:
        case "lien_instruction":
            subject = f"Modify hold on A/c {spec.masked}: lien {inr(d.amount)}, release {inr(d.released_by_change)}"
            body = (f"{head}Please replace the existing hold of {inr(d.current_hold)} on A/c {spec.masked} with a "
                    f"lien of {inr(d.amount)}, the amount traceable to the complaint under the lowest intermediate "
                    f"balance rule, and release {inr(d.released_by_change)} for normal operation.\n\n{trail}"
                    f"Legal basis: {LEGAL_BASIS}.\n\nPlease confirm compliance and inform the account holder.")
        case "release_notice":
            subject = f"Release hold on A/c {spec.masked} in full ({inr(d.released_by_change)})"
            body = (f"{head}Tracing the complainant's money through every participating bank's ledger finds "
                    f"{inr(0)} traceable to A/c {spec.masked}. Please remove the hold of {inr(d.current_hold)} in "
                    f"full and restore normal operation.\n\n{trail}Legal basis: {LEGAL_BASIS}.")
        case "full_freeze_justification":
            subject = f"Full freeze retained on A/c {spec.masked} ({inr(d.amount)}): reasons recorded"
            body = (f"{head}The full freeze of {inr(d.amount)} on A/c {spec.masked} is retained.\n\n"
                    f"{spec.signals}.\n{spec.traceable_alone}. The whole balance is held because of these signals, "
                    f"not this complaint's amount.\n\n{trail}These reasons are recorded so the freeze can be "
                    f"reviewed against the rule that {LEGAL_BASIS.split(': ', 1)[1]}.")
        case "grievance_reply":
            subject = f"Your grievance of {spec.grievance_date} about A/c {spec.masked}"
            outcome = {
                "lien": f"the hold is reduced to a lien of {inr(d.amount)}, the amount traceable to the complaint, "
                        f"and {inr(d.released_by_change)} is released",
                "release": f"nothing is traceable to the complaint, and the hold of {inr(d.current_hold)} is "
                           f"removed in full",
                "full_freeze": "the full freeze is retained because the account shows several mule signals; the "
                               "reasons are recorded and you may seek review from the investigating officer",
            }[d.action]
            body = (f"Dear {spec.to},\n\n{head}We have examined your grievance against the hold on A/c "
                    f"{spec.masked}. After tracing the complainant's money, {outcome}.\n\n{trail}"
                    "The decision is subject to approval by the nodal officer and any direction from the "
                    "investigating officer.")
    return subject, body + sign
