import type { CaseModel } from './model'
import { RULES, byRule } from './model'

export interface Mark {
  text: string
  kind: 'plain' | 'amount' | 'utr' | 'account'
  ok?: boolean
  why?: string
}

// ₹ / Rs amounts, 10-22 char UTR-like references, masked account numbers.
const PATTERN = /((?:₹|Rs\.?)\s?\d[\d,]*(?:\.\d{1,2})?)|(\bXXXX\d{4}\b)|(\b(?=[A-Z0-9]*\d)[A-Z0-9]{12,22}\b)/g

/** Numbers the verifier accepts in a letter: decision, ledger and trace amounts; known UTRs and accounts. */
export function knownValues(m: CaseModel) {
  const amounts = new Map<number, string>()
  const add = (p: number, why: string) => {
    if (p > 0 && !amounts.has(p)) amounts.set(p, why)
  }
  m.run.decisions.forEach((d) => {
    add(d.amount, `decision for ${d.account_id}`)
    add(d.current_hold, `current hold on ${d.account_id}`)
    add(d.released_by_change, `released from ${d.account_id}`)
  })
  m.edges.forEach((e) => add(e.amount, `transaction ${e.id}`))
  Object.entries(m.run.trace.accounts).forEach(([id, t]) => {
    const r = byRule(t.by_rule)
    RULES.forEach((k) => add(r[k], `${k} trace for ${id}`))
    add(t.balance_now, `balance of ${id}`)
  })
  add(m.run.complaint.amount_lost, 'amount lost')
  const utrs = new Set(m.txns.map((t) => t.utr).filter(Boolean) as string[])
  const masks = new Set(Object.values(m.accounts).map((a) => a.masked))
  return { amounts, utrs, masks }
}

export function toPaise(s: string): number {
  const n = s.replace(/₹|Rs\.?/g, '').replace(/[,\s]/g, '')
  return Math.round(parseFloat(n) * 100)
}

export function markText(text: string, known: ReturnType<typeof knownValues>): Mark[] {
  const out: Mark[] = []
  let last = 0
  for (const m of text.matchAll(PATTERN)) {
    const i = m.index ?? 0
    if (i > last) out.push({ text: text.slice(last, i), kind: 'plain' })
    if (m[1]) {
      const p = toPaise(m[1])
      const why = known.amounts.get(p)
      out.push({ text: m[1], kind: 'amount', ok: !!why, why: why ?? 'does not match any decision, ledger or trace figure' })
    } else if (m[2]) {
      out.push({ text: m[2], kind: 'account', ok: known.masks.has(m[2]), why: known.masks.has(m[2]) ? 'account in the case' : 'unknown account' })
    } else {
      const ok = known.utrs.has(m[3])
      if (ok || /^\d{12}$/.test(m[3])) out.push({ text: m[3], kind: 'utr', ok, why: ok ? 'UTR in the ledgers' : 'UTR not in any ledger' })
      else out.push({ text: m[3], kind: 'plain' })
    }
    last = i + m[0].length
  }
  if (last < text.length) out.push({ text: text.slice(last), kind: 'plain' })
  return out
}
