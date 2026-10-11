import { useWorkspace } from '../../state/workspace'
import { lienUnder } from '../../lib/model'
import { ACTION_LABEL, RULE_LABEL, inr } from '../../lib/format'
import { Conservation } from '../Conservation'
import { Check } from '../Icons'

export function DecisionsPanel() {
  const ws = useWorkspace()
  const { model, rule, approvals } = ws
  const decisions = [...model.run.decisions].sort((a, b) => b.released_by_change - a.released_by_change)
  const approvedCount = decisions.filter((d) => approvals['D:' + d.account_id] === 'approved').length
  return (
    <div className="decisions">
      <Conservation />
      <div className="dec-head">
        <h4 className="block-title">
          Decisions <span className="muted">· {RULE_LABEL[rule]}</span>
        </h4>
        <button
          className="btn sm approve"
          onClick={() => decisions.forEach((d) => ws.setApproval('D:' + d.account_id, 'approved'))}
          disabled={approvedCount === decisions.length}
        >
          <Check width={14} height={14} /> Approve all ({decisions.length - approvedCount})
        </button>
      </div>
      <ul className="dec-list">
        {decisions.map((d) => {
          const a = model.accounts[d.account_id]
          const after = d.action === 'full_freeze' ? d.current_hold : lienUnder(model, d, rule)
          const ok = approvals['D:' + d.account_id] === 'approved'
          return (
            <li key={d.account_id} className={'dec' + (ws.selected === d.account_id ? ' sel' : '')} style={{ ['--bank' as string]: `var(--bank-${model.bankColor[a?.bank ?? '?']})` }}>
              <button
                className="dec-main"
                onClick={() => ws.select(d.account_id)}
                onMouseEnter={() => ws.setHighlight([d.account_id])}
                onMouseLeave={() => ws.setHighlight(null)}
              >
                <span className="dec-who">
                  <b>{a?.holder ?? d.account_id}</b>
                  <span className="mono">
                    {a?.bank} · {a?.masked}
                  </span>
                </span>
                <span className={`dtag d-${d.action}`}>{ACTION_LABEL[d.action]}</span>
                <span className="dec-nums mono">
                  <s>{inr(d.current_hold)}</s>
                  <b>{inr(after)}</b>
                </span>
              </button>
              <button
                className={'dec-approve' + (ok ? ' ok' : '')}
                onClick={() => ws.setApproval('D:' + d.account_id, ok ? null : 'approved')}
                aria-pressed={ok}
                aria-label={ok ? `Undo approval for ${a?.holder}` : `Approve decision for ${a?.holder}`}
              >
                <Check width={15} height={15} />
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
