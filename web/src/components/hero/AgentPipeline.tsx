import { motion, useReducedMotion } from 'framer-motion'
import { AGENTS } from '../../lib/agents'

export function AgentPipeline() {
  const reduce = useReducedMotion()
  return (
    <div className="pipeline" id="how">
      <div className="pipeline-head">
        <p className="eyebrow">Ten roles, one case file</p>
        <ul className="kind-legend" aria-label="Legend">
          <li>
            <i className="k-model" /> model writes
          </li>
          <li>
            <i className="k-code" /> code computes &amp; checks
          </li>
          <li>
            <i className="k-human" /> human approves
          </li>
        </ul>
      </div>
      <ol className="pipeline-list">
        {AGENTS.map((a, i) => (
          <motion.li
            key={a.name}
            className={`pipe-step k-${a.kind}`}
            initial={reduce ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.45, delay: 0.05 * i }}
            style={{ ['--i' as string]: i }}
          >
            <span className="pipe-avatar">{a.short}</span>
            <span className="pipe-text">
              <b>{a.name}</b>
              <span>{a.does}</span>
            </span>
            {a.checkedBy && <span className={`pipe-check k-${a.checkedBy}`} title={`checked by ${a.checkedBy}`} />}
          </motion.li>
        ))}
      </ol>
    </div>
  )
}
