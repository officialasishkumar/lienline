import { memo } from 'react'
import type { Account, Decision } from '../../types'
import { NODE_H, NODE_W, type NodePos } from '../../lib/layout'
import { inr, inrShort, ROLE_LABEL, ACTION_LABEL } from '../../lib/format'

interface Props {
  pos: NodePos
  account: Account
  bankShort: string
  bankSlot: number
  tainted: number
  balance: number | null
  decision?: Decision
  lien?: number
  showDecision: boolean
  selected: boolean
  highlighted: boolean
  dimmed: boolean
  isSource: boolean
  ruleLabel: string
  onSelect: (id: string) => void
  onHover: (id: string | null) => void
}

function clip(s: string, n: number) {
  return s.length > n ? s.slice(0, n - 1) + '…' : s
}

export const GraphNode = memo(function GraphNode(p: Props) {
  const { pos, account: a } = p
  const victim = a.role === 'victim'
  const cash = a.role === 'cashout' || a.kind === 'atm'
  const hot = p.tainted > 0
  const cls = [
    'gnode',
    victim && 'victim',
    cash && 'cash',
    hot && 'hot',
    p.selected && 'selected',
    p.highlighted && 'hl',
    p.dimmed && 'dim',
    p.isSource && 'source',
  ]
    .filter(Boolean)
    .join(' ')
  const label = `${a.holder}, ${p.bankShort} ${a.masked}, ${ROLE_LABEL[a.role] ?? a.role}. ${
    hot ? `${inr(p.tainted)} traceable under ${p.ruleLabel}` : 'no traceable victim money'
  }${p.decision ? `. Decision: ${ACTION_LABEL[p.decision.action]}` : ''}`

  const pill = (victim ? 'lost ' : '') + inrShort(p.tainted)
  const chip = p.showDecision && p.decision ? decisionChip(p.decision, p.lien ?? p.decision.amount) : null

  return (
    <g
      className={cls}
      transform={`translate(${pos.x},${pos.y})`}
      style={{ ['--bank' as string]: `var(--bank-${p.bankSlot})` }}
      role="button"
      tabIndex={0}
      aria-label={label}
      aria-pressed={p.selected}
      onClick={() => p.onSelect(a.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          p.onSelect(a.id)
        }
      }}
      onMouseEnter={() => p.onHover(a.id)}
      onMouseLeave={() => p.onHover(null)}
      onFocus={() => p.onHover(a.id)}
      onBlur={() => p.onHover(null)}
    >
      {p.highlighted && <rect className="gnode-ring" x={-6} y={-6} width={NODE_W + 12} height={NODE_H + 12} rx={13} />}
      <rect className="gnode-card" width={NODE_W} height={NODE_H} rx={9} />
      <rect className="gnode-stripe" x={0} y={0} width={4} height={NODE_H} rx={2} />
      <text className="gnode-role" x={14} y={17}>
        {victim ? 'VICTIM' : cash ? 'CASH OUT' : a.kind === 'external' ? 'NOT TRACED' : (ROLE_LABEL[a.role] ?? a.role).replace('Mule · layer ', 'MULE · L').toUpperCase()}
      </text>
      <text className="gnode-title" x={14} y={34}>
        {clip(a.holder, 21)}
      </text>
      <text className="gnode-sub" x={14} y={49}>
        {p.bankShort} · {a.masked}
      </text>
      {hot && (
        <g className="gnode-taint" transform={`translate(12, ${NODE_H - 6})`}>
          <rect height={15} width={pill.length * 6.3 + 14} rx={7.5} />
          <circle cx={7} cy={7.5} r={2.6} />
          <text x={13} y={11}>
            {pill}
          </text>
        </g>
      )}
      {chip && (
        <g className={`gnode-decision d-${p.decision!.action}`} transform={`translate(${NODE_W - chip.w - 8}, -8)`}>
          <rect width={chip.w} height={16} rx={4} />
          <text x={chip.w / 2} y={11.5} textAnchor="middle">
            {chip.text}
          </text>
        </g>
      )}
    </g>
  )
})

function decisionChip(d: Decision, lien: number) {
  const text = d.action === 'lien' ? `LIEN ${inrShort(lien)}` : d.action === 'full_freeze' ? 'FULL FREEZE' : 'RELEASE'
  return { text, w: text.length * 6.1 + 12 }
}
