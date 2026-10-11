import { Logo } from './TopBar'

export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <span className="brand">
          <Logo />
          <span className="serif">LienLine</span>
        </span>
        <p>
          Scenarios are synthetic and seeded; real complaint data is not public. Every figure shown is computed by the tracer and re-checked by an
          independent verifier. Decisions are drafts until a bank nodal officer approves them.
        </p>
        <p className="mono footer-src">
          Archana v State of MP (MP HC, 27 Jul 2026) · Shree Balaji Enterprises v RBI (Raj HC, 20 Aug 2026) · Supreme Court order on an RBI debit-hold SOP
          (4 Aug 2026) · MHA/I4C SOP (2 Jan 2026)
        </p>
      </div>
    </footer>
  )
}
