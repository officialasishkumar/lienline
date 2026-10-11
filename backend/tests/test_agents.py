"""Agents: code cross-checks of model output, using a scripted stand-in for the model."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from lienline import agents, llm
from lienline.agents import Claim, Gate
from lienline.decide import decide
from lienline.letters import plan_letters
from lienline.money import rupees
from lienline.patterns import signals_for
from lienline.simulate import load
from lienline.trace import trace
from lienline.verify import allowed_amounts


@pytest.fixture
def case():
    s = load("c1-archana")
    tr = trace(s)
    signals = {a: signals_for(s, s.account(a)) for a in tr.accounts}
    decisions = decide(s, tr, signals)
    known = {a.id for a in s.accounts} | {t.id for t in s.transactions}
    return s, tr, signals, decisions, known


def scripted(monkeypatch, replies: list[Any]) -> list[str]:
    """Make llm.chat return ``replies`` in order; returns the prompts it was sent."""
    seen: list[str] = []
    it: Iterator[Any] = iter(replies)

    def fake_chat(prompt: str, **_: Any) -> dict[str, Any]:
        seen.append(prompt)
        return {"json": next(it), "seconds": 2.0, "cached": False, "tokens": 100}

    monkeypatch.setattr(llm, "chat", fake_chat)
    return seen


def test_intake_rejects_a_mistyped_utr_and_points_to_the_real_one():
    s = load("c2-digital-arrest")
    findings = agents.cross_check_intake(s, agents.intake_fallback(s))
    bad = [f for f in findings if not f.ok]
    assert len(bad) == 1
    assert "not in any bank's ledger" in bad[0].detail and bad[0].refs == ["T6"]
    assert next(f for f in findings if f.item == "Amount lost").ok


def test_intake_rejects_a_wrong_loss_figure(case):
    s = case[0]
    ex = agents.intake_fallback(s)
    ex.amount_lost_rupees = 9_800.0
    assert not next(f for f in agents.cross_check_intake(s, ex) if f.item == "Amount lost").ok


def judge(case, **claim: Any):
    _, tr, signals, decisions, known = case
    c = Claim(**{"refs": ["A3", "T9"], "argument": "", "rule": None, **claim})
    return agents.judge("victim", c, tr, {d.account_id: d for d in decisions}, signals, known)


def test_judge_accepts_the_policy_figure(case):
    assert judge(case, account_id="A3", action="lien", amount_rupees=980.0, rule="LIBR").status == "accepted"


def test_judge_rejects_a_citation_that_does_not_exist(case):
    r = judge(case, account_id="A3", action="lien", amount_rupees=980.0, rule="LIBR", refs=["T99"])
    assert (r.status, "T99" in r.detail) == ("rejected", True)


def test_judge_rejects_a_number_that_no_rule_gives(case):
    r = judge(case, account_id="A3", action="lien", amount_rupees=2_51_00_000.0, rule="FIFO")
    assert r.status == "rejected" and "matches no tracing rule" in r.detail


def test_judge_rejects_a_figure_attributed_to_the_wrong_rule(case):
    r = judge(case, account_id="A4", action="lien", amount_rupees=1_200.0, rule="FIFO", refs=["A4"])
    assert r.status == "rejected"


def test_judge_overrules_an_unjustified_full_freeze(case):
    r = judge(case, account_id="A3", action="full_freeze", amount_rupees=2_51_00_000.0)
    assert r.status == "overruled"


def test_gate_retries_once_on_invalid_json(monkeypatch):
    scripted(monkeypatch, [{"wrong": 1}, {"subject": "s", "body": "b"}])
    gate = Gate(enabled=True)
    answer, seconds = gate.ask("t", "prompt", agents.Draft)
    assert answer == agents.Draft(subject="s", body="b")
    assert (len(gate.calls), seconds) == (2, 4.0)


def test_drafter_falls_back_to_the_template_when_figures_are_wrong(monkeypatch, case):
    s, tr, signals, decisions, _ = case
    spec = next(x for x in plan_letters(s, tr, decisions, signals) if x.kind == "lien_instruction")
    allowed = allowed_amounts(spec.decision, tr.accounts[spec.account_id], tr.edges, s.notice.flagged,
                              s.complaint.amount_lost)
    bad = {"subject": "Lien", "body": "Hold ₹2.5 crore."}
    prompts_sent = scripted(monkeypatch, [bad, bad])
    out = agents.draft_letter(Gate(enabled=True), spec, allowed, {t.utr for t in s.transactions},
                              {a.masked for a in s.accounts})
    assert out.source == "code" and len(out.rejected) == 2
    assert "rejected by the number checker" in prompts_sent[1]
    assert rupees(980) in allowed and "₹980.00" in out.body


def test_drafter_keeps_a_model_letter_whose_figures_check_out(monkeypatch, case):
    s, tr, signals, decisions, _ = case
    spec = next(x for x in plan_letters(s, tr, decisions, signals) if x.kind == "lien_instruction")
    allowed = allowed_amounts(spec.decision, tr.accounts[spec.account_id], tr.edges, s.notice.flagged,
                              s.complaint.amount_lost)
    scripted(monkeypatch, [{"subject": "Lien of ₹980.00", "body": "Release ₹2,50,99,020.00."}])
    out = agents.draft_letter(Gate(enabled=True), spec, allowed, set(), set())
    assert (out.source, out.numbers_checked, out.rejected) == ("model", 2, [])


def test_pattern_explanations_with_bad_citations_are_replaced(monkeypatch, case):
    s, _, signals, _, known = case
    scripted(monkeypatch, [{"accounts": [
        {"account_id": "A2", "explanation": "Mule. Refs: A2", "refs": ["A2", "T1"]},
        {"account_id": "A4", "explanation": "See T42.", "refs": ["T42"]},
    ]}])
    explained, findings, source, _ = agents.explain_patterns(Gate(enabled=True), s, signals, known)
    by_acc = {e.account_id: e.explanation for e in explained}
    assert source == "model" and by_acc["A2"] == "Mule."
    assert "T42" not in by_acc["A4"] and len(findings) == 1


def test_disabled_gate_never_calls_the_model(monkeypatch, case):
    monkeypatch.setattr(llm, "chat", lambda *a, **k: pytest.fail("model called"))
    s, tr, signals, decisions, _ = case
    args, source, _ = agents.advocate(Gate(enabled=False), "victim", s, tr, decisions, signals)
    assert source == "code" and args.claims
