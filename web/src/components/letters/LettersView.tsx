import { useMemo, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { useWorkspace } from '../../state/workspace'
import { knownValues, markText } from '../../lib/verifyText'
import { dateLong, rupeeText } from '../../lib/format'
import { Check, Pencil, Shield } from '../Icons'
import '../../styles/letters.css'

const KIND_LABEL: Record<string, string> = {
  lien_instruction: 'Lien instruction',
  release_notice: 'Release notice',
  grievance_reply: 'Grievance reply',
  full_freeze_justification: 'Full-freeze justification',
}

export function LettersView() {
  const ws = useWorkspace()
  const { model, approvals, setApproval } = ws
  const letters = model.run.letters
  const [current, setCurrent] = useState(letters[0]?.id)
  const [edits, setEdits] = useState<Record<string, string>>({})
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const known = useMemo(() => knownValues(model), [model])
  const reduce = useReducedMotion()

  if (!letters.length) return <p className="side-empty">No letters were drafted for this case.</p>
  const L = letters.find((l) => l.id === current) ?? letters[0]
  const body = edits[L.id] ?? L.body
  const marks = markText(rupeeText(editing === L.id ? draft : body), known)
  const nums = marks.filter((m) => m.kind !== 'plain')
  const bad = nums.filter((m) => !m.ok)
  const status = approvals['L:' + L.id]
  const acct = model.accounts[L.account_id]
  const bank = acct ? model.banks[acct.bank] : undefined

  return (
    <div className="letters">
      <nav className="letter-list" aria-label="Letters">
        {letters.map((l) => {
          const st = approvals['L:' + l.id]
          const a = model.accounts[l.account_id]
          return (
            <button key={l.id} className={'letter-item' + (l.id === L.id ? ' on' : '')} onClick={() => { setCurrent(l.id); setEditing(null) }} aria-current={l.id === L.id}>
              <span className="li-kind">{KIND_LABEL[l.kind] ?? l.kind}</span>
              <b>{l.to}</b>
              <span className="li-meta">
                <span className="mono">{l.id}</span> · {a?.holder}
              </span>
              <span className={'li-status ' + (st === 'approved' ? 'ok' : st === 'edited' ? 'edit' : '')}>
                {st === 'approved' ? 'Approved' : st === 'edited' ? 'Edited · needs approval' : l.verified ? `Verified · ${l.numbers_checked ?? 0} numbers` : 'Draft'}
              </span>
            </button>
          )
        })}
      </nav>

      <div className="letter-stage">
        <div className="officer-bar" role="toolbar" aria-label="Nodal officer actions">
          <span className="officer-who">
            <span className="officer-av">NO</span>
            <span>
              <b>Nodal officer</b>
              <span>human approval required</span>
            </span>
          </span>
          <span className="officer-actions">
            {editing === L.id ? (
              <>
                <button className="btn sm ghost" onClick={() => setEditing(null)}>
                  Cancel
                </button>
                <button
                  className="btn sm primary"
                  onClick={() => {
                    setEdits((e) => ({ ...e, [L.id]: draft }))
                    setApproval('L:' + L.id, 'edited')
                    setEditing(null)
                  }}
                >
                  Save edit
                </button>
              </>
            ) : (
              <>
                <button
                  className="btn sm"
                  onClick={() => {
                    setDraft(rupeeText(body))
                    setEditing(L.id)
                    if (status === 'approved') setApproval('L:' + L.id, 'edited')
                  }}
                >
                  <Pencil width={14} height={14} /> Edit
                </button>
                {status === 'approved' ? (
                  <button className="btn sm" onClick={() => setApproval('L:' + L.id, null)}>
                    Undo approval
                  </button>
                ) : (
                  <button className="btn sm approve" disabled={bad.length > 0} onClick={() => setApproval('L:' + L.id, 'approved')}>
                    <Check width={14} height={14} /> Approve &amp; sign
                  </button>
                )}
              </>
            )}
          </span>
        </div>
        {bad.length > 0 && (
          <p className="verify-warn" role="status">
            Verifier: {bad.length} number{bad.length > 1 ? 's' : ''} in this letter {bad.length > 1 ? 'do' : 'does'} not match the case ({bad.map((b) => b.text).join(', ')}). Approval is blocked until fixed.
          </p>
        )}

        <AnimatePresence mode="wait">
          <motion.article
            key={L.id}
            className="paper"
            style={{ ['--bank' as string]: `var(--bank-${model.bankColor[acct?.bank ?? '?'] ?? 0})` }}
            initial={reduce ? false : { opacity: 0, y: 14, rotate: -0.4 }}
            animate={{ opacity: 1, y: 0, rotate: 0 }}
            exit={reduce ? undefined : { opacity: 0, y: -8 }}
            transition={{ duration: 0.35, ease: [0.2, 0.7, 0.1, 1] }}
            aria-label={`${KIND_LABEL[L.kind] ?? L.kind} to ${L.to}`}
          >
            <header className="paper-head">
              <div>
                <p className="paper-org">{bank?.name ?? 'Bank'}</p>
                <p className="paper-dept">Office of the Nodal Officer · Cyber Fraud Cell</p>
              </div>
              <div className="paper-ref mono">
                <span>Ref: LL/{model.run.case_id}/{L.id}</span>
                <span>Date: {dateLong(model.run.generated_at)}</span>
              </div>
            </header>
            <div className="paper-body serif">
              <p className="paper-to">
                To,
                <br />
                {L.to}
              </p>
              <p className="paper-subject">
                <b>Subject:</b> {rupeeText(L.subject)}
              </p>
              {editing === L.id ? (
                <textarea className="paper-edit" value={draft} onChange={(e) => setDraft(e.target.value)} aria-label="Letter body" rows={14} />
              ) : (
                rupeeText(body)
                  .split(/\n{2,}/)
                  .map((para, i) => (
                    <p key={i}>
                      {markText(para, known).map((m, j) =>
                        m.kind === 'plain' ? (
                          <span key={j}>{m.text}</span>
                        ) : (
                          <mark key={j} className={m.ok ? 'vnum ok' : 'vnum bad'} title={m.ok ? `Checked: ${m.why}` : `Not verified: ${m.why}`}>
                            {m.text}
                          </mark>
                        ),
                      )}
                    </p>
                  ))
              )}
              {!/nodal officer[^\n]*$/i.test(body.trim().split('\n').slice(-2).join(' ')) && <div className="paper-sign">
                <p>Yours faithfully,</p>
                <p className="sig-line">Nodal Officer (Cyber Fraud)</p>
                <p className="sig-org">{bank?.name}</p>
              </div>}
            </div>
            <AnimatePresence>
              {status === 'approved' && (
                <motion.div
                  className="stamp"
                  initial={reduce ? false : { scale: 1.8, opacity: 0, rotate: -18 }}
                  animate={{ scale: 1, opacity: 1, rotate: -9 }}
                  exit={{ opacity: 0 }}
                  transition={{ type: 'spring', stiffness: 420, damping: 22 }}
                >
                  <span>APPROVED</span>
                  <small>Nodal officer · {dateLong(model.run.generated_at)}</small>
                </motion.div>
              )}
            </AnimatePresence>
            <footer className="paper-foot">
              <Shield width={15} height={15} />
              {bad.length === 0 ? (
                <span>
                  Verifier: <b>{nums.length}</b> figures in this letter match the decision, ledger and trace.
                </span>
              ) : (
                <span className="bad">Verifier: {bad.length} of {nums.length} figures do not match.</span>
              )}
            </footer>
          </motion.article>
        </AnimatePresence>
      </div>
    </div>
  )
}
