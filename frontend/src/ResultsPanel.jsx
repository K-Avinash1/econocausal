import { useEffect, useState } from 'react'
import './ResultsPanel.css'

const pp = (x) => (x === null || x === undefined ? 'n/a' : `${(x * 100).toFixed(1)} pp`)
const pct = (x) => (x === null || x === undefined ? 'n/a' : `${(x * 100).toFixed(0)}%`)
const money = (x) => (x === null || x === undefined ? 'n/a' : `$${x.toFixed(2)}`)
const interval = (lo, hi) => (lo === null || hi === null ? 'n/a' : `${pp(lo)} to ${pp(hi)}`)

export default function ResultsPanel({ url = '/analysis_demo.json' }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`Could not load ${url} (status ${r.status})`)
        return r.json()
      })
      .then(setData)
      .catch((e) => setError(e.message))
  }, [url])

  if (error) return <div className="res-box res-error">{error}</div>
  if (!data) return <div className="res-box">Loading results...</div>

  const { run, average_effect: ate, effect_summary: s, customers, notes, evaluation } = data
  const isSample = run.estimator === 't_learner' || run.data_source === 'synthetic'

  return (
    <section className="res">
      <h2>Results</h2>
      {isSample && (
        <div className="res-banner">
          Sample or simulated run. Model: {run.estimator_label}. Data: {run.data_source}.
        </div>
      )}

      <div className="res-box">
        <div className="res-label">Average effect of the discount on purchase chance</div>
        <div className="res-big">{pp(ate.ate)}</div>
        <div>
          {ate.ci_low === null
            ? 'Interval not available for this model'
            : `${Math.round(ate.confidence_level * 100)}% interval: ${interval(ate.ci_low, ate.ci_high)}`}
        </div>
      </div>

      <div className="res-box">
        <div className="res-label">How much the effect varies between customers</div>
        <div>5th percentile {pp(s.p05)} | median {pp(s.median)} | 95th percentile {pp(s.p95)}</div>
        <div>Customers with a negative effect: {pct(s.share_negative)}</div>
      </div>

      <div className="res-box">
        <div className="res-label">
          First {data.customers_returned} of {data.customers_total.toLocaleString()} customers
        </div>
        <div className="res-scroll">
          <table>
            <thead>
              <tr>
                <th>Customer</th>
                <th>Effect</th>
                <th>Interval</th>
                <th>Buys without discount</th>
                <th>Typical order</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.customer_id}>
                  <td>{c.customer_id}</td>
                  <td>{pp(c.effect)}</td>
                  <td>{interval(c.effect_low, c.effect_high)}</td>
                  <td>{pct(c.baseline_purchase_prob)}</td>
                  <td>{money(c.expected_list_value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="res-box">
        <div className="res-label">Notes</div>
        <ul>{notes.map((n) => <li key={n}>{n}</li>)}</ul>
      </div>

      {evaluation && (
        <div className="res-box res-sim">
          <div className="res-label">Simulation only: estimate vs known truth</div>
          <div>True average effect {pp(evaluation.true_ate)} | estimated {pp(evaluation.estimated_ate)}</div>
          <div>Simple treated-vs-untreated difference {pp(evaluation.naive_difference)} (this ignores confounding)</div>
          <div>Evaluated on: {evaluation.evaluated_on}</div>
        </div>
      )}
    </section>
  )
}