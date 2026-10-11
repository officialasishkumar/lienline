import { memo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import type { RunEvent } from '../../types'
import { agentMeta } from '../../lib/agents'
import { rupeeText } from '../../lib/format'
import { useTyping } from '../../hooks/useTyping'
import { RefChip } from '../RefChip'
import { Check, Cross, Doc, Lock } from '../Icons'

const TYPE_LABEL: Record<string, string> = {
  start: 'start',
  message: 'note',
  tool: 'tool',
  check: 'check',
  result: 'result',
  debate: 'argues',
  letter: 'letter',
  approval: 'approval',
}

export const EventRow = memo(function EventRow({ e, typing, onReview }: { e: RunEvent; typing: boolean; onReview?: () => void }) {
  const reduce = useReducedMotion()
  const meta = agentMeta(e.agent)
  const text = rupeeText(e.text)
  const shown = useTyping(text, typing && !reduce)
  const rejected = e.ok === false && (e.type === 'debate' || e.type === 'message' || e.type === 'result')
  const failedCheck = e.ok === false && !rejected
  const reason = typeof e.data?.reason === 'string' ? (e.data.reason as string) : null
  const isCheck = e.type === 'check'

  return (
    <motion.li
      className={`ev k-${e.kind}${rejected ? ' rejected' : ''}${failedCheck ? ' failed' : ''}${isCheck ? ' is-check' : ''}`}
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.2, 0.7, 0.1, 1] }}
    >
      <span className="ev-avatar" aria-hidden="true">
        {meta.short}
      </span>
      <div className="ev-body">
        <div className="ev-meta">
          <b>{e.agent}</b>
          <span className={`chip ${e.kind}`}>{e.kind}</span>
          <span className="ev-type">{TYPE_LABEL[e.type] ?? e.type}</span>
          <span className="ev-t mono">+{e.t.toFixed(1)}s</span>
        </div>
        <p className="ev-text">
          {e.type === 'letter' && <Doc className="ev-inline-icon" />}
          <span className={rejected ? 'strike' : ''}>{shown}</span>
          {typing && shown.length < text.length && <span className="caret" aria-hidden="true" />}
        </p>
        {(rejected || (failedCheck && reason)) && (
          <p className="ev-reject">
            <Cross width={13} height={13} /> {rejected ? 'Rejected by code' : 'Flagged'}
            {reason ? `: ${rupeeText(reason)}` : ''}
          </p>
        )}
        {!!e.refs?.length && (
          <div className="refs">
            {e.refs.map((r) => (
              <RefChip key={r} id={r} />
            ))}
          </div>
        )}
        {e.type === 'approval' && onReview && (
          <button className="btn sm approve ev-review" onClick={onReview}>
            <Lock width={14} height={14} /> Review &amp; approve
          </button>
        )}
      </div>
      {isCheck && (
        <span className={'ev-status ' + (e.ok === false ? 'bad' : 'good')} aria-label={e.ok === false ? 'check failed' : 'check passed'}>
          {e.ok === false ? <Cross /> : <Check />}
        </span>
      )}
    </motion.li>
  )
})
