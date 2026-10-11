# LienLine — build spec (shared contract for backend and web)

## The problem (one paragraph)
In India a cyber-fraud victim reports on NCRP / helpline 1930; police send banks notices (Section 106 BNSS) through I4C's CFCFRMS and banks put holds on the accounts the money passed through. Banks routinely freeze the **whole account** even when the traceable disputed amount is tiny. Courts struck this down in 2026: MP High Court (Archana v State of MP, 27 Jul 2026) — a liquor business account with Rs 2.51 crore frozen over a suspected Rs 980; Rajasthan HC (Shree Balaji Enterprises v RBI, 20 Aug 2026) — 105 petitions, 14 guidelines; both say: lien only the identifiable disputed amount. Supreme Court (4 Aug 2026) ordered an RBI debit-hold SOP; MHA/I4C SOP of 2 Jan 2026 sets grievance clocks (7 / 15 / 90 days). Only Rs 18.05 crore restored across 36,290 cases vs Rs 11,158 crore "saved" since 2021. **No tool computes the identifiable disputed amount per account from the money trail.**

**LienLine** = a team of agents that turns a fraud complaint + bank ledgers into a provably proportionate decision per account (lien the traceable amount / justified full freeze / release), with deadlines tracked, letters drafted, every number verified by code, and a bank nodal officer approving.

## Repository layout
```
backend/        Python 3.12, uv, FastAPI. package `lienline`
  lienline/models.py     pydantic models below
  lienline/simulate.py   deterministic scenario generator (seeded)
  lienline/trace.py      tracing engine: FIFO, LIFO, PRO_RATA, LIBR
  lienline/decide.py     per-account policy decision (lien / freeze / release) with reasons
  lienline/clocks.py     SOP + court-guideline deadlines, each rule with a citation
  lienline/verify.py     independent replay + checks of every number the agents output
  lienline/agents.py     model-backed agents (intake, advocates, drafter, explainer) + deterministic fallbacks
  lienline/llm.py        copy of ../_kit/llm.py (OpenAI-compatible: GEMINI_API_KEY / NEBIUS_API_KEY / LLM_BASE_URL / local Ollama gemma4:e4b)
  lienline/pipeline.py   orchestrates a run, emits the event stream (below)
  lienline/server.py     FastAPI: GET /api/health, GET /api/cases, POST /api/run/{case_id} (SSE event stream), POST /api/decision
  scripts/record.py      runs every scenario with the real model and writes web/public/runs/<case_id>.json
  tests/                 pytest: tracing rules on hand-computed examples, conservation, verifier catches tampering, clocks
web/            Vite + React + TypeScript. Reads web/public/runs/*.json (static replay on Vercel); if /api/health answers (local), can run live via SSE.
docs/           deck (PDF), screenshots
```

## Money: always integer paise. Display as ₹ with Indian grouping (12,34,567.89).

## Scenario / run JSON (web/public/runs/<case_id>.json) — THE CONTRACT
```jsonc
{
  "case_id": "c1-archana",                       // stable slug
  "title": "₹980 dispute, ₹2.51 crore frozen",
  "summary": "one sentence for the case list",
  "generated_at": "2026-10-12T10:00:00+05:30",
  "model": {"backend": "ollama", "chat_model": "gemma4:e4b", "calls": 7, "tokens": 12345},
  "complaint": {
    "ack_no": "31509240012345", "filed_at": "...ISO...", "victim": {"name": "...", "account_id": "A1"},
    "amount_lost": 9800000, "channel": "UPI", "narrative": "free text the intake agent reads",
    "police_station": "Cyber PS, Bhopal", "io": "SI R. Verma"
  },
  "notice": {"text": "free text of the police notice the intake agent reads", "issued_at": "...", "section": "106 BNSS",
             "flagged": [{"account_id": "A3", "amount": 98000}]},
  "banks": [{"id": "HDFC", "name": "HDFC Bank", "kind": "private"}],
  "accounts": [{"id": "A3", "bank": "HDFC", "masked": "XXXX4421", "holder": "Shree Balaji Wines", "kind": "merchant",
               "role": "victim|mule_l1|mule_l2|cashout|merchant|innocent", "kyc_age_days": 2900,
               "opening_balance": 25100000, "complaints_linked": 1, "registry_hit": false}],
  "transactions": [{"id": "T7", "utr": "426812345678", "ts": "...ISO...", "from": "A1", "to": "A3", "amount": 98000,
                    "channel": "UPI|IMPS|NEFT|RTGS|ATM|POS|CASH", "tainted_origin": true, "note": "..."}],
  "trace": {
    "as_of": "...ISO...",
    "rules": ["FIFO", "LIFO", "PRO_RATA", "LIBR"],
    "policy_rule": "LIBR",
    "accounts": {
      "A3": {
        "by_rule": {"FIFO": 98000, "LIFO": 98000, "PRO_RATA": 98000, "LIBR": 98000},   // traceable tainted paise held now
        "balance_now": 25120000,
        "series": [{"ts": "...", "balance": 25198000, "tainted": {"FIFO": 98000, "LIFO": 98000, "PRO_RATA": 98000, "LIBR": 98000}}],
        "outflows": [{"txn": "T9", "to": "A5", "tainted": {"FIFO": 50000, "LIFO": 0, "PRO_RATA": 1950, "LIBR": 0}}]
      }
    },
    "edges": [{"txn": "T7", "from": "A1", "to": "A3", "amount": 98000, "tainted": {"FIFO": 98000, "LIFO": 98000, "PRO_RATA": 98000, "LIBR": 98000}}],
    "conservation": {"lost": 9800000, "held": 9000000, "cashed_out": 600000, "untraced": 200000}   // under policy_rule; must sum to lost
  },
  "decisions": [{"account_id": "A3", "action": "lien|full_freeze|release", "amount": 98000,
                 "current_hold": 25120000, "released_by_change": 25022000,
                 "reasons": [{"text": "...", "refs": ["T7", "A3"]}], "confidence": "high|medium|low",
                 "range": {"min": 0, "max": 98000}}],
  "clocks": [{"id": "grievance_forward", "account_id": "A3", "label": "Forward grievance to IO", "start": "...", "due": "...",
              "rule": "MHA/I4C SOP 2 Jan 2026, cl. 10", "source": "https://...", "status": "running|met|breached"}],
  "events": [   // the agent run, in order; the UI replays these with their relative timing
    {"t": 0.0, "agent": "Intake", "kind": "model|code|human", "type": "start|message|tool|check|result|debate|letter|approval",
     "text": "Read the police notice: 1 account, ₹980 flagged.", "refs": ["A3", "T7"], "data": {}, "ok": true}
  ],
  "letters": [{"id": "L1", "account_id": "A3", "kind": "lien_instruction|release_notice|grievance_reply|full_freeze_justification",
               "to": "Branch Manager, HDFC Bank", "subject": "...", "body": "...", "verified": true, "numbers_checked": 4}],
  "verification": {"passed": true, "checks": [{"name": "conservation", "ok": true, "detail": "..."}]}
}
```
Also `web/public/runs/index.json`: `[{case_id, title, summary, accounts, banks, lost, held_before, held_after, status}]`.

## Agents (the event stream names these)
1. **Intake** (model): reads `notice.text` + `complaint.narrative`, extracts accounts, UTRs, amounts; **code cross-checks** each against the ledgers (unknown UTR → rejected).
2. **Tracer** (code): runs all four rules over the multi-bank ledgers (hop by hop, chronological), produces `trace`.
3. **Pattern analyst** (code features + model explanation): mule signals per account (pass-through ratio, velocity, fan-in from multiple complaints, KYC age, registry hit).
4. **Victim's advocate** and **Account holder's advocate** (model): each argues lien size per contested account, must cite txn/account ids; **code rejects** any argument whose citations don't exist or whose numbers don't match the trace.
5. **Decider** (code policy): lien = traceable amount under `policy_rule` (LIBR, the legal tracing standard); full freeze only with ≥2 mule signals incl. registry hit or ≥3 linked complaints; release when traceable = 0.
6. **Clock keeper** (code): SOP and court-guideline deadlines with citations.
7. **Drafter** (model): letters (lien instruction, release notice, grievance reply); **verifier** checks every number in each letter equals the decision.
8. **Verifier** (code): replays ledgers independently, conservation (held + cashed_out + untraced = lost), decisions ≤ balances, letters' numbers.
9. **Nodal officer** (human): approves / edits each decision in the UI.

## Scenarios (seeded, realistic, synthetic — real complaint data is not public)
- `c1-archana`: one ₹980 credit into a long-standing merchant account holding ₹2.51 crore → lien ₹980, release ₹2.50 crore (mirrors the MP HC case).
- `c2-digital-arrest`: ₹18.4 lakh "digital arrest" victim → L1 mule (new account) → splits to 6 accounts in 4 banks within 40 min → ATM cash-outs, gold merchant, a freelancer paid ₹12,000 for real work hours later, round-tripping between two mules → per-account liens; rules disagree; freelancer released.
- `c3-rules-disagree`: an account with heavy legitimate turnover where FIFO / LIFO / PRO_RATA / LIBR give very different amounts → shows the range and why LIBR is chosen.
- `c4-hardened-mule`: account linked to 7 complaints + registry hit + 98% pass-through → justified full freeze with reasons.
