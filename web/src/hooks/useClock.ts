import { useCallback, useEffect, useRef, useState } from 'react'

export interface Clock {
  value: number
  playing: boolean
  speed: number
  max: number
  play: () => void
  pause: () => void
  toggle: () => void
  seek: (v: number) => void
  restart: () => void
  setSpeed: (s: number) => void
}

/**
 * A requestAnimationFrame clock running from 0 to `max` at `rate` units per second (times speed).
 * Shared by the ledger scrubber (units = transactions) and the agent console (units = seconds).
 */
export function useClock(max: number, rate: number, opts: { autoplay?: boolean; start?: number } = {}): Clock {
  const [value, setValue] = useState(opts.start ?? 0)
  const [playing, setPlaying] = useState(!!opts.autoplay)
  const [speed, setSpeed] = useState(1)
  const valueRef = useRef(value)

  useEffect(() => {
    if (!playing) return
    let raf = 0
    let last = performance.now()
    const tick = (now: number) => {
      const dt = Math.min(0.1, (now - last) / 1000)
      last = now
      const next = Math.min(max, valueRef.current + dt * rate * speed)
      valueRef.current = next
      setValue(next)
      if (next >= max) {
        setPlaying(false)
        return
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [playing, max, rate, speed])

  const play = useCallback(() => {
    if (valueRef.current >= max) {
      valueRef.current = 0
      setValue(0)
    }
    setPlaying(true)
  }, [max])
  const pause = useCallback(() => setPlaying(false), [])
  const toggle = useCallback(() => (playing ? pause() : play()), [playing, pause, play])
  const seek = useCallback(
    (v: number) => {
      const c = Math.max(0, Math.min(max, v))
      valueRef.current = c
      setValue(c)
    },
    [max],
  )
  const restart = useCallback(() => {
    valueRef.current = 0
    setValue(0)
    setPlaying(true)
  }, [])

  return { value, playing, speed, max, play, pause, toggle, seek, restart, setSpeed }
}
