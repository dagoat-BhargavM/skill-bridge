import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ProfileForm from '../components/ProfileForm'
import GapDashboard from '../components/GapDashboard'
import { createProfile, getProfile, updateProfile, runAnalysis, getAnalysis } from '../services/api'

export default function ProfilePage() {
  const { id }      = useParams()               // 'new' for create, numeric id for view/edit
  const navigate    = useNavigate()
  const isNew       = id === 'new'
  const isEdit      = window.location.pathname.endsWith('/edit')

  const [profile,  setProfile]  = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading,  setLoading]  = useState(!isNew)
  const [saving,   setSaving]   = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error,    setError]    = useState('')

  // Load existing profile + any saved analysis
  useEffect(() => {
    if (isNew) return
    Promise.all([
      getProfile(id),
      getAnalysis(id).catch(() => null),   // 404 is fine — no analysis yet
    ]).then(([profRes, anaRes]) => {
      setProfile(profRes.data)
      if (anaRes) setAnalysis(anaRes.data)
    }).catch(() => setError('Profile not found.'))
    .finally(() => setLoading(false))
  }, [id, isNew])

  const handleCreate = async (data) => {
    setSaving(true)
    try {
      const res  = await createProfile(data)
      const newId = res.data.id
      // Auto-run analysis immediately after profile creation
      setAnalyzing(true)
      const anaRes = await runAnalysis(newId)
      navigate(`/profile/${newId}`, { state: { analysis: anaRes.data, profile: res.data } })
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create profile.')
    } finally {
      setSaving(false)
      setAnalyzing(false)
    }
  }

  const handleUpdate = async (data) => {
    setSaving(true)
    try {
      await updateProfile(id, data)
      // Profile updated → re-run analysis with new data
      setAnalyzing(true)
      const anaRes = await runAnalysis(id)
      setAnalysis(anaRes.data)
      const profRes = await getProfile(id)
      setProfile(profRes.data)
      navigate(`/profile/${id}`)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to update profile.')
    } finally {
      setSaving(false)
      setAnalyzing(false)
    }
  }

  const handleReanalyze = async () => {
    setAnalyzing(true)
    setError('')
    try {
      const res = await runAnalysis(id)
      setAnalysis(res.data)
    } catch {
      setError('Analysis failed. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) return <div className="text-center py-20 text-gray-400">Loading…</div>

  // ── Create mode ──────────────────────────────────────────────────────────────
  if (isNew) return (
    <div className="max-w-2xl mx-auto py-10 px-4">
      <button onClick={() => navigate('/')} className="text-sm text-gray-500 hover:underline mb-4 block">← Back</button>
      <h1 className="text-xl font-bold mb-6">Create Profile</h1>
      {error && <p className="text-red-500 text-sm bg-red-50 p-3 rounded-lg mb-4">{error}</p>}
      <ProfileForm onSubmit={handleCreate} loading={saving || analyzing} />
      {analyzing && <p className="text-sm text-blue-600 mt-3 text-center">Running analysis…</p>}
    </div>
  )

  // ── Edit mode ────────────────────────────────────────────────────────────────
  if (isEdit && profile) return (
    <div className="max-w-2xl mx-auto py-10 px-4">
      <button onClick={() => navigate(`/profile/${id}`)} className="text-sm text-gray-500 hover:underline mb-4 block">← Back</button>
      <h1 className="text-xl font-bold mb-6">Edit Profile</h1>
      {error && <p className="text-red-500 text-sm bg-red-50 p-3 rounded-lg mb-4">{error}</p>}
      <ProfileForm initialData={profile} onSubmit={handleUpdate} loading={saving || analyzing} />
    </div>
  )

  // ── View mode ────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto py-10 px-6 space-y-6">
      <div className="flex items-center justify-between">
        <button onClick={() => navigate('/')} className="text-sm text-gray-500 hover:underline">← All Profiles</button>
        <button onClick={() => navigate(`/profile/${id}/edit`)}
          className="text-sm px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50">
          Edit Profile
        </button>
      </div>

      {/* Profile summary */}
      {profile && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-xl font-semibold mb-1">{profile.name}</h2>
          <p className="text-sm text-gray-500 mb-3">{profile.target_role} · {profile.experience_level}</p>
          <div className="flex flex-wrap gap-1.5 mb-3">
            {profile.skills.map(s => (
              <span key={s} className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">{s}</span>
            ))}
          </div>
          {profile.projects?.filter(p => p.description).length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-gray-500 mb-1">Projects</p>
              <ul className="space-y-1">
                {profile.projects.map(p => (
                  <li key={p.id} className="text-sm text-gray-600">• {p.description}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {error && <p className="text-red-500 text-sm bg-red-50 p-3 rounded-lg">{error}</p>}

      {/* Analysis section */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        {analysis ? (
          <>
            <GapDashboard analysis={analysis} profileName={profile?.name} />
            <button onClick={handleReanalyze} disabled={analyzing}
              className="mt-4 text-sm text-blue-600 hover:underline disabled:opacity-50">
              {analyzing ? 'Re-analyzing…' : '↻ Re-run analysis'}
            </button>
          </>
        ) : (
          <div className="text-center py-6">
            <p className="text-gray-500 text-sm mb-3">No analysis yet.</p>
            <button onClick={handleReanalyze} disabled={analyzing}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-60">
              {analyzing ? 'Analyzing…' : 'Run Analysis'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
