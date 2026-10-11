import { useCallback, useEffect, useState } from 'react'
import type { Run } from './types'
import { loadCases, summarize, type LoadedCases } from './lib/data'
import { useTheme } from './hooks/useTheme'
import { TopBar } from './components/TopBar'
import { Hero } from './components/hero/Hero'
import { CaseStrip } from './components/CaseStrip'
import { Workspace } from './components/Workspace'
import { Footer } from './components/Footer'

export default function App() {
  const [theme, toggleTheme] = useTheme()
  const [data, setData] = useState<LoadedCases | null>(null)
  const [caseId, setCaseId] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    loadCases().then((d) => {
      if (!alive) return
      setData(d)
      const want = new URLSearchParams(location.search).get('case')
      setCaseId(want && d.runs[want] ? want : d.index[0]?.case_id ?? null)
    })
    return () => {
      alive = false
    }
  }, [])

  // A live run's final JSON replaces the recorded one for that case.
  const onRun = useCallback((r: Run) => {
    setData((d) => {
      if (!d) return d
      const runs = { ...d.runs, [r.case_id]: r }
      const index = d.index.map((c) => (c.case_id === r.case_id ? { ...c, ...summarize(r) } : c))
      return { ...d, runs, index }
    })
  }, [])

  const run = data && caseId ? data.runs[caseId] : null

  return (
    <>
      <a className="skip" href="#desk">
        Skip to the case desk
      </a>
      <TopBar theme={theme} onTheme={toggleTheme} source={!data ? 'loading' : data.sample ? 'sample' : 'recorded'} />
      <main id="top">
        <Hero />
        <section id="desk" className="desk" aria-labelledby="desk-title">
          <div className="desk-head">
            <p className="eyebrow">The case desk</p>
            <h2 id="desk-title" className="serif">
              Every hold, traced to the rupee.
            </h2>
            <p className="desk-lede">
              Pick a case. The ledger replays transaction by transaction while the agents argue, compute and draft. Click any account to see what is
              actually traceable to the victim, under each tracing rule.
            </p>
          </div>
          {data && caseId && (
            <CaseStrip
              index={data.index}
              runs={data.runs}
              current={caseId}
              onPick={(id) => {
                setCaseId(id)
                document.getElementById('workspace')?.scrollIntoView({ block: 'start' })
              }}
            />
          )}
          <div id="workspace">
            {run ? <Workspace key={run.case_id} run={run} sample={!!data?.sample} onRun={onRun} /> : <div className="ws-loading">Loading cases…</div>}
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}
