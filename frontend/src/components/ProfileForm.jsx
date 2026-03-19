import { useState, useEffect } from 'react'
import SkillTag from './SkillTag'
import DeadlineToggle from './DeadlineToggle'
import { listRoles } from '../services/api'

const EXPERIENCE_LEVELS = ['entry', 'mid', 'senior']

export default function ProfileForm({ initialData = null, onSubmit, loading = false }) {
  const [name, setName]               = useState(initialData?.name || '')
  const [skillInput, setSkillInput]   = useState('')
  const [skills, setSkills]           = useState(initialData?.skills || [])
  const [experience, setExperience]   = useState(initialData?.experience_level || 'entry')
  const [targetRole, setTargetRole]   = useState(initialData?.target_role || '')
  const [roleOptions, setRoleOptions] = useState([])
  const [projects, setProjects]       = useState(
    initialData?.projects?.map(p => p.description) || ['']
  )
  const [timeline, setTimeline]       = useState({
    mode: initialData?.timeline_mode || 'relaxed',
    days: initialData?.timeline_days || null,
  })
  const [errors, setErrors]           = useState({})

  useEffect(() => {
    listRoles().then(r => setRoleOptions(r.data)).catch(() => {})
  }, [])

  // ── Skill tag input ──────────────────────────────────────────────────────────
  const addSkill = () => {
    const trimmed = skillInput.trim()
    if (trimmed && !skills.includes(trimmed)) {
      setSkills(prev => [...prev, trimmed])
    }
    setSkillInput('')
  }
  const handleSkillKeyDown = e => {
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); addSkill() }
  }
  const removeSkill = skill => setSkills(prev => prev.filter(s => s !== skill))

  // ── Projects ─────────────────────────────────────────────────────────────────
  const updateProject = (i, val) => setProjects(prev => prev.map((p, idx) => idx === i ? val : p))
  const addProject    = ()       => setProjects(prev => [...prev, ''])
  const removeProject = i        => setProjects(prev => prev.filter((_, idx) => idx !== i))

  // ── Validation ───────────────────────────────────────────────────────────────
  const validate = () => {
    const errs = {}
    if (!name.trim())      errs.name = 'Name is required.'
    if (!skills.length)    errs.skills = 'Add at least one skill.'
    if (!targetRole.trim()) errs.targetRole = 'Target role is required.'
    if (timeline.mode === 'deadline' && (!timeline.days || timeline.days < 1))
      errs.timeline = 'Enter how many days you have to prepare.'
    return errs
  }

  const handleSubmit = e => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setErrors({})

    onSubmit({
      name: name.trim(),
      skills,
      experience_level: experience,
      target_role: targetRole,
      timeline_mode: timeline.mode,
      timeline_days: timeline.mode === 'deadline' ? timeline.days : null,
      projects: projects.filter(p => p.trim()).map(d => ({ description: d.trim() })),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">

      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
        <input
          value={name} onChange={e => setName(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="e.g. Priya Sharma"
        />
        {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
      </div>

      {/* Skills */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Current Skills</label>
        <div className="flex gap-2 mb-2 flex-wrap">
          {skills.map(s => <SkillTag key={s} label={s} onRemove={() => removeSkill(s)} />)}
        </div>
        <div className="flex gap-2">
          <input
            value={skillInput} onChange={e => setSkillInput(e.target.value)}
            onKeyDown={handleSkillKeyDown}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="Type a skill and press Enter"
          />
          <button type="button" onClick={addSkill}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
            Add
          </button>
        </div>
        {errors.skills && <p className="text-red-500 text-xs mt-1">{errors.skills}</p>}
      </div>

      {/* Experience Level */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Experience Level</label>
        <div className="flex gap-3">
          {EXPERIENCE_LEVELS.map(lvl => (
            <button key={lvl} type="button"
              onClick={() => setExperience(lvl)}
              className={`flex-1 py-2 rounded-lg border-2 text-sm capitalize font-medium transition-colors ${
                experience === lvl
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300'
              }`}>
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Target Role */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Target Role</label>
        <select
          value={targetRole} onChange={e => setTargetRole(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
        >
          <option value="">Select a role…</option>
          {roleOptions.map(r => (
            <option key={r.role} value={r.role}>{r.role} — {r.category}</option>
          ))}
        </select>
        {errors.targetRole && <p className="text-red-500 text-xs mt-1">{errors.targetRole}</p>}
      </div>

      {/* Projects */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Past Projects <span className="text-gray-400 font-normal">(optional — helps AI infer your experience)</span>
        </label>
        <div className="space-y-2">
          {projects.map((p, i) => (
            <div key={i} className="flex gap-2">
              <textarea
                value={p} onChange={e => updateProject(i, e.target.value)}
                rows={2}
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
                placeholder={`e.g. "Built a REST API with Flask deployed on AWS EC2"`}
              />
              {projects.length > 1 && (
                <button type="button" onClick={() => removeProject(i)}
                  className="text-red-400 hover:text-red-600 text-lg font-bold self-start mt-1">×</button>
              )}
            </div>
          ))}
        </div>
        <button type="button" onClick={addProject}
          className="mt-2 text-sm text-blue-600 hover:underline">
          + Add another project
        </button>
      </div>

      {/* Learning Timeline */}
      <DeadlineToggle
        mode={timeline.mode} days={timeline.days}
        onChange={setTimeline}
      />
      {errors.timeline && <p className="text-red-500 text-xs">{errors.timeline}</p>}

      {/* Submit */}
      <button type="submit" disabled={loading}
        className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-60 transition-colors">
        {loading ? 'Saving…' : initialData ? 'Update Profile' : 'Create Profile & Analyze'}
      </button>
    </form>
  )
}
