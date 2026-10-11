import { motion, useReducedMotion } from 'framer-motion'
import { CountUp } from './CountUp'
import { HeroBackdrop } from './HeroBackdrop'
import { AgentPipeline } from './AgentPipeline'
import { ArrowDown } from '../Icons'
import { groupIN } from '../../lib/format'
import '../../styles/hero.css'

const rise = (i: number, reduce: boolean | null) =>
  reduce
    ? {}
    : {
        initial: { opacity: 0, y: 18 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.7, delay: 0.1 + i * 0.09, ease: [0.2, 0.7, 0.1, 1] as const },
      }

export function Hero() {
  const reduce = useReducedMotion()
  return (
    <section className="hero" aria-labelledby="hero-title">
      <HeroBackdrop />
      <div className="hero-inner">
        <motion.p className="hero-kicker" {...rise(0, reduce)}>
          <span className="pulse-dot" /> Cyber-fraud holds in Indian banks · 2026
        </motion.p>
        <motion.h1 id="hero-title" className="hero-title" {...rise(1, reduce)}>
          A <span className="t-red">₹980</span> complaint froze <span className="t-strike">₹2.51 crore</span>.
          <span className="hero-title-2">The courts said: hold the ₹980.</span>
        </motion.h1>
        <motion.p className="hero-lede" {...rise(2, reduce)}>
          Banks freeze whole accounts on a police notice, even when the traceable money is tiny. LienLine is a team of agents that
          follows the money hop by hop across banks, computes the identifiable disputed amount for each account, and drafts the lien,
          release and grievance letters. Code checks every number. A bank nodal officer approves.
        </motion.p>
        <motion.div className="hero-cta" {...rise(3, reduce)}>
          <a className="btn hero-primary" href="#desk">
            Open the case desk <ArrowDown width={16} height={16} />
          </a>
          <a className="btn hero-ghost" href="#how">
            How the agents work
          </a>
        </motion.div>

        <div className="hero-stats">
          <motion.article className="stat" {...rise(4, reduce)}>
            <p className="stat-num serif">
              <CountUp to={25100000} format={(n) => '₹' + groupIN(n)} />
            </p>
            <p className="stat-label">
              frozen over a disputed <b className="t-red">₹980</b>
            </p>
            <div className="ratio-bar" aria-hidden="true">
              <motion.span
                className="ratio-fill"
                initial={reduce ? false : { scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1.6, ease: [0.2, 0.7, 0.1, 1] }}
              />
              <span className="ratio-taint" />
            </div>
            <p className="stat-foot">
              The red sliver is drawn 2 px wide; at true scale ₹980 is 0.0039% of the balance. <cite>Archana v State of MP, MP High Court, 27 Jul 2026</cite>
            </p>
          </motion.article>

          <motion.article className="stat" {...rise(5, reduce)}>
            <p className="stat-num serif">
              <CountUp to={105} format={(n) => String(Math.round(n))} ms={1400} />
              <span className="stat-unit"> petitions</span>
            </p>
            <p className="stat-label">in one High Court, from account holders frozen in full</p>
            <PetitionGrid />
            <p className="stat-foot">
              14 guidelines issued: lien only the identifiable amount. <cite>Shree Balaji Enterprises v RBI, Rajasthan High Court, 20 Aug 2026</cite>
            </p>
          </motion.article>

          <motion.article className="stat" {...rise(6, reduce)}>
            <p className="stat-num serif">
              <CountUp to={18.05} format={(n) => '₹' + n.toFixed(2) + ' cr'} />
              <span className="stat-unit"> restored</span>
            </p>
            <p className="stat-label">
              vs <b>₹11,158 crore</b> “saved” by holds since 2021
            </p>
            <div className="vs-bars" aria-hidden="true">
              <div className="vs-row">
                <motion.span
                  className="vs-bar saved"
                  initial={reduce ? false : { scaleX: 0 }}
                  whileInView={{ scaleX: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 1.4, delay: 0.2, ease: [0.2, 0.7, 0.1, 1] }}
                />
                <span className="vs-tag">held</span>
              </div>
              <div className="vs-row">
                <span className="vs-bar restored" />
                <span className="vs-tag">returned · 0.16%</span>
              </div>
            </div>
            <p className="stat-foot">
              Across 36,290 restored cases. <cite>MHA / I4C figures</cite>
            </p>
          </motion.article>
        </div>

        <AgentPipeline />
      </div>
    </section>
  )
}

function PetitionGrid() {
  const reduce = useReducedMotion()
  return (
    <div className="petitions" aria-hidden="true">
      {Array.from({ length: 105 }, (_, i) => (
        <motion.span
          key={i}
          initial={reduce ? false : { opacity: 0, scale: 0.3 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.25, delay: 0.3 + i * 0.012 }}
        />
      ))}
    </div>
  )
}
