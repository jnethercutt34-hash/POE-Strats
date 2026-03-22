const tierColors = {
  S: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
  A: 'bg-purple-500/20 text-purple-400 border-purple-500/40',
  B: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
  C: 'bg-gray-500/20 text-gray-400 border-gray-500/40',
};

export default function TierBadge({ tier }) {
  if (!tier) return null;
  const colors = tierColors[tier] || tierColors.C;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold border ${colors}`}>
      {tier}
    </span>
  );
}
