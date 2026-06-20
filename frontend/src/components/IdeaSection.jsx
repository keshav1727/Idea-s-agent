import { useState } from 'react';
import GenButton from './GenButton';

export default function IdeaSection({ title, items, icon, section, btnLabel, onGenerated, showToast }) {
  return (
    <div className="mb-9">
      <div className="flex items-center gap-2 text-[15px] font-bold text-gray-900 mb-3.5 pb-2 border-b border-gray-200">
        {title}
        <span className="text-[11px] font-medium text-gray-400 bg-gray-50 border border-gray-200 px-2 py-0.5 rounded-full">{items.length}</span>
        <GenButton label={btnLabel} section={section} onDone={onGenerated} showToast={showToast} />
      </div>
      <div className="grid gap-2.5">
        {items.length === 0 && <div className="p-5 text-gray-400 text-sm">No ideas generated yet. Click Generate.</div>}
        {items.map((idea, i) => <IdeaCard key={i} idea={idea} index={i} total={items.length} icon={icon} />)}
      </div>
    </div>
  );
}

function IdeaCard({ idea, index, total, icon }) {
  const [open, setOpen] = useState(false);
  const outline = idea.script_outline || idea.tweets || [];

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden hover:shadow-sm transition-shadow">
      <div className="flex items-center gap-3 px-4 py-3.5 cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="text-xl w-8 text-center shrink-0">{icon}</div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] text-gray-400 uppercase tracking-wide">Idea {index + 1} of {total}</div>
          <div className="text-sm font-semibold text-gray-900 truncate">{idea.topic || ''}</div>
        </div>
        <div className={`text-xs text-gray-400 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}>▼</div>
      </div>
      {open && (
        <div className="px-4 pb-4 pl-16">
          <Field label="Hook" value={idea.hook} bold />
          <Field label="Angle / Storyline" value={idea.angle} />
          {idea.why_it_works && <Field label="Why it works" value={idea.why_it_works} muted />}
          {outline.length > 0 && (
            <div className="mb-3.5">
              <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">{idea.tweets ? 'Full Thread' : 'Script Outline'}</div>
              <div className="bg-white border border-gray-200 rounded-lg p-3 mt-1">
                {outline.map((step, j) => (
                  <div key={j} className="flex gap-2.5 py-1 text-xs text-gray-500">
                    <span className="font-bold text-blue-500 min-w-[18px]">{j + 1}.</span>
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Field({ label, value, bold, muted }) {
  if (!value) return null;
  const cls = bold ? 'text-sm font-semibold text-gray-900 leading-relaxed' : muted ? 'text-xs text-gray-400 italic leading-relaxed' : 'text-[13px] text-gray-500 leading-relaxed';
  return (
    <div className="mb-3.5">
      <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">{label}</div>
      <div className={cls}>{value}</div>
    </div>
  );
}
