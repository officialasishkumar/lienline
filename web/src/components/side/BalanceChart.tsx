import { useId, useMemo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { scaleLinear } from 'd3-scale'
import { area, curveStepAfter, line } from 'd3-shape'
import { max } from 'd3-array'
import type { Rule, TraceAccount } from '../../types'
import { RULES, byRule } from '../../lib/model'
import { RULE_LABEL, day, inrShort, time } from '../../lib/format'

const W = 360
const H = 236
const PAD = { l: 8, r: 8 }
const TOP = { y0: 22, y1: 112 } // balance panel
const BOT = { y0: 142, y1: 206 } // traceable-money panel (own scale)

/**
 * Balance over time (top) with the traceable victim money under the selected rule drawn in red on
 * the same scale; below, the same red area magnified on its own scale, with the other rules as faint lines.
 */
export function BalanceChart({ trace, rule, nowMs }: { trace: TraceAccount; rule: Rule; nowMs: number }) {
  const reduce = useReducedMotion()
  const clipId = 'bc' + useId().replace(/:/g, '')
  const pts = trace.series.map((s) => ({ ms: Date.parse(s.ts), bal: s.balance, t: byRule(s.tainted) }))
  const n = pts.length
  const x = useMemo(() => scaleLinear().domain([0, Math.max(1, n - 1)]).range([PAD.l, W - PAD.r]), [n])
  const yTop = scaleLinear()
    .domain([0, max(pts, (p) => p.bal) || 1])
    .range([TOP.y1, TOP.y0])
  const tMax = max(pts, (p) => Math.max(...RULES.map((r) => p.t[r]))) || 1
  const yBot = scaleLinear().domain([0, tMax]).range([BOT.y1, BOT.y0])

  const balArea = area<(typeof pts)[number]>()
    .x((_, i) => x(i))
    .y0(TOP.y1)
    .y1((p) => yTop(p.bal))
    .curve(curveStepAfter)(pts)!
  const balLine = line<(typeof pts)[number]>()
    .x((_, i) => x(i))
    .y((p) => yTop(p.bal))
    .curve(curveStepAfter)(pts)!
  const taintTop = area<(typeof pts)[number]>()
    .x((_, i) => x(i))
    .y0(TOP.y1)
    .y1((p) => yTop(p.t[rule]))
    .curve(curveStepAfter)(pts)!
  const taintBot = area<(typeof pts)[number]>()
    .x((_, i) => x(i))
    .y0(BOT.y1)
    .y1((p) => yBot(p.t[rule]))
    .curve(curveStepAfter)(pts)!
  const ruleLine = (r: Rule) =>
    line<(typeof pts)[number]>()
      .x((_, i) => x(i))
      .y((p) => yBot(p.t[r]))
      .curve(curveStepAfter)(pts)!

  let cur = 0
  pts.forEach((p, i) => {
    if (p.ms <= nowMs) cur = i
  })
  const cx = x(cur)
  const last = pts[n - 1]
  const share = last && last.bal ? last.t[rule] / last.bal : 0
  const tr = { duration: reduce ? 0 : 0.6, ease: [0.2, 0.7, 0.1, 1] as const }

  return (
    <figure className="bchart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Balance and traceable victim money over ${n} ledger points under ${RULE_LABEL[rule]}`}>
        <defs>
          <clipPath id={clipId}>
            <rect x={0} y={0} width={cx + 1} height={H} />
          </clipPath>
        </defs>
        <text className="bc-cap" x={PAD.l} y={12}>
          BALANCE · max {inrShort(yTop.domain()[1])}
        </text>
        <line className="bc-base" x1={PAD.l} x2={W - PAD.r} y1={TOP.y1} y2={TOP.y1} />
        <path className="bc-bal-future" d={balArea} />
        <g clipPath={`url(#${clipId})`}>
          <path className="bc-bal" d={balArea} />
          <path className="bc-bal-line" d={balLine} />
          <motion.path className="bc-taint" initial={false} animate={{ d: taintTop }} transition={tr} />
        </g>

        <text className="bc-cap taint" x={PAD.l} y={BOT.y0 - 8}>
          TRACEABLE VICTIM MONEY · {RULE_LABEL[rule]} · max {inrShort(tMax)}
          {share > 0 && share < 0.02 ? ' · magnified' : ''}
        </text>
        <line className="bc-base" x1={PAD.l} x2={W - PAD.r} y1={BOT.y1} y2={BOT.y1} />
        {RULES.filter((r) => r !== rule).map((r) => (
          <motion.path key={r} className="bc-rule" initial={false} animate={{ d: ruleLine(r) }} transition={tr} />
        ))}
        <g clipPath={`url(#${clipId})`}>
          <motion.path className="bc-taint strong" initial={false} animate={{ d: taintBot }} transition={tr} />
        </g>

        <line className="bc-cursor" x1={cx} x2={cx} y1={TOP.y0 - 4} y2={BOT.y1 + 4} />
        {pts.map((_, i) => (
          <circle key={i} className={i <= cur ? 'bc-pt on' : 'bc-pt'} cx={x(i)} cy={BOT.y1} r={1.8} />
        ))}
        <text className="bc-axis" x={PAD.l} y={H - 8}>
          {n ? `${day(pts[0].ms)} ${time(pts[0].ms)}` : ''}
        </text>
        <text className="bc-axis" x={W - PAD.r} y={H - 8} textAnchor="end">
          {last ? `${day(last.ms)} ${time(last.ms)}` : ''}
        </text>
      </svg>
      <figcaption className="sr-only">Each step is one ledger entry. Red is the traceable share under the selected rule.</figcaption>
    </figure>
  )
}
