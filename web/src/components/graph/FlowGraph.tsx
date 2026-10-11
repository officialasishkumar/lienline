import { useCallback, useEffect, useMemo, useRef, useState, type PointerEvent } from 'react'
import { useReducedMotion } from 'framer-motion'
import { scaleLog } from 'd3-scale'
import { select } from 'd3-selection'
import 'd3-transition'
import { zoom as d3zoom, zoomIdentity, type ZoomBehavior, type ZoomTransform } from 'd3-zoom'
import { useWorkspace } from '../../state/workspace'
import { ledgerTime, lienUnder, stateAt } from '../../lib/model'
import { RULE_LABEL, dayTime, inr } from '../../lib/format'
import { GraphNode } from './GraphNode'
import { GraphEdge } from './GraphEdge'
import { EdgeTooltip } from './EdgeTooltip'
import { Fit, Minus, Plus } from '../Icons'
import '../../styles/graph.css'

export function FlowGraph({ height }: { height: number }) {
  const ws = useWorkspace()
  const { model, layout, rule, ledger, highlight, selected } = ws
  const reduce = useReducedMotion()
  const wrapRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const zoomRef = useRef<ZoomBehavior<SVGSVGElement, unknown> | null>(null)
  const [tf, setTf] = useState<ZoomTransform>(zoomIdentity)
  const [hoverEdge, setHoverEdge] = useState<{ id: string; x: number; y: number } | null>(null)
  const [hoverNode, setHoverNode] = useState<string | null>(null)

  const p = ledger.value
  const n = model.edges.length
  const nowMs = ledgerTime(model, p)
  const complete = p >= n

  // Width ∝ amount on a log scale, so ₹980 and ₹40 lakh both stay legible.
  const widthOf = useMemo(() => {
    const amts = model.edges.map((e) => e.amount).filter((a) => a > 0)
    const lo = Math.max(1, Math.min(...amts))
    const hi = Math.max(lo * 10, ...amts)
    const s = scaleLog().domain([lo, hi]).range([1.6, 13]).clamp(true)
    return (a: number) => (a > 0 ? s(a) : 1)
  }, [model])

  const fit = useCallback(
    (animate = true) => {
      const svg = svgRef.current
      const wrap = wrapRef.current
      const z = zoomRef.current
      if (!svg || !wrap || !z) return
      // Keep the top strip (clock, zoom buttons) and the bottom legend clear of the graph.
      const top = 44
      const cw = wrap.clientWidth
      const ch = wrap.clientHeight - top - 30
      let k = Math.min(1.1, cw / layout.width, ch / layout.height)
      if (cw < 700) k = Math.max(k, Math.min(0.74, ch / layout.height))
      const x = layout.width * k < cw ? (cw - layout.width * k) / 2 : 8
      const y = top + (layout.height * k < ch ? (ch - layout.height * k) / 2 : 0)
      const t = zoomIdentity.translate(x, y).scale(k)
      const sel = select(svg)
      if (animate && !reduce) sel.transition().duration(500).call(z.transform, t)
      else sel.call(z.transform, t)
    },
    [layout, reduce],
  )

  useEffect(() => {
    const svg = svgRef.current
    if (!svg) return
    const z = d3zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.25, 3])
      // Plain wheel scrolls the page; ⌘/Ctrl + wheel (and trackpad pinch) zooms the graph.
      .filter((ev: Event) => {
        const e = ev as WheelEvent & MouseEvent
        if (e.type === 'wheel') return e.ctrlKey || e.metaKey
        if (e.type === 'dblclick') return false
        return !e.button
      })
      .on('zoom', (ev) => setTf(ev.transform))
    zoomRef.current = z
    select(svg).call(z)
    fit(false)
    const ro = new ResizeObserver(() => fit(false))
    if (wrapRef.current) ro.observe(wrapRef.current)
    return () => {
      ro.disconnect()
      select(svg).on('.zoom', null)
    }
  }, [fit])

  const zoomBy = (f: number) => {
    const svg = svgRef.current
    if (svg && zoomRef.current) select(svg).transition().duration(reduce ? 0 : 250).call(zoomRef.current.scaleBy, f)
  }

  const onEdgeHover = useCallback((id: string | null, e?: PointerEvent) => {
    if (!id || !e || !wrapRef.current) return setHoverEdge(null)
    const r = wrapRef.current.getBoundingClientRect()
    setHoverEdge({ id, x: e.clientX - r.left, y: e.clientY - r.top })
  }, [])

  // What to emphasise: agent/console highlight, else hovered or selected account and its edges.
  const focusSet = useMemo(() => {
    if (highlight.size) return highlight
    const id = hoverNode ?? selected
    if (!id) return null
    const s = new Set<string>([id])
    model.edges.forEach((e) => {
      if (e.from === id || e.to === id) {
        s.add(e.id)
        s.add(e.from)
        s.add(e.to)
      }
    })
    return s
  }, [highlight, hoverNode, selected, model])

  const edgeEmph = (id: string, from: string, to: string): 'normal' | 'hl' | 'dim' => {
    if (!focusSet) return 'normal'
    if (focusSet.has(id)) return 'hl'
    if (highlight.size && focusSet.has(from) && focusSet.has(to) && ![...highlight].some((h) => model.txnById[h])) return 'hl'
    return 'dim'
  }

  const hovered = hoverEdge ? model.edges.find((e) => e.id === hoverEdge.id) : null
  const currentTxn = Math.floor(p) < n ? model.edges[Math.min(n - 1, Math.floor(p))] : null

  return (
    <div className="graph-wrap" ref={wrapRef} style={{ height }}>
      <svg ref={svgRef} className="graph-svg" role="group" aria-label={`Money trail: ${Object.keys(model.accounts).length} accounts, ${n} transactions`}>
        <defs>
          <pattern id="dotgrid" width="22" height="22" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" className="dotgrid" />
          </pattern>
        </defs>
        <rect className="graph-bg" width="100%" height="100%" fill="url(#dotgrid)" />
        <g transform={tf.toString()}>
          {Array.from({ length: layout.layers }, (_, i) => (
            <text key={i} className="col-head" x={layout.colCenters[i]} y={24} textAnchor="middle">
              {i === 0 ? 'ORIGIN' : `HOP ${i}`}
            </text>
          ))}
          {layout.groups.map((g) => (
            <g key={g.key} className="bank-group" style={{ ['--bank' as string]: `var(--bank-${model.bankColor[g.bank]})` }}>
              <rect x={g.x} y={g.y} width={g.w} height={g.h} rx={12} />
              <text x={g.x + 10} y={g.y + 13}>
                {(model.banks[g.bank]?.name ?? g.bank).toUpperCase()}
              </text>
            </g>
          ))}
          <g className="edges">
            {layout.edges.map((ep) => {
              const e = ep.edge
              const prog = Math.max(0, Math.min(1, p - e.index))
              const w = widthOf(e.amount)
              const t = e.tainted[rule]
              const tw = t > 0 ? Math.max(1.4, w * Math.min(1, t / e.amount)) : 0
              const emph = edgeEmph(e.id, e.from, e.to)
              return (
                <GraphEdge
                  key={e.id}
                  path={ep}
                  progress={prog}
                  width={w}
                  taintWidth={tw}
                  tainted={t}
                  emphasis={emph}
                  showLabel={emph === 'hl' || hoverEdge?.id === e.id}
                  ambient={!reduce && complete}
                  onHover={onEdgeHover}
                />
              )
            })}
          </g>
          <g className="nodes">
            {Object.values(layout.nodes).map((pos) => {
              const a = model.accounts[pos.id]
              const st = stateAt(model, pos.id, nowMs)
              const victim = a.role === 'victim'
              const sentSoFar = victim ? model.edges.filter((e) => e.from === a.id && e.txn.tainted_origin && e.index < p).reduce((s, e) => s + e.amount, 0) : 0
              const d = model.decisions[pos.id]
              return (
                <GraphNode
                  key={pos.id}
                  pos={pos}
                  account={a}
                  bankShort={a.bank === '?' ? 'EXT' : a.bank}
                  bankSlot={model.bankColor[a.bank]}
                  tainted={victim ? sentSoFar : (st?.tainted[rule] ?? 0)}
                  balance={st?.balance ?? null}
                  decision={d}
                  lien={d ? lienUnder(model, d, rule) : undefined}
                  showDecision={complete}
                  selected={selected === pos.id}
                  highlighted={highlight.has(pos.id)}
                  dimmed={!!focusSet && !focusSet.has(pos.id)}
                  isSource={!victim && !model.traceOf(pos.id)}
                  ruleLabel={RULE_LABEL[rule]}
                  onSelect={ws.select}
                  onHover={setHoverNode}
                />
              )
            })}
          </g>
        </g>
      </svg>

      <div className="graph-hud top">
        <span className="hud-clock mono" aria-live="off">
          <span className={ledger.playing ? 'rec on' : 'rec'} />
          {dayTime(nowMs)}
        </span>
        {currentTxn && ledger.playing && (
          <span className="hud-txn mono">
            {currentTxn.id} · {currentTxn.txn.channel} · {inr(currentTxn.amount)}
          </span>
        )}
      </div>

      <div className="graph-zoom" role="group" aria-label="Zoom">
        <button className="icon-btn" onClick={() => zoomBy(1.25)} aria-label="Zoom in">
          <Plus />
        </button>
        <button className="icon-btn" onClick={() => zoomBy(0.8)} aria-label="Zoom out">
          <Minus />
        </button>
        <button className="icon-btn" onClick={() => fit()} aria-label="Fit graph to view">
          <Fit />
        </button>
      </div>

      <div className="graph-legend" aria-hidden="true">
        <span>
          <i className="lg-taint" /> victim money · {RULE_LABEL[rule]}
        </span>
        <span>
          <i className="lg-flow" /> other money
        </span>
        <span>
          <i className="lg-width" /> width ∝ amount
        </span>
        <span className="lg-hint">drag to pan · ⌘/Ctrl + scroll to zoom</span>
        <span className="lg-hint-touch">drag to pan · pinch to zoom</span>
      </div>

      {hovered && hoverEdge && <EdgeTooltip edge={hovered} rule={rule} x={hoverEdge.x} y={hoverEdge.y} model={model} />}
    </div>
  )
}
