"""Deck styling shared with the Phantom Order deck: base typography, slide frame, and the component classes slides use."""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800;900&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap');
@page { size: 1280px 720px; margin: 0 }
:root { --ink:#0d1b2a; --muted:#56657a; --line:#d6dde7; --bg:#ffffff; --soft:#f2f5f9; --red:#c0322c; --red-soft:#fbe5e3; --amber:#8f5300; --amber-soft:#fbefd9; --green:#1f6e44; --green-soft:#dff3e7; --blue:#1f4fd1; --blue-soft:#e3eafc }
* { box-sizing: border-box }
body { margin: 0; font-family: 'IBM Plex Sans', system-ui, sans-serif; color: var(--ink); -webkit-print-color-adjust: exact; print-color-adjust: exact }
.slide { width: 1280px; height: 720px; padding: 44px 64px 54px 76px; background: var(--bg); position: relative; overflow: hidden; page-break-after: always; display: flex; flex-direction: column; gap: 12px }
.bar { position: absolute; left: 0; top: 0; width: 14px; height: 100%; background: var(--red) }
header { display: flex; justify-content: space-between; align-items: center }
.k { font: 600 14px 'IBM Plex Sans'; letter-spacing: .12em; text-transform: uppercase; color: var(--red) }
.ptag { font: 600 12px 'IBM Plex Sans'; background: var(--amber-soft); color: var(--amber); padding: 4px 10px; border-radius: 99px }
h1 { font: 800 34px/1.12 'Archivo', sans-serif; margin: 0; letter-spacing: -.01em; max-width: 1120px }
.body { flex: 1; min-height: 0; font-size: 18px; line-height: 1.45 }
footer { position: absolute; left: 76px; right: 64px; bottom: 18px; display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 8px }
.note { font-size: 13px; color: var(--muted); margin: 0 }
.note2 { font-size: 13.5px; color: var(--muted); margin: 10px 0 0; line-height: 1.45 }
b { font-weight: 700 }
.cover { background: linear-gradient(135deg, #0d1b2a 0%, #13263b 62%, #3a1414 100%); color: #fff; justify-content: center; gap: 18px }
.cover .k { color: #ffb4ae }
.giant { font: 900 104px/1 'Archivo'; color: #fff; letter-spacing: -.02em }
.sub { font-size: 25px; line-height: 1.35; max-width: 980px; margin: 0; color: #e6ecf3 }
.covergrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 10px }
.covergrid div { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.18); border-radius: 12px; padding: 14px 16px; display: grid; gap: 4px }
.covergrid b { color: #ffb4ae; font-size: 14px; text-transform: uppercase; letter-spacing: .08em }
.covergrid span { font-size: 15.5px; line-height: 1.4; color: #eef2f7 }
.team { font-size: 16px; color: #c6d0dc; margin: 6px 0 0 }
.brief { display: grid; gap: 8px; margin-top: 8px }
.brief .bk { color: #ffb4ae; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em }
.brief ol { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px }
.brief li { display: grid; grid-template-columns: auto 1fr; gap: 2px 8px; align-items: baseline; border-top: 2px solid rgba(255,180,174,.5); padding-top: 8px }
.brief i { font-style: normal; font-weight: 800; font-size: 18px; color: #ffb4ae; grid-row: span 2 }
.brief b { font-size: 14px; font-weight: 700; color: #fff }
.brief span { font-size: 13px; line-height: 1.3; color: #c6d0dc }
.cover footer { color: #9fb0c3; border-color: rgba(255,255,255,.2) }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px }
.grid2.r { grid-template-columns: 1.15fr 1fr; align-items: start }
.card { background: var(--soft); border-radius: 12px; padding: 14px 18px }
.card h3 { margin: 0 0 6px; font: 700 15px 'IBM Plex Sans'; text-transform: uppercase; letter-spacing: .08em; color: var(--red) }
.card p { margin: 0; font-size: 15.5px; line-height: 1.45 }
.timeline { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; position: relative; margin-top: 4px }
.ev { border-top: 4px solid var(--line); padding-top: 10px; display: grid; gap: 5px; align-content: start }
.ev b { font: 800 17px 'Archivo' }
.ev span { font-size: 14px; line-height: 1.38 }
.ev.bad { border-color: var(--red) } .ev.bad b { color: var(--red) }
.ev.ours { border-color: var(--blue) } .ev.ours b { color: var(--blue) }
.lead { margin: 14px 0 0; padding: 14px 18px; background: var(--red-soft); border-radius: 10px; font-size: 16.5px; line-height: 1.45 }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 12px }
.stats div { background: var(--soft); border-radius: 12px; padding: 12px 16px; display: grid; gap: 2px }
.stats b { font: 900 38px/1.05 'Archivo'; color: var(--red) }
.stats span { font-size: 14px; color: var(--muted) }
.pts { margin: 0; padding-left: 20px; display: grid; gap: 7px }
.pts.sm { font-size: 14.5px; gap: 6px }
.t { border-collapse: collapse; width: 100%; font-size: 16px }
.t th { text-align: left; font-size: 11.5px; text-transform: uppercase; letter-spacing: .07em; color: var(--muted); padding: 6px 10px; border-bottom: 2px solid var(--ink) }
.t td { padding: 7px 10px; border-bottom: 1px solid var(--line); vertical-align: top }
.t td.n { text-align: right; font-family: 'IBM Plex Mono'; font-variant-numeric: tabular-nums; white-space: nowrap }
.t tr.tot td { border-top: 2px solid var(--ink); border-bottom: 0 }
.gaps td { font-size: 16px; padding: 9px 10px } .gaps td:first-child { width: 24% } .gaps td:last-child { width: 30%; color: var(--green) }
.bench { font-size: 13.4px } .bench td { padding: 5.2px 9px; line-height: 1.32 } .bench td:first-child { font-weight: 700; white-space: nowrap } .bench td:last-child { color: var(--red) }
.posmap { display: grid; grid-template-columns: 1.15fr 1fr; gap: 28px }
.map2 { display: grid; gap: 6px } .grid4 { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 10px; height: 390px }
.yl { font-size: 13.5px; color: var(--muted); font-weight: 600 } .xl { display: flex; justify-content: space-between; font-size: 13.5px; color: var(--muted); font-weight: 600 }
.map { position: relative; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 10px; padding: 26px 0 36px 40px; height: 470px }
.ax { position: absolute; font-size: 12.5px; color: var(--muted) }
.ax.y { left: 0; top: 0; width: 34px; writing-mode: vertical-rl; transform: rotate(180deg); height: 100%; text-align: center }
.ax.x { left: 40px; bottom: 0 }
.q { border-radius: 12px; padding: 14px; display: grid; gap: 6px; align-content: start; background: var(--soft) }
.q b { font: 800 20px 'Archivo' } .q span { font-size: 15px; color: var(--muted); line-height: 1.4 }
.q1 { background: var(--red); } .q1 b, .q1 span { color: #fff }
.learn h3 { margin: 0 0 8px; font: 700 15px 'IBM Plex Sans'; text-transform: uppercase; letter-spacing: .08em; color: var(--red) }
.learn ul { margin: 0; padding-left: 20px; display: grid; gap: 12px; font-size: 16.5px }
.arch { display: grid; grid-template-columns: repeat(6, 1fr); gap: 0 }
.st { position: relative; background: var(--soft); border-radius: 10px; padding: 14px 13px; margin-right: 16px; display: flex; flex-direction: column; gap: 8px; min-height: 268px }
.st:not(:last-child)::after { content: "→"; position: absolute; right: -15px; top: 42%; font: 800 18px 'Archivo'; color: var(--red) }
.st b { font: 800 18px 'Archivo' } .st span { font-size: 15px; line-height: 1.38 } .st i { font-size: 13px; color: var(--muted); font-style: normal; border-top: 1px dashed var(--line); padding-top: 6px; margin-top: auto }
.st.m { background: var(--blue-soft) } .st.h { background: var(--green-soft) }
.stack { display: grid; grid-template-columns: 1.3fr 1fr 1fr; gap: 14px; margin-top: 16px }
.stack div { border-left: 4px solid var(--red); padding: 2px 12px; display: grid; gap: 4px }
.stack b { font-size: 13.5px; text-transform: uppercase; letter-spacing: .08em; color: var(--red) } .stack span { font-size: 15px; line-height: 1.42 }
.proof { display: grid; grid-template-columns: 1fr 520px; gap: 22px; align-items: start }
.proof img { width: 520px; border-radius: 10px; border: 1px solid var(--line); box-shadow: 0 2px 10px rgba(13,27,42,.12) }
.pill { display: inline-block; padding: 2px 10px; border-radius: 99px; font-weight: 700; font-size: 13px }
.pill.esc { background: var(--red-soft); color: var(--red) } .pill.rev { background: var(--amber-soft); color: var(--amber) } .pill.clr { background: var(--green-soft); color: var(--green) }
.cost { font-size: 14.5px } .cost td { padding: 6.5px 10px } .cost td:last-child { color: var(--muted); font-size: 12px }
.mkt { display: grid; gap: 12px; margin-top: 6px }
.lvl { border-radius: 12px; padding: 14px 18px; display: grid; gap: 6px }
.lvl b { font: 800 22px 'Archivo' } .lvl span { font-size: 16.5px; line-height: 1.5 }
.t1 { background: var(--soft); width: 100% } .t2 { background: var(--blue-soft); width: 88% } .t3 { background: var(--red); color: #fff; width: 62% }
.tiers { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px }
.tiers div { background: var(--soft); border-radius: 12px; padding: 12px 14px; display: grid; gap: 4px; align-content: start }
.tiers b { font: 800 18px 'Archivo' } .tiers i { font-style: normal; font: 700 16px 'IBM Plex Mono'; color: var(--red) } .tiers span { font-size: 14px; line-height: 1.4; color: var(--muted) }
.pl { font-size: 16px } .pl td.neg { color: var(--red) } .pl td.pos { color: var(--green) }
.road { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px }
.road div { border-top: 4px solid var(--red); background: var(--soft); border-radius: 0 0 10px 10px; padding: 10px 12px; display: grid; gap: 5px; align-content: start }
.road b { font: 800 20px 'Archivo' } .road span { font-size: 15.5px; line-height: 1.4 } .road i { font-style: normal; font: 700 15px 'IBM Plex Mono'; color: var(--red) }
.refs { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0 22px }
.refs ol { margin: 0; padding-left: 24px; display: grid; gap: 6px; align-content: start }
.refs li { font-size: 10px; line-height: 1.3 } .refs li span { color: var(--blue); font-family: 'IBM Plex Mono'; font-size: 9px; word-break: break-all }

.row2 { display: grid; grid-template-columns: 1fr 1.25fr; gap: 16px; margin-top: 18px }
.row2 .lead { margin: 0 }
blockquote { margin: 0; padding: 16px 20px; border-left: 5px solid var(--red); background: var(--soft); border-radius: 0 10px 10px 0; font: 600 18.5px/1.45 'IBM Plex Sans' }
blockquote cite { display: block; margin-top: 8px; font: 400 13px 'IBM Plex Sans'; color: var(--muted); font-style: normal }
.card p { font-size: 18.5px !important; line-height: 1.5 !important }
.ev b { font-size: 20px } .ev span { font-size: 16.5px !important; line-height: 1.42 }
.lead { font-size: 18px !important }
.pts { font-size: 18.5px; gap: 10px } .pts.sm { font-size: 16px }
.stats b { font-size: 44px !important } .stats span { font-size: 15px !important }
"""

CSS += """
/* ---- visual layer: icons, flags and charts. Colour carries one meaning throughout: violet = the AI model, blue = code, green = a person / good outcome, red = risk */
:root { --violet:#6236c9; --violet-soft:#ece6fb; --amber-mid:#d99a2b; --green-mid:#8fc3a5; --slate:#8a97a8 }
.ic { width: 1em; height: 1em; flex: none; display: inline-block; vertical-align: -.14em }
.flag { width: 22px; height: 16.5px; border-radius: 2px; box-shadow: 0 0 0 1px rgba(13,27,42,.14); vertical-align: -3px; margin-right: 8px; flex: none }
.k { display: flex; align-items: center; gap: 8px } .k .ic { width: 18px; height: 18px }
header { gap: 16px; min-height: 26px }

/* cover */
.cover { gap: 16px }
.hero { display: grid; grid-template-columns: 1fr 390px; gap: 40px; align-items: center }
.hero-l { display: grid; gap: 14px }
.cover .giant { font-size: 80px; white-space: nowrap }
.cover .sub { font-size: 22px }
.filing { background: #fff; color: var(--ink); border-radius: 14px; padding: 14px 16px; display: grid; gap: 7px; box-shadow: 0 18px 44px rgba(0,0,0,.38) }
.fh { display: flex; align-items: center; gap: 8px; font: 500 11.5px 'IBM Plex Mono'; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; border-bottom: 1px dashed var(--line); padding-bottom: 7px }
.fh .ic { width: 17px; height: 17px; color: var(--blue) }
.fco { font: 800 19px 'Archivo' }
.fclaim { margin: 0; font-size: 14.5px; line-height: 1.4 } .fclaim em { font-style: normal; font-weight: 700; background: var(--amber-soft); padding: 0 4px; border-radius: 4px }
.fchecks { list-style: none; margin: 0; padding: 0; display: grid; gap: 5px }
.fchecks li { display: grid; grid-template-columns: 19px 1fr auto; gap: 8px; align-items: center; font-size: 13.5px }
.fchecks .ic { width: 18px; height: 18px } .fchecks .no .ic { color: var(--red) } .fchecks .warn .ic { color: var(--amber-mid) }
.fchecks i { font: 600 12.5px 'IBM Plex Mono'; font-style: normal; color: var(--red) }
.fverdict { display: flex; align-items: center; gap: 9px; background: var(--red); color: #fff; border-radius: 10px; padding: 9px 12px; margin-top: 2px }
.fverdict .ic { width: 22px; height: 22px } .fverdict b { font: 800 16px 'Archivo' } .fverdict span { font-size: 12.5px; opacity: .92; margin-left: auto }
.covergrid { margin-top: 4px }
.covergrid div { grid-template-columns: 26px 1fr; gap: 3px 12px; align-content: start; padding: 12px 14px }
.covergrid .ic { width: 26px; height: 26px; color: #ffb4ae; grid-row: span 2 }
.covergrid span { font-size: 14.5px }
.team { margin: 0 }
.brief { margin-top: 2px }

/* executive summary cards */
.card h3 { display: flex; align-items: center; gap: 10px }
.card h3 .ic { width: 32px; height: 32px; padding: 7px; border-radius: 9px; background: var(--red-soft); color: var(--red) }
.card.c-blue h3 { color: var(--blue) } .card.c-blue h3 .ic { background: var(--blue-soft); color: var(--blue) }
.card.c-green h3 { color: var(--green) } .card.c-green h3 .ic { background: var(--green-soft); color: var(--green) }
.card.c-amber h3 { color: var(--amber) } .card.c-amber h3 .ic { background: var(--amber-soft); color: var(--amber) }

/* problem timeline: one node per event on a shared line */
.timeline::before { content: ""; position: absolute; left: 21px; right: 40px; top: 20px; height: 3px; background: var(--line) }
.timeline .ev { border-top: 0; padding-top: 0 }
.node { position: relative; display: flex; align-items: center; gap: 8px; height: 42px }
.node .ic { width: 42px; height: 42px; padding: 9px; border-radius: 50%; background: #fff; border: 3px solid var(--slate); color: var(--slate) }
.node em { font: 600 11.5px 'IBM Plex Mono'; font-style: normal; color: var(--muted); background: #fff; padding: 2px 7px; border-radius: 99px; border: 1px solid var(--line) }
.ev.bad .node .ic { border-color: var(--red); color: var(--red) } .ev.bad .node em { color: var(--red); border-color: var(--red) }
.ev.ours .node .ic { border-color: var(--blue); background: var(--blue); color: #fff } .ev.ours .node em { color: var(--blue); border-color: var(--blue) }
.row2 { margin-top: 10px }
.timeline .ev span { font-size: 15px !important; line-height: 1.38 }
.row2 .lead { font-size: 16px !important; padding: 12px 16px } .row2 blockquote { font-size: 16.5px; padding: 12px 18px }
blockquote { position: relative } .qm { position: absolute; right: 14px; top: 12px; width: 30px; height: 30px; color: var(--red); opacity: .22 }

/* relevance stats and icon bullets */
.stats div { grid-template-columns: 52px 1fr; gap: 2px 14px; align-items: center }
.stats .ic { width: 52px; height: 52px; padding: 12px; border-radius: 50%; background: var(--red-soft); color: var(--red); grid-row: span 2 }
.ipts { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; font-size: 18px; line-height: 1.45 }
.ipts li { display: grid; grid-template-columns: 34px 1fr; gap: 14px; align-items: start }
.ipts .ic { width: 34px; height: 34px; padding: 7px; border-radius: 9px; background: var(--soft); color: var(--red) }
.ipts.sm { font-size: 15.5px; gap: 8px; line-height: 1.42 } .ipts.sm li { grid-template-columns: 28px 1fr; gap: 10px } .ipts.sm .ic { width: 28px; height: 28px; padding: 6px; background: #fff }

/* market gaps */
.lh { display: flex; gap: 10px; align-items: flex-start }
.gaps .lh > .ic { width: 32px; height: 32px; padding: 7px; border-radius: 9px; background: var(--red-soft); color: var(--red) }
.gaps td.fix .lh > .ic { width: 20px; height: 20px; padding: 0; background: none; color: var(--green); margin-top: 2px }

/* benchmarking */
.flags7 { display: flex; gap: 6px } .flags7 .flag { margin: 0; width: 28px; height: 21px }
.bench td:last-child .ic { width: 13px; height: 13px; margin-right: 5px; vertical-align: -2px }
.q .ic { width: 30px; height: 30px; color: var(--red) } .q1 .ic { color: #fff }
.learn ul { list-style: none; padding: 0 }
.learn li { display: grid; grid-template-columns: 52px 1fr; gap: 10px; align-items: start }
.learn .fl { display: flex; gap: 4px; padding-top: 4px } .learn .fl .flag { margin: 0 }

/* architecture: who does each step */
.who { display: flex; gap: 8px }
.who span { display: inline-flex; align-items: center; gap: 6px; font: 600 12.5px 'IBM Plex Sans'; padding: 4px 11px; border-radius: 99px }
.who .ic { width: 15px; height: 15px }
.wm { background: var(--violet-soft); color: var(--violet) } .wc { background: var(--blue-soft); color: var(--blue) } .wp { background: var(--green-soft); color: var(--green) }
.arch { grid-template-columns: 1fr 1fr 1.7fr 1fr 1fr 1fr }
.st { gap: 7px; padding: 13px 12px }
.st .big { width: 44px; height: 44px; padding: 10px; border-radius: 12px; background: #fff; color: var(--ink) }
.st.c { background: var(--blue-soft) } .st.c .big, .st.c i { color: var(--blue) }
.st.m { background: var(--violet-soft) } .st.m .big, .st.m i { color: var(--violet) }
.st.h { background: var(--green-soft) } .st.h .big, .st.h i { color: var(--green) }
.st i { display: flex; gap: 6px; align-items: flex-start; line-height: 1.3 } .st i .ic { width: 14px; height: 14px; margin-top: 1px }
.checks { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; font-size: 13.5px; line-height: 1.28 }
.checks li { display: grid; grid-template-columns: 16px 22px 1fr; gap: 5px; align-items: start }
.checks .ic { width: 16px; height: 16px; color: var(--blue); margin-top: 1px }
.checks em { font: 600 11.5px 'IBM Plex Mono'; font-style: normal; color: var(--muted); margin-top: 1px }
.checks li.ai .ic, .checks li.ai em { color: var(--violet) }
.stack { margin-top: 14px }
.stack b { display: flex; align-items: center; gap: 6px } .stack b .ic { width: 16px; height: 16px }

/* validation: the backtest as a chart and as companies */
.proof { grid-template-columns: 1fr 440px; gap: 26px }
.proof img { width: 440px; margin-top: 4px }
.pv { display: grid; gap: 12px }
.cap { display: flex; align-items: center; gap: 7px; font: 600 12px 'IBM Plex Sans'; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); margin-bottom: 4px }
.cap .ic { width: 15px; height: 15px; color: var(--red) } .cap .capx { width: 13px; height: 13px; padding: 2px; border-radius: 50%; background: var(--red); color: #fff; stroke-width: 3.5 }
.rank { width: 100%; height: auto; display: block; overflow: visible }
.rank rect.esc { fill: var(--red) } .rank rect.rev { fill: var(--amber-mid) } .rank rect.clr { fill: var(--green-mid) }
.rank .axis { stroke: var(--ink); stroke-width: 1.2 } .rank .thr { stroke: var(--muted); stroke-dasharray: 4 4; stroke-width: 1 }
.rank text { font: 600 11px 'IBM Plex Sans'; fill: var(--muted) } .rank text.hl { fill: var(--red); font-weight: 700; font-size: 12.5px }
.rank .xm { fill: var(--red) } .rank .xx { stroke: #fff; stroke-width: 1.8; fill: none; stroke-linecap: round }
.trow { display: grid; grid-template-columns: 108px 1fr 128px; gap: 10px; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--line) }
.trow .pill { display: inline-flex; align-items: center; gap: 5px; justify-self: start } .trow .pill .ic { width: 14px; height: 14px }
.dots { display: flex; flex-wrap: wrap; gap: 4px }
.dot { width: 17px; height: 17px; border-radius: 50%; display: grid; place-items: center; box-sizing: border-box }
.dot.esc { background: var(--red-soft); border: 2px solid var(--red) } .dot.rev { background: var(--amber-soft); border: 2px solid var(--amber-mid) } .dot.clr { background: var(--green-soft); border: 2px solid var(--green-mid) }
.dot.x { background: var(--red) } .dot .ic { width: 11px; height: 11px; color: #fff; stroke-width: 3.5 }
.tout { font-size: 14px; color: var(--muted) } .tout b { color: var(--ink) }

/* tech-stack expense */
.costbar { display: grid; gap: 7px }
.segs { display: flex; height: 20px; border-radius: 6px; overflow: hidden; gap: 2px }
.seg.data, .lg.data i { background: var(--red) } .seg.host, .lg.host i { background: var(--blue) } .seg.ops, .lg.ops i { background: var(--slate) } .seg.model, .lg.model i { background: var(--violet) }
.legs { display: flex; flex-wrap: wrap; gap: 4px 22px; font-size: 13.5px; color: var(--muted) }
.lg { display: inline-flex; align-items: center; gap: 6px } .lg i { display: inline-block; width: 10px; height: 10px; border-radius: 3px } .lg b { color: var(--ink); font: 600 13px 'IBM Plex Mono' }
.lg .ic { width: 15px; height: 15px }
.cost td { padding: 4.4px 10px }
.ri { display: inline-flex; align-items: center; gap: 8px } .ri .ic { width: 17px; height: 17px; color: var(--muted) }
.cost tr.model td { background: var(--violet-soft) } .cost tr.model .ri .ic { color: var(--violet) }
.cost tr.data .ri .ic { color: var(--red) }

/* R&D lines with bars to scale */
.rl { display: grid; grid-template-columns: 26px 1fr; gap: 10px; align-items: start }
.rl > .ic { width: 26px; height: 26px; padding: 5px; border-radius: 7px; background: var(--red-soft); color: var(--red) }
.hb { height: 7px; background: var(--soft); border-radius: 4px; margin-top: 6px; overflow: hidden } .hb i { display: block; height: 100%; background: var(--red); border-radius: 4px }

/* market size */
.mk2 { display: grid; grid-template-columns: 360px 1fr; gap: 44px; align-items: center; margin-top: 4px }
.tam { position: relative; width: 360px; height: 360px }
.tam > div { position: absolute; border-radius: 50%; display: flex; flex-direction: column; align-items: center; text-align: center; padding-top: 20px; gap: 1px; box-sizing: border-box }
.c1 { inset: 0; background: var(--soft); border: 2px solid var(--line) }
.c2 { width: 236px; height: 236px; left: 62px; top: 124px; background: var(--blue-soft); border: 2px solid #b9c8f5 }
.c3 { width: 124px; height: 124px; left: 118px; top: 236px; background: var(--red); color: #fff; padding-top: 28px !important }
.tam b { font: 800 15px 'Archivo'; letter-spacing: .1em } .tam span { font-size: 12.5px; color: var(--muted) } .tam em { font: 800 17px/1.25 'Archivo'; font-style: normal; max-width: 250px } .tam small { font-size: 11.5px; color: var(--muted) }
.c3 span { color: #ffe1de }
.ns { position: absolute; left: 0; bottom: -24px; margin: 0; font-size: 11.5px; color: var(--muted) }
.samb h3 { margin: 0 0 4px; font: 700 15px 'IBM Plex Sans'; text-transform: uppercase; letter-spacing: .08em; color: var(--blue) }
.sr { display: grid; grid-template-columns: 34px 1fr 108px; gap: 12px; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--line) }
.sr > .ic { width: 34px; height: 34px; padding: 7px; border-radius: 9px; background: var(--blue-soft); color: var(--blue) }
.sr b { font-size: 16px } .sr span { display: block; font-size: 13.5px; color: var(--muted) } .sr em { font: 700 16px 'IBM Plex Mono'; font-style: normal; text-align: right; white-space: nowrap }
.sr .hb i { background: var(--blue) }
.som { display: grid; grid-template-columns: 30px 1fr; gap: 12px; margin-top: 14px; background: var(--red); color: #fff; border-radius: 12px; padding: 12px 16px; align-items: center }
.som .ic { width: 30px; height: 30px } .som b { font: 800 18px 'Archivo'; display: block } .som span { font-size: 14px; color: #ffe1de }

/* revenue model */
.tiers .ic { width: 30px; height: 30px; padding: 6px; border-radius: 8px; background: #fff; color: var(--red) }
.plrow { display: grid; grid-template-columns: 1fr 320px; gap: 26px; align-items: end }
.plc { display: grid; gap: 8px }
.plleg { display: flex; gap: 14px; font-size: 12.5px; color: var(--muted); align-items: center }
.plleg i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; vertical-align: -1px }
.plleg i.rv, .b.rv { background: var(--green) } .plleg i.cs, .b.cs { background: #e3a6a1 }
.plbars { padding-top: 16px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; align-items: end }
.yr { display: grid; gap: 3px; justify-items: center }
.bars { height: 150px; width: 100%; display: flex; align-items: flex-end; justify-content: center; gap: 6px; border-bottom: 1.5px solid var(--ink) }
.b { width: 34px; border-radius: 5px 5px 0 0; position: relative }
.b em { position: absolute; top: -17px; left: 50%; transform: translateX(-50%); font: 600 11px 'IBM Plex Mono'; font-style: normal; color: var(--muted); white-space: nowrap }
.yr b { font-size: 13px } .yr span { font: 700 13px 'IBM Plex Mono' } .yr .neg { color: var(--red) } .yr .pos { color: var(--green) }

/* marketing */
.road div { grid-template-columns: auto 1fr; align-items: center; column-gap: 8px }
.road .ic { width: 26px; height: 26px; color: var(--red) } .road span, .road i { grid-column: 1 / -1 }
.pbc { white-space: nowrap } .pb { display: inline-block; width: 92px; height: 8px; background: var(--soft); border-radius: 4px; overflow: hidden; vertical-align: middle; margin-right: 9px }
.pb i { display: block; height: 100%; background: var(--green) } .pbc b { font: 600 15px 'IBM Plex Mono' }
.cac .ri .ic { color: var(--red) }

/* references by kind */
.rkinds { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 12.5px; color: var(--muted); margin-bottom: 8px }
.rkinds span { display: inline-flex; align-items: center; gap: 5px } .rkinds .ic { width: 15px; height: 15px } .rkinds b { color: var(--ink) }
.refs li::marker { font-weight: 700 }
.rkinds .k-r .ic, .refs li.k-r::marker { color: var(--blue) } .rkinds .k-p .ic, .refs li.k-p::marker { color: var(--amber) }
.rkinds .k-c .ic, .refs li.k-c::marker { color: var(--green) } .rkinds .k-m .ic, .refs li.k-m::marker { color: var(--violet) }
.rkinds .k-v .ic, .refs li.k-v::marker { color: var(--slate) } .rkinds .k-o .ic, .refs li.k-o::marker { color: var(--red) }
"""

CSS += """
/* ---- short-copy layout: fewer words, larger type */
.cover { gap: 34px }
.hero-l .team { margin-top: 6px }
.cover .sub { font-size: 25px; max-width: 640px }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 18px }
.kpi { background: var(--soft); border-radius: 14px; padding: 20px 18px; display: grid; gap: 8px; align-content: start; border-top: 5px solid var(--red) }
.kpi > .ic { width: 44px; height: 44px; padding: 10px; border-radius: 12px; background: var(--red-soft); color: var(--red) }
.kpi h3 { margin: 4px 0 0; font: 700 14px 'IBM Plex Sans'; text-transform: uppercase; letter-spacing: .08em; color: var(--red) }
.kpi b { font: 900 44px/1.05 'Archivo'; color: var(--ink) }
.kpi p { margin: 0; font-size: 17px; line-height: 1.45; color: var(--muted) }
.kpi.c-blue { border-color: var(--blue) } .kpi.c-blue > .ic { background: var(--blue-soft); color: var(--blue) } .kpi.c-blue h3 { color: var(--blue) }
.kpi.c-green { border-color: var(--green) } .kpi.c-green > .ic { background: var(--green-soft); color: var(--green) } .kpi.c-green h3 { color: var(--green) }
.kpi.c-amber { border-color: var(--amber-mid) } .kpi.c-amber > .ic { background: var(--amber-soft); color: var(--amber) } .kpi.c-amber h3 { color: var(--amber) }
.timeline { margin-top: 18px }
.timeline .ev span { font-size: 17px !important; line-height: 1.42 }
.pstate { display: grid; grid-template-columns: 40px 1fr; gap: 16px; align-items: center; margin-top: 30px; background: var(--red-soft); border-radius: 14px; padding: 20px 24px }
.pstate .ic { width: 40px; height: 40px; color: var(--red) } .pstate p { margin: 0; font-size: 20px; line-height: 1.45 }
.stats { margin: 6px 0 22px }
.ipts { gap: 18px; font-size: 19px }
.gaps td { font-size: 18px; padding: 12px 10px }
.bench { font-size: 15.5px } .bench td { padding: 7px 10px }
.q span { font-size: 16px } .learn ul { gap: 16px; font-size: 17.5px }
.st span { font-size: 16px } .checks { font-size: 14.5px }
.stack span { font-size: 15.5px }
.cost { font-size: 15px } .cost td { padding: 4.5px 10px } .cost tr.est td:nth-child(2) { color: var(--muted); font-style: italic }
.costbar { margin-bottom: 6px } .legs { font-size: 14.5px }
.ipts.sm { font-size: 17px; gap: 14px }
.tiers span { font-size: 15px } .road span { font-size: 17px } .cac { font-size: 17px }
"""

CSS += """
/* ---- layout fixes (alignment, orphans, overlap-prone spots) */
body { text-wrap: pretty }
h1 { max-width: 1140px }
.fclaim em { box-decoration-break: clone; -webkit-box-decoration-break: clone }
/* numeric column headers sit over their right-aligned figures */
.cost th:last-child, .pl th:not(:first-child), .cac th:nth-child(2), .cac th:nth-child(3), .grid2.r .t th:last-child { text-align: right }
/* 2 executive summary */
.kpis { height: 100%; max-height: 400px; margin-top: 14px }
.kpi { padding: 26px 22px }
.kpi p { font-size: 18px }
/* 3 problem timeline */
.timeline { margin-top: 30px; gap: 10px 24px } .pstate { margin-top: 56px }
.timeline .ev b { font-size: 22px } .timeline .ev span { font-size: 18px !important }
.pstate p { font-size: 22px }
/* 4 relevance */
.stats { margin: 6px 0 30px }
.stats div { grid-template-columns: 46px 1fr; gap: 2px 12px; padding: 14px 14px }
.stats .ic { width: 46px; height: 46px; padding: 11px }
.stats div span { font-size: 14px !important }
.ipts { gap: 32px; font-size: 19px }
.ipts.sm { gap: 14px; font-size: 17px }
/* 5 market gaps */
.gaps td { vertical-align: middle; padding: 17px 10px }
.gaps td:first-child { width: 29% } .gaps td:last-child { width: 28% }
.gaps .lh, .gaps td.fix .lh { align-items: center } .gaps td.fix .lh > .ic { margin-top: 0 }
/* 7 positioning */
.learn ul { gap: 24px }
/* 8 architecture: last stage flush with the right margin, arrows centred in the gaps */
.arch { gap: 0 16px }
.st { margin-right: 0 }
.st > span, .q span, .brief span { text-wrap: balance }
.st:not(:last-child)::after { right: -15.5px }
/* 9 validation */
.proof { grid-template-columns: 1fr 480px } .proof img { width: 480px }
/* 10 tech-stack expense */
.cost td { padding: 3.6px 10px }
.cost td.n { font-size: 14px; color: var(--ink) }
.cost th:nth-child(1) { width: 40% } .cost th:nth-child(3) { width: 16% }
/* 11 R&D */
.grid2.r { align-items: stretch }
.grid2.r .card { display: flex; flex-direction: column; justify-content: center }
.grid2.r .card .ipts { align-content: space-evenly }
/* 12 market size: single-line TAM range, kept inside its circle */
.tam em { font-size: 15px; max-width: none; white-space: nowrap }
/* 13 revenue */
.plrow { align-items: center }
/* 14 marketing */
.road div { grid-template-rows: auto 1fr auto }
.road i { align-self: end }
.cac td { padding: 13px 10px }
/* 15 references */
.refs li { font-size: 10.2px } .refs li span { font-size: 9.2px }
"""

