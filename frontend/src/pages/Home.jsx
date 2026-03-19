import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { listProfiles, deleteProfile } from '../services/api'
import SearchFilter from '../components/SearchFilter'

export default function Home() {
  const [profiles, setProfiles] = useState([])
  const [search, setSearch]     = useState('')
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')
  const navigate                = useNavigate()

  const fetchProfiles = async (q = '') => {
    setLoading(true)
    try {
      const res = await listProfiles(q ? { search: q } : {})
      setProfiles(res.data)
      setError('')
    } catch {
      setError('Could not load profiles. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchProfiles() }, [])
  useEffect(() => { fetchProfiles(search) }, [search])

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete profile for ${name}?`)) return
    try {
      await deleteProfile(id)
      setError('')
      fetchProfiles(search)
    } catch (err) {
      setError(`Failed to delete profile: ${err.message || 'Unknown error'}`)
      console.error('Delete failed:', err)
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-10 px-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Skill-Bridge</h1>
        <button onClick={() => navigate('/profile/new')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
          + New Profile
        </button>
      </div>

      <SearchFilter
        value={search} onChange={setSearch}
        placeholder="Search by name or target role…"
      />

      {error && <p className="text-red-500 text-sm bg-red-50 p-3 rounded-lg">{error}</p>}

      {loading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : profiles.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🎯</p>
          <p className="font-medium">{search ? 'No profiles match your search.' : 'No profiles yet.'}</p>
          <p className="text-sm mt-1">Create your first profile to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {profiles.map(p => (
            <div key={p.id}
              className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between hover:border-blue-300 transition-colors cursor-pointer"
              onClick={() => navigate(`/profile/${p.id}`)}>
              <div>
                <p className="font-medium">{p.name}</p>
                <p className="text-sm text-gray-500">{p.target_role} · {p.experience_level}</p>
                <div className="flex gap-1 mt-1">
                  {p.timeline_mode === 'deadline'
                    ? <span className="text-xs text-orange-600">🔥 {p.timeline_days} days</span>
                    : <span className="text-xs text-blue-600">📚 Relaxed</span>
                  }
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={e => { e.stopPropagation(); navigate(`/profile/${p.id}/edit`) }}
                  className="text-xs px-2 py-1 border border-gray-200 rounded-md hover:bg-gray-50">Edit</button>
                <button onClick={e => { e.stopPropagation(); handleDelete(p.id, p.name) }}
                  className="text-xs px-2 py-1 border border-red-200 text-red-500 rounded-md hover:bg-red-50">Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
