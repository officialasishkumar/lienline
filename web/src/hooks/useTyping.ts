import { useEffect, useState } from 'react'

/** Reveals `text` character by character (about `cps` per second) when `active`; returns the visible part. */
export function useTyping(text: string, active: boolean, cps = 110): string {
  const [n, setN] = useState(active ? 0 : text.length)
  useEffect(() => {
    if (!active) {
      setN(text.length)
      return
    }
    setN(0)
    let raf = 0
    const t0 = performance.now()
    const tick = (now: number) => {
      const k = Math.min(text.length, Math.floor(((now - t0) / 1000) * cps))
      setN(k)
      if (k < text.length) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [text, active, cps])
  return text.slice(0, n)
}
