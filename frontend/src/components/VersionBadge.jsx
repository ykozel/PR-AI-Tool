import { useState, useEffect } from 'react'
import { getVersionString } from '../services/version'
import './VersionBadge.css'

export default function VersionBadge() {
  const [version, setVersion] = useState('loading...')
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    getVersionString()
      .then((v) => setVersion(v || 'unknown'))
      .catch(() => setVersion('unknown'))
  }, [])

  return (
    <div className="version-badge" title={`PR Profile v${version}`}>
      <span className="version-text">v{version}</span>
      {showDetails && (
        <span className="version-tooltip">
          PR Profile Version {version}
        </span>
      )}
    </div>
  )
}
