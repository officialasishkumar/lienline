import type { AgentKind } from '../types'

export interface AgentMeta {
  name: string
  short: string
  kind: AgentKind
  checkedBy?: AgentKind
  does: string
}

// The nine roles from SPEC.md. `kind` is who acts; `checkedBy` marks model output that code verifies.
export const AGENTS: AgentMeta[] = [
  { name: 'Intake', short: 'IN', kind: 'model', checkedBy: 'code', does: 'Reads the notice and complaint; code cross-checks every UTR' },
  { name: 'Tracer', short: 'TR', kind: 'code', does: 'Replays the ledgers hop by hop under four tracing rules' },
  { name: 'Pattern analyst', short: 'PA', kind: 'code', checkedBy: 'model', does: 'Mule signals: pass-through, velocity, KYC age, registry' },
  { name: "Victim's advocate", short: 'VA', kind: 'model', checkedBy: 'code', does: 'Argues for a larger hold, must cite ledger ids' },
  { name: "Account holder's advocate", short: 'AH', kind: 'model', checkedBy: 'code', does: 'Argues for release, must cite ledger ids' },
  { name: 'Decider', short: 'DE', kind: 'code', does: 'Lien = traceable amount under LIBR; freeze only on hard signals' },
  { name: 'Clock keeper', short: 'CK', kind: 'code', does: 'SOP and court deadlines, each with its citation' },
  { name: 'Drafter', short: 'DR', kind: 'model', checkedBy: 'code', does: 'Lien, release and grievance letters' },
  { name: 'Verifier', short: 'VE', kind: 'code', does: 'Independent replay; every number in every letter' },
  { name: 'Nodal officer', short: 'NO', kind: 'human', does: 'Approves or edits each decision and letter' },
]

const byName: Record<string, AgentMeta> = {}
AGENTS.forEach((a) => (byName[a.name.toLowerCase()] = a))

export function agentMeta(name: string): AgentMeta {
  const key = name.toLowerCase()
  if (byName[key]) return byName[key]
  const found = AGENTS.find((a) => key.includes(a.name.toLowerCase().split(' ')[0].replace(/'s$/, '')))
  if (found) return found
  const short = name
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
  return { name, short, kind: 'code', does: '' }
}

export const KIND_LABEL: Record<AgentKind, string> = { model: 'model', code: 'code', human: 'human' }
