"""Deadlines as data. Every rule carries the citation it comes from.

Sources (as summarised in the linked reports; re-read the primary documents before relying on them):

* MHA/I4C SOP on NCRP/CFCFRMS, 2 Jan 2026. The grievance procedure for a hold on an account
  sets 7 / 15 / 90-day clocks. The summary we used numbers this section 9.1 (grievance
  redressal), with section 10 covering restoration of money; it does not always say what starts
  a clock, and where it does not, the label says how we measure it.
* MP High Court, Archana v State of MP, 27 Jul 2026, and Rajasthan High Court, Shree Balaji
  Enterprises v RBI, 20 Aug 2026: a hold must be limited to the identifiable disputed amount.
  Neither report gives a duration for this, so it is a compliance check that applies from the
  moment of the hold (due == start), not a timer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from lienline.models import Clock, ClockStatus, Decision, Scenario

SOP_URL = "https://www.prashantkanha.com/ncrp-cfcfrms-cyber-fraud-sop-2026/"
SOP = "MHA/I4C SOP 2 Jan 2026, grievance redressal (s. 9.1)"
MP_HC_URL = "https://www.livelaw.in/high-court/madhya-pradesh-high-court/freezing-bank-accounts-guidelines-cyberc"
MP_HC = "MP High Court, Archana v State of MP, 27 Jul 2026"
RAJ_HC_URL = "https://www.livelaw.in/high-court/rajasthan-high-court/rajasthan-high-court-account-freeze-cyber-cri"
RAJ_HC = "Rajasthan High Court, Shree Balaji Enterprises v RBI, 20 Aug 2026"


@dataclass(frozen=True)
class ClockRule:
    id: str
    label: str
    days: int
    starts: Literal["grievance_received", "hold_placed"]
    rule: str
    source: str


GRIEVANCE_RULES: tuple[ClockRule, ...] = (
    ClockRule("grievance_forward", "Bank forwards the holder's grievance to the online Grievance Module (7 days; "
              "source does not state the start, measured from receipt)", 7, "grievance_received", SOP, SOP_URL),
    ClockRule("io_decision", "IO decides on the grievance or the District Grievance Officer is auto-notified "
              "(15 days; source does not state the start, measured from receipt)", 15, "grievance_received",
              SOP, SOP_URL),
    ClockRule("lea_notice", "Bank notifies the police 15 days before the 90-day hold period ends", 75,
              "grievance_received", SOP, SOP_URL),
    ClockRule("hold_review", "No lawful direction within 90 days of the bank raising the grievance: bank may remove "
              "the hold after enhanced due diligence", 90, "grievance_received", SOP, SOP_URL),
)

PROPORTIONATE_HOLD = ClockRule(
    "proportionate_hold", "Hold limited to the identifiable disputed amount (no duration stated in the cited "
    "report; applies from the moment of the hold)", 0, "hold_placed", f"{MP_HC}; {RAJ_HC}", MP_HC_URL,
)


def clocks_for(scenario: Scenario, decisions: list[Decision]) -> list[Clock]:
    """All clocks for a case, as of ``scenario.as_of``."""
    out: list[Clock] = []
    for g in scenario.grievances:
        for r in GRIEVANCE_RULES:
            due = g.received_at + timedelta(days=r.days)
            met = r.id == "grievance_forward" and g.forwarded_at is not None and g.forwarded_at <= due
            out.append(_clock(r, g.account_id, g.received_at, due, _status(met, due, scenario.as_of)))
    for d in decisions:
        if d.current_hold == 0:
            continue
        # The current hold complies only if it does not exceed what the policy would hold.
        status: ClockStatus = "met" if d.current_hold <= d.amount else "breached"
        issued = scenario.notice.issued_at
        out.append(_clock(PROPORTIONATE_HOLD, d.account_id, issued, issued, status))
    return out


def _status(met: bool, due: datetime, as_of: datetime) -> ClockStatus:
    if met:
        return "met"
    return "breached" if as_of > due else "running"


def _clock(r: ClockRule, account_id: str, start: datetime, due: datetime, status: ClockStatus) -> Clock:
    return Clock(id=f"{r.id}-{account_id}", account_id=account_id, label=r.label, start=start, due=due,
                 rule=r.rule, source=r.source, status=status)
