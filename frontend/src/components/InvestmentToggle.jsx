const tiers = ['low', 'medium', 'high'];

export default function InvestmentToggle({ value, onChange }) {
  return (
    <div className="flex rounded-lg overflow-hidden border border-[var(--poe-border)]">
      {tiers.map((tier) => (
        <button
          key={tier}
          onClick={() => onChange(tier)}
          className={`px-4 py-1.5 text-sm font-medium capitalize transition-colors
            ${value === tier
              ? 'bg-[var(--poe-gold)]/20 text-[var(--poe-gold)]'
              : 'bg-[var(--poe-card)] text-gray-400 hover:text-gray-200'
            }`}
        >
          {tier}
        </button>
      ))}
    </div>
  );
}
