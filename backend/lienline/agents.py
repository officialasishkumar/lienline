"""The model-backed agents and the code that checks them.

Each agent asks the model for JSON matching a pydantic schema. Code then checks every id and
number in the answer against the ledgers; anything that does not check out is rejected and
the rejection is shown in the event stream. Every agent has a deterministic fallback, used
when no model is available (tests, CI, the static site) or when the model fails twice.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, TypeVar

from pydantic import BaseModel, BeforeValidator, ValidationError

from lienline import llm, prompts
from lienline.letters import PURPOSE, LetterSpec, template
from lienline.models import RULES, Decision, Scenario, Signal, Trace, Txn
from lienline.money import from_rupees, inr
from lienline.patterns import full_freeze_justified, present
from lienline.verify import figure_problems

T = TypeVar("T", bound=BaseModel)
Source = Literal["model", "code"]
Text = Annotated[str, BeforeValidator(lambda v: str(v))]  # models sometimes return UTRs as numbers


# ---------------------------------------------------------------- model access


@dataclass
class ModelCall:
    step: str
    seconds: float
    tokens: int
    cached: bool


@dataclass
class Gate:
    """Whether the model is used for this run, plus a log of every call made."""

    enabled: bool
    calls: list[ModelCall] = field(default_factory=list)

    @classmethod
    def auto(cls, use_model: bool | None = None) -> Gate:
        """Use the model if one is reachable, unless ``LIENLINE_MODEL=off`` or the caller says otherwise."""
        if use_model is None:
            use_model = os.environ.get("LIENLINE_MODEL") != "off" and llm.describe_backend()["backend"] != "none"
        return cls(enabled=use_model)

    def backend(self) -> dict[str, str]:
        return llm.describe_backend() if self.enabled else {"backend": "none", "chat_model": "deterministic"}

    def ask(self, step: str, prompt: str, schema: type[T], max_tokens: int = 2048) -> tuple[T | None, float]:
        """The validated answer (or None) and the model seconds it took. One corrective retry."""
        if not self.enabled:
            return None, 0.0
        shape = json.dumps(schema.model_json_schema())
        full = f"{prompt}\n\nReturn one JSON object matching this JSON Schema exactly:\n{shape}"
        seconds = 0.0
        for _ in range(2):
            try:
                res = llm.chat(full, step=step, system=prompts.SYSTEM, json_mode=True, max_tokens=max_tokens)
            except (RuntimeError, ValueError):
                return None, seconds
            self.calls.append(ModelCall(step, res["seconds"], res.get("tokens", 0), res["cached"]))
            seconds += res["seconds"]
            try:
                return schema.model_validate(_unwrap(res["json"], schema)), seconds
            except ValidationError as e:
                full = f"{full}\n\nYour previous answer failed validation:\n{e}\nReturn corrected JSON only."
        return None, seconds


def _unwrap(raw: Any, schema: type[BaseModel]) -> Any:
    """Accept {"Schema": {...}} or a one-item list around the object the schema describes."""
    if isinstance(raw, list) and len(raw) == 1:
        raw = raw[0]
    if isinstance(raw, dict) and len(raw) == 1 and not set(raw) & set(schema.model_fields):
        inner = next(iter(raw.values()))
        if isinstance(inner, dict):
            return inner
    return raw


# ---------------------------------------------------------------- intake


class NoticeLine(BaseModel):
    masked: Text
    amount_rupees: float
    utr: Text


class IntakeExtraction(BaseModel):
    notice_lines: list[NoticeLine]
    victim_utrs: list[Text]
    amount_lost_rupees: float


@dataclass
class Finding:
    """One code check on something an agent said."""

    item: str
    ok: bool
    detail: str
    refs: list[str]


def intake_fallback(scenario: Scenario) -> IntakeExtraction:
    """Regex extraction from the notice's numbered lines and the narrative."""
    lines = [NoticeLine(masked=m, amount_rupees=float(a.replace(",", "")), utr=u) for m, a, u in re.findall(
        r"A/c (XXXX\d{4}).*?: ₹([\d,]+\.\d{2}) via UTR (\d{12})", scenario.notice.text)]
    narrative = scenario.complaint.narrative
    amounts = [float(a.replace(",", "")) for a in re.findall(r"Rs ([\d,]+)", narrative)]
    total = re.search(r"Total Rs ([\d,]+)", narrative)
    lost = float(total.group(1).replace(",", "")) if total else sum(amounts)
    return IntakeExtraction(notice_lines=lines, victim_utrs=re.findall(r"UTR (\d{12})", narrative),
                            amount_lost_rupees=lost)


def intake(gate: Gate, scenario: Scenario) -> tuple[IntakeExtraction, Source, float]:
    prompt = prompts.INTAKE.format(notice=scenario.notice.text, narrative=scenario.complaint.narrative)
    answer, seconds = gate.ask("intake", prompt, IntakeExtraction)
    if answer is None:
        return intake_fallback(scenario), "code", seconds
    return answer, "model", seconds


def cross_check_intake(scenario: Scenario, ex: IntakeExtraction) -> list[Finding]:
    """Every extracted UTR, account and amount against the ledgers. Unknown UTRs are rejected."""
    by_utr = {t.utr: t for t in scenario.transactions}
    by_masked = {a.masked: a for a in scenario.accounts}
    victim = scenario.complaint.victim.account_id
    findings: list[Finding] = []
    for line in ex.notice_lines:
        t = by_utr.get(line.utr)
        if t is None:
            near = _nearest_utr(line.utr, by_utr)
            hint = (f"; nearest ledger UTR is {near.utr} ({near.id}), likely a typing error in the notice"
                    if near else "")
            findings.append(Finding(f"UTR {line.utr}", False, f"UTR {line.utr} is not in any bank's ledger: "
                                    f"rejected{hint}. Held for the IO to confirm.", [near.id] if near else []))
            continue
        acc = by_masked.get(line.masked)
        if acc is None or acc.id != t.to:
            findings.append(Finding(f"A/c {line.masked}", False, f"UTR {line.utr} ({t.id}) credited {t.to}, not "
                                    f"{line.masked}: rejected.", [t.id, t.to]))
            continue
        received = sum(x.amount for x in scenario.transactions if x.to == acc.id and x.from_ != "EXT")
        amount = from_rupees(line.amount_rupees)
        ok = amount <= received
        findings.append(Finding(f"A/c {line.masked}", ok, f"{t.id} credited {acc.id} ({acc.holder}); the notice's "
                                f"{inr(amount)} is {'within' if ok else 'more than'} the {inr(received)} the ledgers "
                                f"show it received from traced accounts.", [t.id, acc.id]))
    origin = [t for t in scenario.transactions if t.tainted_origin]
    for utr in ex.victim_utrs:
        t = by_utr.get(utr)
        ok = t is not None and t.from_ == victim
        findings.append(Finding(f"Victim UTR {utr}", ok, f"{t.id}: {inr(t.amount)} from the victim's account {victim}"
                                if ok and t else f"UTR {utr} is not a debit from the victim's account: rejected.",
                                [t.id, victim] if ok and t else []))
    lost = from_rupees(ex.amount_lost_rupees)
    ledger_lost = sum(t.amount for t in origin)
    ok = lost == ledger_lost == scenario.complaint.amount_lost
    plural = "s" if len(origin) != 1 else ""
    findings.append(Finding("Amount lost", ok, f"Complaint states {inr(lost)}; the victim's ledger shows "
                            f"{inr(ledger_lost)} leaving in {len(origin)} transfer{plural}.", [t.id for t in origin]))
    return findings


def _nearest_utr(utr: str, by_utr: dict[str, Txn]) -> Txn | None:
    """A ledger UTR differing in at most two digit positions (a transposition or a slip)."""
    for known, t in by_utr.items():
        if len(known) == len(utr) and sum(a != b for a, b in zip(known, utr, strict=True)) <= 2:
            return t
    return None


# ---------------------------------------------------------------- pattern analyst


class Explanation(BaseModel):
    account_id: Text
    explanation: str
    refs: list[Text]


class Explanations(BaseModel):
    accounts: list[Explanation]


def pattern_features(scenario: Scenario, signals: dict[str, list[Signal]]) -> list[dict[str, Any]]:
    """The code-computed features the model is asked to explain (no roles: those are the answer)."""
    out = []
    for acc_id, sigs in signals.items():
        a = scenario.account(acc_id)
        out.append({"account_id": acc_id, "holder": a.holder, "type": a.kind, "kyc_age_days": a.kyc_age_days,
                    "signals_present": [{"signal": s.id, "detail": s.label, "refs": s.refs} for s in present(sigs)],
                    "signals_absent": [s.id for s in sigs if not s.present]})
    return out


def explain_fallback(scenario: Scenario, signals: dict[str, list[Signal]]) -> list[Explanation]:
    out = []
    for acc_id, sigs in signals.items():
        found = present(sigs)
        if full_freeze_justified(sigs):
            text = f"{len(found)} mule signals including a registry hit or repeated complaints: " + \
                   "; ".join(s.label for s in found) + ". Consistent with a mule account."
        elif found:
            text = "Some mule signals (" + "; ".join(s.label for s in found) + \
                   "), but no registry hit and fewer than 3 linked complaints."
        else:
            text = "No mule signals: the pattern looks like an ordinary customer or merchant."
        out.append(Explanation(account_id=acc_id, explanation=text,
                               refs=sorted({acc_id, *(r for s in found for r in s.refs)})))
    return out


def explain_patterns(gate: Gate, scenario: Scenario, signals: dict[str, list[Signal]],
                     known_ids: set[str]) -> tuple[list[Explanation], list[Finding], Source, float]:
    """Model explanations, each checked: unknown account or citation -> replaced by the code text."""
    prompt = prompts.PATTERNS.format(accounts=json.dumps(pattern_features(scenario, signals), indent=1))
    answer, seconds = gate.ask("patterns", prompt, Explanations)
    fallback = {e.account_id: e for e in explain_fallback(scenario, signals)}
    if answer is None:
        return list(fallback.values()), [], "code", seconds
    findings: list[Finding] = []
    chosen: dict[str, Explanation] = {}
    for e in answer.accounts:
        bad = [r for r in e.refs if r not in known_ids]
        if e.account_id not in signals or bad:
            findings.append(Finding(f"Explanation for {e.account_id}", False,
                                    f"cites unknown {', '.join(bad) or e.account_id}: rejected", []))
            continue
        chosen.setdefault(e.account_id, e)
    for e in chosen.values():  # small models like to repeat the refs inside the prose
        e.explanation = re.sub(r"\s*\(?Refs?:[^)]*\)?\.?\s*$", "", e.explanation).strip()
    explained = [chosen.get(acc_id, fallback[acc_id]) for acc_id in signals]
    return explained, findings, "model", seconds


# ---------------------------------------------------------------- advocates


class Claim(BaseModel):
    account_id: Text
    action: Literal["lien", "full_freeze", "release"]
    amount_rupees: float
    rule: str | None = None
    refs: list[Text]
    argument: str


class Arguments(BaseModel):
    claims: list[Claim]


Side = Literal["victim", "holder"]
Status = Literal["accepted", "overruled", "rejected"]


@dataclass
class Ruling:
    side: Side
    claim: Claim
    status: Status
    detail: str

    def as_data(self) -> dict[str, Any]:
        return {**self.claim.model_dump(), "amount": from_rupees(self.claim.amount_rupees), "status": self.status,
                "accepted": self.status != "rejected", "detail": self.detail}


def contested_table(scenario: Scenario, trace: Trace, decisions: list[Decision],
                    signals: dict[str, list[Signal]]) -> list[dict[str, Any]]:
    """Facts each advocate sees per account: balance, the four rules' figures, signals, tainted credits."""
    flagged = {f.account_id: f.amount for f in scenario.notice.flagged}
    rows = []
    for d in decisions:
        a, at = scenario.account(d.account_id), trace.accounts[d.account_id]
        credits = [{"txn": e.txn, "from": e.from_, "amount_rupees": inr(e.amount)[1:]}
                   for e in trace.edges if e.to == d.account_id and any(e.tainted.values())]
        rows.append({
            "account_id": d.account_id, "holder": a.holder, "type": a.kind, "balance_rupees": inr(at.balance_now)[1:],
            "traceable_rupees_by_rule": {r: inr(v)[1:] for r, v in at.by_rule.items()},
            "registry_hit": a.registry_hit, "complaints_linked": a.complaints_linked,
            "mule_signals": [s.label for s in present(signals[d.account_id])], "tainted_credits": credits,
            "notice_flagged_rupees": inr(flagged.get(d.account_id, 0))[1:],
        })
    return rows


def advocate_fallback(side: Side, scenario: Scenario, trace: Trace, decisions: list[Decision],
                      signals: dict[str, list[Signal]]) -> Arguments:
    """Victim: a full freeze when two or more signals show, else the police notice's figure when it is larger
    than anything traceable, else the largest figure any rule gives. Holder: the smallest figure any rule
    gives (a release when one rule finds nothing)."""
    flagged = {f.account_id: f.amount for f in scenario.notice.flagged}
    claims = []
    for d in decisions:
        at = trace.accounts[d.account_id]
        credits = [e.txn for e in trace.edges if e.to == d.account_id and any(e.tainted.values())]
        refs = [d.account_id, *credits]
        if side == "victim" and len(present(signals[d.account_id])) >= 2:
            claims.append(Claim(account_id=d.account_id, action="full_freeze", amount_rupees=at.balance_now / 100,
                                refs=refs, argument="Several mule signals: freeze the whole balance."))
            continue
        noticed = min(flagged.get(d.account_id, 0), at.balance_now)
        if side == "victim" and noticed > max(at.by_rule.values()):
            claims.append(Claim(account_id=d.account_id, action="lien", amount_rupees=noticed / 100, rule="NOTICE",
                                refs=refs, argument="Hold what the police notice flagged against this account."))
            continue
        pick = max if side == "victim" else min
        rule = pick(RULES, key=lambda r: at.by_rule[r])
        amount = at.by_rule[rule]
        action = "release" if amount == 0 else "lien"
        claims.append(Claim(account_id=d.account_id, action=action, amount_rupees=amount / 100, rule=rule, refs=refs,
                            argument=f"{rule} gives {inr(amount)}, the {'largest' if side == 'victim' else 'smallest'}"
                                     f" traceable figure."))
    return Arguments(claims=claims)


def advocate(gate: Gate, side: Side, scenario: Scenario, trace: Trace, decisions: list[Decision],
             signals: dict[str, list[Signal]]) -> tuple[Arguments, Source, float]:
    table = json.dumps(contested_table(scenario, trace, decisions, signals), indent=1)
    if side == "victim":
        prompt = prompts.VICTIM_ADVOCATE.format(victim=scenario.complaint.victim.name,
                                                lost=inr(scenario.complaint.amount_lost)[1:], accounts=table)
    else:
        prompt = prompts.HOLDER_ADVOCATE.format(accounts=table)
    answer, seconds = gate.ask(f"advocate_{side}", prompt, Arguments, max_tokens=3072)
    if answer is None:
        return advocate_fallback(side, scenario, trace, decisions, signals), "code", seconds
    return answer, "model", seconds


def judge(side: Side, claim: Claim, trace: Trace, decisions: dict[str, Decision],
          signals: dict[str, list[Signal]], known_ids: set[str]) -> Ruling:
    """Code ruling on one claim: bad citations or numbers -> rejected; valid but not policy -> overruled."""
    def rule(status: Status, detail: str) -> Ruling:
        return Ruling(side, claim, status, detail)

    d = decisions.get(claim.account_id)
    if d is None:
        return rule("rejected", f"{claim.account_id} is not a contested account")
    bad = [r for r in claim.refs if r not in known_ids]
    if bad:
        return rule("rejected", f"cites {', '.join(bad)}, which is not in any ledger")
    at = trace.accounts[claim.account_id]
    amount = from_rupees(claim.amount_rupees)
    match claim.action:
        case "lien":
            lo, hi = min(at.by_rule.values()), max(at.by_rule.values())
            if amount not in at.by_rule.values():
                return rule("rejected", f"{inr(amount)} matches no tracing rule; the four rules give {inr(lo)} to "
                                        f"{inr(hi)}")
            if claim.rule not in RULES or at.by_rule[claim.rule] != amount:  # type: ignore[index]
                return rule("rejected", f"{inr(amount)} is not the {claim.rule} figure")
        case "release":
            if amount != 0 or min(at.by_rule.values()) != 0:
                return rule("rejected", f"no tracing rule finds {inr(0)} here; the smallest figure is "
                                        f"{inr(min(at.by_rule.values()))}")
        case "full_freeze":
            if amount != at.balance_now:
                return rule("rejected", f"{inr(amount)} is not the balance; a full freeze holds {inr(at.balance_now)}")
            if not full_freeze_justified(signals[claim.account_id]):
                return rule("overruled", "numbers check out, but policy allows a full freeze only with a registry "
                                         "hit or 3+ linked complaints among 2+ signals")
    if (claim.action, amount) == (d.action, d.amount):
        return rule("accepted", "citations and figures check out, and match the policy decision")
    return rule("overruled", f"citations and figures check out, but policy decides {d.action} of {inr(d.amount)} "
                             f"under {trace.policy_rule}")


# ---------------------------------------------------------------- drafter


class Draft(BaseModel):
    subject: str
    body: str


@dataclass
class Drafted:
    subject: str
    body: str
    source: Source
    seconds: float
    numbers_checked: int
    rejected: list[list[str]]  # problems found in each rejected model draft


def draft_letter(gate: Gate, spec: LetterSpec, allowed: set[int], utrs: set[str], masked: set[str]) -> Drafted:
    """The model drafts; the number checker must pass it, else one retry, else the template."""
    prompt = prompts.DRAFTER.format(kind=spec.kind.replace("_", " "), to=spec.to, purpose=PURPOSE[spec.kind],
                                    facts="\n".join(f"- {f}" for f in spec.facts), bank=spec.bank)
    rejected: list[list[str]] = []
    seconds = 0.0
    ask = prompt
    for _ in range(2):
        draft, s = gate.ask(f"draft_{spec.id}", ask, Draft)
        seconds += s
        if draft is None:
            break
        problems, n = figure_problems(f"{draft.subject}\n{draft.body}", allowed, utrs, masked)
        if not problems:
            return Drafted(draft.subject, draft.body, "model", seconds, n, rejected)
        rejected.append(problems)
        ask = prompts.DRAFTER_RETRY.format(prompt=prompt, problems="\n".join(f"- {p}" for p in problems))
    subject, body = template(spec)
    _, n = figure_problems(f"{subject}\n{body}", allowed, utrs, masked)
    return Drafted(subject, body, "code", seconds, n, rejected)
