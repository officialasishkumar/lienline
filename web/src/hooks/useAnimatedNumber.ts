import { useEffect, useRef, useState } from 'react'
import { useReducedMotion } from 'framer-motion'

/** Tweens from the previous value to `value` (ease-out) so rule switches visibly re-count. */
export function useAnimatedNumber(value: number, ms = 700): number {
  const reduce = useReducedMotion()
  const [shown, setShown] = useState(value)
  const from = useRef(value)
  useEffect(() => {
    if (reduce || from.current === value) {
      from.current = value
      setShown(value)
      return
    }
    const start = from.current
    const t0 = performance.now()
    let raf = 0
    const tick = (now: number) => {
      const k = Math.min(1, (now - t0) / ms)
      const e = 1 - Math.pow(1 - k, 3)
      const v = start + (value - start) * e
      from.current = v
      setShown(v)
      if (k < 1) raf = requestAnimationFrame(tick)
      else from.current = value
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value, ms, reduce])
  return shown
}
