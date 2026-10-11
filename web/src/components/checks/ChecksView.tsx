import { useWorkspace } from '../../state/workspace'
import { useCaseNow } from '../../hooks/useCaseNow'
import { countdown, dayTime, inr, rupeeText } from '../../lib/format'
import { clockStatus } from '../../lib/clocks'
import { Check, ClockIcon, Cross, Shield } from '../Icons'
import { RefChip } from '../RefChip'
import '../../styles/checks.css'

export function ChecksView() {
  const { model } = useWorkspace()
  const run = model.run
  const now = useCaseNow(run.trace.as_of)
  const clocks = [...run.clocks].sort((a, b) => Date.parse(a.due) - Date.parse(b.due))

  return (
    <div className="checks">
      <section className="checks-col">
        <h3 className="section-title">
          <ClockIcon width={18} height={18} /> Deadlines
          <span className="muted mono">case time {dayTime(now)}</span>
        </h3>
        <ul className="clock-list">
          {clocks.map((c) => {
            const st = clockStatus(c, now)
            const start = Date.parse(c.start)
            const due = Date.parse(c.due)
            const frac = Math.max(0, Math.min(1, (now - start) / Math.max(1, due - start)))
            const left = due - now
            return (
              <li key={c.id} className={`clock s-${st}`}>
                <div className="clock-top">
                  <b>{c.label}</b>
                  <span className={`clock-state s-${st}`}>{st === 'met' ? 'Met' : st === 'breached' ? 'Breached' : 'Running'}</span>
                </div>
                <div className="clock-bar" aria-hidden="true">
                  <span style={{ width: `${(st === 'met' ? 1 : frac) * 100}%` }} />
                </div>
                <div className="clock-meta">
                  <span className="mono clock-count">
                    {st === 'running' ? `${countdown(left)} left` : st === 'breached' ? `${countdown(-left)} overdue` : `due ${dayTime(due)}`}
                  </span>
                  {c.account_id && <RefChip id={c.account_id} />}
                </div>
                <p className="clock-rule">
                  {c.source ? (
                    <a href={c.source} target="_blank" rel="noreferrer noopener">
                      {c.rule}
                    </a>
                  ) : (
                    c.rule
                  )}
                </p>
              </li>
            )
          })}
        </ul>
      </section>

      <section className="checks-col">
        <h3 className="section-title">
          <Shield width={18} height={18} /> Verifier
          <span className={'chip ' + (run.verification.passed ? 'ok' : 'taint')}>{run.verification.passed ? 'all checks passed' : 'checks failed'}</span>
        </h3>
        <ul className="vcheck-list">
          {run.verification.checks.map((c) => (
            <li key={c.name} className={c.ok ? 'ok' : 'bad'}>
              <span className="vc-icon">{c.ok ? <Check /> : <Cross />}</span>
              <span>
                <b>{c.name.replace(/_/g, ' ')}</b>
                {c.detail && <span className="vc-detail">{rupeeText(c.detail)}</span>}
              </span>
            </li>
          ))}
        </ul>

        <h3 className="section-title sub">Complaint &amp; notice</h3>
        <dl className="facts">
          <div>
            <dt>NCRP ack</dt>
            <dd className="mono">{run.complaint.ack_no}</dd>
          </div>
          <div>
            <dt>Lost</dt>
            <dd className="mono">{inr(run.complaint.amount_lost)}</dd>
          </div>
          <div>
            <dt>Police</dt>
            <dd>
              {run.complaint.police_station}
              {run.complaint.io ? ` · IO ${run.complaint.io}` : ''}
            </dd>
          </div>
          {run.notice && (
            <div>
              <dt>Notice</dt>
              <dd>
                Sec. {run.notice.section} · {dayTime(run.notice.issued_at)}
              </dd>
            </div>
          )}
          {run.model && (
            <div>
              <dt>Model</dt>
              <dd className="mono">
                {run.model.chat_model} via {run.model.backend}
                {run.model.calls ? ` · ${run.model.calls} calls` : ''}
              </dd>
            </div>
          )}
        </dl>
        {run.complaint.narrative && <blockquote className="narrative serif">“{rupeeText(run.complaint.narrative)}”</blockquote>}
        {run.notice?.text && <blockquote className="narrative notice mono">{rupeeText(run.notice.text)}</blockquote>}
      </section>
    </div>
  )
}
