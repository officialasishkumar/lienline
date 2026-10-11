import type { Rule } from '../../types'
import type { CaseModel, EdgeModel } from '../../lib/model'
import { RULES } from '../../lib/model'
import { RULE_LABEL, dayTime, inr } from '../../lib/format'

export function EdgeTooltip({ edge, rule, x, y, model }: { edge: EdgeModel; rule: Rule; x: number; y: number; model: CaseModel }) {
  const t = edge.txn
  const from = model.accounts[edge.from]
  const to = model.accounts[edge.to]
  return (
    <div className="edge-tip" style={{ left: x, top: y }} role="tooltip">
      <div className="tip-head">
        <span className="mono">{t.id}</span>
        <span className="chip">{t.channel}</span>
        {t.tainted_origin && <span className="chip taint">origin</span>}
      </div>
      <p className="tip-amt mono">{inr(edge.amount)}</p>
      <p className="tip-route">
        {from?.holder} → {to?.holder}
      </p>
      <p className="tip-meta mono">
        {dayTime(t.ts)} · UTR {t.utr}
      </p>
      {t.note && <p className="tip-note">{t.note}</p>}
      <table className="tip-rules">
        <tbody>
          {RULES.map((r) => (
            <tr key={r} className={r === rule ? 'on' : ''}>
              <th>{RULE_LABEL[r]}</th>
              <td className="mono">{inr(edge.tainted[r])}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
