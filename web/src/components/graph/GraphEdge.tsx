import { memo, type PointerEvent } from 'react'
import type { EdgePath } from '../../lib/layout'
import { bezier } from '../../lib/layout'
import { inrShort } from '../../lib/format'

interface Props {
  path: EdgePath
  progress: number // 0..1 drawn
  width: number
  taintWidth: number
  tainted: number
  emphasis: 'normal' | 'hl' | 'dim'
  showLabel: boolean
  ambient: boolean
  onHover: (id: string | null, e?: PointerEvent) => void
}

export const GraphEdge = memo(function GraphEdge(p: Props) {
  const { path, progress } = p
  const e = path.edge
  const cash = e.txn.channel === 'ATM' || e.txn.channel === 'CASH'
  const active = progress > 0 && progress < 1
  const done = progress >= 1
  const head = active ? bezier(path.pts, progress) : null
  const cls = ['gedge', p.emphasis, cash && 'cash', active && 'active', path.back && 'back'].filter(Boolean).join(' ')
  const offset = 1 - progress

  return (
    <g className={cls} onPointerEnter={(ev) => p.onHover(e.id, ev)} onPointerMove={(ev) => p.onHover(e.id, ev)} onPointerLeave={() => p.onHover(null)}>
      {progress === 0 && <path className="gedge-ghost" d={path.d} />}
      {progress > 0 && (
        <>
          <path className="gedge-hit" d={path.d} />
          <path
            className="gedge-flow"
            d={path.d}
            pathLength={1}
            strokeDasharray="1 1"
            strokeDashoffset={offset}
            style={{ strokeWidth: p.width }}
          />
          {p.tainted > 0 && (
            <path
              className="gedge-taint"
              d={path.d}
              pathLength={1}
              strokeDasharray="1 1"
              strokeDashoffset={offset}
              style={{ strokeWidth: p.taintWidth }}
            />
          )}
        </>
      )}
      {head && (
        <g className={p.tainted > 0 ? 'gedge-head taint' : 'gedge-head'}>
          {[0.06, 0.12].map((lag) => {
            const q = bezier(path.pts, Math.max(0, progress - lag))
            return <circle key={lag} cx={q[0]} cy={q[1]} r={Math.max(2, p.width / 2.6) * (1 - lag * 4)} opacity={0.5 - lag * 2.5} />
          })}
          <circle cx={head[0]} cy={head[1]} r={Math.max(3, p.width / 2 + 1)} />
        </g>
      )}
      {done && p.ambient && p.tainted > 0 && (
        <circle className="gedge-particle" r={Math.max(1.8, p.taintWidth / 2.4)}>
          <animateMotion dur={`${2.4 + (e.index % 4) * 0.35}s`} repeatCount="indefinite" path={path.d} />
        </circle>
      )}
      {(p.showLabel || active) && progress > 0.25 && (
        <g className="gedge-label" transform={`translate(${path.mid[0]},${path.mid[1] - p.width / 2 - 9})`}>
          <rect x={-labelW(e.amount, p.tainted) / 2} y={-9} width={labelW(e.amount, p.tainted)} height={17} rx={8.5} />
          <text textAnchor="middle" y={3.5}>
            <tspan className="l-id">{e.id}</tspan>
            <tspan dx={5}>{inrShort(e.amount)}</tspan>
            {p.tainted > 0 && p.tainted < e.amount && (
              <tspan className="l-taint" dx={5}>
                {inrShort(p.tainted)}
              </tspan>
            )}
          </text>
        </g>
      )}
    </g>
  )
})

function labelW(amount: number, tainted: number) {
  const t = `${inrShort(amount)}` + (tainted > 0 && tainted < amount ? ' ' + inrShort(tainted) : '')
  return (t.length + 4) * 6.2 + 14
}
