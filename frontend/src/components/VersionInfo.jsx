import { useState, useEffect } from 'react'
import { getAppInfo } from '../services/version'
import './VersionInfo.css'

export default function VersionInfo() {
  const [info, setInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    if (showModal && !info) {
      setLoading(true)
      getAppInfo()
        .then((data) => {
          setInfo(data)
          setLoading(false)
        })
        .catch(() => {
          setLoading(false)
        })
    }
  }, [showModal, info])

  if (!info && !showModal) {
    return null
  }

  return (
    <>
      <button 
        className="version-info-button" 
        onClick={() => setShowModal(true)}
        title="View version information"
      >
        About
      </button>

      {showModal && (
        <div className="version-info-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="version-info-modal" onClick={(e) => e.stopPropagation()}>
            <button 
              className="version-info-close" 
              onClick={() => setShowModal(false)}
            >
              ×
            </button>

            <h2 className="version-info-title">About PR Profile</h2>

            {loading ? (
              <div className="version-info-loading">Loading version information...</div>
            ) : info ? (
              <div className="version-info-content">
                <div className="version-info-section">
                  <h3>{info.app_name}</h3>
                  <p className="version-info-description">{info.description}</p>
                </div>

                <div className="version-info-section">
                  <h4>Version Information</h4>
                  <div className="version-info-grid">
                    <div className="version-info-item">
                      <span className="version-info-label">Version:</span>
                      <span className="version-info-value">{info.version}</span>
                    </div>
                    <div className="version-info-item">
                      <span className="version-info-label">Release Channel:</span>
                      <span className={`version-info-value channel-${info.release_channel}`}>
                        {info.release_channel}
                      </span>
                    </div>
                    <div className="version-info-item">
                      <span className="version-info-label">Release Date:</span>
                      <span className="version-info-value">{new Date(info.release_date).toLocaleDateString()}</span>
                    </div>
                    <div className="version-info-item">
                      <span className="version-info-label">Build Number:</span>
                      <span className="version-info-value">{info.build_number}</span>
                    </div>
                  </div>
                </div>

                <div className="version-info-section">
                  <h4>Build Information</h4>
                  <div className="version-info-grid">
                    <div className="version-info-item">
                      <span className="version-info-label">Git Branch:</span>
                      <code className="version-info-code">{info.git_info.branch}</code>
                    </div>
                    <div className="version-info-item">
                      <span className="version-info-label">Git Commit:</span>
                      <code className="version-info-code">{info.git_info.commit}</code>
                    </div>
                    <div className="version-info-item full-width">
                      <span className="version-info-label">Status:</span>
                      <span className="version-info-value status-running">● Running</span>
                    </div>
                  </div>
                </div>

                <div className="version-info-footer">
                  <p className="version-info-copyright">
                    &copy; 2024-2027 PR Profile. All rights reserved.
                  </p>
                </div>
              </div>
            ) : (
              <div className="version-info-error">
                Failed to load version information. Please try again later.
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
