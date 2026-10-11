import type { Account, Bank, ByRule, Decision, Rule, Run, RunEvent, TraceAccount, Txn } from '../types'

export const RULES: Rule[] = ['FIFO', 'LIFO', 'PRO_RATA', 'LIBR']

export interface EdgeModel {
  id: string
  index: number // chronological position
  txn: Txn
  from: string
  to: string
  amount: number
  tainted: ByRule
}

export interface CaseModel {
  run: Run
  accounts: Record<string, Account>
  banks: Record<string, Bank>
  bankOrder: string[]
  bankColor: Record<string, number> // palette slot
  txns: Txn[] // chronological
  txnById: Record<string, Txn>
  edges: EdgeModel[]
  decisions: Record<string, Decision>
  traceOf: (id: string) => TraceAccount | undefined
  times: number[] // epoch ms per txn
  startMs: number
  asOfMs: number
}

const fill = (p: Partial<ByRule> | undefined): ByRule => ({
  FIFO: p?.FIFO ?? 0,
  LIFO: p?.LIFO ?? 0,
  PRO_RATA: p?.PRO_RATA ?? 0,
  LIBR: p?.LIBR ?? 0,
})

export function buildModel(run: Run): CaseModel {
  const accounts: Record<string, Account> = {}
  run.accounts.forEach((a) => (accounts[a.id] = a))
  const banks: Record<string, Bank> = {}
  run.banks.forEach((b) => (banks[b.id] = b))

  const txns = [...run.transactions].sort((a, b) => Date.parse(a.ts) - Date.parse(b.ts))
  const txnById: Record<string, Txn> = {}
  txns.forEach((t) => (txnById[t.id] = t))

  // Any id used in a transaction but missing from accounts becomes a visible external node.
  for (const t of txns) {
    for (const id of [t.from, t.to]) {
      if (!accounts[id]) {
        const cash = t.channel === 'ATM' || t.channel === 'CASH'
        accounts[id] = { id, bank: '?', masked: cash ? 'ATM / branch' : 'no ledger', holder: t.channel === 'ATM' || t.channel === 'CASH' ? 'Cash withdrawal' : 'Outside the ledgers', role: t.channel === 'ATM' || t.channel === 'CASH' ? 'cashout' : 'innocent', kind: 'external' }
      }
    }
  }

  const bankOrder = run.banks.map((b) => b.id)
  Object.values(accounts).forEach((a) => {
    if (!bankOrder.includes(a.bank)) bankOrder.push(a.bank)
    if (!banks[a.bank]) banks[a.bank] = { id: a.bank, name: a.bank === '?' ? 'Outside traced banks' : a.bank }
  })
  const bankColor: Record<string, number> = {}
  bankOrder.forEach((b, i) => (bankColor[b] = i % 8))

  const traceEdges: Record<string, Partial<ByRule>> = {}
  run.trace.edges.forEach((e) => (traceEdges[e.txn] = e.tainted))
  const edges: EdgeModel[] = txns.map((t, index) => ({
    id: t.id,
    index,
    txn: t,
    from: t.from,
    to: t.to,
    amount: t.amount,
    tainted: fill(traceEdges[t.id] ?? (t.tainted_origin ? { FIFO: t.amount, LIFO: t.amount, PRO_RATA: t.amount, LIBR: t.amount } : undefined)),
  }))

  const decisions: Record<string, Decision> = {}
  run.decisions.forEach((d) => (decisions[d.account_id] = d))

  const times = txns.map((t) => Date.parse(t.ts))
  const startMs = times.length ? times[0] - 60_000 : Date.parse(run.trace.as_of)
  const asOfMs = Date.parse(run.trace.as_of) || (times.length ? times[times.length - 1] : Date.now())

  return {
    run,
    accounts,
    banks,
    bankOrder,
    bankColor,
    txns,
    txnById,
    edges,
    decisions,
    traceOf: (id) => run.trace.accounts[id],
    times,
    startMs,
    asOfMs,
  }
}

/** Ledger clock for a playhead position p in [0, N]: the time of the last completed transaction. */
export function ledgerTime(m: CaseModel, p: number): number {
  const n = m.times.length
  if (p >= n) return m.asOfMs
  const k = Math.floor(p)
  if (k <= 0) return m.startMs
  return m.times[k - 1]
}

/** Account state (balance + traceable taint per rule) as of ledger time `ms`. */
export function stateAt(m: CaseModel, id: string, ms: number): { balance: number; tainted: ByRule } | null {
  const tr = m.traceOf(id)
  if (!tr || !tr.series.length) return null
  let pt = tr.series[0]
  for (const s of tr.series) {
    if (Date.parse(s.ts) <= ms) pt = s
    else break
  }
  return { balance: pt.balance, tainted: fill(pt.tainted) }
}

export function byRule(p: Partial<ByRule> | undefined): ByRule {
  return fill(p)
}

/** Lien amount the selected rule would imply for an account's decision. */
export function lienUnder(m: CaseModel, d: Decision, rule: Rule): number {
  if (d.action === 'full_freeze') return d.amount
  if (d.action === 'release' && rule === m.run.trace.policy_rule) return 0
  const t = m.traceOf(d.account_id)
  const v = t ? fill(t.by_rule)[rule] : d.amount
  return Math.min(v, d.current_hold || v)
}

export function displayName(a: Account | undefined): string {
  return a ? a.holder : 'Unknown'
}

/**
 * Recorded runs keep each event's real offset `t`. Runs produced by the deterministic fallback finish
 * in milliseconds, so their offsets are re-paced for a readable replay (order is unchanged).
 */
export function paceEvents(events: RunEvent[]): RunEvent[] {
  if (!events.length) return events
  const span = events[events.length - 1].t - events[0].t
  if (span >= events.length * 0.25) return events
  let t = 0
  return events.map((e, i) => {
    if (i > 0) {
      const base = e.kind === 'model' ? 1.5 : e.kind === 'human' ? 1.2 : 0.55
      t += base + Math.min(1.2, e.text.length / 140)
    }
    return { ...e, t: Math.round(t * 10) / 10 }
  })
}
