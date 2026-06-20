const BADGE = {
  surging: 'bg-red-50 text-red-600',
  hot: 'bg-amber-50 text-amber-600',
  rising: 'bg-green-50 text-green-700',
  emerging: 'bg-blue-50 text-blue-500',
  stable: 'bg-gray-50 text-gray-400',
};

export default function Trends({ topics }) {
  if (!topics.length) return null;
  return (
    <div className="mb-9">
      <div className="text-[15px] font-bold text-gray-900 mb-3.5 pb-2 border-b border-gray-200">📡 Trending Topics</div>
      <table className="w-full border-collapse">
        <thead>
          <tr>
            {['#', 'Topic', 'Trend', 'Signal'].map(h => (
              <th key={h} className="text-[10px] uppercase tracking-wide text-gray-400 text-left px-3 py-2 border-b border-gray-200">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {topics.map((t, i) => (
            <tr key={i} className="hover:bg-gray-50 transition-colors">
              <td className="px-3 py-2.5 border-b border-gray-100 font-bold text-sm">{t.engagement_rank}</td>
              <td className="px-3 py-2.5 border-b border-gray-100 text-sm">{t.topic}</td>
              <td className="px-3 py-2.5 border-b border-gray-100">
                <span className={`inline-block px-2 py-0.5 text-[10px] font-semibold rounded uppercase tracking-wide ${BADGE[t.trend_direction] || BADGE.stable}`}>
                  {t.trend_direction}
                </span>
              </td>
              <td className="px-3 py-2.5 border-b border-gray-100 text-xs text-gray-400">{t.why || ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
