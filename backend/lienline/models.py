"""Data model for a LienLine case and the run JSON the web app replays.

Every amount is an integer number of paise. Field names follow the run-JSON contract in
SPEC.md; `from` is a Python keyword, so transactions expose it as `from_` and serialise it
with its alias. Always dump with `by_alias=True` (see `Run.to_json`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, PositiveInt

Paise = int

Rule = Literal["FIFO", "LIFO", "PRO_RATA", "LIBR"]
RULES: tuple[Rule, ...] = ("FIFO", "LIFO", "PRO_RATA", "LIBR")
POLICY_RULE: Rule = "LIBR"

# Transaction endpoints that are not accounts in any participating bank's ledger.
CASH = "CASH"  # cash withdrawn at an ATM or branch: the money has left the banking system
EXTERNAL = "EXT"  # an account outside the traced banks: the trail goes cold here
SINKS = frozenset({CASH, EXTERNAL})

Role = Literal["victim", "mule_l1", "mule_l2", "cashout", "merchant", "innocent"]
Channel = Literal["UPI", "IMPS", "NEFT", "RTGS", "ATM", "POS", "CASH"]
Action = Literal["lien", "full_freeze", "release"]
Confidence = Literal["high", "medium", "low"]
AgentName = Literal[
    "Intake", "Tracer", "Pattern analyst", "Victim's advocate", "Account holder's advocate",
    "Decider", "Clock keeper", "Drafter", "Verifier", "Nodal officer",
]
EventKind = Literal["model", "code", "human"]
EventType = Literal["start", "message", "tool", "check", "result", "debate", "letter", "approval"]
LetterKind = Literal["lien_instruction", "release_notice", "grievance_reply", "full_freeze_justification"]
ClockStatus = Literal["running", "met", "breached"]


class Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


# ---------------------------------------------------------------- case inputs


class Victim(Model):
    name: str
    account_id: str


class Complaint(Model):
    ack_no: str
    filed_at: datetime
    victim: Victim
    amount_lost: PositiveInt
    channel: Channel
    narrative: str
    police_station: str
    io: str


class Flag(Model):
    account_id: str
    amount: PositiveInt


class Notice(Model):
    text: str
    issued_at: datetime
    section: str
    flagged: list[Flag]


class Bank(Model):
    id: str
    name: str
    kind: Literal["public", "private", "small_finance", "regional_rural", "cooperative", "payments"]


class Account(Model):
    id: str
    bank: str
    masked: str
    holder: str
    kind: Literal["savings", "current", "merchant"]
    role: Role
    kyc_age_days: NonNegativeInt
    opening_balance: NonNegativeInt
    complaints_linked: NonNegativeInt
    registry_hit: bool


class Txn(Model):
    id: str
    utr: str
    ts: datetime
    from_: str = Field(alias="from")
    to: str
    amount: PositiveInt
    channel: Channel
    tainted_origin: bool
    note: str


class Grievance(Model):
    """An account holder's grievance against a hold, received by the bank."""

    account_id: str
    received_at: datetime
    forwarded_at: datetime | None
    text: str


class Scenario(Model):
    """Everything a bank nodal officer has in hand before LienLine runs."""

    case_id: str
    title: str
    summary: str
    as_of: datetime
    complaint: Complaint
    notice: Notice
    banks: list[Bank]
    accounts: list[Account]
    transactions: list[Txn]
    grievances: list[Grievance]

    def account(self, account_id: str) -> Account:
        return next(a for a in self.accounts if a.id == account_id)

    def bank(self, bank_id: str) -> Bank:
        return next(b for b in self.banks if b.id == bank_id)

    def txn(self, txn_id: str) -> Txn:
        return next(t for t in self.transactions if t.id == txn_id)

    def flagged_ids(self) -> set[str]:
        return {f.account_id for f in self.notice.flagged}


# ---------------------------------------------------------------- trace

RuleAmounts = dict[Rule, NonNegativeInt]


class SeriesPoint(Model):
    ts: datetime
    txn: str | None  # None for the opening point
    balance: NonNegativeInt
    tainted: RuleAmounts


class Outflow(Model):
    txn: str
    to: str
    amount: PositiveInt
    tainted: RuleAmounts


class AccountTrace(Model):
    by_rule: RuleAmounts  # traceable tainted paise held now
    balance_now: NonNegativeInt
    series: list[SeriesPoint]
    outflows: list[Outflow]


class Edge(Model):
    txn: str
    from_: str = Field(alias="from")
    to: str
    amount: PositiveInt
    tainted: RuleAmounts


class Conservation(Model):
    lost: NonNegativeInt
    held: NonNegativeInt
    cashed_out: NonNegativeInt
    untraced: NonNegativeInt


class Trace(Model):
    as_of: datetime
    rules: list[Rule]
    policy_rule: Rule
    accounts: dict[str, AccountTrace]
    edges: list[Edge]
    conservation: Conservation  # under policy_rule
    conservation_by_rule: dict[Rule, Conservation]


# ---------------------------------------------------------------- patterns, decisions, clocks


class Signal(Model):
    """One mule indicator computed by code for one account."""

    id: Literal["registry_hit", "linked_complaints", "new_account", "pass_through", "rapid_movement", "round_trip"]
    label: str
    present: bool
    value: float | int | bool
    threshold: str
    refs: list[str]


class Reason(Model):
    text: str
    refs: list[str]


class AmountRange(Model):
    min: NonNegativeInt
    max: NonNegativeInt


class Decision(Model):
    account_id: str
    action: Action
    amount: NonNegativeInt
    current_hold: NonNegativeInt
    released_by_change: int  # current_hold - amount; negative means a new hold is added
    reasons: list[Reason]
    confidence: Confidence
    range: AmountRange


class Clock(Model):
    id: str
    account_id: str
    label: str
    start: datetime
    due: datetime
    rule: str
    source: str
    status: ClockStatus


# ---------------------------------------------------------------- run output


class Event(Model):
    t: float
    agent: AgentName
    kind: EventKind
    type: EventType
    text: str
    refs: list[str] = []
    data: dict[str, Any] = {}
    ok: bool = True


class Letter(Model):
    id: str
    account_id: str
    kind: LetterKind
    to: str
    subject: str
    body: str
    verified: bool
    numbers_checked: NonNegativeInt


class Check(Model):
    name: str
    ok: bool
    detail: str


class Verification(Model):
    passed: bool
    checks: list[Check]


class ModelInfo(Model):
    backend: str
    chat_model: str
    calls: NonNegativeInt
    tokens: NonNegativeInt


class Run(Model):
    case_id: str
    title: str
    summary: str
    generated_at: datetime
    model: ModelInfo
    complaint: Complaint
    notice: Notice
    banks: list[Bank]
    accounts: list[Account]
    transactions: list[Txn]
    grievances: list[Grievance]
    trace: Trace
    decisions: list[Decision]
    clocks: list[Clock]
    events: list[Event]
    letters: list[Letter]
    verification: Verification

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True)


class IndexEntry(Model):
    case_id: str
    title: str
    summary: str
    accounts: int
    banks: int
    lost: int
    held_before: int
    held_after: int
    status: Literal["verified", "failed"]
    model_calls: int
