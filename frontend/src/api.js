const BASE = '';

export async function fetchIdeas() {
  const r = await fetch(`${BASE}/api/ideas`);
  return r.ok ? r.json() : {};
}

export async function fetchPatterns() {
  const r = await fetch(`${BASE}/api/patterns`);
  return r.ok ? r.json() : {};
}

export async function fetchCollected() {
  const r = await fetch(`${BASE}/api/collected`);
  return r.ok ? r.json() : [];
}

export async function fetchSourceStatus() {
  const r = await fetch(`${BASE}/api/source-status`);
  return r.ok ? r.json() : {};
}

export async function fetchStatus() {
  const r = await fetch(`${BASE}/api/status`);
  return r.json();
}

export async function postGenerate(section) {
  const url = section ? `${BASE}/api/generate/${section}` : `${BASE}/api/generate`;
  const r = await fetch(url, { method: 'POST' });
  return r.json();
}

export async function postRefresh() {
  const r = await fetch(`${BASE}/api/refresh`, { method: 'POST' });
  return r.json();
}

export function fmtNum(n) {
  if (n == null) return '—';
  n = Number(n);
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return String(n);
}
