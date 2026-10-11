import { useEffect, useRef, useState } from 'react'
import { useInView, useReducedMotion } from 'framer-motion'

/** Counts from 0 to `to` once the element scrolls into view. */
export function CountUp({ to, format, ms = 1600, delay = 0 }: { to: number; format: (n: number) => string; ms?: number; delay?: number }) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, margin: '0px 0px -10% 0px' })
  const reduce = useReducedMotion()
  const [v, setV] = useState(reduce ? to : 0)
  useEffect(() => {
    if (!inView || reduce) {
      if (reduce) setV(to)
      return
    }
    let raf = 0
    const t0 = performance.now() + delay
    const tick = (now: number) => {
      const k = Math.max(0, Math.min(1, (now - t0) / ms))
      setV(to * (1 - Math.pow(1 - k, 4)))
      if (k < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [inView, reduce, to, ms, delay])
  return (
    <span ref={ref} aria-label={format(to)}>
      <span aria-hidden="true">{format(v)}</span>
    </span>
  )
}
