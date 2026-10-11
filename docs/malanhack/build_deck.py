"""LienLine — MalanHack 2026 Round 1 deck (15 slides, 16:9 PDF).

Order follows what winning decks do (one message per slide, claim titles, big sourced numbers, a before/after, an early demo,
architecture as a flow, tables for benchmarks and costs, end on the ask) while covering MalanHack's required pillars.
Every figure is either cited ([n] = slide 15) or computed below from stated assumptions; source URLs are looked up from the
research files so no link is retyped by hand.
    uv run --with playwright python build_deck.py   ->  LienLine_MalanHack2026.pdf
"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from deck_style import CSS
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "LienLine_MalanHack2026.pdf"
RESEARCH = ROOT.parents[1] / "hackathon-projects" / "research" / "malanhack"
FACTS = json.loads((ROOT / "docs" / "deck_facts.json").read_text())
NEWS = json.loads((RESEARCH / "news-lien.json").read_text())
RUNS = ROOT / "web" / "public" / "runs"
SHOT = ROOT / "docs" / "screens" / "desk.png"
N = 15
ICONS, FLAGS = HERE / "icons", HERE / "flags"

# ---------------------------------------------------------------- sources: looked up by a distinctive substring of the URL
_ALL_URLS = re.findall(r"https?://[^\s;,'\"|)]+", json.dumps(FACTS) + json.dumps(NEWS) + (RESEARCH / "priorart-lien.json").read_text())


def url(part: str) -> str:
    hit = next((u for u in _ALL_URLS if part in u), None)
    assert hit, f"no source URL contains {part!r}"
    return hit


REFS = [  # (citation text, url)
    ("MP High Court, Archana v State of MP, WP 29117/2026, 27 Jul 2026 (LiveLaw)", url("freezing-bank-accounts-guidelines")),
    ("Rajasthan High Court, Shree Balaji Enterprises v RBI & batch, 20 Aug 2026: 105 petitions, 14 guidelines (LiveLaw)", url("rajasthan-high-court-account-freeze")),
    ("Supreme Court, In re Victims of Digital Arrest, SMW(Crl) 3/2025, order of 4 Aug 2026 (Verdictum)", url("digital-arrest-scams-interim-directions")),
    ("Lok Sabha Unstarred Question 251 (MHA), 21 Jul 2026: NCRP complaints, amount reported, lien marked, FIRs", url("AU251")),
    ("Rajya Sabha Unstarred Question 1349 (MHA), 11 Feb 2026", url("RS11022026")),
    ("The420: one Rs 4.43 crore scam froze 36,000+ accounts (Faridabad), Dec 2025", url("faridabad")),
    ("Delhi High Court, Neelkanth Pharma Logistics v HDFC Bank, 28 Feb 2025 (MediaNama)", url("medianama.com/2025/03")),
    ("Andhra Pradesh High Court, Sri Sai Wines v UoI, 22 Jun 2026 (MediaNama)", url("medianama.com/2026/07")),
    ("MHA/I4C SOP for NCRP-CFCFRMS, custody, restoration and grievance redressal, 2 Jan 2026 (summary)", url("prashantkanha")),
    ("RBI draft KYC amendment directions on bank debit holds, 11 Sep 2026 (Cyril Amarchand Mangaldas blog)", url("cyrilamarchand")),
    ("Moneylife: 2.81 million cybercrime cases in 2025, 55,484 FIRs, Rs 22,495 crore lost", url("moneylife")),
    ("SCC Times analysis of the Rajasthan HC guidelines (four conditions for a lawful freeze), 18 Sep 2026", url("scconline.com/blog/post/2026/09/18")),
    ("Kerala High Court, Kunnamangalam Co-operative Rural Bank v Inspector of Police, 2 Mar 2026 (Verdictum)", url("kunnaman")),
    ("UK Payment Systems Regulator, APP scams reimbursement dashboard (to 31 Mar 2026)", url("psr.org.uk/information-for-consumers")),
    ("Singapore: Protection from Scams Act and Anti-Scam Centre results H1 2026 (BBC; CNA)", url("bbc.com")),
    ("Australian Banking Association, Scam-Safe Accord; AFCX Fraud Reporting Exchange", url("ausbanking")),
    ("FinCEN Section 314(b) information sharing fact sheet, Jun 2026", url("fincen.gov")),
    ("LSEG: Verification of Payee mandatory in the euro area from Oct 2025", url("lseg.com")),
    ("RMA India: RBIH MuleHunter.AI live across 31 banks, Sep 2026", url("rmaindia")),
    ("CashGuard-AI (SIH 2026 project): CFCFRMS fund-block queue, GitHub", url("CashGuard")),
    ("Google Gemini API pricing (Gemini 3.1 Flash-Lite), Oct 2026", url("ai.google.dev")),
    ("Azure Retail Prices API: D4s_v5 VM and PostgreSQL Flexible Server, Central India, Oct 2026", url("prices.azure.com")),
    ("Wikipedia, List of banks in India (secondary; category counts approximate)", url("wikipedia.org/wiki/List_of_banks")),
    ("Madras High Court: police cannot freeze an entire account, only the fraud quantum, 14 Sep 2024 (The Hindu)", url("thehindu.com")),
    ("Bombay High Court (Nagpur), Kartik Yogeshwar Chatur v UoI, 20 Nov 2025 (SCC Times)", url("scconline.com/blog/post/2025/12/01")),
]


def cite(*n: int) -> str:
    return " ".join(f"[{k}]" for k in n)


# ---------------------------------------------------------------- the product's own results (recorded runs)
INDEX = json.loads((RUNS / "index.json").read_text())
BEFORE = sum(r["held_before"] for r in INDEX)
AFTER = sum(r["held_after"] for r in INDEX)
C3 = json.loads((RUNS / "c3-rules-disagree.json").read_text())


def inr(paise: float, short: bool = False) -> str:
    """Indian-grouped rupees; short=True uses lakh/crore."""
    r = paise / 100
    if short:
        if r >= 1e7:
            return f"₹{r / 1e7:.2f} crore"
        if r >= 1e5:
            return f"₹{r / 1e5:.1f} lakh"
    s = f"{r:,.0f}" if r >= 1000 else f"{r:.0f}"
    if r >= 1e5:  # Indian grouping: last three digits, then pairs
        whole = f"{int(round(r))}"
        head, tail = whole[:-3], whole[-3:]
        head = ",".join(re.findall(r"\d{1,2}", head[::-1]))[::-1]
        s = f"{head},{tail}"
    return f"₹{s}"


# ---------------------------------------------------------------- projections: stated assumptions -> slides 10-12 (Rs lakh)
FX = 88  # Rs per USD (assumption)
CASES_PER_MONTH = 25_000  # cases handled across customers at year-3 scale (assumption)
TOK_IN, TOK_OUT = 54_000, 9_000  # per case: 9 model calls (intake, analyst, 2 advocates x2 rounds, drafter x3) (measured shape, rounded)
LLM_MONTH_USD = CASES_PER_MONTH * (TOK_IN * 0.25 + TOK_OUT * 1.50) / 1e6  # Gemini 3.1 Flash-Lite [21]
TECH = [  # (item, basis, Rs per month, cited?)
    ("Application servers (x2)", "Azure D4s_v5, Central India, $0.202/h [22]", 2 * 0.202 * 730 * FX, True),
    ("Managed Postgres (ledger + audit)", "Azure PostgreSQL 4 vCore, $0.502/h [22]", 0.502 * 730 * FX, True),
    ("Model inference", f"{CASES_PER_MONTH:,} cases x 9 calls, Gemini 3.1 Flash-Lite [21]", LLM_MONTH_USD * FX, True),
    ("Monitoring, backups, logs", "estimate", 20_000, False),
    ("Security audit (CERT-In empanelled)", "Rs 3 lakh a year, estimate", 25_000, False),
]
TECH_MONTH = sum(t[2] for t in TECH)
PER_CASE = LLM_MONTH_USD * FX / CASES_PER_MONTH
RND = [("Synthetic multi-bank ledger benchmark + legal-rule encoding (lawyer review)", 6.0), ("CBS / FRMS / CFCFRMS connectors in a bank sandbox", 6.0),
       ("Model evaluation and red-teaming of the advocate agents", 3.0), ("Hindi and regional-language notices", 2.0), ("On-prem packaging for air-gapped banks", 3.0)]
RND_Y = [sum(x for _, x in RND), 25.0, 35.0]
PRICE = {"bank": 24.0, "rrb": 3.0, "state": 12.0}  # Rs lakh per customer per year (assumption)
CUST = {"bank": [1, 6, 14], "rrb": [0, 8, 20], "state": [2, 6, 12]}  # paying at year end
PILOT = [0.5, 1, 1]  # year-1 pilots at half price
CAC = {"bank": 6.0, "rrb": 0.5, "state": 2.0}  # Rs lakh per new customer (assumption)
BRAND = [2.0, 3.0, 4.0]
TEAM = [24.0, 90.0, 160.0]
TECH_Y = [TECH_MONTH * 12 / 1e5, 30.0, 45.0]


def rev(y: int) -> float:
    return sum(CUST[k][y] * PRICE[k] for k in PRICE) * PILOT[y]


def mkt(y: int) -> float:
    return sum((CUST[k][y] - (CUST[k][y - 1] if y else 0)) * CAC[k] for k in CAC) + BRAND[y]


def cost(y: int) -> float:
    return TECH_Y[y] + RND_Y[y] + TEAM[y] + mkt(y)


SAM = {"bank": (49, "commercial, small finance and payments banks (approx.) [23]"), "rrb": (28, "regional rural banks (approx.) [23]"),
       "state": (36, "States/UTs running cyber cells under the SC order [3]")}
SAM_TOTAL = sum(n * PRICE[k] for k, (n, _) in SAM.items())


# ---------------------------------------------------------------- helpers
def ic(name: str, cls: str = "") -> str:
    svg = " ".join((ICONS / f"{name}.svg").read_text().split("-->", 1)[-1].split())
    head, rest = svg.split(">", 1)
    head = re.sub(r'\s(?:class|width|height)="[^"]*"', "", head).replace("<svg", f'<svg class="ic {cls}" aria-hidden="true"', 1)
    return f"{head}>{rest}"


def flag(code: str) -> str:
    return f'<img class="flag" src="data:image/svg+xml;base64,{base64.b64encode((FLAGS / f"{code}.svg").read_bytes()).decode()}" alt="">'


def slide(i: int, kicker: str, title: str, body: str, src: str = "", cls: str = "", icon: str = "", aside: str = "") -> str:
    tag = '<span class="ptag">Projection: our assumptions</span>' if "proj" in cls else ""
    cls = cls.replace("proj", "").strip()
    return (f'<section class="slide {cls}"><div class="bar"></div><header><div class="k">{ic(icon) if icon else ""}{kicker}</div>{aside}{tag}</header>'
            f'<h1>{title}</h1><div class="body">{body}</div>'
            f'<footer><span>LienLine · MalanHack 2026 · FinTech</span><span>{"Sources: " + src if src else ""}</span><span>{i} / {N}</span></footer></section>')


S: list[str] = []

# 1 — cover
S.append(f"""<section class="slide cover"><div class="bar"></div>
<div class="hero">
 <div class="hero-l">
  <div class="k">MalanHack 2026 · FinTech · Problem Definition &amp; Solution Framework</div>
  <h1 class="giant">LienLine</h1>
  <p class="sub">When a cyber-fraud complaint names a bank account, freeze <b>only the money the trail proves</b>, not the whole account.</p>
  <p class="team">Asish Kumar · Akash Kumar &nbsp;·&nbsp; October 2026 &nbsp;·&nbsp; Live demo: lienline-desk.vercel.app</p>
 </div>
 <div class="filing">
  <div class="fh">{ic('landmark')}<span>MP High Court · 27 Jul 2026 {cite(1)}</span></div>
  <b class="fco">A liquor shop's current account</b>
  <div class="ba"><div><span>Frozen by the bank</span><b class="frz">₹2,51,00,000</b></div>{ic('arrow-right')}<div><span>Disputed amount</span><b class="lien">₹980</b></div></div>
  <div class="fverdict ok">{ic('scale')}<b>LienLine: lien ₹980, release the rest</b></div>
 </div>
</div>
<div class="brief"><span class="bk">Where the brief's five required items are</span><ol>
 <li><i>1</i><b>slides 2–4</b><span>Problem statement definition</span></li>
 <li><i>2</i><b>slides 5–7</b><span>Proposed technological architecture</span></li>
 <li><i>3</i><b>slide 9</b><span>Global benchmarking, 6 countries</span></li>
 <li><i>4</i><b>slides 10–12</b><span>Market size, revenue, costs</span></li>
 <li><i>5</i><b>slide 15</b><span>Validated references, {len(REFS)} sources</span></li>
</ol></div>
<footer><span>LienLine · MalanHack 2026 · FinTech</span><span></span><span>1 / {N}</span></footer></section>""")

# 2 — problem in big numbers
S.append(slide(2, "Problem statement", "India freezes fraud money fast, and freezes innocent money with it.", f"""
<div class="kpis">
 <div class="kpi c-red">{ic('lock-keyhole')}<h3>Marked as lien</h3><b>₹8,189 cr</b><p>held on fraud complaints, 2021–25, out of ₹55,050 crore reported lost {cite(4)}</p></div>
 <div class="kpi c-amber">{ic('network')}<h3>One scam</h3><b>36,000+</b><p>accounts frozen after a single ₹4.43 crore fraud, small merchants included {cite(6)}</p></div>
 <div class="kpi c-blue">{ic('gavel')}<h3>One High Court</h3><b>105</b><p>freeze petitions decided together, with 14 binding guidelines {cite(2)}</p></div>
 <div class="kpi c-green">{ic('hand-coins')}<h3>Given back</h3><b>₹18 cr</b><p>restored in 36,290 cases, against ₹11,158 crore "saved" since 2021 {cite(3)}</p></div>
</div>
<div class="pstate">{ic('crosshair')}<p><b>Problem statement.</b> Police notices tell banks to "freeze", often without an amount. Banks freeze whole accounts because no one computes how much of the fraud money each account actually holds.</p></div>""",
    cite(2, 3, 4, 6), icon="triangle-alert"))

# 3 — root cause: freeze vs lien
S.append(slide(3, "Problem statement · root cause", "The money trail is never measured, so the safe choice for a bank is to freeze everything.", f"""
<div class="chain">
 <div class="cn v">{ic('user-round-search')}<b>Victim</b><span>loses ₹98,000</span></div>{ic('arrow-right')}
 <div class="cn m">{ic('users')}<b>Mule account</b><span>spends it in minutes</span></div>{ic('arrow-right')}
 <div class="cn i">{ic('building-2')}<b>Liquor shop</b><span>receives ₹980 for a sale</span></div>
</div>
<div class="grid2 rc">
 <div class="card c-red"><h3>{ic('lock-keyhole')}Today</h3><p>Notice reaches the shop's bank via CFCFRMS. Bank cannot see the trail, so it freezes the account: <b>₹2.51 crore</b> locked for months {cite(1)}. Courts: "innocent recipients bear the brunt" {cite(7)}.</p></div>
 <div class="card c-green"><h3>{ic('scale')}With LienLine</h3><p>Trace the trail across banks, compute what is traceable to the fraud in each account, <b>lien ₹980</b>, release the rest, start the grievance clocks {cite(9)}, and document why.</p></div>
</div>
<p class="note2">Courts now demand exactly this test: lawful authority, a prima facie nexus, the transaction and amount identified, and a proportionate hold {cite(12)}.</p>""",
    cite(1, 7, 9, 12), icon="git-fork"))

# 4 — solution
S.append(slide(4, "Solution", "LienLine turns a complaint and the bank ledgers into a provably proportionate hold, per account.", f"""
<div class="road">
 <div>{ic('scan-text')}<b>Read</b><span>The police notice and NCRP complaint, cross-checked against real UTRs</span></div>
 <div>{ic('route')}<b>Trace</b><span>Every hop across banks under four legal tracing rules</span></div>
 <div>{ic('scale')}<b>Decide</b><span>Lien the traceable amount, freeze fully only with recorded reasons, release the rest</span></div>
 <div>{ic('file-text')}<b>Act</b><span>Letters, grievance clocks and an audit trail; a nodal officer approves</span></div>
</div>
<div class="kpis three">
 <div class="kpi c-blue"><h3>For banks</h3><p>Fewer writ petitions, a defensible record for every hold, the SC-ordered debit-hold SOP {cite(3)} met in software.</p></div>
 <div class="kpi c-green"><h3>For victims</h3><p>Every traceable rupee stays on hold; nothing recoverable is released.</p></div>
 <div class="kpi c-amber"><h3>For merchants</h3><p>A ₹980 payment no longer locks a ₹2.51 crore business account.</p></div>
</div>""", cite(3), icon="workflow"))

# 5 — demo
shot = f'<img class="shot" src="data:image/png;base64,{base64.b64encode(SHOT.read_bytes()).decode()}" alt="">' if SHOT.exists() else '<div class="shot ph">Screenshot of the live desk</div>'
S.append(slide(5, "Architecture · the product", "It already runs: replay a case and watch the money, the agents and the hold change.", f"""
<div class="demo">{shot}
 <ul class="ipts sm">
  <li>{ic('route')}<div><b>Money-flow graph</b> animates each hop; red is the traceable share.</div></li>
  <li>{ic('scale')}<div><b>Rule switcher</b> shows FIFO, LIFO, pro-rata and LIBR side by side.</div></li>
  <li>{ic('sparkles')}<div><b>Agent console</b> replays the run: claims, rebuttals, checks.</div></li>
  <li>{ic('user-check')}<div><b>Officer approves</b> each hold; letters are generated and number-checked.</div></li>
 </ul></div>""", "", icon="monitor"))

# 6 — architecture
AG = [("scan-text", "Intake", "m", "reads notice + complaint; code checks every UTR"), ("route", "Tracer", "c", "four tracing rules over all ledgers"),
      ("activity", "Pattern analyst", "m", "mule signals computed in code, explained by model"), ("message-square-warning", "Two advocates", "m", "victim vs account holder argue each hold, must cite"),
      ("shield-check", "Decider", "c", "policy: lien LIBR amount; full freeze needs recorded reasons"), ("timer", "Clock keeper", "c", "SOP and court deadlines, each with a citation"),
      ("file-text", "Drafter", "m", "lien, release and grievance letters"), ("badge-check", "Verifier", "c", "independent replay; every number re-derived"),
      ("user-check", "Nodal officer", "h", "approves, edits or rejects each hold")]
agents = "".join(f'<div class="st {k}">{ic(i, "big")}<b>{n}</b><span>{d}</span></div>' for i, n, k, d in AG)
who = f'<div class="who"><span class="wm">{ic("sparkles")}model</span><span class="wc">{ic("code")}code</span><span class="wp">{ic("user-check")}person</span></div>'
S.append(slide(6, "Proposed technological architecture", "Nine agents: models read and argue, code computes and verifies, a person decides.", f"""
<div class="arch9">{agents}</div>
<div class="stack">
 <div><b>{ic('database')}Data in</b><span>CFCFRMS notice, NCRP complaint, bank ledgers / CBS extracts, Suspect Registry hit</span></div>
 <div><b>{ic('layers')}Stack</b><span>Python · FastAPI · Postgres · React · any OpenAI-compatible model, or fully on-prem with a local model</span></div>
 <div><b>{ic('shield-check')}Rules</b><span>The model never sets an amount · uncited claims are rejected · a person approves every hold</span></div>
</div>""", "", icon="workflow", aside=who))

# 7 — how the amount is computed (real engine output on case 3)
POLICY = C3["trace"]["policy_rule"]  # the case's account where the rules disagree most and the policy rule still holds money
acct = max(C3["trace"]["accounts"].items(), key=lambda kv: (kv[1]["by_rule"][POLICY] > 0, max(kv[1]["by_rule"].values()) - min(kv[1]["by_rule"].values())))
aid, at = acct
vals = at["by_rule"]
vmax = max(vals.values()) or 1
bars = "".join(f'<div class="rb {"pol" if r == C3["trace"]["policy_rule"] else ""}"><span>{ {"PRO_RATA": "Pro-rata"}.get(r, r)}</span><i style="width:{100 * v / vmax:.0f}%"></i><b>{inr(v)}</b></div>' for r, v in vals.items())
holder = next(a["holder"] for a in C3["accounts"] if a["id"] == aid)
S.append(slide(7, "Architecture · how the amount is computed and trusted", "Four legal tracing rules give four answers; LienLine shows all four and holds the defensible one.", f"""
<div class="grid2 r">
 <div class="card"><h3>{ic('scale')}{holder}: traceable fraud money by rule</h3><div class="rbars">{bars}</div>
  <p class="small">Real output of our tracing engine on case 3 (synthetic ledgers). LIBR, the lowest intermediate balance rule, never holds more than the account kept since the fraud money arrived.</p></div>
 <ul class="ipts sm">
  <li>{ic('route')}<div><b>Hop by hop:</b> an outflow carries the tainted share given by the rule to the next account.</div></li>
  <li>{ic('badge-check')}<div><b>Independent verifier:</b> replays ledgers; held + cashed out + untraced must equal the amount lost.</div></li>
  <li>{ic('message-square-warning')}<div><b>Advocates must cite:</b> a claim citing a transaction that does not exist is struck out.</div></li>
  <li>{ic('file-check')}<div><b>Letters:</b> every number in every letter is re-derived before an officer sees it.</div></li>
 </ul>
</div>""", "", icon="flask-conical"))

# 8 — why now (timeline from the news deep dive)
KEY = [("2024-09", "Madras HC: freeze only the fraud quantum", 24), ("2025-02", "Delhi HC: ₹93.5 crore frozen over ₹200", 7), ("2025-12", "One scam freezes 36,000+ accounts", 6),
       ("2026-01", "MHA/I4C SOP: grievance clocks", 9), ("2026-07", "MP HC statewide rules (₹2.51 crore over ₹980)", 1), ("2026-08", "SC orders an RBI debit-hold SOP; Rajasthan HC 105 petitions", 3),
       ("2026-09", "RBI draft: banks' own 60-day holds", 10)]
months = [f"{y}-{m:02d}" for y in (2024, 2025, 2026) for m in range(1, 13)][8:-2]
count = {m: sum(1 for e in NEWS["timeline"] if e["date"] == m) for m in months}
cmax = max(count.values()) or 1
tl = "".join(f'<div class="tm"><i style="height:{12 + 70 * count[m] / cmax:.0f}px" class="{"hot" if count[m] else ""}"></i><span>{m[2:4] + "/" + m[5:] if m.endswith(("01", "07")) else ""}</span></div>' for m in months)
keys = "".join(f'<li><b>{m}</b> {t} [{r}]</li>' for m, t, r in KEY)
S.append(slide(8, "Problem statement · why now", "In 2026 courts, the Supreme Court and RBI all moved at once; the tool they assume does not exist.", f"""
<div class="tl"><div class="tlbars">{tl}</div><p class="small muted">Dated court, regulator and press events on account freezes we found per month, Sep 2024 – Oct 2026 ({len(NEWS['timeline'])} events)</p></div>
<ul class="keys">{keys}</ul>""", cite(1, 3, 6, 7, 9, 10, 24), icon="clock"))

# 9 — global benchmarking
BENCH = [("in", "India", "CFCFRMS + MuleHunter.AI", "Holds on notice; mule detection in 31 banks [19]", "No per-account amount from the trail"),
         ("gb", "UK", "PSR APP reimbursement", "88% of losses refunded, £316m in 18 months [14]", "Victim refunds, not receiving-side holds"),
         ("sg", "Singapore", "Protection from Scams Act", "18 restriction orders, S$97m recovered, H1 2026 [15]", "Person-level orders, not amount-proportionate"),
         ("au", "Australia", "Scam-Safe Accord · AFCX FRX", "Industry fraud exchange; A$100m payee check [16]", "Receiving bank decides how much to freeze"),
         ("us", "USA", "FinCEN 314(b) · Zelle", "Voluntary info sharing; 47% reimbursed [17]", "No tracing-to-hold computation"),
         ("eu", "EU", "Verification of Payee", "Mandatory in euro area since Oct 2025 [18]", "Pre-payment only; nothing after funds land")]
rows = "".join(f"<tr><td>{flag(f)}{c}</td><td><b>{s}</b></td><td>{w}</td><td>{ic('circle-x')}{g}</td></tr>" for f, c, s, w, g in BENCH)
flags6 = "".join(flag(f) for f in ("in", "gb", "sg", "au", "us", "eu"))
S.append(slide(9, "Global product benchmarking · multi-country research", "Six countries fight scams; none sizes the hold on a receiving account from the money trail.", f"""
<table class="t bench"><tr><th>Country</th><th>System</th><th>What it does</th><th>Gap LienLine fills</th></tr>{rows}</table>
<p class="note2">Prior-art sweep (71 searches): closest is CashGuard-AI, an SIH 2026 fund-block queue with no tracing or lien sizing [20]; MuleHunter.AI detects mules but does not size holds [19].</p>""",
    cite(14, 15, 16, 17, 18, 19, 20), icon="globe", aside=f'<div class="flags7">{flags6}</div>'))

# 10 — market size (bottom-up)
samr = "".join(f'<div class="sr">{ic(i)}<div><b>{n} {d.split(" [")[0]}</b><span>{n} × ₹{PRICE[k]:.0f} lakh a year [{d.split("[")[1]}</span><div class="hb"><i style="width:{100 * n * PRICE[k] / max(m * PRICE[kk] for kk, (m, _) in SAM.items()):.0f}%"></i></div></div><em>₹{n * PRICE[k] / 100:.1f} cr</em></div>'
               for (k, (n, d)), i in zip(SAM.items(), ("landmark", "building-2", "siren")))
S.append(slide(10, "Market size", f"A ₹{SAM_TOTAL / 100:.0f} crore-a-year serviceable market in India, protecting ₹8,189 crore already under lien.", f"""
<div class="mk2">
 <div class="tam">
  <div class="c1"><b>AT STAKE</b><span>marked as lien, 2021–25</span><em>₹8,189 crore [4]</em><small>₹55,050 crore reported lost</small></div>
  <div class="c2"><b>SAM</b><span>India, bottom-up</span><em>₹{SAM_TOTAL / 100:.1f} crore / yr</em></div>
  <div class="c3"><b>SOM</b><span>year-3 ARR</span><em>₹{rev(2) / 100:.2f} cr</em></div>
  <p class="ns">Circles not to scale</p>
 </div>
 <div class="samb"><h3>SAM, built bottom-up</h3>{samr}
  <div class="som">{ic('target')}<div><b>Year 3: {CUST['bank'][2]} banks, {CUST['rrb'][2]} RRBs, {CUST['state'][2]} states</b><span>₹{rev(2) / 100:.2f} crore ARR, {100 * rev(2) / SAM_TOTAL:.0f}% of SAM (projection)</span></div></div>
 </div>
</div>""", cite(3, 4, 23), "proj", icon="target"))

# 11 — revenue model + GTM / CAC
pl = "".join(f"<tr><td>Year {y + 1}</td><td class='n'>{rev(y):.1f}</td><td class='n'>{cost(y):.1f}</td><td class='n {'neg' if rev(y) < cost(y) else 'pos'}'>{rev(y) - cost(y):+.1f}</td></tr>" for y in range(3))
S.append(slide(11, "Revenue model · go-to-market", f"Annual licences per bank and per state; break-even in year 2, {100 * (rev(2) - cost(2)) / rev(2):.0f}% margin in year 3.", f"""
<div class="tiers">
 <div>{ic('landmark')}<b>Bank licence</b><i>₹{PRICE['bank']:.0f} lakh / yr</i><span>Commercial, small finance and payments banks; on-prem option</span></div>
 <div>{ic('building-2')}<b>RRB / co-op</b><i>₹{PRICE['rrb']:.0f} lakh / yr</i><span>Sold through sponsor banks and federations</span></div>
 <div>{ic('siren')}<b>State cyber cell</b><i>₹{PRICE['state']:.0f} lakh / yr</i><span>Lien sizing before notices go out</span></div>
 <div>{ic('target')}<b>CAC</b><i>₹{CAC['bank']:.0f} / {CAC['rrb']:.1f} / {CAC['state']:.0f} lakh</i><span>Bank / RRB / state; payback &lt; 4 months</span></div>
</div>
<div class="plrow">
 <table class="t pl"><tr><th>₹ lakh</th><th>Revenue</th><th>Total cost</th><th>Profit</th></tr>{pl}</table>
 <ul class="ipts sm">
  <li>{ic('landmark')}<div><b>Q1–Q2:</b> two paid bank pilots (half price) and two state cyber cells.</div></li>
  <li>{ic('users')}<div><b>Channel:</b> I4C's Cyber Fraud Mitigation Centre seats banks and intermediaries together.</div></li>
  <li>{ic('scale')}<div><b>Wedge:</b> courts and the SC order make proportionate holds mandatory [1] [2] [3].</div></li>
 </ul>
</div>""", cite(1, 2, 3), "proj", icon="indian-rupee"))

# 12 — tech stack + R&D costs
trows = "".join(f"<tr class='{'' if s else 'est'}'><td>{a}</td><td>{b}</td><td class='n'>{inr(c * 100)}</td></tr>" for a, b, c, s in TECH)
rrows = "".join(f"<tr><td>{a}</td><td class='n'>{b:.1f}</td></tr>" for a, b in RND)
S.append(slide(12, "Implementation, tech-stack and R&D expense", f"About ₹{TECH_MONTH * 12 / 1e5:.0f} lakh a year to run, ₹{PER_CASE:.1f} of model cost per case; year-1 R&D ₹{RND_Y[0]:.0f} lakh.", f"""
<div class="grid2 r">
 <table class="t cost"><tr><th>Item</th><th>Basis</th><th>₹ / month</th></tr>{trows}
  <tr class="tot"><td colspan="2"><b>Total</b> · ₹{TECH_MONTH * 12 / 1e5:.1f} lakh a year</td><td class="n"><b>{inr(TECH_MONTH * 100)}</b></td></tr></table>
 <table class="t"><tr><th>Year-1 R&amp;D</th><th>₹ lakh</th></tr>{rrows}<tr class="tot"><td><b>Total year 1</b></td><td class="n"><b>{RND_Y[0]:.1f}</b></td></tr></table>
</div>
<p class="note2">At {CASES_PER_MONTH:,} cases a month; USD at ₹{FX}. Banks that need air-gapped deployment run a local model on their own hardware, removing the inference line.</p>""",
    cite(21, 22), "proj", icon="server"))

# 13 — validation
vr = "".join(f"<tr><td><b>{r['title']}</b></td><td class='n'>{inr(r['lost'], True)}</td><td class='n frz'>{inr(r['held_before'], True)}</td><td class='n lien'>{inr(r['held_after'], True)}</td><td>{ic('badge-check')} verified</td></tr>" for r in INDEX)
S.append(slide(13, "Validation", f"Across four scenarios, frozen money fell from {inr(BEFORE, True)} to {inr(AFTER, True)} while every traceable rupee stayed on hold.", f"""
<table class="t val"><tr><th>Scenario (synthetic multi-bank ledgers)</th><th>Lost</th><th>Held today</th><th>LienLine hold</th><th>Verifier</th></tr>{vr}</table>
<div class="kpis three">
 <div class="kpi c-green"><h3>Innocent money released</h3><b>{100 * (BEFORE - AFTER) / BEFORE:.0f}%</b><p>of what whole-account freezes held</p></div>
 <div class="kpi c-blue"><h3>Victim protection</h3><b>100%</b><p>of traceable money still on hold (conservation check)</p></div>
 <div class="kpi c-violet"><h3>Every number checked</h3><b>4 / 4</b><p>runs pass the independent verifier</p></div>
</div>
<p class="note2">Real complaint ledgers are not public, so scenarios are synthetic but mirror court-recorded cases [1] [6] [7] [8]. Next: a bank sandbox pilot on masked historic cases.</p>""",
    cite(1, 6, 7, 8), icon="flask-conical"))

# 14 — risks, roadmap, ask
S.append(slide(14, "Risks · roadmap · the ask", "Pilot with one bank and one state cyber cell, and measure holds released and petitions avoided.", f"""
<div class="grid2">
 <div class="card"><h3>{ic('triangle-alert')}Risks and how we handle them</h3><ul class="ipts sm">
  <li>{ic('scale')}<div><b>Legal rule unsettled:</b> show all four rules; policy rule is configurable per bank's counsel.</div></li>
  <li>{ic('lock-keyhole')}<div><b>Data sensitivity:</b> on-prem with a local model; no data leaves the bank.</div></li>
  <li>{ic('triangle-alert')}<div><b>RBI draft may entrench whole-account holds [10]:</b> LienLine documents the reasons RBI's draft requires.</div></li>
 </ul></div>
 <div class="card"><h3>{ic('rocket')}Roadmap</h3><ul class="ipts sm">
  <li>{ic('flask-conical')}<div><b>0–3 months:</b> bank sandbox, CFCFRMS notice format, masked historic cases.</div></li>
  <li>{ic('landmark')}<div><b>3–9 months:</b> two paid pilots; Hindi and regional notices.</div></li>
  <li>{ic('globe')}<div><b>9–18 months:</b> RRBs via sponsor banks; state cyber cells before notices are sent.</div></li>
 </ul></div>
</div>
<div class="pstate ask">{ic('handshake')}<p><b>The ask.</b> One introduction to a bank's fraud-operations head and one state cyber cell; Malansoft's ThreatSentry can carry LienLine's case file and chain of custody.</p></div>""",
    cite(10), icon="rocket"))

# 15 — references


def balanced(refs: list, k: int = 3) -> list[list[int]]:
    total = sum(len(t) + len(u) for t, u in refs)
    cols, cur, acc = [], [], 0
    for i, (t, u) in enumerate(refs):
        cur.append(i)
        acc += len(t) + len(u)
        if acc >= total * (len(cols) + 1) / k and len(cols) < k - 1:
            cols.append(cur)
            cur = []
    cols.append(cur)
    return cols


col = lambda idx: "".join(f'<li value="{i + 1}">{REFS[i][0]}. <span>{REFS[i][1]}</span></li>' for i in idx)  # noqa: E731
S.append(slide(15, "Validated references", f"{len(REFS)} sources behind every figure, each opened and checked in October 2026", f"""
<div class="refs">{"".join(f"<ol>{col(c)}</ol>" for c in balanced(REFS))}</div>""", icon="book-open-check"))

EXTRA = """
.ba{display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:center;margin:4px 0}
.ba span{display:block;font-size:12px;color:var(--muted)} .ba b{font:900 26px/1.1 'Archivo'} .ba .ic{width:22px;height:22px;color:var(--muted)}
.frz{color:var(--red)} .lien{color:var(--green)}
.fverdict.ok{background:var(--green)}
.kpis.three{grid-template-columns:repeat(3,1fr);margin-top:14px}
.kpi.c-violet{border-color:var(--violet)} .kpi.c-violet h3{color:var(--violet)}
.chain{display:flex;align-items:center;gap:14px;justify-content:center;margin:6px 0 18px}
.chain>.ic{width:26px;height:26px;color:var(--muted)}
.cn{display:grid;justify-items:center;gap:2px;padding:14px 22px;border-radius:14px;background:var(--soft);min-width:200px}
.cn .ic{width:30px;height:30px} .cn b{font:800 18px 'Archivo'} .cn span{font-size:14px;color:var(--muted)}
.cn.v .ic{color:var(--blue)} .cn.m .ic{color:var(--red)} .cn.i .ic{color:var(--green)}
.rc .card p{font-size:17px !important}
.demo{display:grid;grid-template-columns:1.6fr 1fr;gap:22px;align-items:start}
.shot{width:100%;border-radius:12px;border:1px solid var(--line);box-shadow:0 8px 28px rgba(13,27,42,.16)}
.shot.ph{height:380px;display:grid;place-items:center;background:var(--soft);color:var(--muted)}
.arch9{display:grid;grid-template-columns:repeat(9,1fr);gap:8px}
.arch9 .st{margin:0;min-height:0;padding:12px 10px;gap:6px}
.arch9 .st span{font-size:13px} .arch9 .st b{font-size:15px}
.st.h{background:var(--green-soft)} .st.h .big{color:var(--green)}
.rbars{display:grid;gap:10px;margin:10px 0}
.rb{display:grid;grid-template-columns:80px 1fr 110px;gap:10px;align-items:center}
.rb span{font:600 14px 'IBM Plex Mono'} .rb i{height:16px;border-radius:5px;background:#e3a6a1} .rb b{font:700 15px 'IBM Plex Mono';text-align:right}
.rb.pol i{background:var(--red)} .rb.pol span,.rb.pol b{color:var(--red)}
.tl{display:grid;gap:6px}
.tlbars{display:flex;align-items:flex-end;gap:3px;height:96px;border-bottom:1.5px solid var(--ink)}
.tm{flex:1;display:grid;justify-items:center;gap:3px;align-content:end}
.tm i{display:block;width:100%;border-radius:3px 3px 0 0;background:var(--line)} .tm i.hot{background:var(--red)}
.tm span{font:500 10px 'IBM Plex Mono';color:var(--muted);height:12px;white-space:nowrap}
.keys{list-style:none;margin:10px 0 0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:8px 24px;font-size:15.5px}
.keys b{font:700 13px 'IBM Plex Mono';color:var(--red);margin-right:8px}
.val{font-size:15px} .val td{padding:8px 10px} .val .ic{width:16px;height:16px;color:var(--green);vertical-align:-3px}
.val td.frz{color:var(--red);font-weight:700} .val td.lien{color:var(--green);font-weight:700}
.pstate.ask{background:var(--green-soft);margin-top:16px} .pstate.ask .ic{color:var(--green)}
.muted{color:var(--muted)}
.kpis{align-items:start} .kpi{padding:16px 16px}
.pstate{margin-top:22px}
.tlbars{height:150px}
.keys{font-size:17px;gap:12px 28px;margin-top:16px}
.chain{margin:14px 0 26px} .cn{min-width:240px;padding:18px 26px}
.road{margin-bottom:6px}
"""
HTML = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}{EXTRA}</style></head><body>{''.join(S)}</body></html>"

if __name__ == "__main__":
    assert len(S) == N, len(S)
    (HERE / "deck.html").write_text(HTML)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": 1280, "height": 720})
        pg.set_content(HTML, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(1200)
        over = pg.evaluate("""() => [...document.querySelectorAll('.slide')].map((s, i) => {
            const r = s.getBoundingClientRect(); const foot = s.querySelector('footer').getBoundingClientRect();
            const bad = [...s.querySelectorAll('.body *, h1')].filter(e => { const q = e.getBoundingClientRect(); return q.height && (q.bottom > foot.top + 1 || q.right > r.right - 20); }).length;
            return bad ? `slide ${i + 1}: ${bad} element(s) overflow` : null }).filter(Boolean)""")
        print("overflow:", over or "none")
        pg.pdf(path=str(OUT), width="1280px", height="720px", print_background=True)
        b.close()
    print(OUT, f"{OUT.stat().st_size / 1e6:.2f} MB")
    print({"tech_month": round(TECH_MONTH), "per_case_rs": round(PER_CASE, 2), "rev": [round(rev(y), 1) for y in range(3)], "cost": [round(cost(y), 1) for y in range(3)],
           "SAM_lakh": SAM_TOTAL, "before": BEFORE, "after": AFTER})
