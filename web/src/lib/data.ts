import type { CaseIndexEntry, Run } from '../types'
import mockRun from '../mock/c1-archana.json'

const BASE = import.meta.env.BASE_URL || './'

async function getJSON<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(BASE + path, { headers: { Accept: 'application/json' } })
    if (!res.ok) return null
    const type = res.headers.get('content-type') || ''
    // The dev server answers unknown paths with index.html; treat that as "not there".
    if (!type.includes('json')) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

function isRun(x: unknown): x is Run {
  const r = x as Run
  return !!r && typeof r === 'object' && typeof r.case_id === 'string' && Array.isArray(r.accounts) && !!r.trace
}

export function summarize(run: Run): CaseIndexEntry {
  const before = run.decisions.reduce((s, d) => s + d.current_hold, 0)
  const after = run.decisions.reduce((s, d) => s + (d.action === 'release' ? 0 : Math.min(d.amount, d.current_hold || d.amount)), 0)
  return {
    case_id: run.case_id,
    title: run.title,
    summary: run.summary,
    accounts: run.accounts.length,
    banks: run.banks.length,
    lost: run.complaint.amount_lost,
    held_before: before,
    held_after: after,
    status: run.verification?.passed ? 'verified' : 'needs review',
  }
}

export interface LoadedCases {
  index: CaseIndexEntry[]
  runs: Record<string, Run>
  sample: boolean
}

/** Recorded runs from public/runs; falls back to the bundled sample when none are published yet. */
export async function loadCases(): Promise<LoadedCases> {
  const index = await getJSON<CaseIndexEntry[]>('runs/index.json')
  if (Array.isArray(index) && index.length) {
    const loaded = await Promise.all(index.map((c) => getJSON<Run>(`runs/${encodeURIComponent(c.case_id)}.json`)))
    const runs: Record<string, Run> = {}
    loaded.forEach((r) => {
      if (isRun(r)) runs[r.case_id] = r
    })
    const usable = index.filter((c) => runs[c.case_id])
    if (usable.length) return { index: usable.map((c) => ({ ...summarize(runs[c.case_id]), ...c })), runs, sample: false }
  }
  const run = mockRun as unknown as Run
  return { index: [summarize(run)], runs: { [run.case_id]: run }, sample: true }
}
