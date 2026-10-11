import type { Run, RunEvent } from '../types'

// The FastAPI backend (backend/lienline/server.py) is only probed when it can exist, so a static
// deploy never fires a request that would 404 into the console:
//   ?api=http://127.0.0.1:8000   explicit origin
//   ?live=1                      same origin (the Vite dev server proxies /api to :8000)
//   VITE_API_BASE                build-time origin
//   served from port 8000        the backend is serving this build itself
function apiBase(): string | null {
  const params = new URLSearchParams(location.search)
  const q = params.get('api')
  if (q) return q.replace(/\/$/, '')
  if (params.get('live') === '1') return ''
  const env = import.meta.env.VITE_API_BASE as string | undefined
  if (env) return env.replace(/\/$/, '')
  if (location.port === '8000') return ''
  return null
}

export async function backendAvailable(): Promise<boolean> {
  const base = apiBase()
  if (base === null) return false
  const ctl = new AbortController()
  const timer = setTimeout(() => ctl.abort(), 1500)
  try {
    const res = await fetch(`${base}/api/health`, { signal: ctl.signal })
    if (!res.ok || !(res.headers.get('content-type') || '').includes('json')) return false
    const body = (await res.json()) as { ok?: boolean; status?: string }
    return body.ok !== false
  } catch {
    return false
  } finally {
    clearTimeout(timer)
  }
}

function isRun(x: unknown): x is Run {
  const r = x as Run
  return !!r && typeof r === 'object' && typeof r.case_id === 'string' && !!r.trace && Array.isArray(r.accounts)
}

function isEvent(x: unknown): x is RunEvent {
  const e = x as RunEvent
  return !!e && typeof e === 'object' && typeof e.agent === 'string' && typeof e.text === 'string'
}

/**
 * POST /api/run/{case_id} and read its server-sent events. Each `data:` line is either one agent
 * event or, at the end, the full run JSON (possibly wrapped as {run: …} or {data: {run: …}}).
 */
export async function runLive(
  caseId: string,
  handlers: { onEvent: (e: RunEvent) => void; onRun: (r: Run) => void },
  signal: AbortSignal,
): Promise<void> {
  const base = apiBase() ?? ''
  const res = await fetch(`${base}/api/run/${encodeURIComponent(caseId)}`, {
    method: 'POST',
    headers: { Accept: 'text/event-stream' },
    signal,
  })
  if (!res.ok || !res.body) throw new Error(`Backend answered ${res.status}`)
  const reader = res.body.getReader()
  const dec = new TextDecoder()
  let buf = ''
  const t0 = performance.now()
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buf += dec.decode(value, { stream: true })
    let cut: number
    while ((cut = buf.indexOf('\n\n')) >= 0) {
      const block = buf.slice(0, cut)
      buf = buf.slice(cut + 2)
      const data = block
        .split('\n')
        .filter((l) => l.startsWith('data:'))
        .map((l) => l.slice(5).trimStart())
        .join('\n')
      if (!data) continue
      let msg: unknown
      try {
        msg = JSON.parse(data)
      } catch {
        continue
      }
      const m = msg as { run?: unknown; data?: { run?: unknown } }
      const run = isRun(msg) ? msg : isRun(m.run) ? m.run : isRun(m.data?.run) ? m.data?.run : null
      if (run) handlers.onRun(run as Run)
      else if (isEvent(msg)) handlers.onEvent({ ...msg, t: typeof msg.t === 'number' ? msg.t : (performance.now() - t0) / 1000 })
    }
  }
}
