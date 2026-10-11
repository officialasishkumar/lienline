"""Shared fixtures. Tests never call a model: the deterministic fallbacks are forced."""

from __future__ import annotations

import os
from datetime import timedelta

os.environ["LIENLINE_MODEL"] = "off"

from lienline.models import Account, Complaint, Notice, Scenario, Txn, Victim
from lienline.simulate import ist

START = ist(9, 1, 10, 0)


def ledger(openings: dict[str, int], moves: list[tuple[str, str, int, bool]]) -> Scenario:
    """A minimal case: account ``V`` is the victim; ``moves`` are (from, to, paise, tainted_origin) one minute apart."""
    accounts = [
        Account(id=acc, bank="NRB", masked=f"XXXX{1000 + i}", holder=acc, kind="savings",
                role="victim" if acc == "V" else "mule_l1", kyc_age_days=30, opening_balance=bal,
                complaints_linked=0, registry_hit=False)
        for i, (acc, bal) in enumerate(openings.items())
    ]
    txns = [Txn(id=f"T{i + 1}", utr=f"{600000000000 + i}", ts=START + timedelta(minutes=i), from_=f, to=t, amount=a,
                channel="IMPS", tainted_origin=taint, note="") for i, (f, t, a, taint) in enumerate(moves)]
    lost = sum(t.amount for t in txns if t.tainted_origin) or 1
    return Scenario(
        case_id="test", title="test", summary="test", as_of=START + timedelta(days=1),
        complaint=Complaint(ack_no="1", filed_at=START, victim=Victim(name="V", account_id="V"), amount_lost=lost,
                            channel="IMPS", narrative="", police_station="PS", io="IO"),
        notice=Notice(text="", issued_at=START, section="106 BNSS", flagged=[]),
        banks=[], accounts=accounts, transactions=txns, grievances=[],
    )
