import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadDoc, UPLOAD_TYPE_OPTIONS } from '../services/api'

export default function SubmitFeedback() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [personName, setPersonName] = useState('')
  const [reviewYear, setReviewYear] = useState(new Date().getFullYear())
  const [uploadType, setUploadType] = useState('auto_feedback')
  const [file, setFile] = useState(null)
  const [email, setEmail] = useState('')
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  function acceptFile(f) {
    if (!f.name.match(/\.(doc|docx)$/i)) {
      setError('Only .doc or .docx files are accepted.')
      return
    }
    setFile(f)
    setError(null)
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) acceptFile(f)
  }

  function onFileChange(e) {
    const f = e.target.files?.[0]
    if (f) acceptFile(f)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)

    if (!personName.trim()) { setError('Employee name is required.'); return }
    if (!file) { setError('Please select a .doc or .docx file.'); return }

    setLoading(true)
    try {
      const res = await uploadDoc({
        file,
        upload_type: uploadType,
        person_name: personName.trim(),
        review_year: reviewYear,
        uploaded_by_email: email.trim() || undefined,
      })
      setResult(res)
    } catch (err) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : (err.message ?? 'Upload failed.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="form-page">
      <h1>Upload Document</h1>

      <form className="card form-card" onSubmit={handleSubmit}>
        {/* Employee name */}
        <div className="form-group">
          <label className="form-label">
            Employee name <span className="required">*</span>
          </label>
          <input
            type="text"
            className="form-input"
            value={personName}
            onChange={(e) => setPersonName(e.target.value)}
            placeholder="e.g. Emma Laurent"
            required
          />
        </div>

        {/* Review year */}
        <div className="form-group">
          <label className="form-label">
            Review year <span className="required">*</span>
          </label>
          <input
            type="number"
            className="form-input"
            value={reviewYear}
            onChange={(e) => setReviewYear(Number(e.target.value))}
            min={2000}
            max={2100}
            required
          />
        </div>

        {/* Document type */}
        <div className="form-group">
          <label className="form-label">
            Document type <span className="required">*</span>
          </label>
          <select
            className="form-input"
            value={uploadType}
            onChange={(e) => setUploadType(e.target.value)}
          >
            {UPLOAD_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Uploader email */}
        <div className="form-group">
          <label className="form-label">Your email <span className="optional">(optional)</span></label>
          <input
            type="email"
            className="form-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
        </div>

        {/* File drop zone */}
        <div className="form-group">
          <label className="form-label">
            File (.doc / .docx) <span className="required">*</span>
          </label>
          <div
            className={`dropzone${dragging ? ' dropzone-active' : ''}${file ? ' dropzone-has-file' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            {file ? (
              <span className="dropzone-filename">{file.name}</span>
            ) : (
              <>
                <span className="dropzone-hint">Drag & drop a .doc or .docx file here</span>
                <span className="dropzone-sub">or click to browse</span>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={onFileChange}
            style={{ display: 'none' }}
          />
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
          {loading ? 'Uploading…' : 'Upload & Generate Report'}
        </button>
      </form>

      {result && (
        <div className="alert alert-success" style={{ marginTop: '1.5rem' }}>
          <strong>{result.html_updated ? 'Report updated!' : 'Upload saved (HTML not updated).'}</strong>
          <p style={{ marginTop: '0.25rem' }}>{result.message}</p>
          {result.html_updated && (
            <button
              className="btn-link btn-link-green"
              style={{ marginTop: '0.75rem', display: 'inline-block' }}
              onClick={() =>
                navigate(`/profile/${encodeURIComponent(result.employee_name)}/${result.review_year}`)
              }
            >
              View profile →
            </button>
          )}
        </div>
      )}
    </div>
  )
}
