// Mirrors the run JSON contract in ../SPEC.md. All money is integer paise.

export type Rule = 'FIFO' | 'LIFO' | 'PRO_RATA' | 'LIBR'
export type ByRule = Record<Rule, number>
export type AgentKind = 'model' | 'code' | 'human'
export type EventType = 'start' | 'message' | 'tool' | 'check' | 'result' | 'debate' | 'letter' | 'approval'
export type Role = 'victim' | 'mule_l1' | 'mule_l2' | 'cashout' | 'merchant' | 'innocent'
export type Action = 'lien' | 'full_freeze' | 'release'
export type ClockStatus = 'running' | 'met' | 'breached'

export interface Bank {
  id: string
  name: string
  kind?: string
}

export interface Account {
  id: string
  bank: string
  masked: string
  holder: string
  kind?: string
  role: Role | string
  kyc_age_days?: number
  opening_balance?: number
  complaints_linked?: number
  registry_hit?: boolean
}

export interface Txn {
  id: string
  utr?: string
  ts: string
  from: string
  to: string
  amount: number
  channel?: string
  tainted_origin?: boolean
  note?: string
}

export interface SeriesPoint {
  ts: string
  balance: number
  tainted: Partial<ByRule>
}

export interface TraceAccount {
  by_rule: Partial<ByRule>
  balance_now: number
  series: SeriesPoint[]
  outflows?: { txn: string; to: string; tainted: Partial<ByRule> }[]
}

export interface TraceEdge {
  txn: string
  from: string
  to: string
  amount: number
  tainted: Partial<ByRule>
}

export interface Trace {
  as_of: string
  rules: Rule[]
  policy_rule: Rule
  accounts: Record<string, TraceAccount>
  edges: TraceEdge[]
  conservation: { lost: number; held: number; cashed_out: number; untraced: number }
}

export interface Reason {
  text: string
  refs?: string[]
}

export interface Decision {
  account_id: string
  action: Action
  amount: number
  current_hold: number
  released_by_change: number
  reasons: Reason[]
  confidence?: 'high' | 'medium' | 'low'
  range?: { min: number; max: number }
}

export interface Clock {
  id: string
  account_id?: string
  label: string
  start: string
  due: string
  rule: string
  source?: string
  status: ClockStatus
}

export interface RunEvent {
  t: number
  agent: string
  kind: AgentKind
  type: EventType | string
  text: string
  refs?: string[]
  data?: Record<string, unknown>
  ok?: boolean
}

export interface Letter {
  id: string
  account_id: string
  kind: string
  to: string
  subject: string
  body: string
  verified?: boolean
  numbers_checked?: number
}

export interface Run {
  case_id: string
  title: string
  summary: string
  generated_at: string
  model?: { backend?: string; chat_model?: string; calls?: number; tokens?: number }
  complaint: {
    ack_no: string
    filed_at: string
    victim: { name: string; account_id: string }
    amount_lost: number
    channel?: string
    narrative?: string
    police_station?: string
    io?: string
  }
  notice?: { text: string; issued_at: string; section: string; flagged: { account_id: string; amount: number }[] }
  banks: Bank[]
  accounts: Account[]
  transactions: Txn[]
  trace: Trace
  decisions: Decision[]
  clocks: Clock[]
  events: RunEvent[]
  letters: Letter[]
  verification: { passed: boolean; checks: { name: string; ok: boolean; detail?: string }[] }
}

export interface CaseIndexEntry {
  case_id: string
  title: string
  summary: string
  accounts?: number
  banks?: number
  lost?: number
  held_before?: number
  held_after?: number
  status?: string
}
