import { useEffect, useState } from 'react'
import { useReducedMotion } from 'framer-motion'

const DIGITS = '0123456789'

/**
 * Rolling-digit display for a pre-formatted string ("₹2,51,00,000"). Columns are keyed from the
 * right, so when the number shrinks the leading columns roll to zero and collapse.
 */
export function Odometer({ value, className, label }: { value: string; className?: string; label?: string }) {
  const reduce = useReducedMotion()
  const [ready, setReady] = useState(!!reduce)
  // Widest value seen so far: columns that disappear stay mounted to animate their collapse.
  const [maxLen, setMaxLen] = useState(value.length)
  if (value.length > maxLen) setMaxLen(value.length)
  useEffect(() => {
    if (ready) return
    const id = requestAnimationFrame(() => requestAnimationFrame(() => setReady(true)))
    return () => cancelAnimationFrame(id)
  }, [ready])

  const chars = [...value].reverse()
  const cols = []
  for (let i = maxLen - 1; i >= 0; i--) {
    const ch = chars[i]
    const present = ch !== undefined
    const isDigit = present && DIGITS.includes(ch)
    const delay = `${(maxLen - i) * 35}ms`
    if (!present || isDigit) {
      const d = isDigit && ready ? Number(ch) : 0
      cols.push(
        <span key={i} className={'odo-col' + (present ? '' : ' gone')} style={{ transitionDelay: delay }}>
          <span className="odo-strip" style={{ transform: `translateY(${-d * 10}%)`, transitionDelay: delay }}>
            {DIGITS.split('').map((x) => (
              <span key={x}>{x}</span>
            ))}
          </span>
        </span>,
      )
    } else {
      cols.push(
        <span key={i} className="odo-sym">
          {ch}
        </span>,
      )
    }
  }
  return (
    <span className={'odo ' + (className ?? '')} role="img" aria-label={label ?? value}>
      <span aria-hidden="true">{cols}</span>
    </span>
  )
}
