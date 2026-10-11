# LienLine web

Vite + React + TypeScript UI for LienLine. It replays recorded agent runs from `public/runs/*.json` (the contract is in `../SPEC.md`). If a local backend is reachable, it can also stream a live run.

```bash
npm install
npm run dev        # http://localhost:5173 (proxies /api to http://127.0.0.1:8000)
npm run build      # type-check + production build to dist/
npm run preview    # serve dist/ on http://localhost:4173
npm run lint       # oxlint
```

## What is on the page

- **Hero**: the problem in numbers, a pipeline of the ten roles, and a faint animated money trail.
- **Case desk**: case cards with live deadline clocks. "Case time" is the run's `as_of` plus the time since the page opened.
- **Money trail and agents**:
  - A hop-layered flow graph, grouped and coloured by bank. Edges animate in ledger order with particles; edge width is proportional to amount (log scale), and the red core shows the tainted share under the selected rule.
  - A play/pause time scrubber and a rule switcher (FIFO / LIFO / Pro-rata / LIBR).
  - Account side panel: balance-over-time chart and per-rule bars.
  - Hold before/after shown with an odometer.
  - Agent console replays `events` with their timing. Evidence chips highlight the graph, rejected claims are struck through, and verifier checks are ticked.
- **Letters**: formal letter rendering with verified-number highlights. The nodal officer can edit, approve or undo approval (local state only). Approval is blocked while any figure fails to match the case.
- **Deadlines and checks**: SOP and court clocks with citations, verifier checks, and the complaint and notice.

## Data

- `public/runs/index.json` and `public/runs/<case_id>.json` are written by `backend/scripts/record.py`; do not edit them by hand.
- If no runs are published, the app falls back to the bundled sample `src/mock/c1-archana.json`. A "Sample case" pill then appears in the top bar.
- Runs made by the deterministic fallback finish in milliseconds. Their event offsets are re-paced for a readable replay, and the order of events is unchanged.

## Live mode

The backend is probed only where it can exist, so a static deploy never sends requests that would 404:

| How the page is opened | Backend it uses |
| --- | --- |
| `?api=http://127.0.0.1:8000` | that origin |
| `?live=1` | same origin (the dev server proxies `/api`) |
| `VITE_API_BASE` set at build time | that origin |
| served from port 8000 | same origin |

When `GET /api/health` answers with JSON, a **Run live** button appears in the agent console. It streams `POST /api/run/{case_id}` as server-sent events. Each `data:` line is one event; a line holding the full run replaces the recorded run for that case.

## Static hosting

`vite.config.ts` sets `base: './'`, so `dist/` works from any sub-path. Fonts are bundled through `@fontsource`, and the page makes no CDN requests at runtime.

## Accessibility

- Graph nodes, chips, tabs, the rule radio group (arrow keys), the scrubber (range input) and the zoom buttons all work from the keyboard.
- `prefers-reduced-motion` disables particles and typing, and starts replays at the end.
- Light and dark themes follow the system and can be toggled.
- The layout works down to 390 px: the graph can be panned and pinched, and the panels stack.
