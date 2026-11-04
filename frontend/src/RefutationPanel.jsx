import { useEffect, useState } from 'react'
import './ResultsPanel.css'

const API_BASE = 'http://127.0.0.1:8000'

const pp2 = (x) => (x === null || x === undefined ? 'n/a' : `${(x * 100).toFixed(2)} pp`)
const VERDICT = {
  true: { text: 'Passed', css: 'res-badge res-ok' },
  false: { text: 'Failed', css: 'res-badge res-bad' },
  null: { text: 'Inconclusive', css: 'res-badge res-warn' },
}

export default function RefutationPanel({ runId }) {
  const [report, setReport] = useState(null)
  const [source, setSource] = useState('saved')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/refutation_demo.json')
      .then((r) => {
        if (!r.ok) throw new Error(`Could not load the saved example (status ${r.status})`)
        return r.json()
      })
      .then(setReport)
      .catch((e) => setError(e.message))
  }, [])

  async function runLive() {
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`${API_BASE}/refute/${runId}?n_sims=3`, { method: 'POST' })
      const data = await response.json()
      if (!data.ok) throw new Error(data.errors?.[0]?.message || 'The checks failed.')
      setReport(data.refutation)
      setSource('live')
    } catch (e) {
      setError(
        e instanceof TypeError
          ? 'We could not reach the analysis server. Check that the backend is running and try again.'
          : e.message,
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="res">
      <div className="res-box res-controls">
        {runId ? (
          <button type="button" className="res-button" onClick={runLive} disabled={loading}>
            {loading ? 'Running...' : 'Run the checks on the current analysis'}
          </button>
        ) : (
          <p className="res-muted">
            Run an analysis on the Discount effects tab to check it here. Below is a saved example.
          </p>
        )}
        {loading && <p className="res-muted">Running about 10 model fits. This can take a minute or more.</p>}
        {error && <p className="res-error-text">{error}</p>}
      </div>

      {!report && !error && <div className="res-box">Loading...</div>}

      {report && (
        <>
          <div className="res-banner">
            {source === 'saved'
              ? 'Saved example from a simulated run. '
              : 'Live result for the current analysis. '}
            Model: {report.settings.estimator}.
            {report.settings.estimator === 't_learner' && ' This is a development sample from a simple baseline model.'}
          </div>

          <div className="res-box res-info">
            <strong>How to read this.</strong> {report.disclaimer}
          </div>

          <div className="res-box">
            <div className="res-label">Summary</div>
            <div>
              {report.n_passed} passed, {report.n_failed} failed, {report.n_inconclusive} inconclusive
            </div>
            <div>
              Original average effect: {pp2(report.original_average_effect)}. Tolerance:{' '}
              {report.tolerance_absolute === null ? 'n/a' : pp2(report.tolerance_absolute)} (25% of the original
              effect).
            </div>
          </div>

          {report.results.map((r) => (
            <div className="res-box" key={r.name}>
              <div className="res-label">
                {r.title} <span className={VERDICT[String(r.passed)].css}>{VERDICT[String(r.passed)].text}</span>
              </div>
              <div>{r.what_it_does}</div>
              <div className="res-muted">Expected: {r.expected}</div>
              <div>Re-estimated average effects: {r.re_estimates.map(pp2).join(', ')}</div>
              <div className="res-muted">Rule: {r.criterion}</div>
            </div>
          ))}

          <div className="res-box">
            <div className="res-label">Not checked (limitations)</div>
            <ul>
              {report.not_done.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          </div>
        </>
      )}
    </section>
  )
}