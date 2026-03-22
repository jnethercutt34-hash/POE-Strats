import { Link } from 'react-router-dom';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import TierBadge from './TierBadge';

function formatChaos(value) {
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
  return Math.round(value).toLocaleString();
}

export default function ProfitCard({ mechanic }) {
  const positive = mechanic.profit_per_hour >= 0;

  return (
    <Link
      to={`/mechanics/${mechanic.mechanic}`}
      className="block bg-[var(--poe-card)] border border-[var(--poe-border)] rounded-lg p-4 hover:border-[var(--poe-gold)]/40 transition-colors"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-white">{mechanic.mechanic}</h3>
          <TierBadge tier={mechanic.meta_tier} />
        </div>
        {mechanic.missing_prices > 0 && (
          <span className="text-xs text-yellow-500">⚠ {mechanic.missing_prices} missing</span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <p className="text-xs text-gray-500 uppercase">Revenue / Map</p>
          <p className="text-sm text-green-400">{formatChaos(mechanic.total_revenue_chaos)}c</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase">Cost / Map</p>
          <p className="text-sm text-red-400">{formatChaos(mechanic.total_cost_chaos)}c</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase">Profit / Map</p>
          <p className={`text-sm font-semibold ${positive ? 'text-green-400' : 'text-red-400'}`}>
            {formatChaos(mechanic.profit_per_map)}c
          </p>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-[var(--poe-border)] flex items-center justify-between">
        <span className="text-xs text-gray-500">Profit / Hour</span>
        <span className={`flex items-center gap-1 text-lg font-bold ${positive ? 'text-green-400' : 'text-red-400'}`}>
          {positive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
          {formatChaos(mechanic.profit_per_hour)}c/hr
        </span>
      </div>
    </Link>
  );
}
