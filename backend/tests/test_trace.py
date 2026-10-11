"""Tracing rules on hand-computed ledgers, then properties over random ledgers.

Amounts are written in rupees with ``rupees()`` and compared in paise.
"""

from __future__ import annotations

import pytest
from conftest import ledger
from hypothesis import given, settings
from hypothesis import strategies as st

from lienline.models import CASH, EXTERNAL, RULES
from lienline.money import rupees
from lienline.simulate import SCENARIOS
from lienline.trace import LedgerError, trace
from lienline.verify import replay_libr

R = rupees


def held(tr, acc):
    return tr.accounts[acc].by_rule


def edge(tr, txn):
    return next(e for e in tr.edges if e.txn == txn).tainted


def test_all_four_rules_differ():
    """X opens with ₹1,000 clean, gets ₹600 of the victim's money, then ₹400 clean, and pays ₹1,500 to Y.

    FIFO      queue [1000c, 600t, 400c]; ₹1,500 out = 1000c + 500t      -> T3 carries 500, X keeps 100
    LIFO      stack [1000c, 600t, 400c]; ₹1,500 out = 400c + 600t + 500c -> T3 carries 600, X keeps 0
    PRO_RATA  600/2000 of the balance is tainted; 1500 x 0.3 = 450 out    -> X keeps 150
    LIBR      own money first; balance after = 500 caps taint at 500      -> T3 carries 100, X keeps 500
    """
    s = ledger({"V": R(10_000), "X": R(1_000), "Y": 0},
               [("V", "X", R(600), True), (EXTERNAL, "X", R(400), False), ("X", "Y", R(1_500), False)])
    tr = trace(s)
    assert held(tr, "X") == {"FIFO": R(100), "LIFO": 0, "PRO_RATA": R(150), "LIBR": R(500)}
    assert edge(tr, "T3") == {"FIFO": R(500), "LIFO": R(600), "PRO_RATA": R(450), "LIBR": R(100)}
    assert held(tr, "Y") == edge(tr, "T3")  # taint propagates to the next hop unchanged
    assert len(set(held(tr, "X").values())) == 4


def test_clayton_case_vs_lifo():
    """₹100 tainted then ₹100 clean, then ₹100 cashed out.
    FIFO spends the tainted ₹100 (keeps 0); LIFO the clean ₹100 (keeps 100); pro-rata half (keeps 50);
    LIBR spends own money first and the balance (100) never drops below the taint (keeps 100)."""
    s = ledger({"V": R(1_000), "X": 0},
               [("V", "X", R(100), True), (EXTERNAL, "X", R(100), False), ("X", CASH, R(100), False)])
    tr = trace(s)
    assert held(tr, "X") == {"FIFO": 0, "LIFO": R(100), "PRO_RATA": R(50), "LIBR": R(100)}
    assert tr.conservation_by_rule["FIFO"].cashed_out == R(100)
    assert tr.conservation_by_rule["LIFO"].cashed_out == 0


def test_libr_is_not_replenished_by_later_clean_credits():
    """₹100 tainted in, ₹80 cashed out (all rules keep ₹20), ₹500 clean in, ₹500 out to an outside account.

    FIFO      queue [20t, 500c]: the ₹500 takes the 20t first                -> keeps 0
    LIFO      stack [20t, 500c]: the ₹500 is the clean credit                 -> keeps ₹20
    PRO_RATA  2000 x 50000 // 52000 = 1923 paise out                          -> keeps 77 paise
    LIBR      the balance fell to ₹20, the later ₹500 does not refill taint   -> keeps ₹20
    """
    s = ledger({"V": R(1_000), "X": 0}, [("V", "X", R(100), True), ("X", CASH, R(80), False),
                                        (EXTERNAL, "X", R(500), False), ("X", EXTERNAL, R(500), False)])
    tr = trace(s)
    assert held(tr, "X") == {"FIFO": 0, "LIFO": R(20), "PRO_RATA": 77, "LIBR": R(20)}
    assert {r: c.untraced for r, c in tr.conservation_by_rule.items()} == {
        "FIFO": R(20), "LIFO": 0, "PRO_RATA": 1923, "LIBR": 0}
    assert all(c.cashed_out == R(80) for c in tr.conservation_by_rule.values())


def test_libr_caps_at_lowest_intermediate_balance():
    """Opening ₹50, ₹100 tainted in (balance 150), ₹120 out (balance 30), ₹200 clean in: LIBR keeps ₹30."""
    s = ledger({"V": R(1_000), "X": R(50)}, [("V", "X", R(100), True), ("X", CASH, R(120), False),
                                            (EXTERNAL, "X", R(200), False)])
    tr = trace(s)
    assert held(tr, "X")["LIBR"] == R(30)
    assert edge(tr, "T2")["LIBR"] == R(70)  # own ₹50 went first, then ₹70 of the victim's


def test_mixed_credit_keeps_its_tainted_fraction_downstream():
    """A (₹100 own) gets ₹100 tainted and pays ₹150 to B; B then cashes out ₹30.

    FIFO  A pays 100c + 50t, so B's ₹150 credit is 1/3 tainted; ₹30 of it carries 50 x 30 / 150 = ₹10 -> B keeps ₹40
    LIFO  A pays 100t + 50c, so B's credit is 2/3 tainted; ₹30 carries ₹20                         -> B keeps ₹80
    """
    s = ledger({"V": R(1_000), "A": R(100), "B": 0},
               [("V", "A", R(100), True), ("A", "B", R(150), False), ("B", CASH, R(30), False)])
    tr = trace(s)
    assert edge(tr, "T2")["FIFO"] == R(50) and edge(tr, "T2")["LIFO"] == R(100)
    assert held(tr, "B")["FIFO"] == R(40)
    assert held(tr, "B")["LIFO"] == R(80)


def test_multi_hop_pure_taint_agrees_under_every_rule():
    s = ledger({"V": R(5_000), "A": 0, "B": 0, "C": 0},
               [("V", "A", R(1_000), True), ("A", "B", R(600), False), ("B", "C", R(600), False),
                ("C", CASH, R(100), False)])
    tr = trace(s)
    for r in RULES:
        assert (held(tr, "A")[r], held(tr, "B")[r], held(tr, "C")[r]) == (R(400), 0, R(500))
        assert tr.conservation_by_rule[r].cashed_out == R(100)


def test_pro_rata_floors_and_still_conserves():
    """7 tainted of 10 paise; 3 paise out carries floor(7 x 3 / 10) = 2."""
    s = ledger({"V": 100, "X": 0}, [("V", "X", 7, True), (EXTERNAL, "X", 3, False), ("X", CASH, 3, False)])
    tr = trace(s)
    assert held(tr, "X")["PRO_RATA"] == 5
    assert tr.conservation_by_rule["PRO_RATA"].cashed_out == 2


@pytest.mark.parametrize("moves, message", [
    ([("X", CASH, 1, False)], "overdrawn"),
    ([("X", "Q", 1, False)], "unknown endpoint"),
    ([("V", "X", 10, True), ("X", "V", 10, False)], "returned to the victim"),
])
def test_bad_ledgers_are_refused(moves, message):
    with pytest.raises(LedgerError, match=message):
        trace(ledger({"V": 100, "X": 0}, moves))


def test_only_the_victim_originates_taint():
    s = ledger({"V": 100, "X": 50}, [("X", CASH, 10, True)])
    with pytest.raises(LedgerError, match="victim"):
        trace(s)


def test_c1_hand_checked():
    """The mule (A2, ₹350 own) receives ₹98,000 and spends down to ₹3,350 before paying the shop ₹980:
    LIBR leaves ₹2,370 in A2, ₹980 in the shop, ₹1,200 in A4; ₹58,450 cashed at ATMs; ₹35,000 left the banks."""
    tr = trace(SCENARIOS["c1-archana"]())
    assert {a: at.by_rule["LIBR"] for a, at in tr.accounts.items()} == {"A2": R(2_370), "A3": R(980), "A4": R(1_200)}
    c = tr.conservation
    assert (c.lost, c.held, c.cashed_out, c.untraced) == (R(98_000), R(4_550), R(58_450), R(35_000))


# ---------------------------------------------------------------- properties over random ledgers

NAMES = ["A", "B", "C", "D"]


@st.composite
def random_ledger(draw):
    openings = {"V": R(1_00_000), **{n: draw(st.integers(0, 50_000)) for n in NAMES}}
    balance = dict(openings)
    moves = []
    for _ in range(draw(st.integers(1, 30))):
        kind = draw(st.sampled_from(["fraud", "transfer", "cash", "out", "in"]))
        src = "V" if kind == "fraud" else EXTERNAL if kind == "in" else draw(st.sampled_from(NAMES))
        if src != EXTERNAL and balance[src] == 0:
            continue
        dst = {"cash": CASH, "out": EXTERNAL}.get(kind) or draw(st.sampled_from([n for n in NAMES if n != src]))
        cap = 20_000 if src == EXTERNAL else min(balance[src], 20_000)
        amount = draw(st.integers(1, cap))
        if src != EXTERNAL:
            balance[src] -= amount
        if dst in balance:
            balance[dst] += amount
        moves.append((src, dst, amount, kind == "fraud"))
    return ledger(openings, moves)


@settings(max_examples=300, deadline=None)
@given(random_ledger())
def test_properties_hold_on_random_ledgers(s):
    tr = trace(s)
    for acc, at in tr.accounts.items():
        for point in at.series:
            for r in RULES:
                assert 0 <= point.tainted[r] <= point.balance, (acc, r, point)
    for e in tr.edges:
        assert all(0 <= v <= e.amount for v in e.tainted.values())
    for r, c in tr.conservation_by_rule.items():
        assert c.held + c.cashed_out + c.untraced == c.lost, r
        assert min(c.held, c.cashed_out, c.untraced) >= 0
    # The verifier's closed-form LIBR agrees with the tracer's step-by-step pool, hop by hop.
    replay = replay_libr(s.accounts, s.transactions, "V")
    assert replay.held == {a: at.by_rule["LIBR"] for a, at in tr.accounts.items()}
    assert replay.edge == {e.txn: e.tainted["LIBR"] for e in tr.edges}
