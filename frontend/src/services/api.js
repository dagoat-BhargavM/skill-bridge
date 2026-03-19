import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// ── Profiles ───────────────────────────────────────────────────────────────────
export const createProfile  = (data)           => api.post('/profiles/', data)
export const listProfiles   = (params = {})    => api.get('/profiles/', { params })
export const getProfile     = (id)             => api.get(`/profiles/${id}`)
export const updateProfile  = (id, data)       => api.put(`/profiles/${id}`, data)
export const deleteProfile  = (id)             => api.delete(`/profiles/${id}`)

// ── Analysis ───────────────────────────────────────────────────────────────────
export const runAnalysis    = (profileId)      => api.post(`/analyze/${profileId}`)
export const getAnalysis    = (profileId)      => api.get(`/analyze/${profileId}`)

// ── Roles ──────────────────────────────────────────────────────────────────────
export const listRoles      = (search = '')    => api.get('/roles', { params: { search } })
