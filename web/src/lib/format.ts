// Money arrives as integer paise; display uses Indian digit grouping (12,34,567.89).

const grouped = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })

/** "2,51,00,000" style grouping for a whole number of rupees. */
export function groupIN(n: number): string {
  return grouped.format(Math.trunc(n))
}

/** ₹ amount from paise; shows paise only when non-zero (or when `paise` is forced). */
export function inr(paise: number, opts: { paise?: boolean; sign?: boolean } = {}): string {
  const neg = paise < 0
  const abs = Math.abs(Math.round(paise))
  const rupees = Math.floor(abs / 100)
  const p = abs % 100
  const showPaise = opts.paise ?? p !== 0
  const body = groupIN(rupees) + (showPaise ? '.' + String(p).padStart(2, '0') : '')
  return (neg ? '−' : opts.sign ? '+' : '') + '₹' + body
}

/** Compact Indian units: ₹980, ₹18.4 L, ₹2.51 cr. */
export function inrShort(paise: number): string {
  const r = paise / 100
  const a = Math.abs(r)
  if (a >= 1e7) return '₹' + trim(r / 1e7, a >= 1e9 ? 0 : 2) + ' cr'
  if (a >= 1e5) return '₹' + trim(r / 1e5, 1) + ' L'
  return inr(paise)
}

function trim(n: number, digits: number): string {
  return n.toFixed(digits).replace(/\.0+$/, '').replace(/(\.\d*?)0+$/, '$1')
}

export function pct(part: number, whole: number, digits = 1): string {
  if (!whole) return '0%'
  const v = (part / whole) * 100
  if (v > 0 && v < 0.01) return '<0.01%'
  return v.toFixed(v < 1 ? Math.max(digits, 2) : digits) + '%'
}

const IST = 'Asia/Kolkata'
const tFmt = new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: IST })
const tsFmt = new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZone: IST })
const dFmt = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', timeZone: IST })
const dLong = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'long', year: 'numeric', timeZone: IST })

export const time = (iso: string | number) => tFmt.format(new Date(iso))
export const timeSec = (iso: string | number) => tsFmt.format(new Date(iso))
export const day = (iso: string | number) => dFmt.format(new Date(iso))
export const dateLong = (iso: string | number) => dLong.format(new Date(iso))
export const dayTime = (iso: string | number) => `${day(iso)}, ${time(iso)}`

/** Countdown text for a duration in ms: "2d 04:12:09" / "04:12:09". */
export function countdown(ms: number): string {
  const s = Math.max(0, Math.floor(Math.abs(ms) / 1000))
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const hms = [h, m, sec].map((v) => String(v).padStart(2, '0')).join(':')
  return d ? `${d}d ${hms}` : hms
}

/** Normalise "Rs 2,51,00,000" / "Rs. 980" in model text to "₹…". */
export function rupeeText(s: string): string {
  return s.replace(/\bRs\.?\s?(?=\d)/g, '₹')
}

export const RULE_LABEL: Record<string, string> = {
  FIFO: 'FIFO',
  LIFO: 'LIFO',
  PRO_RATA: 'Pro-rata',
  LIBR: 'LIBR',
}

export const RULE_HELP: Record<string, string> = {
  FIFO: 'First in, first out: the oldest money in the account leaves first.',
  LIFO: 'Last in, first out: the newest money leaves first.',
  PRO_RATA: 'Every outflow carries victim money in proportion to the balance.',
  LIBR: 'Lowest intermediate balance: the account spends its own money first; victim money is lost only when the balance dips below it. The legal tracing standard.',
}

export const ROLE_LABEL: Record<string, string> = {
  victim: 'Victim',
  mule_l1: 'Mule · layer 1',
  mule_l2: 'Mule · layer 2',
  cashout: 'Cash-out',
  merchant: 'Merchant',
  innocent: 'Bystander',
}

export const ACTION_LABEL: Record<string, string> = {
  lien: 'Lien',
  full_freeze: 'Full freeze',
  release: 'Release',
}
