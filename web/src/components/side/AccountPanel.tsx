import { useWorkspace } from '../../state/workspace'
import { RULES, byRule, ledgerTime, lienUnder } from '../../lib/model'
import { ACTION_LABEL, ROLE_LABEL, RULE_LABEL, dayTime, inr, rupeeText } from '../../lib/format'
import { HoldCompare } from '../HoldCompare'
import { BalanceChart } from './BalanceChart'
import { RefChip } from '../RefChip'
import { useAnimatedNumber } from '../../hooks/useAnimatedNumber'
import { Cross } from '../Icons'

export function AccountPanel() {
  const ws = useWorkspace()
  const { model, selected, rule, ledger } = ws
  if (!selected || !model.accounts[selected]) {
    return (
      <div className="side-empty">
        <p className="serif">Pick an account in the graph.</p>
        <p>Its balance over time, the traceable victim money under each rule, and the decision with its reasons appear here.</p>
      </div>
    )
  }
  const a = model.accounts[selected]
  const bank = model.banks[a.bank]
  const tr = model.traceOf(a.id)
  const d = model.decisions[a.id]
  const policy = model.run.trace.policy_rule
  const lien = d ? lienUnder(model, d, rule) : 0
  const txns = model.edges.filter((e) => e.from === a.id || e.to === a.id)

  return (
    <div className="acct">
      <header className="acct-head" style={{ ['--bank' as string]: `var(--bank-${model.bankColor[a.bank]})` }}>
        <div>
          <p className="eyebrow">
            <span className="bank-dot" /> {bank?.name ?? a.bank} · {a.masked}
          </p>
          <h3 className="acct-name serif">{a.holder}</h3>
          <div className="acct-tags">
            <span className={'chip' + (a.role.startsWith('mule') ? ' taint' : '')}>{ROLE_LABEL[a.role] ?? a.role}</span>
            {a.kyc_age_days !== undefined && a.kyc_age_days > 0 && (
              <span className={'chip' + (a.kyc_age_days < 90 ? ' warn' : '')}>KYC {a.kyc_age_days < 365 ? `${a.kyc_age_days} days` : `${(a.kyc_age_days / 365).toFixed(1)} yrs`}</span>
            )}
            {!!a.complaints_linked && <span className={'chip' + (a.complaints_linked >= 3 ? ' taint' : '')}>{a.complaints_linked} complaint{a.complaints_linked > 1 ? 's' : ''}</span>}
            {a.registry_hit && <span className="chip taint">Registry hit</span>}
          </div>
        </div>
        <button className="icon-btn" onClick={() => ws.select(null)} aria-label="Close account">
          <Cross />
        </button>
      </header>

      {d && (
        <section className="acct-block">
          <div className="acct-decision">
            <span className={`dtag d-${d.action}`}>{ACTION_LABEL[d.action]}</span>
            {d.confidence && <span className="chip">{d.confidence} confidence</span>}
            {rule !== policy && <span className="chip warn">what-if: {RULE_LABEL[rule]}</span>}
          </div>
          <HoldCompare
            before={d.current_hold}
            after={d.action === 'full_freeze' ? d.current_hold : lien}
            beforeLabel={d.current_hold ? 'Frozen today' : 'Held today'}
            afterLabel={d.action === 'full_freeze' ? 'Full freeze kept' : d.action === 'release' && rule === policy ? 'Release' : `Lien · ${RULE_LABEL[rule]}`}
            note={d.action === 'full_freeze' ? 'Full freeze justified by mule signals' : undefined}
            replayKey={a.id + rule}
          />
        </section>
      )}

      {tr && (
        <section className="acct-block">
          <h4 className="block-title">Balance and traceable money</h4>
          <BalanceChart trace={tr} rule={rule} nowMs={ledgerTime(model, ledger.value)} />
          <RuleBars values={byRule(tr.by_rule)} />
        </section>
      )}

      {d && d.reasons.length > 0 && (
        <section className="acct-block">
          <h4 className="block-title">Why</h4>
          <ol className="reasons">
            {d.reasons.map((r, i) => (
              <li key={i}>
                <p>{rupeeText(r.text)}</p>
                {!!r.refs?.length && (
                  <div className="refs">
                    {r.refs.map((x) => (
                      <RefChip key={x} id={x} />
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ol>
        </section>
      )}

      <section className="acct-block">
        <h4 className="block-title">Ledger entries ({txns.length})</h4>
        <ul className="ledger">
          {txns.map((e) => {
            const out = e.from === a.id
            const other = model.accounts[out ? e.to : e.from]
            const t = e.tainted[rule]
            return (
              <li key={e.id}>
                <button
                  className="ledger-row"
                  onMouseEnter={() => ws.setHighlight([e.id, e.from, e.to])}
                  onMouseLeave={() => ws.setHighlight(null)}
                  onClick={() => ws.focusRef(e.id)}
                >
                  <span className={'dir ' + (out ? 'out' : 'in')}>{out ? 'OUT' : 'IN'}</span>
                  <span className="ledger-who">
                    <b>{other?.holder}</b>
                    <span className="mono">
                      {e.id} · {e.txn.channel} · {dayTime(e.txn.ts)}
                    </span>
                  </span>
                  <span className="ledger-amt mono">
                    {out ? '−' : '+'}
                    {inr(e.amount)}
                    {t > 0 && <span className="ledger-taint">{inr(t)} victim</span>}
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      </section>
    </div>
  )
}

function RuleBars({ values }: { values: Record<string, number> }) {
  const { rule, setRule, model } = useWorkspace()
  const policy = model.run.trace.policy_rule
  const maxV = Math.max(1, ...RULES.map((r) => values[r]))
  const lo = Math.min(...RULES.map((r) => values[r]))
  const hi = Math.max(...RULES.map((r) => values[r]))
  return (
    <div className="rulebars">
      <p className="rulebars-cap">
        Traceable now under each rule {hi !== lo ? <span className="chip warn">rules disagree · {inr(lo)}–{inr(hi)}</span> : <span className="chip ok">all rules agree</span>}
      </p>
      {RULES.map((r) => (
        <RuleBar key={r} r={r} v={values[r]} maxV={maxV} on={r === rule} policy={r === policy} onPick={() => setRule(r)} />
      ))}
    </div>
  )
}

function RuleBar({ r, v, maxV, on, policy, onPick }: { r: string; v: number; maxV: number; on: boolean; policy: boolean; onPick: () => void }) {
  const shown = useAnimatedNumber(v)
  return (
    <button className={'rulebar' + (on ? ' on' : '')} onClick={onPick} aria-pressed={on}>
      <span className="rb-name">
        {RULE_LABEL[r]}
        {policy && <span className="policy-dot" aria-label="(policy)" />}
      </span>
      <span className="rb-track">
        <span className="rb-fill" style={{ width: `${(v / maxV) * 100}%` }} />
      </span>
      <span className="rb-val mono">{inr(Math.round(shown))}</span>
    </button>
  )
}
