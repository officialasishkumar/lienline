import { useEffect, useRef, useState } from 'react'
import { useInView, useReducedMotion } from 'framer-motion'
import { Odometer } from './Odometer'
import { inr, pct } from '../lib/format'
import { Arrow } from './Icons'

interface Props {
  before: number
  after: number
  beforeLabel: string
  afterLabel: string
  size?: 'xl' | 'md'
  note?: string
  /** Changing this replays the roll (e.g. on rule switch or case change). */
  replayKey?: string
}

/** "Frozen ₹2,51,00,000 → Lien ₹980": the after-figure starts at the frozen amount and rolls down. */
export function HoldCompare({ before, after, beforeLabel, afterLabel, size = 'md', note, replayKey }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '0px 0px -15% 0px' })
  const reduce = useReducedMotion()
  const [shown, setShown] = useState(reduce ? after : before)
  const [struck, setStruck] = useState(!!reduce)
  const first = useRef(true)

  useEffect(() => {
    if (reduce) {
      setShown(after)
      setStruck(true)
      return
    }
    if (!inView) return
    const delay = first.current ? 650 : 120
    first.current = false
    const t = setTimeout(() => {
      setShown(after)
      setStruck(true)
    }, delay)
    return () => clearTimeout(t)
  }, [inView, after, reduce, replayKey])

  const released = Math.max(0, before - after)
  return (
    <div ref={ref} className={`hold hold-${size}`}>
      <div className="hold-side before">
        <span className="hold-label">{beforeLabel}</span>
        <span className={'hold-amt mono' + (struck && after < before ? ' struck' : '')}>{inr(before)}</span>
      </div>
      <span className="hold-arrow" aria-hidden="true">
        <Arrow />
      </span>
      <div className="hold-side after">
        <span className="hold-label">{afterLabel}</span>
        <Odometer className="hold-amt mono" value={inr(shown)} label={inr(after)} />
      </div>
      <div className="hold-foot">
        {released > 0 ? (
          <>
            <b className="mono">{inr(released)}</b> returned to the account holder · the hold shrinks to {pct(after, before, 2)} of what was frozen
          </>
        ) : (
          note ?? 'Hold unchanged'
        )}
      </div>
    </div>
  )
}
