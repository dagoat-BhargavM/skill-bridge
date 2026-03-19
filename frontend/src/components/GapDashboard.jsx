import SkillTag from './SkillTag'
import GraphRoadmap from './GraphRoadmap'

function MatchMeter({ percent }) {
  const color = percent >= 70 ? 'bg-green-500' : percent >= 40 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm font-medium">
        <span>Role Match</span>
        <span>{percent}%</span>
      </div>
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  )
}

export default function GapDashboard({ analysis, profileName }) {
  if (!analysis) return null

  const isAccelerated = analysis.roadmap_type === 'accelerated'
  const isFallback    = analysis.source === 'fallback'

  return (
    <div className="space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-lg font-semibold">Gap Analysis — {profileName}</h2>
        <div className="flex gap-2 flex-wrap">
          {isAccelerated
            ? <span className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded-full font-medium">🔥 Accelerated roadmap</span>
            : <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">📚 Comprehensive roadmap</span>
          }
          {isFallback && (
            <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">⚠️ Rule-based (AI unavailable)</span>
          )}
        </div>
      </div>

      {/* Match meter */}
      <MatchMeter percent={analysis.match_percentage} />

      {/* Project-inferred skills */}
      {analysis.project_derived_skills?.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-1.5">✓ Skills inferred from your projects</p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.project_derived_skills.map(s => (
              <SkillTag key={s} label={s} variant="purple" />
            ))}
          </div>
        </div>
      )}

      {/* Matching skills */}
      {analysis.matching_skills?.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-1.5">✅ Matching skills</p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.matching_skills.map(s => (
              <SkillTag key={s} label={s} variant="green" />
            ))}
          </div>
        </div>
      )}

      {/* Missing critical */}
      {analysis.missing_critical?.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-1.5">❌ Missing critical skills</p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.missing_critical.map(s => (
              <SkillTag
                key={s}
                label={analysis.estimated_learning_times?.[s] ? `${s} · ${analysis.estimated_learning_times[s]}` : s}
                variant="red"
              />
            ))}
          </div>
        </div>
      )}

      {/* Missing preferred */}
      {analysis.missing_preferred?.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-1.5">⚡ Nice-to-have skills</p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.missing_preferred.map(s => <SkillTag key={s} label={s} variant="yellow" />)}
          </div>
        </div>
      )}

      {/* Roadmap */}
      {analysis.roadmap?.length > 0 && (
        <GraphRoadmap roadmap={analysis.roadmap} isAccelerated={isAccelerated} />
      )}

      {/* Strengths */}
      {analysis.strengths?.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-1.5">💪 Strengths</p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.strengths.map(s => <SkillTag key={s} label={s} variant="green" />)}
          </div>
        </div>
      )}
    </div>
  )
}
