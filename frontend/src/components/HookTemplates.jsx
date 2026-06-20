import GenButton from './GenButton';

export default function HookTemplates({ hooks, onGenerated, showToast }) {
  return (
    <div className="mb-9">
      <div className="flex items-center gap-2 text-[15px] font-bold text-gray-900 mb-3.5 pb-2 border-b border-gray-200">
        🪝 Hook Templates
        <span className="text-[11px] font-medium text-gray-400 bg-gray-50 border border-gray-200 px-2 py-0.5 rounded-full">{hooks.length}</span>
        <GenButton label="Generate Hooks" section="hooks" onDone={onGenerated} showToast={showToast} />
      </div>
      {hooks.length === 0 && <div className="p-5 text-gray-400 text-sm">No hooks generated yet.</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {hooks.map((hook, i) => (
          <div key={i} className="flex gap-2.5 p-3 text-xs text-gray-500 leading-relaxed bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors">
            <span className="font-bold text-gray-400 min-w-[20px]">{i + 1}.</span>
            <span dangerouslySetInnerHTML={{
              __html: hook.replace(/\[([^\]]+)\]/g, '<span class="text-blue-500 font-semibold">[$1]</span>')
            }} />
          </div>
        ))}
      </div>
    </div>
  );
}
