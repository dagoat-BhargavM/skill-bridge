import { useState } from "react"

function ResourceLink({ href, title, type }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-1.5 text-xs text-blue-700 hover:text-blue-900 hover:underline truncate"
    >
      <span>{type === "video" ? "🎥" : "📄"}</span>
      <span className="truncate">{title}</span>
    </a>
  )
}

function RoadmapNode({ node, index, isLast }) {
  const [open, setOpen] = useState(false)

  const isCritical = node.priority === "critical"
  const hasResources =
    node.resources &&
    ((node.resources.videos && node.resources.videos.length > 0) ||
      (node.resources.articles && node.resources.articles.length > 0))

  const borderColor = isCritical ? "border-red-400" : "border-yellow-400"
  const badgeBg = isCritical
    ? "bg-red-100 text-red-700"
    : "bg-yellow-100 text-yellow-700"
  const dotColor = isCritical ? "bg-red-400" : "bg-yellow-400"

  return (
    <div className="flex gap-3">
      {/* Timeline spine */}
      <div className="flex flex-col items-center">
        <div className={`w-3 h-3 rounded-full mt-4 shrink-0 ${dotColor}`} />
        {!isLast && <div className="w-0.5 bg-gray-200 flex-1 mt-1" />}
      </div>

      {/* Node card */}
      <div className={`flex-1 border-l-4 ${borderColor} bg-white rounded-xl shadow-sm mb-4 overflow-hidden`}>
        {/* Header row */}
        <div className="flex items-start justify-between gap-2 p-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-gray-400 font-mono">#{node.order}</span>
              <h3 className="font-semibold text-gray-800 text-sm">{node.skill}</h3>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badgeBg}`}>
                {isCritical ? "Critical" : "Preferred"}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">{node.reason}</p>
          </div>
          <div className="text-right shrink-0">
            <span className="text-sm font-semibold text-gray-700">{node.days_allocated}d</span>
            <p className="text-xs text-gray-400">to learn</p>
          </div>
        </div>

        {/* Resources toggle */}
        {hasResources && (
          <>
            <button
              onClick={() => setOpen(!open)}
              className="w-full flex items-center justify-between px-4 py-2 bg-gray-50 text-xs text-gray-600 hover:bg-gray-100 transition-colors border-t border-gray-100"
            >
              <span>📚 Learning resources</span>
              <span className="text-gray-400">{open ? "▲" : "▼"}</span>
            </button>

            {open && (
              <div className="px-4 py-3 space-y-3 border-t border-gray-100">
                {node.resources.videos && node.resources.videos.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-1">Videos</p>
                    <div className="space-y-1">
                      {node.resources.videos.map((v, i) => (
                        <ResourceLink key={i} href={v.url} title={v.title} type="video" />
                      ))}
                    </div>
                  </div>
                )}
                {node.resources.articles && node.resources.articles.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-1">Articles</p>
                    <div className="space-y-1">
                      {node.resources.articles.map((a, i) => (
                        <ResourceLink key={i} href={a.url} title={a.title} type="article" />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default function RoadmapView({ roadmap, isAccelerated }) {
  if (!roadmap || roadmap.length === 0) return null

  const totalDays = roadmap.reduce((sum, n) => sum + (n.days_allocated || 0), 0)

  return (
    <div>
      {/* Section header */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-semibold text-gray-700">
          🗺️ Learning Roadmap
          {isAccelerated ? " (deadline-optimised)" : " (comprehensive)"}
        </p>
        <span className="text-xs text-gray-400">{totalDays} days total</span>
      </div>

      {/* Nodes */}
      <div>
        {roadmap.map((node, i) => (
          <RoadmapNode
            key={node.order}
            node={node}
            index={i}
            isLast={i === roadmap.length - 1}
          />
        ))}
      </div>
    </div>
  )
}
