export default function SearchFilter({ value, onChange, placeholder = 'Search…' }) {
  return (
    <div className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        placeholder={placeholder}
      />
      {value && (
        <button onClick={() => onChange('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">×</button>
      )}
    </div>
  )
}
