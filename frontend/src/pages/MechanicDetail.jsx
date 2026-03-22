import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react';
import TierBadge from '../components/TierBadge';
import InvestmentToggle from '../components/InvestmentToggle';

function formatChaos(v) {
  if (v >= 1000) return `${(v / 1000).toFixed(1)}k`;
  return v.toFixed(1);
}

export default function MechanicDetail() {
  const { name } = useParams();
  const [investment, setInvestment] = useState('medium');
  const [mapsPerHour, setMapsPerHour] = useState(12);
  const [data, setData] = useState(null);
  const [overrides, setOverrides] = useState({});
  const [loading, setLoading] = useState(true);

  const fetchProfit = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/profit/${name}?investment=${investment}&maps_per_hour=${mapsPerHour}`);
      const json = await res.json();
      setData(json);
      setOverrides({});  // Reset overrides on new fetch
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [name, investment, mapsPerHour]);

  useEffect(() => { fetchProfit(); }, [fetchProfit]);

  // Recalculate with overrides (client-side)
  const getAdjustedRevenue = (item) => {
    const yield_ = overrides[item.item_name] !== undefined 
      ? overrides[item.item_name] 
      : item.yield_per_map;
    return yield_ * item.chaos_value;
  };

  const totalRevenue = data?.revenue_breakdown?.reduce(
    (sum, item) => sum + getAdjustedRevenue(item), 0
  ) || 0;
  const totalCost = data?.total_cost_chaos || 0;
  const profitPerMap = totalRevenue - totalCost;
  const profitPerHour = profitPerMap * mapsPerHour;
  const positive = profitPerHour >= 0;

  if (loading && !data) {
    return <div className="max-w-5xl mx-auto px-4 py-12 text-gray-500 text-center">Loading...</div>;
  }

  if (!data) return null;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Back + Header */}
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-gray-400 hover:text-[var(--poe-gold)] mb-4">
        <ArrowLeft size={14} /> Back to Dashboard
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-white">{data.mechanic}</h1>
          <TierBadge tier={data.meta_tier} />
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
            />
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-[var(--poe-card)] border border-[var(--poe-border)] rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase mb-1">Revenue / Map</p>
          <p className="text-xl font-bold text-green-400">{formatChaos(totalRevenue)}c</p>
        </div>
        <div className="bg-[var(--poe-card)] border border-[var(--poe-border)] rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase mb-1">Cost / Map</p>
          <p className="text-xl font-bold text-red-400">{formatChaos(totalCost)}c</p>
        </div>
        <div className="bg-[var(--poe-card)] border border-[var(--poe-border)] rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase mb-1">Profit / Map</p>
          <p className={`text-xl font-bold ${positive ? 'text-green-400' : 'text-red-400'}`}>
            {formatChaos(profitPerMap)}c
          </p>
        </div>
        <div className="bg-[var(--poe-card)] border border-[var(--poe-gold)]/30 rounded-lg p-4">
          <p className="text-xs text-[var(--poe-gold)] uppercase mb-1">Profit / Hour</p>
          <p className={`text-2xl font-bold flex items-center gap-1 ${positive ? 'text-green-400' : 'text-red-400'}`}>
            {positive ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
            {formatChaos(profitPerHour)}c
          </p>
        </div>
      </div>

      {/* Revenue Breakdown — The Variable Engine */}
      <div className="bg-[var(--poe-card)] border border-[var(--poe-border)] rounded-lg overflow-hidden mb-6">
        <div className="px-4 py-3 border-b border-[var(--poe-border)]">
          <h2 className="text-sm font-semibold text-[var(--poe-gold)] uppercase">
            Revenue Breakdown — Adjust Your Yields
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            Override the default yields with your actual numbers to get personalized profit calculations.
          </p>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase">
              <th className="px-4 py-2 text-left">Item</th>
              <th className="px-4 py-2 text-right">Price</th>
              <th className="px-4 py-2 text-center">Yield / Map</th>
              <th className="px-4 py-2 text-right">Revenue</th>
            </tr>
          </thead>
          <tbody>
            {data.revenue_breakdown.map((item, i) => {
              const currentYield = overrides[item.item_name] !== undefined
                ? overrides[item.item_name]
                : item.yield_per_map;
              const revenue = currentYield * item.chaos_value;
              const isOverridden = overrides[item.item_name] !== undefined;
              return (
                <tr key={i} className="border-t border-[var(--poe-border)]/50 hover:bg-white/[0.02]">
                  <td className="px-4 py-2 text-gray-200">{item.item_name}</td>
                  <td className="px-4 py-2 text-right text-gray-400">{item.chaos_value.toFixed(1)}c</td>
                  <td className="px-4 py-2">
                    <input
                      type="number"
                      value={currentYield}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        setOverrides(prev => ({ ...prev, [item.item_name]: val }));
                      }}
                      step="0.1"
                      min="0"
                      className={`w-20 mx-auto block text-center rounded px-2 py-1 text-sm border
                        ${isOverridden
                          ? 'bg-[var(--poe-gold)]/10 border-[var(--poe-gold)]/30 text-[var(--poe-gold)]'
                          : 'bg-[var(--poe-card)] border-[var(--poe-border)] text-gray-300'
                        }`}
                    />
                  </td>
                  <td className="px-4 py-2 text-right font-medium text-green-400">
                    {formatChaos(revenue)}c
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Cost Breakdown */}
      <div className="bg-[var(--poe-card)] border border-[var(--poe-border)] rounded-lg overflow-hidden mb-6">
        <div className="px-4 py-3 border-b border-[var(--poe-border)]">
          <h2 className="text-sm font-semibold text-red-400 uppercase">Cost Breakdown</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase">
              <th className="px-4 py-2 text-left">Item</th>
              <th className="px-4 py-2 text-right">Price</th>
              <th className="px-4 py-2 text-center">Qty</th>
              <th className="px-4 py-2 text-right">Total</th>
              <th className="px-4 py-2 text-right">Source</th>
            </tr>
          </thead>
          <tbody>
            {data.cost_breakdown.map((cost, i) => (
              <tr key={i} className="border-t border-[var(--poe-border)]/50">
                <td className="px-4 py-2 text-gray-200">{cost.item_name}</td>
                <td className="px-4 py-2 text-right text-gray-400">{cost.chaos_value.toFixed(1)}c</td>
                <td className="px-4 py-2 text-center text-gray-400">{cost.quantity}</td>
                <td className="px-4 py-2 text-right font-medium text-red-400">{cost.total_cost.toFixed(1)}c</td>
                <td className="px-4 py-2 text-right">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    cost.source === 'live' ? 'bg-green-500/10 text-green-400' :
                    cost.source === 'fixed' ? 'bg-gray-500/10 text-gray-400' :
                    'bg-yellow-500/10 text-yellow-400'
                  }`}>
                    {cost.source}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Missing Prices Warning */}
      {data.missing_prices.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 text-sm text-yellow-400">
          <strong>Missing price data:</strong> {data.missing_prices.join(', ')}
        </div>
      )}
    </div>
  );
}
