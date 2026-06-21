import { useState } from 'react';
import GenButton from './GenButton';

export default function ScriptSection({ reelScripts, videoScripts, onGenerated, showToast }) {
  const hasScripts = (reelScripts?.length > 0) || (videoScripts?.length > 0);

  return (
    <div className="mb-9">
      <div className="flex items-center gap-2 text-[15px] font-bold text-gray-900 mb-3.5 pb-2 border-b border-gray-200">
        📝 Script Outlines
        <span className="text-[11px] font-medium text-gray-400 bg-gray-50 border border-gray-200 px-2 py-0.5 rounded-full">
          {(reelScripts?.length || 0) + (videoScripts?.length || 0)}
        </span>
        <GenButton label="Generate Scripts" section="scripts" onDone={onGenerated} showToast={showToast} />
      </div>

      {!hasScripts && (
        <div className="p-5 text-gray-400 text-sm">No scripts generated yet. Generate ideas first, then click Generate Scripts.</div>
      )}

      {reelScripts?.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">📸 Reel Scripts</h3>
          <div className="grid gap-3">
            {reelScripts.map((s, i) => <ScriptCard key={i} script={s} index={i} type="reel" />)}
          </div>
        </div>
      )}

      {videoScripts?.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">▶️ Video Scripts</h3>
          <div className="grid gap-3">
            {videoScripts.map((s, i) => <ScriptCard key={i} script={s} index={i} type="video" />)}
          </div>
        </div>
      )}
    </div>
  );
}

function ScriptCard({ script, index, type }) {
  const [open, setOpen] = useState(false);
  const beats = script.script || [];
  const icon = type === 'reel' ? '📸' : '▶️';

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 cursor-pointer" onClick={() => setOpen(!open)}>
        <span className="text-lg">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] text-gray-400 uppercase tracking-wide">Script {index + 1}</div>
          <div className="text-sm font-semibold text-gray-900 truncate">{script.topic || 'Untitled'}</div>
        </div>
        <div className={`text-xs text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}>▼</div>
      </div>
      {open && (
        <div className="px-4 pb-4 pl-12">
          <div className="bg-white border border-gray-200 rounded-lg p-3">
            {beats.map((beat, j) => (
              <div key={j} className="flex gap-2.5 py-1.5 text-xs text-gray-600 border-b border-gray-100 last:border-0">
                <span className="font-bold text-blue-500 min-w-[24px] shrink-0">{j + 1}.</span>
                <span className="whitespace-pre-wrap">{beat}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
