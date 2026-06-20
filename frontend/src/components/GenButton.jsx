import { useState } from 'react';
import { postGenerate, fetchStatus } from '../api';

export default function GenButton({ label, section, onDone, showToast }) {
  const [running, setRunning] = useState(false);

  const handleClick = async () => {
    if (running) return;
    setRunning(true);
    showToast(`${label}...`, '');

    try {
      const res = await postGenerate(section);
      if (res.status === 'already_running') {
        showToast('Another task is running...', 'error');
        setRunning(false);
        return;
      }
      const poll = setInterval(async () => {
        const st = await fetchStatus();
        if (!st.running) {
          clearInterval(poll);
          setRunning(false);
          if (st.error) showToast(`Error: ${st.error}`, 'error');
          else { showToast('Done!', 'success'); onDone(); }
        }
      }, 2000);
    } catch (e) {
      showToast(`Failed: ${e.message}`, 'error');
      setRunning(false);
    }
  };

  return (
    <button
      className={`ml-auto px-4 py-1.5 text-xs font-semibold rounded transition-all inline-flex items-center gap-1.5 ${
        running
          ? 'bg-gray-50 text-gray-400 border border-gray-200 cursor-wait'
          : 'bg-blue-500 text-white hover:bg-blue-600 cursor-pointer'
      }`}
      onClick={handleClick}
      disabled={running}
    >
      {running && <span className="w-3 h-3 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin inline-block" />}
      {!running && <span>⚡</span>}
      {running ? 'Working...' : label}
    </button>
  );
}
