"""Policy decisions, mule signals and deadline clocks on the scenarios."""

from __future__ import annotations

from datetime import timedelta

import pytest

from lienline.clocks import clocks_for
from lienline.decide import decide
from lienline.money import rupees
from lienline.patterns import full_freeze_justified, signals_for
from lienline.simulate import SCENARIOS
from lienline.trace import trace


def decided(case_id: str):
    s = SCENARIOS[case_id]()
    tr = trace(s)
    signals = {a: signals_for(s, s.account(a)) for a in tr.accounts}
    decisions = decide(s, tr, signals)
    return s, tr, signals, {d.account_id: d for d in decisions}


def test_c1_merchant_keeps_only_the_980():
    _, _, _, d = decided("c1-archana")
    shop = d["A3"]
    assert (shop.action, shop.amount) == ("lien", rupees(980))
    assert shop.current_hold == rupees(2_51_00_000)
    assert shop.released_by_change == rupees(2_50_99_020)
    assert any("T9" in r.refs for r in shop.reasons)


def test_c2_freelancer_paid_for_real_work_is_released():
    _, tr, _, d = decided("c2-digital-arrest")
    free = d["A9"]
    assert (free.action, free.amount) == ("release", 0)
    assert tr.accounts["A9"].by_rule["FIFO"] == rupees(7_000)  # the rules disagree; LIBR decides
    assert (free.range.min, free.range.max) == (0, rupees(7_000))
    assert free.confidence == "low"


def test_c2_mule_with_signals_but_no_registry_hit_gets_a_lien_not_a_freeze():
    _, _, signals, d = decided("c2-digital-arrest")
    assert sum(s.present for s in signals["A7"]) >= 3
    assert not full_freeze_justified(signals["A7"])
    assert d["A7"].action == "lien"
    assert d["A8"].action == "full_freeze"  # registry hit + 3 complaints


def test_c3_rules_give_four_answers_and_libr_decides():
    _, tr, _, d = decided("c3-rules-disagree")
    assert tr.accounts["A3"].by_rule == {"FIFO": 0, "LIFO": rupees(1_50_000), "PRO_RATA": 97_09_277,
                                         "LIBR": rupees(3_50_000)}
    assert d["A3"].amount == rupees(3_50_000)
    assert d["A4"].action == "release"  # supplier: LIBR traces nothing, FIFO would say ₹3.99 lakh


def test_c4_hardened_mule_full_freeze_with_reasons():
    _, tr, signals, d = decided("c4-hardened-mule")
    mule = d["A2"]
    assert mule.action == "full_freeze"
    assert mule.amount == tr.accounts["A2"].balance_now > tr.accounts["A2"].by_rule["LIBR"]
    assert {s.id for s in signals["A2"] if s.present} >= {"registry_hit", "linked_complaints", "pass_through"}
    assert "Full freeze justified" in mule.reasons[1].text
    assert (d["A4"].action, d["A4"].amount) == ("lien", rupees(640))


@pytest.mark.parametrize("case_id", list(SCENARIOS))
def test_decisions_never_exceed_balance(case_id):
    _, tr, _, d = decided(case_id)
    for acc, dec in d.items():
        assert dec.amount <= tr.accounts[acc].balance_now
        assert dec.released_by_change == dec.current_hold - dec.amount


def test_grievance_clocks_follow_the_sop_durations():
    s, _, _, d = decided("c1-archana")
    clocks = {c.id: c for c in clocks_for(s, list(d.values()))}
    received = s.grievances[0].received_at
    expected = {"grievance_forward-A3": 7, "io_decision-A3": 15, "lea_notice-A3": 75, "hold_review-A3": 90}
    for cid, days in expected.items():
        assert clocks[cid].due == received + timedelta(days=days)
        assert clocks[cid].source.startswith("https://")
    assert clocks["grievance_forward-A3"].status == "met"  # forwarded on day 4
    assert clocks["io_decision-A3"].status == "breached"  # as of 12 Oct, no IO decision
    assert clocks["hold_review-A3"].status == "running"


def test_proportionate_hold_clock_is_breached_by_a_whole_account_freeze():
    s, _, _, d = decided("c1-archana")
    clocks = {c.id: c for c in clocks_for(s, list(d.values()))}
    assert clocks["proportionate_hold-A3"].status == "breached"
    assert clocks["proportionate_hold-A2"].status == "met"  # full freeze justified
    assert "no duration stated" in clocks["proportionate_hold-A3"].label


def test_unforwarded_grievance_breaches_the_seven_day_clock():
    s, _, _, d = decided("c2-digital-arrest")
    clocks = {c.id: c for c in clocks_for(s, list(d.values()))}
    assert clocks["grievance_forward-A9"].status == "breached"
