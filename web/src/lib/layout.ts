import type { CaseModel, EdgeModel } from './model'

export const NODE_W = 164
export const NODE_H = 58
const COL_GAP = 104
const ROW_GAP = 22
const GROUP_GAP = 30
const GROUP_PAD = 10
const GROUP_LABEL = 18
const MARGIN = { top: 44, right: 96, bottom: 50, left: 40 }

export interface NodePos {
  id: string
  x: number
  y: number
  layer: number
}

export interface GroupBox {
  key: string
  bank: string
  layer: number
  x: number
  y: number
  w: number
  h: number
}

export interface EdgePath {
  edge: EdgeModel
  d: string
  back: boolean
  // cubic bezier control points, for placing particles without DOM measurement
  pts: [number, number][]
  mid: [number, number]
}

export interface Layout {
  nodes: Record<string, NodePos>
  groups: GroupBox[]
  edges: EdgePath[]
  width: number
  height: number
  layers: number
  colCenters: number[]
}

const ROLE_ORDER: Record<string, number> = { victim: 0, mule_l1: 1, mule_l2: 2, merchant: 3, innocent: 4, cashout: 5 }

/** Hop layers from the victim, grouped by bank inside each column. */
export function layoutGraph(m: CaseModel): Layout {
  const ids = Object.keys(m.accounts)
  const layer: Record<string, number> = {}
  const sources = new Set<string>()
  m.edges.forEach((e) => {
    if (e.txn.tainted_origin) sources.add(e.from)
  })
  ids.forEach((id) => {
    if (m.accounts[id].role === 'victim') sources.add(id)
  })
  if (!sources.size && m.edges.length) sources.add(m.edges[0].from)
  sources.forEach((s) => (layer[s] = 0))

  // Shortest hop count, following transactions in time order (money can only move forward in time).
  let changed = true
  let guard = 0
  while (changed && guard++ < 50) {
    changed = false
    for (const e of m.edges) {
      if (layer[e.from] === undefined) continue
      const cand = layer[e.from] + 1
      if (layer[e.to] === undefined || cand < layer[e.to]) {
        if (sources.has(e.to)) continue
        layer[e.to] = cand
        changed = true
      }
    }
  }
  // Clean sources feeding the trail sit one column before what they feed.
  ids.forEach((id) => {
    if (layer[id] !== undefined) return
    const targets = m.edges.filter((e) => e.from === id && layer[e.to] !== undefined).map((e) => layer[e.to])
    layer[id] = targets.length ? Math.max(0, Math.min(...targets) - 1) : 0
  })

  const maxLayer = Math.max(0, ...Object.values(layer))
  const firstSeen: Record<string, number> = {}
  m.edges.forEach((e) => {
    if (firstSeen[e.to] === undefined) firstSeen[e.to] = e.index
    if (firstSeen[e.from] === undefined) firstSeen[e.from] = e.index
  })

  const cols: string[][] = Array.from({ length: maxLayer + 1 }, () => [])
  ids.forEach((id) => cols[layer[id]].push(id))
  const bankIdx = (b: string) => m.bankOrder.indexOf(b)
  cols.forEach((c) =>
    c.sort((a, b) => {
      const A = m.accounts[a]
      const B = m.accounts[b]
      return (
        bankIdx(A.bank) - bankIdx(B.bank) ||
        (ROLE_ORDER[A.role] ?? 9) - (ROLE_ORDER[B.role] ?? 9) ||
        (firstSeen[a] ?? 99) - (firstSeen[b] ?? 99)
      )
    }),
  )

  // Measure column heights, then centre each column.
  const colStep = NODE_W + COL_GAP
  const colHeights = cols.map((c) => {
    let h = 0
    let prevBank: string | null = null
    c.forEach((id) => {
      const b = m.accounts[id].bank
      if (b !== prevBank) h += (prevBank === null ? 0 : GROUP_GAP) + GROUP_LABEL + GROUP_PAD
      else h += ROW_GAP
      h += NODE_H
      prevBank = b
    })
    return h + GROUP_PAD
  })
  const inner = Math.max(...colHeights, NODE_H)

  const nodes: Record<string, NodePos> = {}
  const groups: GroupBox[] = []
  cols.forEach((c, li) => {
    const x = MARGIN.left + li * colStep
    let y = MARGIN.top + (inner - colHeights[li]) / 2
    let prevBank: string | null = null
    let group: GroupBox | null = null
    c.forEach((id) => {
      const b = m.accounts[id].bank
      if (b !== prevBank) {
        if (group) groups.push(group)
        y += prevBank === null ? 0 : GROUP_GAP
        group = { key: `${li}-${b}-${id}`, bank: b, layer: li, x: x - GROUP_PAD, y, w: NODE_W + GROUP_PAD * 2, h: 0 }
        y += GROUP_LABEL + GROUP_PAD
      } else y += ROW_GAP
      nodes[id] = { id, x, y, layer: li }
      y += NODE_H
      if (group) group.h = y - group.y + GROUP_PAD
      prevBank = b
    })
    if (group) groups.push(group)
  })

  // Edge geometry; parallel transactions between the same pair fan out slightly.
  const pairCount: Record<string, number> = {}
  const pairSeen: Record<string, number> = {}
  m.edges.forEach((e) => {
    const k = e.from + '>' + e.to
    pairCount[k] = (pairCount[k] || 0) + 1
  })
  const edges: EdgePath[] = m.edges.map((e) => {
    const a = nodes[e.from]
    const b = nodes[e.to]
    const k = e.from + '>' + e.to
    const i = (pairSeen[k] = (pairSeen[k] ?? -1) + 1)
    const off = (i - (pairCount[k] - 1) / 2) * 9
    const back = b.layer < a.layer
    const same = b.layer === a.layer
    let pts: [number, number][]
    if (same) {
      // Same hop column: loop out to the right so the curve never crosses the column's cards.
      const sx = a.x + NODE_W
      const sy = a.y + NODE_H / 2 + off
      const tx = b.x + NODE_W
      const ty = b.y + NODE_H / 2 + off
      const bulge = 46 + Math.min(60, Math.abs(ty - sy) * 0.18)
      pts = [
        [sx, sy],
        [sx + bulge, sy],
        [tx + bulge, ty],
        [tx, ty],
      ]
    } else if (!back) {
      const sx = a.x + NODE_W
      const sy = a.y + NODE_H / 2 + off
      const tx = b.x
      const ty = b.y + NODE_H / 2 + off
      const dx = Math.max(40, (tx - sx) * 0.5)
      pts = [
        [sx, sy],
        [sx + dx, sy],
        [tx - dx, ty],
        [tx, ty],
      ]
    } else {
      const sx = a.x + NODE_W / 2 + off
      const sy = a.y + NODE_H
      const tx = b.x + NODE_W / 2 + off
      const ty = b.y + NODE_H
      const dip = Math.max(sy, ty) + 70 + Math.abs(a.layer - b.layer) * 10
      pts = [
        [sx, sy],
        [sx, dip],
        [tx, dip],
        [tx, ty],
      ]
    }
    const d = `M${pts[0][0]},${pts[0][1]} C${pts[1][0]},${pts[1][1]} ${pts[2][0]},${pts[2][1]} ${pts[3][0]},${pts[3][1]}`
    return { edge: e, d, back: back || same, pts, mid: bezier(pts, 0.5) }
  })

  const width = MARGIN.left + (maxLayer + 1) * colStep - COL_GAP + MARGIN.right
  const height = MARGIN.top + inner + MARGIN.bottom
  const colCenters = cols.map((_, i) => MARGIN.left + i * colStep + NODE_W / 2)
  return { nodes, groups, edges, width, height, layers: maxLayer + 1, colCenters }
}

export function bezier(p: [number, number][], t: number): [number, number] {
  const u = 1 - t
  const a = u * u * u
  const b = 3 * u * u * t
  const c = 3 * u * t * t
  const d = t * t * t
  return [a * p[0][0] + b * p[1][0] + c * p[2][0] + d * p[3][0], a * p[0][1] + b * p[1][1] + c * p[2][1] + d * p[3][1]]
}
