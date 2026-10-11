import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from 'react'
import { useReducedMotion } from 'framer-motion'
import type { Rule, Run } from '../types'
import { buildModel, type CaseModel } from '../lib/model'
import { layoutGraph, type Layout } from '../lib/layout'
import { useClock, type Clock } from '../hooks/useClock'

export type SideTab = 'agents' | 'account' | 'decisions'
export type MainTab = 'trace' | 'letters' | 'checks'

interface WorkspaceState {
  model: CaseModel
  layout: Layout
  rule: Rule
  setRule: (r: Rule) => void
  selected: string | null
  select: (id: string | null) => void
  highlight: Set<string>
  setHighlight: (ids: string[] | null, source?: 'hover' | 'agent') => void
  ledger: Clock
  focusRef: (id: string) => void
  sideTab: SideTab
  setSideTab: (t: SideTab) => void
  mainTab: MainTab
  setMainTab: (t: MainTab) => void
  approvals: Record<string, 'approved' | 'edited'>
  setApproval: (id: string, v: 'approved' | 'edited' | null) => void
}

const Ctx = createContext<WorkspaceState | null>(null)

/** Seconds of replay per ledger transaction. */
const SEC_PER_TXN = 1.15

export function WorkspaceProvider({ run, children }: { run: Run; children: ReactNode }) {
  const model = useMemo(() => buildModel(run), [run])
  const layout = useMemo(() => layoutGraph(model), [model])
  const reduce = useReducedMotion()
  const n = model.edges.length
  const ledger = useClock(n, 1 / SEC_PER_TXN, { autoplay: false, start: reduce ? n : 0 })
  const [rule, setRule] = useState<Rule>(run.trace.policy_rule || 'LIBR')
  const [selected, setSelected] = useState<string | null>(null)
  const [highlight, setHL] = useState<Set<string>>(new Set())
  const hoverLock = useRef(false)
  const [sideTab, setSideTab] = useState<SideTab>('agents')
  const [mainTab, setMainTab] = useState<MainTab>('trace')
  const [approvals, setApprovals] = useState<Record<string, 'approved' | 'edited'>>({})

  const setHighlight = useCallback((ids: string[] | null, source: 'hover' | 'agent' = 'hover') => {
    if (source === 'hover') hoverLock.current = !!ids?.length
    else if (hoverLock.current) return
    setHL(new Set(ids ?? []))
  }, [])

  const select = useCallback((id: string | null) => {
    setSelected(id)
    if (id) setSideTab('account')
  }, [])

  const focusRef = useCallback(
    (id: string) => {
      if (model.accounts[id]) {
        select(id)
        return
      }
      const e = model.edges.find((x) => x.id === id)
      if (e) {
        ledger.pause()
        ledger.seek(e.index + 1)
        setHL(new Set([e.id, e.from, e.to]))
      }
    },
    [model, select, ledger],
  )

  const setApproval = useCallback((id: string, v: 'approved' | 'edited' | null) => {
    setApprovals((a) => {
      const next = { ...a }
      if (v) next[id] = v
      else delete next[id]
      return next
    })
  }, [])

  const value: WorkspaceState = {
    model,
    layout,
    rule,
    setRule,
    selected,
    select,
    highlight,
    setHighlight,
    ledger,
    focusRef,
    sideTab,
    setSideTab,
    mainTab,
    setMainTab,
    approvals,
    setApproval,
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useWorkspace(): WorkspaceState {
  const v = useContext(Ctx)
  if (!v) throw new Error('useWorkspace outside WorkspaceProvider')
  return v
}
