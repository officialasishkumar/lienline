"""The event stream, the files the web app reads, and the local API."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from lienline import server
from lienline.agents import Gate
from lienline.models import Run
from lienline.money import group_indian, inr, rupees
from lienline.pipeline import index_entry, rebuild_index, run_case, save
from lienline.simulate import SCENARIOS, load


def test_inr_uses_indian_grouping():
    assert group_indian(25100000) == "2,51,00,000"
    assert inr(rupees(2_51_00_000)) == "₹2,51,00,000.00"
    assert inr(98_000) == "₹980.00" and inr(5) == "₹0.05" and inr(-150) == "-₹1.50"


@pytest.mark.parametrize("case_id", list(SCENARIOS))
def test_run_emits_every_agent_in_order(case_id):
    run = run_case(load(case_id), Gate(enabled=False))
    ts = [e.t for e in run.events]
    assert ts == sorted(ts)
    agents_seen = list(dict.fromkeys(e.agent for e in run.events))
    assert agents_seen == ["Intake", "Tracer", "Pattern analyst", "Victim's advocate", "Account holder's advocate",
                           "Decider", "Clock keeper", "Drafter", "Verifier", "Nodal officer"]
    assert run.verification.passed and run.model.calls == 0


def test_rejected_advocate_claims_are_shown_as_failed_debate_events():
    run = run_case(load("c2-digital-arrest"), Gate(enabled=False))
    rejected = [e for e in run.events if e.type == "debate" and not e.ok]
    assert rejected and all(e.data["claims"][0]["status"] == "rejected" for e in rejected)
    assert "matches no tracing rule" in rejected[0].text


def test_saved_run_round_trips_and_index_has_headlines(tmp_path):
    run = run_case(load("c1-archana"), Gate(enabled=False))
    path = save(run, tmp_path)
    raw = json.loads(path.read_text())
    assert raw["transactions"][0]["from"] == "A1"  # contract field name, not from_
    assert Run.model_validate(raw) == run
    rebuild_index(tmp_path, SCENARIOS)
    [entry] = json.loads((tmp_path / "index.json").read_text())
    assert entry == index_entry(run).model_dump()
    assert (entry["lost"], entry["held_before"], entry["held_after"]) == (
        rupees(98_000), rupees(2_51_03_570), rupees(4_550))


@pytest.fixture
def client(tmp_path, monkeypatch):
    run = run_case(load("c1-archana"), Gate(enabled=False))
    save(run, tmp_path)
    monkeypatch.setattr(server, "RUNS", tmp_path)
    monkeypatch.setattr(server, "APPROVALS", tmp_path / "approvals.json")
    return TestClient(server.app)


def test_health_and_cases(client):
    assert client.get("/api/health").json()["ok"] is True
    assert [c["case_id"] for c in client.get("/api/cases").json()] == list(SCENARIOS)


def test_live_run_streams_events_then_the_run(client):
    with client.stream("POST", "/api/run/c1-archana") as r:
        body = "".join(r.iter_text())
    events = [json.loads(line[6:]) for line in body.splitlines() if line.startswith("data: {\"t\"")]
    assert events[0]["agent"] == "Intake" and events[-1]["agent"] == "Nodal officer"
    run_line = body.split("event: run\ndata: ", 1)[1].split("\n", 1)[0]
    assert json.loads(run_line)["verification"]["passed"] is True
    assert body.rstrip().endswith("event: done\ndata: {}")


def test_unknown_case_is_404(client):
    assert client.post("/api/run/nope").status_code == 404


def test_officer_can_approve(client, tmp_path):
    r = client.post("/api/decision", json={"case_id": "c1-archana", "account_id": "A3", "verdict": "approve",
                                           "officer": "R. Iyer"})
    assert r.status_code == 200
    assert "approved lien ₹980.00 on A3" in r.json()["event"]["text"]
    assert json.loads((tmp_path / "approvals.json").read_text())[0]["amount"] == rupees(980)


@pytest.mark.parametrize("edit, status", [
    ({"action": "lien", "amount": rupees(5_000)}, 422),  # above traceable without a reason
    ({"action": "lien", "amount": rupees(5_000), "note": "IO asked for a margin"}, 200),
    ({"action": "lien", "amount": rupees(3_00_00_000), "note": "x"}, 422),  # above the balance
    ({"action": "full_freeze", "amount": rupees(2_51_00_000)}, 422),  # no mule signals, no reason
    ({"action": "release", "amount": rupees(1)}, 422),
])
def test_officer_edits_are_bounded(client, edit, status):
    body = {"case_id": "c1-archana", "account_id": "A3", "verdict": "edit", "officer": "R. Iyer", **edit}
    assert client.post("/api/decision", json=body).status_code == status
