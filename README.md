# LienLine

**When a cyber-fraud complaint names a bank account, freeze only the money the trail proves — not the whole account.**

- Live demo (replays real recorded runs): https://lienline-desk.vercel.app
- MalanHack 2026 Round 1 deck: [docs/malanhack/LienLine_MalanHack2026.pdf](docs/malanhack/LienLine_MalanHack2026.pdf) (15 slides, 25 cited sources; rebuilt by `docs/malanhack/build_deck.py`)
- Spec: [SPEC.md](SPEC.md) · Backend: [backend/README.md](backend/README.md) · Web: [web/README.md](web/README.md)

## The problem
Indian banks put holds on accounts named in NCRP / CFCFRMS cyber-fraud notices and routinely freeze the whole account, even when the traceable disputed amount is tiny: the MP High Court (Archana v State of MP, 27 Jul 2026) found Rs 2.51 crore frozen over a suspected Rs 980; the Rajasthan High Court decided 105 such petitions together (20 Aug 2026); the Supreme Court ordered an RBI debit-hold SOP (4 Aug 2026). Rs 8,189 crore is already under lien (Lok Sabha, Jul 2026). No tool computes, per account, how much of the fraud money it actually holds.

## What LienLine does
A team of agents turns a police notice, the victim's complaint and the bank ledgers into a provably proportionate decision per account:

| Agent | Kind | Job |
|---|---|---|
| Intake | model, code-checked | reads the notice and complaint; every UTR and amount is checked against the ledgers |
| Tracer | code | follows the money hop by hop under four legal tracing rules: FIFO, LIFO, pro-rata, LIBR |
| Pattern analyst | code + model | mule signals computed in code, explained in words |
| Victim's / account holder's advocates | model, code-checked | argue each hold; claims citing non-existent transactions or wrong numbers are struck out |
| Decider | code | lien the LIBR amount; full freeze only with recorded reasons; release when nothing is traceable |
| Clock keeper | code | SOP and court deadlines, each with a citation |
| Drafter | model, code-checked | lien, release and grievance letters; every number re-derived |
| Verifier | code | independent replay: conservation (held + cashed out + untraced = lost), bounds, citations, letters |
| Nodal officer | person | approves or edits every hold |

Across the four recorded scenarios (synthetic multi-bank ledgers mirroring court-recorded cases), frozen money falls from Rs 2.75 crore to Rs 6.7 lakh while every traceable rupee stays on hold. Runs were recorded with a local model (gemma4:e4b via Ollama); any OpenAI-compatible model works.

## Run it
```bash
cd backend && uv sync && uv run pytest -q          # 69 tests
uv run python -m lienline.server                   # API + live runs (SSE)
uv run python scripts/record.py                    # re-record the scenarios into web/public/runs
cd ../web && npm install && npm run dev            # the desk; static build: npm run build
```
