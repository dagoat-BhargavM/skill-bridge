import { Routes, Route, Navigate } from 'react-router-dom'
import Home    from './pages/Home'
import Profile from './pages/Profile'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/"                    element={<Home />} />
        <Route path="/profile/:id"         element={<Profile />} />
        <Route path="/profile/:id/edit"    element={<Profile />} />
        <Route path="*"                    element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}
