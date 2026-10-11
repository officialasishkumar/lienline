import { useEffect, useMemo, useRef } from 'react'
import type { RunEvent } from '../../types'
import type { Clock } from '../../hooks/useClock'
import type { LiveRun } from '../../hooks/useLiveRun'
import { useWorkspace } from '../../state/workspace'
import { AGENTS, agentMeta } from '../../lib/agents'
import { EventRow } from './EventRow'
import { Bolt, Pause, Play, Restart } from '../Icons'
import '../../styles/console.css'

interface Props {
  events: RunEvent[]
  clock: Clock
  live: LiveRun
}

/** Replays the recorded multi-agent run with its original timing (or shows a live SSE run). */
export function AgentConsole({ events, clock, live }: Props) {
  const ws = useWorkspace()
  const listRef = useRef<HTMLOListElement>(null)
  const stick = useRef(true)
  const isLive = live.events !== null
  const shownEvents = useMemo(() => (isLive ? live.events! : events.filter((e) => e.t <= clock.value)), [isLive, live.events, events, clock.value])
  const count = shownEvents.length
  const latest = shownEvents[count - 1]
  const total = events.length ? events[events.length - 1].t : 0

  // Each new event lights up what it cites in the graph for a moment.
  useEffect(() => {
    if (!latest?.refs?.length) return
    ws.setHighlight(latest.refs, 'agent')
    const t = setTimeout(() => ws.setHighlight([], 'agent'), 2600)
    return () => clearTimeout(t)
  }, [count])

  useEffect(() => {
    const el = listRef.current
    if (el && stick.current) el.scrollTop = el.scrollHeight
  }, [count])

  const spoken = new Set(shownEvents.map((e) => agentMeta(e.agent).name))
  const active = latest ? agentMeta(latest.agent).name : null
  const running = isLive ? live.running : clock.playing
  const checks = shownEvents.filter((e) => e.type === 'check')
  const passed = checks.filter((e) => e.ok !== false).length
  const rejected = shownEvents.filter((e) => e.ok === false && e.type !== 'check').length

  return (
    <div className="console">
      <div className="console-top">
        <div className="roster" aria-label="Agents">
          {AGENTS.map((a) => (
            <span
              key={a.name}
              className={`roster-av k-${a.kind}${spoken.has(a.name) ? ' spoke' : ''}${active === a.name && running ? ' active' : ''}`}
              title={`${a.name} (${a.kind})`}
            >
              {a.short}
            </span>
          ))}
        </div>
        <div className="console-ctl">
          {!isLive && (
            <>
              <button className="icon-btn" onClick={clock.toggle} aria-label={clock.playing ? 'Pause agent replay' : 'Play agent replay'}>
                {clock.playing ? <Pause /> : <Play />}
              </button>
              <button className="icon-btn" onClick={clock.restart} aria-label="Replay agent run from the start">
                <Restart />
              </button>
            </>
          )}
          {live.available && (
            <button className="btn sm primary" onClick={live.running ? live.stop : live.start}>
              <Bolt width={13} height={13} /> {live.running ? 'Stop' : 'Run live'}
            </button>
          )}
        </div>
      </div>
      <div className="console-status">
        <span className={'pill ' + (isLive ? 'live' : 'replay')}>
          {running && <span className="pulse-dot" />}
          {isLive ? (live.running ? 'LIVE · streaming' : 'LIVE · finished') : running ? 'REPLAY · recorded run' : count >= events.length ? 'REPLAY · complete' : 'REPLAY · paused'}
        </span>
        <span className="console-tally mono">
          <span className="good">{passed} ✓</span>
          <span className="bad">{rejected + (checks.length - passed)} ✗</span>
          <span>
            {count}/{isLive ? count : events.length}
          </span>
        </span>
      </div>
      {!isLive && (
        <div className="console-progress" aria-hidden="true">
          <span style={{ width: `${total ? Math.min(100, (clock.value / total) * 100) : 100}%` }} />
        </div>
      )}
      {live.error && <p className="console-error">Live run failed: {live.error}. Showing the recorded run.</p>}
      <ol
        className="ev-list"
        ref={listRef}
        aria-live="polite"
        aria-relevant="additions"
        tabIndex={0}
        aria-label="Agent events"
        onScroll={(e) => {
          const el = e.currentTarget
          stick.current = el.scrollHeight - el.scrollTop - el.clientHeight < 60
        }}
      >
        {count === 0 && (
          <li className="ev-empty">{isLive ? 'Waiting for the first agent…' : 'Press play to replay the agents working this case.'}</li>
        )}
        {shownEvents.map((e, i) => (
          <EventRow key={i} e={e} typing={i === count - 1 && running} onReview={() => ws.setMainTab('letters')} />
        ))}
      </ol>
    </div>
  )
}
