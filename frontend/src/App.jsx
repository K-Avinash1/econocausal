import { useState } from 'react'
import './App.css'
import UploadPanel from './components/UploadPanel'

const SECTIONS = [
  { id: 'upload', label: '1. Upload data' },
  { id: 'summary', label: '2. Data summary' },
  { id: 'effects', label: '3. Discount effects' },
  { id: 'budget', label: '4. Budget plan' },
  { id: 'validation', label: '5. Validation' },
]

export default function App() {
  const [active, setActive] = useState('upload')
  const current = SECTIONS.find((section) => section.id === active)

  return (
    <div className="app">
      <header className="app-header">
        <h1>EconoCausal</h1>
        <p>Find out which customers a discount really helps.</p>
      </header>
      <div className="app-body">
        <nav className="app-nav" aria-label="Dashboard sections">
          {SECTIONS.map((section) => (
            <button
              key={section.id}
              type="button"
              className={section.id === active ? 'nav-item active' : 'nav-item'}
              aria-current={section.id === active ? 'page' : undefined}
              onClick={() => setActive(section.id)}
            >
              {section.label}
            </button>
          ))}
        </nav>
        <main className="app-main">
          <h2>{current.label}</h2>
          {current.id === 'upload' ? (
            <UploadPanel />
          ) : (
            <p className="coming-later">This section is built later in the project.</p>
          )}
        </main>
      </div>
    </div>
  )
}