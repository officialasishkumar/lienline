import { useCallback, useEffect, useRef, useState } from 'react'
import type { Run, RunEvent } from '../types'
import { backendAvailable, runLive } from '../lib/live'

export interface LiveRun {
  available: boolean
  running: boolean
  events: RunEvent[] | null // null = no live run yet; replay recorded events
  error: string | null
  start: () => void
  stop: () => void
}

let probe: Promise<boolean> | null = null

/** Detects the local backend once per page and streams POST /api/run/{case_id} when asked. */
export function useLiveRun(caseId: string, onRun: (r: Run) => void): LiveRun {
  const [available, setAvailable] = useState(false)
  const [running, setRunning] = useState(false)
  const [events, setEvents] = useState<RunEvent[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const ctl = useRef<AbortController | null>(null)

  useEffect(() => {
    probe ??= backendAvailable()
    let alive = true
    probe.then((ok) => alive && setAvailable(ok))
    return () => {
      alive = false
    }
  }, [])

  useEffect(() => () => ctl.current?.abort(), [])

  const start = useCallback(() => {
    ctl.current?.abort()
    const c = new AbortController()
    ctl.current = c
    setEvents([])
    setError(null)
    setRunning(true)
    runLive(caseId, { onEvent: (e) => setEvents((xs) => [...(xs ?? []), e]), onRun }, c.signal)
      .catch((e: unknown) => {
        if (!c.signal.aborted) setError(e instanceof Error ? e.message : 'Live run failed')
      })
      .finally(() => {
        if (ctl.current === c) setRunning(false)
      })
  }, [caseId, onRun])

  const stop = useCallback(() => {
    ctl.current?.abort()
    setRunning(false)
  }, [])

  return { available, running, events, error, start, stop }
}
