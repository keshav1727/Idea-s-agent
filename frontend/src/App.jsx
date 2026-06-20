import { useState, useEffect, useCallback } from 'react';
import { fetchIdeas, fetchPatterns, fetchCollected, fetchSourceStatus, postRefresh, fetchStatus } from './api';
import Topbar from './components/Topbar';
import FetchedPage from './components/FetchedPage';
import GeneratedPage from './components/GeneratedPage';
import Toast from './components/Toast';

export default function App() {
  const [tab, setTab] = useState('fetched');
  const [collected, setCollected] = useState([]);
  const [ideas, setIdeas] = useState({});
  const [patterns, setPatterns] = useState({});
  const [sourceStatus, setSourceStatus] = useState({});
  const [toast, setToast] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadAll = useCallback(async () => {
    const [c, i, p, s] = await Promise.all([
      fetchCollected(), fetchIdeas(), fetchPatterns(), fetchSourceStatus(),
    ]);
    setCollected(c);
    setIdeas(i);
    setPatterns(p);
    setSourceStatus(s);
  }, []);

  // Auto-refresh fetched data on page load
  useEffect(() => {
    setRefreshing(true);
    postRefresh().then(() => {
      const poll = setInterval(async () => {
        const st = await fetchStatus();
        if (!st.running) {
          clearInterval(poll);
          setRefreshing(false);
          loadAll();
        }
      }, 2000);
    }).catch(() => {
      setRefreshing(false);
      loadAll();
    });
  }, [loadAll]);

  const showToast = (msg, type) => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  return (
    <div className="max-w-[1100px] mx-auto px-6 pb-16">
      <Topbar tab={tab} setTab={setTab} />
      {tab === 'fetched' && (
        <FetchedPage
          collected={collected}
          sourceStatus={sourceStatus}
          refreshing={refreshing}
        />
      )}
      {tab === 'generated' && (
        <GeneratedPage
          ideas={ideas}
          patterns={patterns}
          onGenerated={loadAll}
          showToast={showToast}
        />
      )}
      {toast && <Toast msg={toast.msg} type={toast.type} />}
    </div>
  );
}
