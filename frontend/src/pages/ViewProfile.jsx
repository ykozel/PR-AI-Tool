import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { downloadHtml, getHtmlPreviewUrl, regenerateHtml, renameProfile } from '../services/api'

export default function ViewProfile() {
  const { personName, year } = useParams()
  const navigate = useNavigate()
  const decodedName = decodeURIComponent(personName ?? '')
  const numYear = Number(year)

  const [previewUrl, setPreviewUrl] = useState(null)
  const [loadingPreview, setLoadingPreview] = useState(true)
  const [previewError, setPreviewError] = useState(null)

  const [regenerating, setRegenerating] = useState(false)
  const [regenMsg, setRegenMsg] = useState(null)
  const [regenError, setRegenError] = useState(null)

  const [newName, setNewName] = useState(decodedName)
  const [renaming, setRenaming] = useState(false)
  const [renameMsg, setRenameMsg] = useState(null)
  const [renameError, setRenameError] = useState(null)

  function loadPreview(name, yr) {
    setLoadingPreview(true)
    setPreviewError(null)
    getHtmlPreviewUrl(name, yr)
      .then((url) => {
        setPreviewUrl((prev) => { if (prev) URL.revokeObjectURL(prev); return url })
      })
      .catch((e) => {
        const detail = e?.response?.data?.detail
        setPreviewError(typeof detail === 'string' ? detail : (e.message ?? 'Could not load report'))
      })
      .finally(() => setLoadingPreview(false))
  }

  useEffect(() => {
    loadPreview(decodedName, numYear)
    return () => { if (previewUrl) URL.revokeObjectURL(previewUrl) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [personName, year])

  async function handleRegenerate() {
    setRegenerating(true)
    setRegenMsg(null)
    setRegenError(null)
    try {
      const res = await regenerateHtml(decodedName, numYear)
      setRegenMsg(res.message ?? 'Regenerated successfully.')
      loadPreview(decodedName, numYear)
    } catch (e) {
      const detail = e?.response?.data?.detail
      setRegenError(typeof detail === 'string' ? detail : (e.message ?? 'Regeneration failed'))
    } finally {
      setRegenerating(false)
    }
  }

  async function handleRename(e) {
    e.preventDefault()
    const trimmed = newName.trim()
    if (!trimmed || trimmed === decodedName) return
    setRenaming(true)
    setRenameMsg(null)
    setRenameError(null)
    try {
      const res = await renameProfile(decodedName, numYear, trimmed)
      setRenameMsg(res.message ?? 'Renamed successfully.')
      navigate(`/profile/${encodeURIComponent(trimmed)}/${numYear}`, { replace: true })
    } catch (e) {
      const detail = e?.response?.data?.detail
      setRenameError(typeof detail === 'string' ? detail : (e.message ?? 'Rename failed'))
    } finally {
      setRenaming(false)
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="page-header" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <button className="btn-back" onClick={() => navigate('/')}>← All Profiles</button>
          <h1 style={{ margin: 0 }}>{decodedName}</h1>
          <p className="text-muted" style={{ marginTop: '0.25rem' }}>Review year {numYear}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            className="btn btn-secondary"
            onClick={() => downloadHtml(decodedName, numYear)}
          >
            Download HTML
          </button>
          <button
            className="btn btn-primary"
            disabled={regenerating}
            onClick={handleRegenerate}
          >
            {regenerating ? 'Regenerating…' : 'Regenerate Report'}
          </button>
        </div>
      </div>

      {regenMsg && <div className="alert alert-success" style={{ marginBottom: '1rem' }}>{regenMsg}</div>}
      {regenError && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{regenError}</div>}

      {/* Preview */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="preview-header">
          <span className="preview-title">HTML Report Preview</span>
          {previewUrl && (
            <a href={previewUrl} target="_blank" rel="noreferrer" className="btn-link">
              Open in new tab ↗
            </a>
          )}
        </div>
        <div className="preview-body">
          {loadingPreview && <div className="preview-placeholder">Loading preview…</div>}
          {previewError && !loadingPreview && (
            <div className="preview-placeholder preview-error">{previewError}</div>
          )}
          {previewUrl && !loadingPreview && (
            <iframe
              src={previewUrl}
              title="HTML Report"
              className="preview-iframe"
              sandbox="allow-same-origin"
            />
          )}
        </div>
      </div>

      {/* Rename */}
      <div className="card">
        <h2 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>Rename Employee</h2>
        <form onSubmit={handleRename} style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            type="text"
            className="form-input"
            style={{ flex: 1 }}
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="New employee name"
          />
          <button
            type="submit"
            className="btn btn-secondary"
            disabled={renaming || !newName.trim() || newName.trim() === decodedName}
          >
            {renaming ? 'Renaming…' : 'Rename'}
          </button>
        </form>
        {renameMsg && <p className="text-success" style={{ marginTop: '0.5rem' }}>{renameMsg}</p>}
        {renameError && <p className="text-error" style={{ marginTop: '0.5rem' }}>{renameError}</p>}
      </div>
    </div>
  )
}
