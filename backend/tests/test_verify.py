"""The verifier passes honest runs and catches every kind of tampering."""

from __future__ import annotations

import pytest

from lienline.agents import Gate
from lienline.models import Event, Run
from lienline.money import rupees
from lienline.pipeline import run_case
from lienline.simulate import SCENARIOS, load
from lienline.verify import amounts_in, figure_problems, verify

_RUNS: dict[str, Run] = {}


def fresh(case_id: str = "c1-archana") -> Run:
    """A deep copy of a deterministic run, safe to tamper with."""
    if case_id not in _RUNS:
        _RUNS[case_id] = run_case(load(case_id), Gate(enabled=False))
    return _RUNS[case_id].model_copy(deep=True)


def failed(run: Run) -> set[str]:
    return {c.name for c in verify(run).checks if not c.ok}


@pytest.mark.parametrize("case_id", list(SCENARIOS))
def test_honest_runs_pass(case_id):
    run = fresh(case_id)
    assert run.verification.passed
    assert failed(run) == set()


def test_tampered_transaction_amount_is_caught():
    run = fresh()
    t = next(t for t in run.transactions if t.id == "T9")
    t.amount += 100
    assert {"ledger_replay", "policy_rule_replay"} <= failed(run)


def test_inflated_lien_is_caught():
    run = fresh()
    shop = next(d for d in run.decisions if d.account_id == "A3")
    shop.amount += rupees(1)
    shop.released_by_change -= rupees(1)
    assert "decisions" in failed(run)


def test_lien_above_balance_is_caught():
    run = fresh()
    mule = next(d for d in run.decisions if d.account_id == "A4")
    mule.amount = mule.current_hold + 1
    assert "decisions" in failed(run)


def test_tampered_trace_figure_is_caught():
    run = fresh()
    run.trace.accounts["A3"].by_rule["LIBR"] = rupees(2_000)
    assert {"policy_rule_replay", "flow_balance"} <= failed(run)


def test_conservation_tampering_is_caught():
    run = fresh()
    run.trace.conservation.untraced -= 1
    assert "conservation" in failed(run)


def test_letter_with_a_wrong_figure_is_caught():
    run = fresh()
    letter = next(x for x in run.letters if x.account_id == "A3" and x.kind == "lien_instruction")
    letter.body = letter.body.replace("₹980.00", "₹9,800.00", 1)
    assert "letters" in failed(run)


def test_crore_figures_must_be_exact():
    run = fresh()
    letter = next(x for x in run.letters if x.account_id == "A3")
    letter.body += "\nThe account held ₹2.51 crore."  # exactly the ₹2,51,00,000.00 hold
    letter.numbers_checked += 1  # the letter must also say how many figures it carries
    assert "letters" not in failed(run)
    letter.body += "\nAbout ₹2.5 crore is released."  # a rounded figure is not a decision figure
    assert "letters" in failed(run)


def test_unknown_citation_is_caught():
    run = fresh()
    run.events.append(Event(t=99.0, agent="Victim's advocate", kind="model", type="debate", text="see T99",
                            refs=["T99"]))
    assert "citations" in failed(run)


def test_flipped_clock_status_is_caught():
    run = fresh()
    clock = next(c for c in run.clocks if c.id == "io_decision-A3")
    clock.status = "running"
    assert "clocks" in failed(run)


def test_unjustified_full_freeze_is_caught():
    run = fresh()
    shop = next(d for d in run.decisions if d.account_id == "A3")
    shop.action, shop.amount, shop.released_by_change = "full_freeze", shop.current_hold, 0
    assert "decisions" in failed(run)


def test_amount_parser_reads_indian_formats():
    assert amounts_in("₹2,51,00,000.00 and Rs. 980 and INR 12.5 lakh and ₹2.51 crore") == [
        2_510_000_000, 98_000, 125_000_000, 2_510_000_000]


def test_figure_checker_flags_unknown_utrs_and_accounts():
    problems, n = figure_problems("UTR 123456789012 on XXXX0000 for ₹5.00", {500}, {"999999999999"}, {"XXXX1111"})
    assert n == 3
    assert len(problems) == 2
