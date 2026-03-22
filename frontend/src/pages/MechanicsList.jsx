import { Link } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import TierBadge from '../components/TierBadge';
import { ChevronRight } from 'lucide-react';

export default function MechanicsList() {
  const { data, loading, error } = useApi('/api/mechanics/');

  if (loading) return <div className="max-w-5xl mx-auto px-4 py-12 text-gray-500 text-center">Loading...</div>;
  if (error) return <div className="max-w-5xl mx-auto px-4 py-12 text-red-400">{error}</div>;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-2">Mechanics</h1>
      <p className="text-gray-400 mb-8">All tracked PoE mechanics with meta tier and scaling info.</p>

      <div className="space-y-2">
        {data.mechanics.map((m) => {
          const tags = JSON.parse(m.scaling_tags || '[]');
          return (
            <Link
              key={m.id}
              to={`/mechanics/${m.name}`}
              className="flex items-center justify-between bg-[var(--poe-card)] border border-[var(--poe-border)] rounded-lg px-4 py-3 hover:border-[var(--poe-gold)]/40 transition-colors"
            >
              <div className="flex items-center gap-3">
                <TierBadge tier={m.meta_tier} />
                <span className="text-white font-medium">{m.name}</span>
                <div className="flex gap-1.5">
                  {tags.map((tag) => (
                    <span key={tag} className="text-xs bg-white/5 text-gray-400 px-2 py-0.5 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              <ChevronRight size={16} className="text-gray-500" />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
