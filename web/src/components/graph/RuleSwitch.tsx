import { motion } from 'framer-motion'
import { useWorkspace } from '../../state/workspace'
import { RULES } from '../../lib/model'
import { RULE_HELP, RULE_LABEL } from '../../lib/format'

export function RuleSwitch({ id = 'rule' }: { id?: string }) {
  const { rule, setRule, model } = useWorkspace()
  const policy = model.run.trace.policy_rule
  return (
    <div className="rule-switch">
      <div className="seg" role="radiogroup" aria-label="Tracing rule" aria-describedby={`${id}-help`}>
        {RULES.map((r) => (
          <button
            key={r}
            role="radio"
            aria-checked={rule === r}
            onClick={() => setRule(r)}
            onKeyDown={(e) => {
              const i = RULES.indexOf(rule)
              const step = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0
              if (!step) return
              e.preventDefault()
              const j = (i + step + RULES.length) % RULES.length
              setRule(RULES[j])
              ;(e.currentTarget.parentElement?.children[j] as HTMLElement | undefined)?.focus()
            }}
            tabIndex={rule === r ? 0 : -1}
            title={RULE_HELP[r]}
          >
            {rule === r && <motion.span layoutId={`${id}-thumb`} className="seg-thumb" transition={{ type: 'spring', stiffness: 500, damping: 38 }} />}
            {RULE_LABEL[r]}
            {r === policy && <span className="policy-dot" aria-label="(policy rule)" />}
          </button>
        ))}
      </div>
      <p id={`${id}-help`} className="rule-help">
        {RULE_HELP[rule]}
        {rule !== policy && <span className="rule-note"> Policy uses {RULE_LABEL[policy]}; this view is a what-if.</span>}
      </p>
    </div>
  )
}
