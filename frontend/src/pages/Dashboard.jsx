import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import ProfitCard from '../components/ProfitCard';
import InvestmentToggle from '../components/InvestmentToggle';
import { RefreshCw } from 'lucide-react';

export default function Dashboard() {
  const [investment, setInvestment] = useState('medium');
  const [mapsPerHour, setMapsPerHour] = useState(12);
  const { data, loading, error, refetch } = useApi(
    `/api/profit/?investment=${investment}&maps_per_hour=${mapsPerHour}`
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Meta Tracker</h1>
          <p className="text-gray-400 mt-1">Real-time mechanic profitability rankings</p>
        </div>
        <div className="flex items-center gap-4">
          <InvestmentToggle value={investment} onChange={setInvestment} />
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">Maps/hr</label>
            <input
              type="number"
              value={mapsPerHour}
              onChange={(e) => setMapsPerHour(Math.max(1, Math.min(60, Number(e.target.value))))}
              className="w-16 bg-[var(--poe-card)] border border-[var(--poe-border)] rounded px-2 py-1 text-sm text-white text-center"
              min="1"
              max="60"
            />
          </div>
          <button
            onClick={refetch}
            className="p-2 text-gray-400 hover:text-[var(--poe-gold)] transition-colors"
            title="Refresh"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6 text-red-400">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && !data && (
        <div className="text-center py-12 text-gray-500">Loading profit data...</div>
      )}

      {/* Mechanic Grid */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.mechanics.map((m) => (
            <ProfitCard key={m.mechanic} mechanic={m} />
          ))}
        </div>
      )}
    </div>
  );
}
