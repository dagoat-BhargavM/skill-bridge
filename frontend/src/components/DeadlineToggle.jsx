export default function DeadlineToggle({ mode, days, onChange }) {
  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">Learning Timeline</label>
      <div className="flex gap-3">
        {/* Relaxed */}
        <button
          type="button"
          onClick={() => onChange({ mode: 'relaxed', days: null })}
          className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium transition-colors ${
            mode === 'relaxed'
              ? 'border-blue-500 bg-blue-50 text-blue-700'
              : 'border-gray-200 text-gray-600 hover:border-gray-300'
          }`}
        >
          📚 Relaxed
          <p className="text-xs font-normal text-gray-500 mt-0.5">No time pressure</p>
        </button>

        {/* Deadline */}
        <button
          type="button"
          onClick={() => onChange({ mode: 'deadline', days: days || 14 })}
          className={`flex-1 py-2 px-3 rounded-lg border-2 text-sm font-medium transition-colors ${
            mode === 'deadline'
              ? 'border-orange-500 bg-orange-50 text-orange-700'
              : 'border-gray-200 text-gray-600 hover:border-gray-300'
          }`}
        >
          🔥 Deadline
          <p className="text-xs font-normal text-gray-500 mt-0.5">Fast-track learning</p>
        </button>
      </div>

      {mode === 'deadline' && (
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">I have</label>
          <input
            type="number"
            min={1}
            value={days || ''}
            onChange={e => onChange({ mode: 'deadline', days: parseInt(e.target.value) || null })}
            placeholder="14"
            className="w-20 border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
          />
          <label className="text-sm text-gray-600">days to prepare</label>
        </div>
      )}
    </div>
  )
}
