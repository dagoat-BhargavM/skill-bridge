import { useState, useMemo } from "react"

const NODE_W = 170
const NODE_H = 72
const COL_GAP = 50
const ROW_GAP = 100
const PAD = 30

// ── Layout engine ─────────────────────────────────────────────────────────────
// Uses Kahn's algorithm (BFS topological sort) to assign each node a level.
// Level = longest prerequisite chain to reach this node from a root.
// Nodes at the same level share a row, centered horizontally.

function computeLayout(nodes) {
  if (!nodes?.length) return null

  const validSkills = new Set(nodes.map(n => n.skill))

  // Build graph edges: prerequisite → child
  const childrenOf = {}
  const inDegree = {}
  nodes.forEach(n => { childrenOf[n.skill] = []; inDegree[n.skill] = 0 })

  nodes.forEach(n => {
    ;(n.prerequisites || []).forEach(prereq => {
      if (validSkills.has(prereq)) {
        childrenOf[prereq].push(n.skill)
        inDegree[n.skill]++
      }
      // Silently ignore prerequisites that don't exist as nodes (Gemini hallucination guard)
    })
  })

  // BFS — assign level = max(parent level) + 1
  const level = {}
  const queue = nodes.filter(n => inDegree[n.skill] === 0).map(n => n.skill)
  queue.forEach(s => (level[s] = 0))

  const bfs = [...queue]
  while (bfs.length > 0) {
    const skill = bfs.shift()
    childrenOf[skill].forEach(child => {
      level[child] = Math.max(level[child] ?? 0, level[skill] + 1)
      inDegree[child]--
      if (inDegree[child] === 0) bfs.push(child)
    })
  }

  // Fallback for unreached nodes (cycles — shouldn't happen if prompt is followed)
  nodes.forEach(n => { if (level[n.skill] === undefined) level[n.skill] = 0 })

  // Group by level
  const byLevel = {}
  nodes.forEach(n => {
    const lvl = level[n.skill]
    byLevel[lvl] = byLevel[lvl] || []
    byLevel[lvl].push(n)
  })

  // Compute SVG canvas size
  const maxPerRow = Math.max(...Object.values(byLevel).map(g => g.length))
  const svgW = Math.max(maxPerRow * (NODE_W + COL_GAP) - COL_GAP + PAD * 2, 400)
  const maxLevel = Math.max(...Object.keys(byLevel).map(Number))
  const svgH = (maxLevel + 1) * (NODE_H + ROW_GAP) - ROW_GAP + PAD * 2

  // Compute x, y positions — center each row
  const pos = {}
  Object.entries(byLevel).forEach(([lvl, levelNodes]) => {
    const y = Number(lvl) * (NODE_H + ROW_GAP) + PAD
    const rowW = levelNodes.length * (NODE_W + COL_GAP) - COL_GAP
    const startX = (svgW - rowW) / 2
    levelNodes.forEach((node, i) => {
      pos[node.skill] = { x: startX + i * (NODE_W + COL_GAP), y }
    })
  })

  return { pos, svgW, svgH }
}

// ── SVG bezier edge with arrowhead ────────────────────────────────────────────
function Edge({ from, to }) {
  const x1 = from.x + NODE_W / 2
  const y1 = from.y + NODE_H
  const x2 = to.x + NODE_W / 2
  const y2 = to.y
  const midY = (y1 + y2) / 2

  return (
    <path
      d={`M${x1},${y1} C${x1},${midY} ${x2},${midY} ${x2},${y2}`}
      fill="none"
      stroke="#cbd5e1"
      strokeWidth={2}
      markerEnd="url(#arrowhead)"
    />
  )
}

// ── Resource panel (shown below graph on node click) ─────────────────────────
function ResourcePanel({ node, onClose }) {
  const isCritical = node.priority === "critical"
  const videos = node.resources?.videos || []
  const articles = node.resources?.articles || []
  const hasResources = videos.length > 0 || articles.length > 0

  return (
    <div className="mt-4 border border-gray-200 rounded-xl p-4 bg-white shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-gray-800 text-sm">{node.skill}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${isCritical ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"}`}>
              {isCritical ? "Critical" : "Preferred"} · {node.days_allocated}d
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">{node.reason}</p>
          {node.prerequisites?.length > 0 && (
            <p className="text-xs text-gray-400 mt-1">
              Prerequisites: {node.prerequisites.join(", ")}
            </p>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-xl leading-none ml-2 shrink-0"
        >
          ×
        </button>
      </div>

      {!hasResources ? (
        <p className="text-xs text-gray-400">No resources available for this skill.</p>
      ) : (
        <div className="space-y-3">
          {videos.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1.5">🎥 Videos</p>
              <div className="space-y-1">
                {videos.map((v, i) => (
                  <a key={i} href={v.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-xs text-blue-700 hover:underline">
                    <span className="shrink-0">▶</span>
                    <span className="truncate">{v.title}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
          {articles.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1.5">📄 Articles</p>
              <div className="space-y-1">
                {articles.map((a, i) => (
                  <a key={i} href={a.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-xs text-blue-700 hover:underline">
                    <span className="shrink-0">→</span>
                    <span className="truncate">{a.title}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function GraphRoadmap({ roadmap, isAccelerated }) {
  const [selected, setSelected] = useState(null)
  const layout = useMemo(() => computeLayout(roadmap), [roadmap])

  if (!roadmap?.length || !layout) return null

  const { pos, svgW, svgH } = layout
  const nodeMap = Object.fromEntries(roadmap.map(n => [n.skill, n]))
  const selectedNode = selected ? nodeMap[selected] : null
  const totalDays = roadmap.reduce((sum, n) => sum + (n.days_allocated || 0), 0)

  // Collect edges from prerequisites
  const edges = []
  roadmap.forEach(node => {
    ;(node.prerequisites || []).forEach(prereq => {
      if (pos[prereq] && pos[node.skill]) {
        edges.push({ from: prereq, to: node.skill })
      }
    })
  })

  const handleClick = (skill) =>
    setSelected(prev => (prev === skill ? null : skill))

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-gray-700">
          🗺️ Learning Roadmap
          {isAccelerated ? " (deadline-optimised)" : " (comprehensive)"}
        </p>
        <span className="text-xs text-gray-400">
          {totalDays} days total · click a node to see resources
        </span>
      </div>

      {/* Graph container: SVG edges behind, HTML nodes on top */}
      <div className="overflow-x-auto rounded-xl border border-gray-100 bg-gray-50 p-2">
        <div className="relative mx-auto" style={{ width: svgW, height: svgH }}>

          {/* SVG layer — edges only */}
          <svg
            className="absolute inset-0 pointer-events-none"
            width={svgW}
            height={svgH}
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="8"
                markerHeight="6"
                refX="7"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#cbd5e1" />
              </marker>
            </defs>
            {edges.map((e, i) => (
              <Edge key={i} from={pos[e.from]} to={pos[e.to]} />
            ))}
          </svg>

          {/* HTML layer — clickable nodes */}
          {roadmap.map(node => {
            const p = pos[node.skill]
            const isCritical = node.priority === "critical"
            const isSelected = selected === node.skill

            return (
              <div
                key={node.skill}
                onClick={() => handleClick(node.skill)}
                style={{
                  position: "absolute",
                  left: p.x,
                  top: p.y,
                  width: NODE_W,
                  height: NODE_H,
                }}
                className={`
                  rounded-xl border-2 cursor-pointer transition-all bg-white
                  flex flex-col justify-center px-3 py-2 select-none
                  ${isSelected
                    ? "border-blue-500 bg-blue-50 shadow-lg"
                    : isCritical
                      ? "border-red-300 hover:border-red-400 hover:shadow-md"
                      : "border-yellow-300 hover:border-yellow-400 hover:shadow-md"
                  }
                `}
              >
                <div className="flex items-center justify-between gap-1">
                  <span className="text-xs font-semibold text-gray-800 truncate leading-tight">
                    {node.skill}
                  </span>
                  <span className={`text-xs px-1.5 py-0.5 rounded-full shrink-0 font-medium ${isCritical ? "bg-red-100 text-red-600" : "bg-yellow-100 text-yellow-600"}`}>
                    {node.days_allocated}d
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-0.5 truncate leading-tight">
                  {node.reason}
                </p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Resource panel — appears below graph on click */}
      {selectedNode && (
        <ResourcePanel node={selectedNode} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}
