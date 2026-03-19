export default function SkillTag({ label, onRemove, variant = 'default' }) {
  const styles = {
    default:  'bg-blue-100 text-blue-800',
    green:    'bg-green-100 text-green-800',
    red:      'bg-red-100 text-red-800',
    yellow:   'bg-yellow-100 text-yellow-800',
    purple:   'bg-purple-100 text-purple-800',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${styles[variant]}`}>
      {label}
      {onRemove && (
        <button onClick={onRemove} className="ml-0.5 hover:opacity-70 font-bold" aria-label={`Remove ${label}`}>
          ×
        </button>
      )}
    </span>
  )
}
