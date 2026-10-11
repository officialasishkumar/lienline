# LienLine backend

Python 3.12, [uv](https://docs.astral.sh/uv/), FastAPI, pydantic v2. Money is integer paise everywhere.

```
lienline/
  models.py     the run-JSON contract (SPEC.md) as pydantic models
  simulate.py   four seeded, synthetic cases (fictional banks, people and businesses)
  trace.py      tracing engine: FIFO, LIFO, PRO_RATA, LIBR over every bank's ledger, hop by hop
  patterns.py   mule signals computed by code (registry hit, linked complaints, account age,
                pass-through, rapid movement, round trips)
  decide.py     policy: lien the LIBR-traceable amount; full freeze only with >= 2 signals incl. a
                registry hit or >= 3 complaints; release when nothing is traceable
  clocks.py     SOP and court deadlines as data, each with its citation
  letters.py    which letters a case needs, the facts each may state, plain templates
  agents.py     model agents (intake, pattern analyst, two advocates, drafter) + the code that checks them
  prompts.py    every prompt, in one place
  verify.py     independent replay: LIBR in closed form, conservation, decisions, letter figures, citations
  pipeline.py   runs the agents in order and emits the event stream
  server.py     local API with SSE for live runs
  llm.py        the shared model kit (OpenAI-compatible; local Ollama gemma4:e4b by default)
scripts/record.py   records every case into ../web/public/runs/ for the static site
```

## Run, test, record

```bash
uv sync
uv run pytest -q                         # no model needed: tests force the deterministic fallbacks
uv run lienline                          # API on http://localhost:8300
uv run python scripts/record.py          # re-record all cases with the real model (gemma4:e4b on Ollama)
uv run python scripts/record.py --no-model c1-archana   # deterministic fallbacks only
uv run python -m lienline.verify ../web/public/runs/c*.json   # re-verify recorded runs
```

Model backend selection is the kit's: `GEMINI_API_KEY`, `NEBIUS_API_KEY`, `LLM_BASE_URL`+`LLM_MODEL`,
`AI_GATEWAY_API_KEY`, else local Ollama. `LIENLINE_MODEL=off` forces the fallbacks. Every model call is
cached in `.cache/llm/`, so a re-record replays the same answers with their original timings.

## How the tracing works

Each account keeps one taint pool per rule. A debit asks the pool what share of the outgoing amount is the
victim's money; that share is credited to the receiving account's pool, so taint moves hop by hop in time
order across banks. `CASH` (ATM or branch withdrawal) and `EXT` (an account outside the traced banks) are
sinks; per rule, `held + cashed_out + untraced == lost` exactly, because shares are floored integer paise
and a pool never pays out more taint than it holds.

| Rule | A debit spends... |
|---|---|
| FIFO (Clayton's case) | the oldest money first (opening balance, then credits in order) |
| LIFO | the newest money first |
| PRO_RATA (rolling charge) | taint in proportion to the tainted share of the balance |
| LIBR (Re Hallett + lowest intermediate balance) | the holder's own money first; taint is capped by the lowest balance since it arrived and is never refilled by later clean credits |

LIBR is the policy rule. The verifier recomputes it with the closed form
`held = D + min(0, min_k(B_k - D_k))` (D: cumulative tainted credits; B_k: balance after debit k) and
shares no code with the tracer; a property test checks the two agree on random ledgers.

## API

| Method | Path | |
|---|---|---|
| GET | `/api/health` | `{ok, model, live_model}` |
| GET | `/api/cases` | `[{case_id, title, summary}]` |
| POST | `/api/run/{case_id}` | SSE: one `data: <event>` per pipeline event, then `event: run` (full run JSON), then `event: done` |
| POST | `/api/decision` | `{case_id, account_id, verdict: approve\|edit, action?, amount? (paise), officer, note}`; edits above the traceable amount or a full freeze without the policy's signals need a `note`; nothing above the balance |

Run JSON is exactly SPEC.md, plus three additive fields: `grievances` (the holders' grievances the clocks run
from), `trace.conservation_by_rule`, and per-point `series[].txn` / `outflows[].amount`. Transaction
endpoints `CASH` and `EXT` are sinks, not accounts.

## Sources for the clocks

* MHA/I4C SOP of 2 Jan 2026 on NCRP/CFCFRMS, as summarised at
  <https://www.prashantkanha.com/ncrp-cfcfrms-cyber-fraud-sop-2026/>. That summary puts the 7 / 15 / 90-day
  grievance clocks in section 9.1 (section 10 covers restoration). Where it does not say what starts a clock,
  the rule label says how LienLine measures it.
* MP High Court, Archana v State of MP, 27 Jul 2026, and Rajasthan High Court, Shree Balaji Enterprises v RBI,
  20 Aug 2026, cited by their LiveLaw report URLs (these returned 404 when re-fetched on 11 Oct 2026, so their
  text is not re-checked here). LienLine relies on them only for the holding that a hold is limited to the
  identifiable disputed amount. No duration is taken from them: the rule is checked as a compliance condition
  from the moment of the hold, not as a timer.

All case data is synthetic. Real complaint data is not public.
