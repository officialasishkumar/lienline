"""Seeded, synthetic case files. Real complaint data is not public, so each scenario is built
by hand to mirror a pattern from the 2026 judgments and I4C reporting. Bank names, people
and businesses are fictional; UTRs and masked account numbers come from a seeded RNG so a
scenario is byte-for-byte reproducible.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from lienline.models import (
    CASH,
    EXTERNAL,
    Account,
    Bank,
    Channel,
    Complaint,
    Flag,
    Grievance,
    Notice,
    Role,
    Scenario,
    Txn,
    Victim,
)
from lienline.money import inr, rupees

IST = timezone(timedelta(hours=5, minutes=30))

BANKS = {
    "NRB": Bank(id="NRB", name="Narmada Bank", kind="public"),
    "SHB": Bank(id="SHB", name="Sahyadri Bank", kind="private"),
    "KSF": Bank(id="KSF", name="Konark Small Finance Bank", kind="small_finance"),
    "VGB": Bank(id="VGB", name="Vindhya Gramin Bank", kind="regional_rural"),
}


def ist(month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(2026, month, day, hour, minute, tzinfo=IST)


class CaseBuilder:
    """Accumulates accounts and transactions with stable ids (A1.., T1..)."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)
        self.accounts: list[Account] = []
        self.txns: list[Txn] = []

    def account(self, bank: str, holder: str, kind: str, role: Role, *, kyc_age_days: int, opening: int,
                complaints_linked: int = 0, registry_hit: bool = False) -> str:
        acc_id = f"A{len(self.accounts) + 1}"
        self.accounts.append(Account(
            id=acc_id, bank=bank, masked=f"XXXX{self._rng.randint(1000, 9999)}", holder=holder, kind=kind, role=role,
            kyc_age_days=kyc_age_days, opening_balance=opening, complaints_linked=complaints_linked,
            registry_hit=registry_hit,
        ))
        return acc_id

    def pay(self, ts: datetime, frm: str, to: str, amount: int, channel: Channel, note: str,
            *, tainted: bool = False) -> str:
        if self.txns and ts < self.txns[-1].ts:
            raise ValueError("add transactions in time order so ids read chronologically")
        txn_id = f"T{len(self.txns) + 1}"
        utr = f"6{ts:%y}{self._rng.randint(10**8, 10**9 - 1)}"  # 12 digits, year-prefixed like an RRN
        self.txns.append(Txn(id=txn_id, utr=utr, ts=ts, from_=frm, to=to, amount=amount, channel=channel,
                             tainted_origin=tainted, note=note))
        return txn_id

    def acct(self, acc_id: str) -> Account:
        return next(a for a in self.accounts if a.id == acc_id)

    def utr(self, txn_id: str) -> str:
        return next(t.utr for t in self.txns if t.id == txn_id)

    def banks(self) -> list[Bank]:
        used = {a.bank for a in self.accounts}
        return [b for b in BANKS.values() if b.id in used]


def notice_text(b: CaseBuilder, *, ps: str, io: str, ack: str, issued: datetime, lines: list[tuple[str, str, int]],
                typo: dict[str, str] | None = None) -> str:
    """The police notice as a bank receives it. ``lines`` are (account, txn, amount) triples;
    ``typo`` maps a txn id to a mistyped UTR, as happens in real notices."""
    typo = typo or {}
    rows = []
    for n, (acc_id, txn_id, amount) in enumerate(lines, 1):
        a = b.acct(acc_id)
        rows.append(f"{n}. A/c {a.masked} ({BANKS[a.bank].name}), {a.holder}: {inr(amount)} via UTR "
                    f"{typo.get(txn_id, b.utr(txn_id))}")
    return (
        f"NOTICE UNDER SECTION 106 BNSS\nFrom: {io}, {ps}\nDate: {issued:%d %b %Y}\nNCRP acknowledgement: {ack}\n\n"
        "The following accounts have received proceeds of cyber fraud reported on NCRP. You are directed to put "
        "on hold the disputed amounts mentioned against each account and preserve KYC and statements.\n\n"
        + "\n".join(rows)
    )


# ---------------------------------------------------------------- c1


def c1_archana() -> Scenario:
    """A ₹980 card-free UPI spend lands in a liquor merchant holding ₹2.51 crore (cf. Archana v State of MP)."""
    b = CaseBuilder(seed=101)
    victim = b.account("NRB", "Sunita Rao", "savings", "victim", kyc_age_days=3650, opening=rupees(1_40_000))
    mule = b.account("SHB", "Vikas Kumar", "savings", "mule_l1", kyc_age_days=41, opening=rupees(350),
                     complaints_linked=2, registry_hit=True)
    shop = b.account("SHB", "Narmada Wines & Spirits", "merchant", "merchant", kyc_age_days=2900,
                     opening=rupees(2_50_49_020))
    l2 = b.account("KSF", "Imran Shaikh", "savings", "mule_l2", kyc_age_days=120, opening=rupees(1_200))

    t1 = b.pay(ist(9, 14, 11, 2), victim, mule, rupees(98_000), "IMPS", "Paid to 'KYC update' caller", tainted=True)
    t2 = b.pay(ist(9, 14, 11, 9), mule, l2, rupees(45_000), "IMPS", "Transfer to second-layer account")
    b.pay(ist(9, 14, 11, 15), mule, CASH, rupees(10_000), "ATM", "ATM withdrawal, Bhopal")
    b.pay(ist(9, 14, 11, 16), mule, CASH, rupees(10_000), "ATM", "ATM withdrawal, Bhopal")
    b.pay(ist(9, 14, 11, 31), mule, EXTERNAL, rupees(30_000), "UPI", "To a P2P crypto seller outside traced banks")
    b.pay(ist(9, 14, 11, 40), l2, CASH, rupees(20_000), "ATM", "ATM withdrawal, Indore")
    b.pay(ist(9, 14, 11, 42), l2, CASH, rupees(20_000), "ATM", "ATM withdrawal, Indore")
    b.pay(ist(9, 14, 12, 5), l2, EXTERNAL, rupees(5_000), "UPI", "To a wallet outside traced banks")
    t9 = b.pay(ist(9, 14, 19, 48), mule, shop, rupees(980), "UPI", "Counter purchase at liquor shop")
    b.pay(ist(9, 15, 21, 30), EXTERNAL, shop, rupees(3_40_000), "POS", "Card and UPI settlement for the day")
    b.pay(ist(9, 15, 22, 5), shop, EXTERNAL, rupees(2_90_000), "RTGS", "Payment to distillery for stock")

    issued = ist(9, 16, 12, 0)
    ack = "31509260012345"
    ps, io = "Cyber PS, Bhopal", "SI R. Verma"
    return Scenario(
        case_id="c1-archana",
        title="₹980 dispute, ₹2.51 crore frozen",
        summary="A ₹980 UPI spend by a mule froze a liquor merchant's entire ₹2.51 crore balance; "
                "LienLine liens ₹980 and releases the rest.",
        as_of=ist(10, 12, 10, 0),
        complaint=Complaint(
            ack_no=ack, filed_at=ist(9, 14, 13, 20), victim=Victim(name="Sunita Rao", account_id=victim),
            amount_lost=rupees(98_000), channel="IMPS", police_station=ps, io=io,
            narrative=(
                "I got a call at 10:50 am on 14 Sep from a man saying my bank KYC had expired and the account "
                "would be blocked. He sent a link and I entered my details. At 11:02 Rs 98,000 was debited by "
                f"IMPS to account {b.acct(mule).masked} at Sahyadri Bank, UTR {b.utr(t1)}. I called 1930 at "
                "1:10 pm."
            ),
        ),
        notice=Notice(
            issued_at=issued, section="106 BNSS",
            flagged=[Flag(account_id=mule, amount=rupees(98_000)), Flag(account_id=l2, amount=rupees(45_000)),
                     Flag(account_id=shop, amount=rupees(980))],
            text=notice_text(b, ps=ps, io=io, ack=ack, issued=issued, lines=[
                (mule, t1, rupees(98_000)), (l2, t2, rupees(45_000)), (shop, t9, rupees(980))]),
        ),
        banks=b.banks(), accounts=b.accounts, transactions=b.txns,
        grievances=[Grievance(
            account_id=shop, received_at=ist(9, 22, 11, 0), forwarded_at=ist(9, 26, 16, 0),
            text="Our entire current account of ₹2.51 crore is frozen over a ₹980 counter sale. We cannot pay "
                 "excise duty, salaries or the distillery. We ask that only the disputed amount be held.",
        )],
    )


# ---------------------------------------------------------------- c2


def c2_digital_arrest() -> Scenario:
    """₹18.4 lakh 'digital arrest': one new mule fans out to six accounts in four banks in 40 minutes."""
    b = CaseBuilder(seed=202)
    victim = b.account("NRB", "Dr. Meera Iyer", "savings", "victim", kyc_age_days=9100, opening=rupees(22_00_000))
    l1 = b.account("SHB", "Yadav Traders (Rahul Yadav)", "current", "mule_l1", kyc_age_days=19, opening=rupees(1_500),
                   complaints_linked=2)
    atm = b.account("KSF", "Sandeep Mehra", "savings", "cashout", kyc_age_days=33, opening=rupees(900),
                    complaints_linked=1)
    atm2 = b.account("VGB", "Pooja Rawat", "savings", "cashout", kyc_age_days=61, opening=rupees(2_100),
                     complaints_linked=1)
    gold = b.account("NRB", "Shree Ganesh Jewellers", "merchant", "merchant", kyc_age_days=4100,
                     opening=rupees(6_80_000))
    payer = b.account("SHB", "Arjun Nair", "savings", "mule_l2", kyc_age_days=210, opening=rupees(2_000),
                      complaints_linked=1)
    rt1 = b.account("KSF", "Kunal Bhatia", "savings", "mule_l2", kyc_age_days=27, opening=rupees(1_000),
                    complaints_linked=2)
    rt2 = b.account("VGB", "Deepak Solanki", "savings", "mule_l2", kyc_age_days=45, opening=rupees(500),
                    complaints_linked=3, registry_hit=True)
    freelancer = b.account("NRB", "Neha Joshi", "savings", "innocent", kyc_age_days=1500, opening=rupees(38_000))

    d = 2
    t1 = b.pay(ist(9, d, 10, 0), victim, l1, rupees(12_00_000), "RTGS",
               "Victim told to move savings to 'RBI safe account' during video call", tainted=True)
    t2 = b.pay(ist(9, d, 10, 24), victim, l1, rupees(6_40_000), "RTGS", "Second transfer to 'safe account'",
               tainted=True)
    t3 = b.pay(ist(9, d, 10, 27), l1, gold, rupees(4_10_000), "RTGS", "Gold coins and bar, invoice SGJ/26/0915")
    t4 = b.pay(ist(9, d, 10, 31), l1, atm, rupees(3_50_000), "IMPS", "Layer 2 transfer")
    t5 = b.pay(ist(9, d, 10, 36), l1, atm2, rupees(2_95_000), "IMPS", "Layer 2 transfer")
    t6 = b.pay(ist(9, d, 10, 44), l1, payer, rupees(3_00_000), "IMPS", "Layer 2 transfer")
    b.pay(ist(9, d, 10, 49), atm2, CASH, rupees(50_000), "ATM", "ATM withdrawal, Rewa")
    b.pay(ist(9, d, 10, 51), atm2, CASH, rupees(50_000), "ATM", "ATM withdrawal, Rewa")
    t7 = b.pay(ist(9, d, 10, 52), l1, rt1, rupees(2_40_000), "IMPS", "Layer 2 transfer")
    b.pay(ist(9, d, 10, 58), atm, CASH, rupees(2_00_000), "CASH", "Self cheque encashed at branch")
    t8 = b.pay(ist(9, d, 11, 1), l1, rt2, rupees(2_30_000), "IMPS", "Layer 2 transfer")
    b.pay(ist(9, d, 11, 5), rt1, rt2, rupees(2_00_000), "IMPS", "Round trip leg 1")
    b.pay(ist(9, d, 11, 12), atm2, CASH, rupees(50_000), "ATM", "ATM withdrawal, Satna")
    b.pay(ist(9, d, 11, 14), atm2, CASH, rupees(50_000), "ATM", "ATM withdrawal, Satna")
    b.pay(ist(9, d, 11, 20), rt2, rt1, rupees(1_50_000), "IMPS", "Round trip leg 2")
    b.pay(ist(9, d, 11, 20), payer, CASH, rupees(2_00_000), "CASH", "Self cheque encashed at branch")
    b.pay(ist(9, d, 11, 25), atm, CASH, rupees(50_000), "ATM", "ATM withdrawal, Jabalpur")
    b.pay(ist(9, d, 11, 27), atm, CASH, rupees(50_000), "ATM", "ATM withdrawal, Jabalpur")
    b.pay(ist(9, d, 11, 34), payer, EXTERNAL, rupees(95_000), "IMPS", "To a P2P USDT seller outside traced banks")
    b.pay(ist(9, d, 11, 40), rt1, rt2, rupees(1_80_000), "IMPS", "Round trip leg 3")
    b.pay(ist(9, d, 11, 40), atm2, EXTERNAL, rupees(45_000), "POS", "Phones bought at an electronics store")
    b.pay(ist(9, d, 12, 30), rt2, CASH, rupees(3_00_000), "CASH", "Self cheque encashed at branch")
    b.pay(ist(9, d, 13, 5), gold, EXTERNAL, rupees(9_50_000), "RTGS", "Bullion supplier, Mumbai")
    b.pay(ist(9, d, 13, 10), rt2, EXTERNAL, rupees(1_50_000), "IMPS", "To a crypto exchange outside traced banks")
    b.pay(ist(9, d, 14, 10), EXTERNAL, payer, rupees(15_000), "UPI", "Refund from an online store")
    b.pay(ist(9, d, 16, 10), EXTERNAL, gold, rupees(2_70_000), "POS", "Showroom sales for the day")
    t_free = b.pay(ist(9, d, 16, 40), payer, freelancer, rupees(12_000), "UPI", "Logo design, invoice NJ-114")

    issued = ist(9, 3, 15, 0)
    ack = "31509260054321"
    ps, io = "State Cyber Cell, Jabalpur", "Insp. K. Thakur"
    lines = [(l1, t1, rupees(18_40_000)), (gold, t3, rupees(4_10_000)), (atm, t4, rupees(3_50_000)),
             (atm2, t5, rupees(2_95_000)), (payer, t6, rupees(3_00_000)), (rt1, t7, rupees(2_40_000)),
             (rt2, t8, rupees(2_30_000)), (freelancer, t_free, rupees(12_000))]
    return Scenario(
        case_id="c2-digital-arrest",
        title="₹18.4 lakh 'digital arrest', 8 accounts frozen",
        summary="A retired professor's ₹18.4 lakh fans out across 4 banks in 40 minutes; LienLine liens each "
                "account's traceable share and releases a freelancer paid for real work.",
        as_of=ist(10, 12, 10, 0),
        complaint=Complaint(
            ack_no=ack, filed_at=ist(9, d, 15, 5), victim=Victim(name="Dr. Meera Iyer", account_id=victim),
            amount_lost=rupees(18_40_000), channel="RTGS", police_station=ps, io=io,
            narrative=(
                "Callers posing as CBI officers kept me on a video call from 8 am, said my Aadhaar was used in a "
                "money-laundering case and I was under 'digital arrest'. They made me transfer my savings to an "
                f"'RBI safe account' {b.acct(l1).masked} at Sahyadri Bank: Rs 12,00,000 by RTGS at 10:00 "
                f"(UTR {b.utr(t1)}) and Rs 6,40,000 at 10:24 (UTR {b.utr(t2)}). Total Rs 18,40,000."
            ),
        ),
        notice=Notice(
            issued_at=issued, section="106 BNSS", flagged=[Flag(account_id=a, amount=amt) for a, _, amt in lines],
            text=notice_text(b, ps=ps, io=io, ack=ack, issued=issued, lines=lines,
                             typo={t6: _transpose(b.utr(t6))}),
        ),
        banks=b.banks(), accounts=b.accounts, transactions=b.txns,
        grievances=[Grievance(
            account_id=freelancer, received_at=ist(9, 8, 10, 30), forwarded_at=None,
            text="I am a graphic designer. Arjun Nair paid me ₹12,000 for a logo. My whole account is frozen and "
                 "I cannot pay rent.",
        )],
    )


def _transpose(utr: str) -> str:
    """Swap the last two digits, the commonest typing error in a hand-copied UTR."""
    return utr[:-2] + utr[-1] + utr[-2]


# ---------------------------------------------------------------- c3


def c3_rules_disagree() -> Scenario:
    """A pharma distributor with heavy legitimate turnover: the four rules give four answers."""
    b = CaseBuilder(seed=303)
    victim = b.account("NRB", "Harish Choudhary", "savings", "victim", kyc_age_days=5200, opening=rupees(9_00_000))
    l1 = b.account("KSF", "Manoj Pal", "savings", "mule_l1", kyc_age_days=50, opening=rupees(800),
                   complaints_linked=2)
    dist = b.account("SHB", "Malwa Pharma Distributors", "current", "merchant", kyc_age_days=3000,
                     opening=rupees(2_00_000))
    supplier = b.account("NRB", "Indore Medical Agencies", "current", "merchant", kyc_age_days=3600,
                         opening=rupees(12_00_000))

    t1 = b.pay(ist(9, 24, 10, 5), victim, l1, rupees(6_00_000), "NEFT",
               "'Stock tips' group: deposit for guaranteed returns", tainted=True)
    t2 = b.pay(ist(9, 24, 10, 40), l1, dist, rupees(4_50_000), "RTGS", "Against invoice MPD/7781, bulk medicines")
    b.pay(ist(9, 24, 11, 10), l1, CASH, rupees(1_00_000), "CASH", "Self cheque encashed at branch")
    b.pay(ist(9, 24, 11, 50), l1, EXTERNAL, rupees(45_000), "IMPS", "To an account outside traced banks")
    b.pay(ist(9, 24, 12, 0), EXTERNAL, dist, rupees(7_00_000), "NEFT", "Receipts from chemists")
    t5 = b.pay(ist(9, 24, 13, 30), dist, supplier, rupees(6_00_000), "RTGS", "Supplier payment, invoice IMA/2209")
    b.pay(ist(9, 24, 15, 0), EXTERNAL, dist, rupees(1_50_000), "NEFT", "Receipts from chemists")
    b.pay(ist(9, 24, 17, 0), dist, EXTERNAL, rupees(5_50_000), "NEFT", "GST and salaries")
    b.pay(ist(9, 25, 11, 0), EXTERNAL, dist, rupees(4_00_000), "NEFT", "Receipts from chemists")
    b.pay(ist(9, 25, 16, 0), supplier, EXTERNAL, rupees(9_00_000), "RTGS", "Manufacturer payment")

    issued = ist(9, 26, 11, 0)
    ack = "31509260077777"
    ps, io = "Cyber PS, Indore", "SI P. Malviya"
    lines = [(l1, t1, rupees(6_00_000)), (dist, t2, rupees(4_50_000)), (supplier, t5, rupees(6_00_000))]
    return Scenario(
        case_id="c3-rules-disagree",
        title="One distributor, four tracing rules, four answers",
        summary="₹4.5 lakh of fraud money mixes into a pharma distributor's busy account; FIFO, LIFO, pro-rata "
                "and LIBR disagree, and LienLine shows the range and why LIBR is used.",
        as_of=ist(10, 12, 10, 0),
        complaint=Complaint(
            ack_no=ack, filed_at=ist(9, 24, 18, 0), victim=Victim(name="Harish Choudhary", account_id=victim),
            amount_lost=rupees(6_00_000), channel="NEFT", police_station=ps, io=io,
            narrative=(
                "A WhatsApp 'stock tips' group promised 4% a week. On 24 Sep at 10:05 I sent Rs 6,00,000 by NEFT "
                f"to {b.acct(l1).masked} at Konark Small Finance Bank (UTR {b.utr(t1)}). The app stopped working "
                "the same evening."
            ),
        ),
        notice=Notice(
            issued_at=issued, section="106 BNSS", flagged=[Flag(account_id=a, amount=amt) for a, _, amt in lines],
            text=notice_text(b, ps=ps, io=io, ack=ack, issued=issued, lines=lines),
        ),
        banks=b.banks(), accounts=b.accounts, transactions=b.txns,
        grievances=[
            Grievance(account_id=dist, received_at=ist(9, 29, 12, 0), forwarded_at=ist(10, 3, 12, 0),
                      text="We sold medicines against a genuine invoice. Our working capital of ₹7.5 lakh is frozen."),
            Grievance(account_id=supplier, received_at=ist(9, 30, 10, 0), forwarded_at=ist(10, 1, 15, 0),
                      text="We were paid by our distributor for supplies. Our account is frozen in full."),
        ],
    )


# ---------------------------------------------------------------- c4


def c4_hardened_mule() -> Scenario:
    """A current account on 7 complaints and the suspect registry passes 98% of what it receives."""
    b = CaseBuilder(seed=404)
    victim = b.account("NRB", "Farhan Qureshi", "savings", "victim", kyc_age_days=2400, opening=rupees(4_00_000))
    mule = b.account("SHB", "Om Sai Enterprises", "current", "mule_l1", kyc_age_days=74, opening=rupees(3_200),
                     complaints_linked=7, registry_hit=True)
    l2 = b.account("KSF", "Ravi Teja", "savings", "mule_l2", kyc_age_days=140, opening=rupees(1_100),
                   complaints_linked=2)
    kirana = b.account("VGB", "Annapurna Kirana Stores", "merchant", "innocent", kyc_age_days=2200,
                       opening=rupees(84_000))

    d = 20
    b.pay(ist(9, d, 9, 12), EXTERNAL, mule, rupees(1_85_000), "IMPS", "Credit from an account outside traced banks")
    b.pay(ist(9, d, 9, 20), mule, l2, rupees(1_80_000), "IMPS", "Layer 2 transfer")
    b.pay(ist(9, d, 9, 45), l2, EXTERNAL, rupees(1_75_000), "IMPS", "To an account outside traced banks")
    t4 = b.pay(ist(9, d, 10, 5), victim, mule, rupees(2_00_000), "IMPS", "'Task' deposit to unlock earnings",
               tainted=True)
    t5 = b.pay(ist(9, d, 10, 11), mule, l2, rupees(1_96_000), "IMPS", "Layer 2 transfer")
    b.pay(ist(9, d, 10, 30), l2, CASH, rupees(50_000), "ATM", "ATM withdrawal, Hyderabad")
    b.pay(ist(9, d, 10, 32), l2, CASH, rupees(50_000), "ATM", "ATM withdrawal, Hyderabad")
    b.pay(ist(9, d, 10, 35), l2, CASH, rupees(50_000), "ATM", "ATM withdrawal, Hyderabad")
    t9 = b.pay(ist(9, d, 10, 40), victim, mule, rupees(1_20_000), "IMPS", "'Task' deposit, VIP level", tainted=True)
    b.pay(ist(9, d, 10, 47), mule, CASH, rupees(1_00_000), "CASH", "Self cheque encashed at branch")
    b.pay(ist(9, d, 11, 0), l2, EXTERNAL, rupees(50_000), "IMPS", "To an account outside traced banks")
    b.pay(ist(9, d, 11, 30), EXTERNAL, mule, rupees(2_40_000), "IMPS", "Credit from an account outside traced banks")
    b.pay(ist(9, d, 11, 36), mule, EXTERNAL, rupees(2_69_000), "IMPS", "To a crypto exchange outside traced banks")
    b.pay(ist(9, d, 12, 20), EXTERNAL, mule, rupees(16_000), "UPI", "Credit from an account outside traced banks")
    t15 = b.pay(ist(9, d, 13, 0), l2, kirana, rupees(640), "UPI", "Groceries")

    issued = ist(9, 22, 12, 0)
    ack = "31509260099001"
    ps, io = "Cyber Crime PS, Hyderabad", "SI M. Rao"
    lines = [(mule, t4, rupees(2_00_000)), (mule, t9, rupees(1_20_000)), (l2, t5, rupees(1_96_000)),
             (kirana, t15, rupees(640))]
    flagged: dict[str, int] = {}
    for acc, _, amt in lines:
        flagged[acc] = flagged.get(acc, 0) + amt
    return Scenario(
        case_id="c4-hardened-mule",
        title="A mule on 7 complaints: full freeze, justified",
        summary="A 74-day-old current account on the suspect registry, linked to 7 complaints, passes 98% of its "
                "money through; LienLine justifies a full freeze and still liens a kirana store only ₹640.",
        as_of=ist(10, 12, 10, 0),
        complaint=Complaint(
            ack_no=ack, filed_at=ist(9, d, 16, 0), victim=Victim(name="Farhan Qureshi", account_id=victim),
            amount_lost=rupees(3_20_000), channel="IMPS", police_station=ps, io=io,
            narrative=(
                "A 'part-time job' on Telegram paid small amounts for liking videos, then asked for deposits to "
                f"unlock earnings. I paid Rs 2,00,000 (UTR {b.utr(t4)}) and Rs 1,20,000 (UTR {b.utr(t9)}) by IMPS "
                f"to Om Sai Enterprises, account {b.acct(mule).masked}, Sahyadri Bank."
            ),
        ),
        notice=Notice(
            issued_at=issued, section="106 BNSS",
            flagged=[Flag(account_id=a, amount=amt) for a, amt in flagged.items()],
            text=notice_text(b, ps=ps, io=io, ack=ack, issued=issued, lines=lines),
        ),
        banks=b.banks(), accounts=b.accounts, transactions=b.txns,
        grievances=[Grievance(
            account_id=mule, received_at=ist(9, 25, 15, 0), forwarded_at=ist(9, 29, 11, 0),
            text="Om Sai Enterprises is a genuine trading firm. The freeze of our whole current account is illegal "
                 "after the High Court judgments; release everything above the disputed amount.",
        )],
    )


SCENARIOS: dict[str, Callable[[], Scenario]] = {
    "c1-archana": c1_archana,
    "c2-digital-arrest": c2_digital_arrest,
    "c3-rules-disagree": c3_rules_disagree,
    "c4-hardened-mule": c4_hardened_mule,
}


def load(case_id: str) -> Scenario:
    try:
        return SCENARIOS[case_id]()
    except KeyError:
        raise KeyError(f"unknown case {case_id!r}; known: {', '.join(SCENARIOS)}") from None
