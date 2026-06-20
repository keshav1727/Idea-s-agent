import { useState } from 'react';
import { fmtNum } from '../api';

const ICONS = { youtube: '▶️', reddit: '💬', news: '📰', social: '🌐', twitter: '🐦' };
const ALL_SOURCES = ['youtube', 'reddit', 'news', 'twitter'];

export default function FetchedPage({ collected, sourceStatus, refreshing }) {
  const [filter, setFilter] = useState('all');

  if (refreshing && !collected.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] gap-3 pt-6">
        <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
        <p className="text-sm text-gray-500">Scraping fresh data from all platforms...</p>
      </div>
    );
  }

  if (!collected.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] gap-3 pt-6">
        <p className="text-base font-semibold text-gray-500">No data yet</p>
        <p className="text-sm text-gray-400">Data will auto-refresh when you open this page.</p>
      </div>
    );
  }

  const platforms = {};
  collected.forEach(i => { platforms[i.platform] = (platforms[i.platform] || 0) + 1; });
  const filtered = filter === 'all' ? collected : collected.filter(i => i.platform === filter);

  return (
    <div className="pt-6">
      {/* Stats */}
      <div className="flex gap-3 mb-7 flex-wrap">
        <StatCard num={collected.length} label="Total scraped" />
        {ALL_SOURCES.map(src => {
          const count = platforms[src] || 0;
          return (
            <StatCard
              key={src}
              num={count || 'Unavailable'}
              label={`${src} ${count ? '✓' : '✗'}`}
              ok={count > 0}
            />
          );
        })}
      </div>

      {refreshing && (
        <div className="flex items-center gap-2 mb-4 text-sm text-blue-500">
          <span className="w-3 h-3 border-2 border-blue-200 border-t-blue-500 rounded-full animate-spin inline-block" />
          Refreshing data...
        </div>
      )}

      {/* Filters */}
      <div className="mb-9">
        <div className="flex items-center gap-2 text-[15px] font-bold text-gray-900 mb-3.5 pb-2 border-b border-gray-200">
          Scraped Viral Content
          <span className="text-[11px] font-medium text-gray-400 bg-gray-50 border border-gray-200 px-2 py-0.5 rounded-full">Last 90 days</span>
        </div>
        <div className="flex gap-1.5 mb-3 flex-wrap">
          <FilterBtn active={filter === 'all'} onClick={() => setFilter('all')}>All</FilterBtn>
          {Object.keys(platforms).map(p => (
            <FilterBtn key={p} active={filter === p} onClick={() => setFilter(p)}>{p}</FilterBtn>
          ))}
        </div>
        <div className="grid gap-1.5">
          {filtered.slice(0, 60).map((item, i) => <ContentItem key={i} item={item} />)}
        </div>
      </div>
    </div>
  );
}

function StatCard({ num, label, ok }) {
  const numColor = ok === false ? 'text-red-600 text-sm' : 'text-gray-900';
  const labelColor = ok === false ? 'text-red-500' : ok ? 'text-green-700' : 'text-gray-400';
  return (
    <div className="flex-1 min-w-[120px] p-3.5 bg-gray-50 border border-gray-200 rounded-lg">
      <div className={`text-2xl font-bold ${numColor}`}>{num}</div>
      <div className={`text-[11px] uppercase tracking-wide ${labelColor}`}>{label}</div>
    </div>
  );
}

function FilterBtn({ active, onClick, children }) {
  return (
    <button
      className={`px-3.5 py-1 text-xs font-medium rounded cursor-pointer transition-all border ${
        active ? 'bg-blue-50 border-blue-500 text-blue-600' : 'bg-gray-50 border-gray-200 text-gray-400 hover:text-gray-600'
      }`}
      onClick={onClick}
    >{children}</button>
  );
}

function ContentItem({ item }) {
  const p = item.platform || 'news';
  const raw = item.engagement_raw || {};
  const title = (item.title || '').split('\n')[0];
  const kws = (item.source_keywords || []).slice(0, 3);
  const date = item.published_at ? new Date(item.published_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';

  return (
    <div className="grid grid-cols-[52px_1fr_auto] gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg items-start hover:bg-gray-100 transition-colors">
      <div className="text-center text-[10px] font-semibold uppercase text-gray-400 tracking-wide">
        <div className="text-lg mb-0.5">{ICONS[p] || '📄'}</div>
        {p}
      </div>
      <div className="min-w-0">
        <div className="text-[13px] font-semibold text-gray-900 leading-snug mb-1">
          <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-500 transition-colors">{title}</a>
        </div>
        {item.description && (
          <div className="text-[11px] text-gray-400 leading-snug mb-1 line-clamp-1">{item.description.split('\n')[0]}</div>
        )}
        <div className="flex gap-1 flex-wrap">
          {kws.map(k => <span key={k} className="text-[10px] px-1.5 bg-blue-50 text-blue-500 rounded">{k}</span>)}
          {date && <span className="text-[10px] px-1.5 bg-blue-50 text-blue-500 rounded">{date}</span>}
        </div>
      </div>
      <div className="flex gap-3.5 min-w-[140px] flex-wrap">
        {p === 'youtube' && <><Met val={raw.views} label="views" /><Met val={raw.likes} label="likes" /><Met val={raw.comments} label="comments" /></>}
        {p === 'reddit' && <><Met val={raw.score} label="upvotes" /><Met val={raw.num_comments} label="comments" /></>}
        {p === 'twitter' && <><Met val={raw.likes} label="likes" /><Met val={raw.retweets} label="RTs" /></>}
      </div>
    </div>
  );
}

function Met({ val, label }) {
  return (
    <div className="text-right">
      <div className="text-sm font-bold text-gray-900">{fmtNum(val)}</div>
      <div className="text-[9px] text-gray-400 uppercase tracking-wide">{label}</div>
    </div>
  );
}
