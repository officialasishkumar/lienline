import { useWorkspace } from '../../state/workspace'
import { ledgerTime } from '../../lib/model'
import { dayTime, inrShort } from '../../lib/format'
import { Pause, Play, Restart } from '../Icons'

export function Scrubber() {
  const { model, ledger, rule } = useWorkspace()
  const n = model.edges.length
  const p = ledger.value
  const maxAmt = Math.max(...model.edges.map((e) => e.amount), 1)
  const done = Math.min(n, Math.floor(p))
  const now = ledgerTime(model, p)

  return (
    <div className="scrubber">
      <div className="scrub-buttons">
        <button className="icon-btn play" onClick={ledger.toggle} aria-label={ledger.playing ? 'Pause ledger replay' : 'Play ledger replay'}>
          {ledger.playing ? <Pause /> : <Play />}
        </button>
        <button className="icon-btn" onClick={ledger.restart} aria-label="Replay ledger from the start">
          <Restart />
        </button>
      </div>
      <div className="scrub-main">
        <div className="scrub-track">
          <div className="scrub-ticks" aria-hidden="true">
            {model.edges.map((e) => {
              const t = e.tainted[rule]
              const h = 30 + 70 * Math.sqrt(Math.log10(1 + e.amount / 100) / Math.log10(1 + maxAmt / 100))
              return (
                <span
                  key={e.id}
                  className={(t > 0 ? 'tick taint' : 'tick') + (e.index < done ? ' done' : '')}
                  style={{ left: `${((e.index + 0.5) / n) * 100}%`, height: `${h}%` }}
                  title={`${e.id} ${inrShort(e.amount)}`}
                />
              )
            })}
          </div>
          <div className="scrub-fill" style={{ width: `${(p / n) * 100}%` }} aria-hidden="true" />
          <input
            type="range"
            min={0}
            max={n}
            step={0.01}
            value={p}
            onChange={(e) => {
              ledger.pause()
              ledger.seek(Number(e.target.value))
            }}
            aria-label="Ledger time"
            aria-valuetext={`${done} of ${n} transactions, ${dayTime(now)}`}
          />
        </div>
        <div className="scrub-meta mono">
          <span>{model.txns.length ? dayTime(model.txns[0].ts) : ''}</span>
          <span className="scrub-count">
            {done}/{n} txns
          </span>
          <span>{dayTime(model.asOfMs)}</span>
        </div>
      </div>
      <div className="seg speed" role="group" aria-label="Replay speed">
        {[1, 2, 4].map((s) => (
          <button key={s} aria-pressed={ledger.speed === s} onClick={() => ledger.setSpeed(s)}>
            {ledger.speed === s && <span className="seg-thumb" />}
            {s}×
          </button>
        ))}
      </div>
    </div>
  )
}
