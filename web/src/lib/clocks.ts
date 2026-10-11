import type { Clock, ClockStatus, Run } from '../types'

/** Live status at case time: a running clock past its due time counts as breached. */
export function clockStatus(c: Clock, now: number): ClockStatus {
  if (c.status === 'met' || c.status === 'breached') return c.status
  return now > Date.parse(c.due) ? 'breached' : 'running'
}

/** The running deadline due soonest, for the case list. */
export function nextClock(run: Run, now: number): Clock | null {
  const running = run.clocks.filter((c) => clockStatus(c, now) === 'running').sort((a, b) => Date.parse(a.due) - Date.parse(b.due))
  return running[0] ?? null
}
