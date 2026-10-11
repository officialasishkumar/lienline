import { useEffect, useMemo, useRef } from 'react'
import { motion, useInView, useReducedMotion } from 'framer-motion'
import type { Run } from '../types'
import { WorkspaceProvider, useWorkspace, type MainTab, type SideTab } from '../state/workspace'
import { lienUnder, paceEvents } from '../lib/model'
import { RULE_LABEL, inr, rupeeText } from '../lib/format'
import { useClock } from '../hooks/useClock'
import { useLiveRun } from '../hooks/useLiveRun'
import { useMedia } from '../hooks/useMedia'
import { FlowGraph } from './graph/FlowGraph'
import { Scrubber } from './graph/Scrubber'
import { RuleSwitch } from './graph/RuleSwitch'
import { AgentConsole } from './console/AgentConsole'
import { AccountPanel } from './side/AccountPanel'
import { DecisionsPanel } from './side/DecisionsPanel'
import { LettersView } from './letters/LettersView'
import { ChecksView } from './checks/ChecksView'
import { HoldCompare } from './HoldCompare'
import { Check, Shield } from './Icons'
import '../styles/workspace.css'
import '../styles/side.css'

export function Workspace({ run, sample, onRun }: { run: Run; sample: boolean; onRun: (r: Run) => void }) {
  return (
    <WorkspaceProvider run={run}>
      <WorkspaceBody sample={sample} onRun={onRun} />
    </WorkspaceProvider>
  )
}

function WorkspaceBody({ sample, onRun }: { sample: boolean; onRun: (r: Run) => void }) {
  const ws = useWorkspace()
  const { model, mainTab, setMainTab } = ws
  const run = model.run
  const tabs: { id: MainTab; label: string; count?: number }[] = [
    { id: 'trace', label: 'Money trail & agents' },
    { id: 'letters', label: 'Letters', count: run.letters.length },
    { id: 'checks', label: 'Deadlines & checks', count: run.clocks.length },
  ]
  const approvedLetters = run.letters.filter((l) => ws.approvals['L:' + l.id] === 'approved').length

  return (
    <div className="ws">
      <header className="ws-head">
        <div className="ws-title">
          <p className="eyebrow">
            Case {run.case_id} · NCRP {run.complaint.ack_no} · {run.complaint.police_station}
          </p>
          <h2 className="serif">{rupeeText(run.title)}</h2>
          <p className="ws-sum">{rupeeText(run.summary)}</p>
        </div>
        <div className="ws-badges">
          <span className={'chip ' + (run.verification.passed ? 'ok' : 'taint')}>
            <Shield width={13} height={13} /> {run.verification.passed ? `Verified · ${run.verification.checks.length} checks` : 'Verification failed'}
          </span>
          {run.model?.chat_model && <span className="chip model">{run.model.chat_model}</span>}
          <span className="chip human">
            <Check width={13} height={13} /> {approvedLetters}/{run.letters.length} letters approved
          </span>
          {sample && <span className="chip warn">sample data</span>}
        </div>
      </header>

      <HoldHero />

      <div className="tabs ws-tabs" role="tablist" aria-label="Case views">
        {tabs.map((t) => (
          <button key={t.id} role="tab" id={`tab-${t.id}`} aria-controls={`panel-${t.id}`} aria-selected={mainTab === t.id} className="tab" onClick={() => setMainTab(t.id)}>
            {t.label}
            {t.count !== undefined && <span className="count">{t.count}</span>}
            {mainTab === t.id && <motion.span layoutId="ws-tab-line" className="tab-line" />}
          </button>
        ))}
      </div>

      <div role="tabpanel" id="panel-trace" aria-labelledby="tab-trace" className="ws-panel" hidden={mainTab !== 'trace'}>
        <TraceTab onRun={onRun} />
      </div>
      {mainTab !== 'trace' && (
        <div role="tabpanel" id={`panel-${mainTab}`} aria-labelledby={`tab-${mainTab}`} className="ws-panel">
          {mainTab === 'letters' ? <LettersView /> : <ChecksView />}
        </div>
      )}
    </div>
  )
}

function HoldHero() {
  const { model, rule } = useWorkspace()
  const ds = model.run.decisions
  if (!ds.length) return null
  const head = [...ds].sort((a, b) => b.released_by_change - a.released_by_change)[0]
  const a = model.accounts[head.account_id]
  const after = head.action === 'full_freeze' ? head.current_hold : lienUnder(model, head, rule)
  const totalBefore = ds.reduce((s, d) => s + d.current_hold, 0)
  const totalAfter = ds.reduce((s, d) => s + (d.action === 'full_freeze' ? d.current_hold : lienUnder(model, d, rule)), 0)
  return (
    <section className="hold-hero card" aria-label="Hold before and after">
      <div className="hh-who">
        <p className="eyebrow">Headline account</p>
        <p className="hh-name serif">{a?.holder}</p>
        <p className="mono hh-acct">
          {model.banks[a?.bank ?? '']?.name} · {a?.masked}
        </p>
      </div>
      <HoldCompare
        size="xl"
        before={head.current_hold}
        after={after}
        beforeLabel="Frozen today"
        afterLabel={`Lien · ${RULE_LABEL[rule]}`}
        replayKey={model.run.case_id + rule}
      />
      <div className="hh-total">
        <p className="eyebrow">All {ds.length} accounts</p>
        <p className="mono">
          <s>{inr(totalBefore)}</s>
        </p>
        <p className="mono hh-total-after">{inr(totalAfter)}</p>
        <p className="muted">held after decisions</p>
      </div>
    </section>
  )
}

function TraceTab({ onRun }: { onRun: (r: Run) => void }) {
  const ws = useWorkspace()
  const { model, ledger, sideTab, setSideTab } = ws
  const reduce = useReducedMotion()
  const events = useMemo(() => paceEvents(model.run.events), [model.run.events])
  const total = events.length ? events[events.length - 1].t + 1 : 1
  const consoleClock = useClock(total, 1, { start: reduce ? total : 0 })
  const live = useLiveRun(model.run.case_id, onRun)
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, amount: 0.35 })
  const phone = useMedia('(max-width: 760px)')

  // Both replays start the first time the workspace scrolls into view.
  useEffect(() => {
    if (!inView || reduce) return
    ledger.play()
    consoleClock.play()
  }, [inView, reduce])

  const sideTabs: { id: SideTab; label: string }[] = [
    { id: 'agents', label: 'Agent run' },
    { id: 'account', label: ws.selected ? (model.accounts[ws.selected]?.holder ?? 'Account') : 'Account' },
    { id: 'decisions', label: 'Decisions' },
  ]

  return (
    <div className="trace-grid" ref={ref}>
      <div className="graph-col">
        <div className="graph-toolbar">
          <RuleSwitch />
        </div>
        <FlowGraph height={phone ? 440 : 600} />
        <Scrubber />
      </div>
      <aside className="side card" aria-label="Case detail">
        <div className="side-inner">
          <div className="tabs side-tabs" role="tablist" aria-label="Detail views">
            {sideTabs.map((t) => (
              <button key={t.id} role="tab" aria-selected={sideTab === t.id} className="tab" onClick={() => setSideTab(t.id)} id={`stab-${t.id}`} aria-controls="side-panel">
                <span className="tab-text">{t.label}</span>
                {sideTab === t.id && <motion.span layoutId="side-tab-line" className="tab-line" />}
              </button>
            ))}
          </div>
          <div className="side-body" id="side-panel" role="tabpanel" aria-labelledby={`stab-${sideTab}`}>
            <div hidden={sideTab !== 'agents'} className="side-pane console-pane">
              <AgentConsole events={events} clock={consoleClock} live={live} />
            </div>
            {sideTab === 'account' && (
              <div className="side-pane scroll">
                <AccountPanel />
              </div>
            )}
            {sideTab === 'decisions' && (
              <div className="side-pane scroll">
                <DecisionsPanel />
              </div>
            )}
          </div>
        </div>
      </aside>
    </div>
  )
}
