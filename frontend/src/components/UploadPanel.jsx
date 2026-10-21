import { useState } from 'react'
import { API_URL, MAX_UPLOAD_BYTES, MAX_ERRORS_SHOWN } from '../config'

function percent(fraction) {
  return `${(fraction * 100).toFixed(1)}%`
}

function PreviewTable({ columns, rows }) {
  return (
    <div className="table-wrap">
      <table>
        <caption>Preview: first {rows.length} rows</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column} scope="col">{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column}>{String(row[column] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function UploadPanel() {
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [pageError, setPageError] = useState('')
  const [fileName, setFileName] = useState('')
  const [notice, setNotice] = useState('')

  function fail(message) {
    setResult(null)
    setPageError(message)
    setStatus('failed')
  }

  async function handleFileChange(event) {
    const file = event.target.files[0]
    event.target.value = ''
    if (!file) return

    setFileName(file.name)
    setResult(null)
    setPageError('')
    setNotice('')

    if (!file.name.toLowerCase().endsWith('.csv')) {
      fail('Please choose a CSV file (a file whose name ends in .csv).')
      return
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      fail('This file is larger than 10 MB. Please upload a smaller file.')
      return
    }

    setStatus('checking')
    try {
      const response = await fetch(`${API_URL}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'text/csv' },
        body: file,
      })
      if (!response.ok) {
        throw new Error(`Server answered ${response.status}`)
      }
      setResult(await response.json())
      setStatus('done')
    } catch {
      fail('We could not reach the analysis server. Check that the backend is running and try again.')
    }
  }

  const errors = result ? result.errors : []
  const warnings = result ? result.warnings : []
  const shownErrors = errors.slice(0, MAX_ERRORS_SHOWN)
  const hiddenErrors = errors.length - shownErrors.length
  const accepted = status === 'done' && result !== null && result.ok

  return (
    <section className="upload">
      <p>
        Upload a CSV file with one row per customer. The file needs the columns listed in
        docs/dataset_schema.md.
      </p>

      <label htmlFor="csv-file" className="file-label">Choose a CSV file</label>
      <input id="csv-file" type="file" accept=".csv,text/csv" onChange={handleFileChange} />
      {fileName && <p className="file-name">Selected file: {fileName}</p>}

      {status === 'checking' && <p role="status">Checking your file...</p>}

      {pageError && (
        <div className="message error" role="alert">
          <strong>⛔ Error</strong>
          <p>{pageError}</p>
        </div>
      )}

      {errors.length > 0 && (
        <div className="message error" role="alert">
          <strong>⛔ Error</strong>
          <ul>
            {shownErrors.map((error, index) => (
              <li key={index}>{error.message}</li>
            ))}
          </ul>
          {hiddenErrors > 0 && <p>and {hiddenErrors} more</p>}
          <p>Fix these problems and upload the file again.</p>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="message warning">
          <strong>⚠ Warning</strong>
          <ul>
            {warnings.map((warning, index) => (
              <li key={index}>{warning.message}</li>
            ))}
          </ul>
        </div>
      )}

      {accepted && (
        <div className="message success" role="status">
          <strong>✔ File accepted</strong>
          <p>
            {result.summary.n_rows.toLocaleString()} customers. {percent(result.summary.treated_share)} were
            offered the discount and {percent(result.summary.purchase_rate)} purchased.
          </p>
        </div>
      )}

      {result && result.preview.length > 0 && (
        <PreviewTable columns={result.columns} rows={result.preview} />
      )}

      <button
        type="button"
        className="run-button"
        disabled={!accepted}
        onClick={() => setNotice('Analysis is not connected yet. It is built in a later phase of the project.')}
      >
        Run analysis
      </button>
      {notice && <p role="status">{notice}</p>}
    </section>
  )
}