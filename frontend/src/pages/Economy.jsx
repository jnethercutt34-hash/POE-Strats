import { useApi } from '../hooks/useApi';
import { RefreshCw } from 'lucide-react';

function formatChaos(v) {
  if (!v) return '—';
  if (v >= 1000) return `${(v / 1000).toFixed(1)}k`;
  return v.toFixed(1);
}

export default function Economy() {
  const { data, loading, error, refetch } = useApi('/api/economy/');

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Economy</h1>
          <p className="text-gray-400 mt-1">Top 50 most valuable items from poe.ninja</p>
        </div>
        <button
          onClick={refetch}
          className="p-2 text-gray-400 hover:text-[var(--poe-gold)] transition-colors"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6 text-red-400">{error}</div>
      )}

      {loading && !data && (
        <div className="text-center py-12 text-gray-500">Loading economy data...</div>
      )}

      {data && (
        <div className="bg-[var(--poe-card)] border border-[var(--poe-border)] rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase border-b border-[var(--poe-border)]">
                <th className="px-4 py-3 text-left">#</th>
                <th className="px-4 py-3 text-left">Item</th>
                <th className="px-4 py-3 text-left">Type</th>
                <th className="px-4 py-3 text-right">Chaos Value</th>
                <th className="px-4 py-3 text-right">Divine Value</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item, i) => (
                <tr key={i} className="border-t border-[var(--poe-border)]/50 hover:bg-white/[0.02]">
                  <td className="px-4 py-2 text-gray-500">{i + 1}</td>
                  <td className="px-4 py-2 text-gray-200 font-medium">{item.item_name}</td>
                  <td className="px-4 py-2">
                    <span className="text-xs bg-white/5 text-gray-400 px-2 py-0.5 rounded">
                      {item.ninja_type}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-right text-[var(--poe-gold)]">
                    {formatChaos(item.chaos_value)}c
                  </td>
                  <td className="px-4 py-2 text-right text-gray-400">
                    {item.divine_value ? `${item.divine_value.toFixed(2)}d` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
