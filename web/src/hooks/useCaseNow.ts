import { useEffect, useState } from 'react'

/**
 * "Case time": the run's as-of instant plus the wall-clock time since the page opened, ticking every
 * second. Deadlines stay meaningful when the recorded run is replayed days later.
 */
export function useCaseNow(baseIso: string | undefined): number {
  const [mounted] = useState(() => Date.now())
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])
  const base = baseIso ? Date.parse(baseIso) : mounted
  return base + (now - mounted)
}
