import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listProfiles, downloadHtml } from '../services/api'

export default function Dashboard() {
  const [profiles, setProfiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [downloading, setDownloading] = useState(null) // profile id being downloaded
  const navigate = useNavigate()

  const fetchProfiles = useCallback(() => {
    setLoading(true)
    setError(null)
    listProfiles()
      .then(setProfiles)
      .catch((e) => setError(e?.response?.data?.detail ?? e.message ?? 'Failed to load profiles'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { fetchProfiles() }, [fetchProfiles])

  async function handleDownload(profile) {
    setDownloading(profile.id)
    try {
      await downloadHtml(profile.employee_name, profile.year)
    } catch (e) {
      alert(e?.response?.data?.detail ?? e.message ?? 'Download failed')
    } finally {
      setDownloading(null)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Employee Profiles</h1>
        <Link to="/submit-feedback" className="btn btn-primary">+ New Upload</Link>
      </div>

      {loading && <p className="text-muted">Loading profiles…</p>}
      {error && <div className="alert alert-error">{error}</div>}

      {!loading && !error && profiles.length === 0 && (
        <div className="empty-state">
          <p>No profiles yet.</p>
          <Link to="/submit-feedback" className="btn btn-primary" style={{ marginTop: '1rem' }}>
            Upload your first document
          </Link>
        </div>
      )}

      {!loading && profiles.length > 0 && (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Year</th>
                <th style={{ textAlign: 'center' }}>Files</th>
                <th style={{ textAlign: 'center' }}>Report</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {profiles.map((p) => (
                <tr key={p.id}>
                  <td className="td-name">{p.employee_name}</td>
                  <td>{p.year}</td>
                  <td style={{ textAlign: 'center' }}>
                    <span className="badge">{p.files}</span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {p.has_html ? <span className="status-ok">✓ Ready</span> : <span className="status-na">—</span>}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn-link"
                      onClick={() =>
                        navigate(`/profile/${encodeURIComponent(p.employee_name)}/${p.year}`)
                      }
                    >
                      View
                    </button>
                    {p.has_html && (
                      <button
                        className="btn-link btn-link-green"
                        disabled={downloading === p.id}
                        onClick={() => handleDownload(p)}
                      >
                        {downloading === p.id ? 'Downloading…' : 'Download'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
