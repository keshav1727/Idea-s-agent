export default function Toast({ msg, type }) {
  const color = type === 'error' ? 'border-red-500 text-red-600' : type === 'success' ? 'border-green-600 text-green-700' : 'border-gray-200 text-gray-700';
  return (
    <div className={`fixed top-4 right-4 z-[999] px-5 py-3 text-sm bg-white border rounded-lg shadow-md animate-[slideIn_.25s_ease] ${color}`}>
      {msg}
    </div>
  );
}
