# Design notes: how fund-flow tools present money trails

Research on 11 Oct 2026 (product pages of Chainalysis Reactor, TRM Forensics, Elliptic Investigator, Unit21; Arkham, Crystal, Hawk AI and Feedzai pages were unreachable or had no UI detail, so those points come from prior familiarity and are marked).

1. **Graph first, follow the money "from first deposit to final cash-out"** (Chainalysis Reactor). LienLine opens a case on the graph, with the victim at the left and cash-outs at the right.
2. **Hop structure is the mental model.** TRM's multi-route pathfinding shows every path across multiple hops, and investigators read trails hop by hop. LienLine lays accounts out in columns by hop distance from the victim, so "Hop 2" means something.
3. **Attribute entities, not just addresses.** Reactor and Elliptic label wallets with the institution behind them. Here every node carries its bank, colour-coded and grouped, plus holder, masked number and role (mule L1/L2, merchant, cash-out).
4. **Edge weight encodes value** (Arkham visualizer, from familiarity). Edge width is proportional to amount on a log scale, so ₹980 and ₹40 lakh both stay legible. The tainted share is drawn as a red core inside each edge.
5. **Time is a first-class control.** Reactor and Arkham let you filter by time. LienLine replays the ledger with a play/pause scrubber; ticks are sized by amount and coloured red when they carry victim money.
6. **Interpretation shown as readable steps** (Reactor turns swaps and bridges into plain steps). The agent console turns every tool call, check and argument into a one-line event, with the agent and its kind (model, code or human).
7. **Evidence chips everywhere.** Unit21 stresses decisions "traceable, mapped to policies, backed by documented reasoning and evidence". Each reason and agent event carries chips for the transactions and accounts it cites; hovering a chip lights them up in the graph.
8. **Detail lives in a side panel next to the graph** (Elliptic's transaction detail panel; standard in Reactor and Arkham). Clicking an account opens its balance-over-time chart, the traceable amount under each rule, the decision with reasons, and its ledger lines, while the graph stays in view.
9. **Case management with human in the loop** (Unit21: "investigations executed by AI, human-in-the-loop"; TRM keeps graphs and notes per case). Cases show live deadline clocks; decisions and letters wait for a nodal officer's approval, and approval is blocked while any figure fails verification.
10. **Built to be shown to others** (Reactor: graphs shared "with leadership, across teams, and in court"; Elliptic exports an evidence record). Letters render as formal bank letters, and every verified figure is highlighted so a reader can see it was checked.

Visual identity: ink and paper neutrals for a forensic, documentary feel. Red is reserved for traceable victim money. Violet, blue and green mark who acted: a model, code, or a human. Newsreader (serif) is used for headlines and letters, IBM Plex Sans for the UI, and IBM Plex Mono for figures and ids. All fonts are self-hosted.
