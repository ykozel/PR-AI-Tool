import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './App.css'
import Dashboard from './pages/Dashboard'
import SubmitFeedback from './pages/SubmitFeedback'
import ViewProfile from './pages/ViewProfile'
import Navigation from './components/Navigation'

function App() {
  return (
    <BrowserRouter>
      <Navigation />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/submit-feedback" element={<SubmitFeedback />} />
          <Route path="/profile/:personName/:year" element={<ViewProfile />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

export default App
