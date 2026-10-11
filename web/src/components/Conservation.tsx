import { motion, useReducedMotion } from 'framer-motion'
import { useWorkspace } from '../state/workspace'
import { RULE_LABEL, inr } from '../lib/format'

/** Where the victim's money is now: held + cashed out + untraced = lost (under the policy rule). */
export function Conservation() {
  const { model } = useWorkspace()
  const reduce = useReducedMotion()
  const c = model.run.trace.conservation
  const lost = c.lost || 1
  const parts = [
    { k: 'held', label: 'Held in accounts', v: c.held },
    { k: 'cashed', label: 'Cashed out', v: c.cashed_out },
    { k: 'untraced', label: 'Untraced', v: c.untraced },
  ]
  const sum = c.held + c.cashed_out + c.untraced
  return (
    <div className="conserve">
      <div className="conserve-head">
        <h4 className="block-title">Where the ₹ went</h4>
        <span className={'chip ' + (sum === c.lost ? 'ok' : 'taint')}>
          {sum === c.lost ? 'adds up' : 'does not add up'} · {RULE_LABEL[model.run.trace.policy_rule]}
        </span>
      </div>
      <div className="conserve-bar" role="img" aria-label={parts.map((p) => `${p.label} ${inr(p.v)}`).join(', ') + `, of ${inr(c.lost)} lost`}>
        {parts.map((p, i) => (
          <motion.span
            key={p.k}
            className={`cb-${p.k}`}
            style={{ flexBasis: `${(p.v / lost) * 100}%` }}
            initial={reduce ? false : { scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.8, delay: 0.15 * i, ease: [0.2, 0.7, 0.1, 1] }}
          />
        ))}
      </div>
      <dl className="conserve-legend">
        {parts.map((p) => (
          <div key={p.k}>
            <dt>
              <i className={`cb-${p.k}`} /> {p.label}
            </dt>
            <dd className="mono">{inr(p.v)}</dd>
          </div>
        ))}
        <div className="total">
          <dt>Lost by the victim</dt>
          <dd className="mono">{inr(c.lost)}</dd>
        </div>
      </dl>
    </div>
  )
}
