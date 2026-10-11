import { useWorkspace } from '../state/workspace'
import { inrShort } from '../lib/format'

function short(s: string, n = 16) {
  return s.length > n ? s.slice(0, n - 1) + '…' : s
}

/** Evidence chip for an account or transaction id; hovering lights it up in the graph, clicking focuses it. */
export function RefChip({ id }: { id: string }) {
  const { model, setHighlight, focusRef, highlight } = useWorkspace()
  const acct = model.accounts[id]
  const txn = model.txnById[id]
  if (!acct && !txn) {
    return (
      <span className="chip ref missing" title="Not found in any ledger">
        <span className="mono">{id}</span> not in ledgers
      </span>
    )
  }
  const label = acct ? short(acct.holder) : `${inrShort(txn!.amount)} ${txn!.channel ?? ''}`.trim()
  const ids = acct ? [id] : [id, txn!.from, txn!.to]
  return (
    <button
      type="button"
      className={'chip ref' + (highlight.has(id) ? ' on' : '') + (txn?.tainted_origin ? ' origin' : '')}
      onMouseEnter={() => setHighlight(ids)}
      onMouseLeave={() => setHighlight(null)}
      onFocus={() => setHighlight(ids)}
      onBlur={() => setHighlight(null)}
      onClick={() => focusRef(id)}
      aria-label={acct ? `Show account ${acct.holder} in the graph` : `Show transaction ${id} in the graph`}
    >
      <span className="mono">{id}</span>
      <span>{label}</span>
    </button>
  )
}
