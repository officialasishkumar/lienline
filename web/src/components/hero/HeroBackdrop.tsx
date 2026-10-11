/** A faint money trail behind the headline: hop columns, curved flows, and taint particles. */
const NODES: [number, number][] = [
  [80, 300],
  [330, 170],
  [330, 430],
  [600, 90],
  [600, 280],
  [600, 470],
  [880, 160],
  [880, 380],
  [1140, 250],
  [1140, 520],
]
const LINKS: [number, number, boolean][] = [
  [0, 1, true],
  [0, 2, false],
  [1, 3, true],
  [1, 4, true],
  [2, 5, false],
  [4, 6, true],
  [4, 7, false],
  [5, 7, false],
  [6, 8, true],
  [7, 9, false],
  [3, 6, false],
]

function path(a: [number, number], b: [number, number]) {
  const dx = (b[0] - a[0]) / 2
  return `M${a[0] + 60},${a[1]} C${a[0] + 60 + dx},${a[1]} ${b[0] - dx},${b[1]} ${b[0]},${b[1]}`
}

export function HeroBackdrop() {
  return (
    <svg className="hero-backdrop" viewBox="0 0 1260 600" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <linearGradient id="hb-fade" x1="0" x2="1">
          <stop offset="0" stopColor="#fff" stopOpacity="0.9" />
          <stop offset="0.65" stopColor="#fff" stopOpacity="0.35" />
          <stop offset="1" stopColor="#fff" stopOpacity="0.05" />
        </linearGradient>
        <mask id="hb-mask">
          <rect width="1260" height="600" fill="url(#hb-fade)" />
        </mask>
      </defs>
      <g mask="url(#hb-mask)">
        {LINKS.map(([a, b, t], i) => {
          const d = path(NODES[a], NODES[b])
          return (
            <g key={i}>
              <path d={d} className={t ? 'hb-link taint' : 'hb-link'} style={{ animationDelay: `${i * 0.35}s` }} />
              {t && (
                <circle r="3" className="hb-particle">
                  <animateMotion dur={`${3.2 + (i % 3) * 0.6}s`} begin={`${i * 0.4}s`} repeatCount="indefinite" path={d} />
                </circle>
              )}
            </g>
          )
        })}
        {NODES.map(([x, y], i) => (
          <rect key={i} x={x} y={y - 15} width="60" height="30" rx="6" className={i === 0 ? 'hb-node victim' : 'hb-node'} />
        ))}
      </g>
    </svg>
  )
}
