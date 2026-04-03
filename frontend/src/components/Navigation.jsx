import { Link, useLocation } from 'react-router-dom'
import VersionBadge from './VersionBadge'
import VersionInfo from './VersionInfo'
import '../App.css'

export default function Navigation() {
  const { pathname } = useLocation()
  return (
    <header className="header">
      <nav className="nav">
        <Link to="/" className="nav-brand">PR Profile Manager</Link>
        <ul className="nav-menu">
          <li>
            <Link to="/" className={`nav-link${pathname === '/' ? ' nav-link-active' : ''}`}>
              Profiles
            </Link>
          </li>
          <li>
            <Link
              to="/submit-feedback"
              className={`nav-link${pathname === '/submit-feedback' ? ' nav-link-active' : ''}`}
            >
              Upload
            </Link>
          </li>
        </ul>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'auto' }}>
          <VersionBadge />
          <VersionInfo />
        </div>
      </nav>
    </header>
  )
}
