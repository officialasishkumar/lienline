import { Moon, Sun } from './Icons'
import type { Theme } from '../hooks/useTheme'

export function Logo() {
  return (
    <svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true" className="logo">
      <rect width="32" height="32" rx="8" className="logo-bg" />
      <path d="M6 21h20" className="logo-line" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M6 21c4-9 7-11 10-11s6 2 10 11" fill="none" className="logo-arc" strokeWidth="2.4" strokeLinecap="round" />
      <circle cx="16" cy="10" r="2.6" className="logo-dot" />
    </svg>
  )
}

export function TopBar({ theme, onTheme, source }: { theme: Theme; onTheme: () => void; source: 'sample' | 'recorded' | 'loading' }) {
  return (
    <header className="topbar">
      <a className="brand" href="#top" aria-label="LienLine, back to top">
        <Logo />
        <span className="serif">LienLine</span>
      </a>
      <nav className="topnav" aria-label="Sections">
        <a href="#top">Problem</a>
        <a href="#how">Agents</a>
        <a href="#desk">Case desk</a>
      </nav>
      <div className="topbar-right">
        <span className={'source-pill ' + source} title={source === 'sample' ? 'No recorded runs found in runs/; showing the bundled sample case' : 'Recorded agent runs'}>
          <span className="dot" />
          {source === 'sample' ? 'Sample case' : source === 'recorded' ? 'Recorded runs' : 'Loading'}
        </span>
        <button className="icon-btn" onClick={onTheme} aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}>
          {theme === 'dark' ? <Sun /> : <Moon />}
        </button>
      </div>
    </header>
  )
}
