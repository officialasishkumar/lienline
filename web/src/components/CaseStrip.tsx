import { motion, useReducedMotion } from 'framer-motion'
import type { CaseIndexEntry, Run } from '../types'
import { useCaseNow } from '../hooks/useCaseNow'
import { clockStatus, nextClock } from '../lib/clocks'
import { countdown, inrShort } from '../lib/format'

interface Props {
  index: CaseIndexEntry[]
  runs: Record<string, Run>
  current: string
  onPick: (id: string) => void
}

export function CaseStrip({ index, runs, current, onPick }: Props) {
  return (
    <div className="case-strip" role="list" aria-label="Cases">
      {index.map((c, i) => (
        <CaseCard key={c.case_id} c={c} run={runs[c.case_id]} active={c.case_id === current} onPick={onPick} i={i} />
      ))}
    </div>
  )
}

function CaseCard({ c, run, active, onPick, i }: { c: CaseIndexEntry; run?: Run; active: boolean; onPick: (id: string) => void; i: number }) {
  const now = useCaseNow(run?.trace.as_of)
  const reduce = useReducedMotion()
  const next = run ? nextClock(run, now) : null
  const breached = run ? run.clocks.filter((k) => clockStatus(k, now) === 'breached').length : 0
  const left = next ? Date.parse(next.due) - now : 0
  const span = next ? Date.parse(next.due) - Date.parse(next.start) : 1
  const urgent = next && left < 24 * 3600e3
  const frac = next ? Math.max(0, Math.min(1, 1 - left / span)) : 0
  const R = 15
  const C = 2 * Math.PI * R

  return (
    <motion.div
      role="listitem"
      initial={reduce ? false : { opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay: i * 0.06 }}
    >
      <button className={'case-card' + (active ? ' active' : '')} onClick={() => onPick(c.case_id)} aria-current={active ? 'true' : undefined}>
        <span className="cc-id mono">{c.case_id}</span>
        <span className="cc-title serif">{c.title}</span>
        <span className="cc-sum">{c.summary}</span>
        <span className="cc-nums">
          {c.held_before !== undefined && c.held_after !== undefined && (
            <span className="mono">
              <s>{inrShort(c.held_before)}</s> → <b>{inrShort(c.held_after)}</b>
            </span>
          )}
          {c.accounts !== undefined && (
            <span className="muted">
              {c.accounts} accts · {c.banks} banks
            </span>
          )}
        </span>
        <span className={'cc-clock' + (urgent ? ' urgent' : '')}>
          {next ? (
            <>
              <svg viewBox="0 0 36 36" className="cc-ring" aria-hidden="true">
                <circle cx="18" cy="18" r={R} className="track" />
                <circle cx="18" cy="18" r={R} className="fill" strokeDasharray={C} strokeDashoffset={C * (1 - frac)} />
              </svg>
              <span className="cc-clock-text">
                <span className="mono cc-count">{countdown(left)}</span>
                <span className="cc-label">{next.label}</span>
              </span>
            </>
          ) : (
            <span className="cc-label">No running deadlines</span>
          )}
          {breached > 0 && <span className="chip taint cc-breach">{breached} breached</span>}
        </span>
      </button>
    </motion.div>
  )
}
