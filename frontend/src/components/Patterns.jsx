export default function Patterns({ patterns }) {
  const hooks = patterns.viral_hooks || [];
  const narratives = patterns.trending_narratives || [];
  if (!hooks.length && !narratives.length) return null;

  const maxStrength = Math.max(...narratives.map(n => n.strength_score || 0), 1);

  return (
    <div className="mb-9">
      <div className="flex items-center gap-2 text-[15px] font-bold text-gray-900 mb-3.5 pb-2 border-b border-gray-200">
        🔬 Detected Patterns
        <span className="text-[11px] font-medium text-gray-400 bg-gray-50 border border-gray-200 px-2 py-0.5 rounded-full">auto-updated from fetched data</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="text-xs font-bold text-gray-900 uppercase tracking-wide mb-3">Hook Categories</div>
          {hooks.slice(0, 8).map((h, i) => (
            <div key={i} className="flex justify-between py-1.5 border-b border-gray-200 last:border-0 text-sm">
              <span className="text-gray-500">{h.category}</span>
              <span className="font-bold text-gray-900">{h.count}</span>
            </div>
          ))}
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="text-xs font-bold text-gray-900 uppercase tracking-wide mb-3">Trending Narratives</div>
          {narratives.slice(0, 8).map((n, i) => (
            <div key={i}>
              <div className="flex justify-between py-1.5 border-b border-gray-200 last:border-0 text-sm">
                <span className="text-gray-500">{n.narrative}</span>
                <span className="font-bold text-gray-900">{n.content_count}</span>
              </div>
              <div className="h-[3px] bg-gray-200 rounded mt-1 overflow-hidden">
                <div className="h-full bg-blue-500 rounded transition-all duration-600" style={{ width: `${(n.strength_score / maxStrength * 100).toFixed(0)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
