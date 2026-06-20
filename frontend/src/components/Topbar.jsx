export default function Topbar({ tab, setTab }) {
  const tabClass = (t) =>
    `px-5 py-2 text-sm font-medium rounded cursor-pointer transition-all ${
      tab === t ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-400 hover:text-gray-600'
    }`;

  return (
    <div className="flex items-center justify-between py-5 border-b border-gray-200 sticky top-0 bg-white z-50">
      <div className="text-lg font-bold text-gray-900">
        Viral<span className="text-blue-500">Crypto</span>Ideas
      </div>
      <div className="flex gap-0.5 bg-gray-50 border border-gray-200 rounded-lg p-1">
        <button className={tabClass('fetched')} onClick={() => setTab('fetched')}>Fetched Data</button>
        <button className={tabClass('generated')} onClick={() => setTab('generated')}>Generated Ideas</button>
      </div>
    </div>
  );
}
