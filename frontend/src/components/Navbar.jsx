import { Link, useLocation } from 'react-router-dom';
import { TrendingUp, BarChart3, Pickaxe } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: BarChart3 },
  { to: '/mechanics', label: 'Mechanics', icon: Pickaxe },
  { to: '/economy', label: 'Economy', icon: TrendingUp },
];

export default function Navbar() {
  const location = useLocation();

  return (
    <nav className="border-b border-[var(--poe-border)] bg-[var(--poe-card)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-[var(--poe-gold)] font-bold text-xl">⚔ POE MetaTracker</span>
          </Link>
          <div className="flex gap-1">
            {navItems.map(({ to, label, icon: Icon }) => {
              const active = location.pathname === to || 
                (to !== '/' && location.pathname.startsWith(to));
              return (
                <Link
                  key={to}
                  to={to}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors
                    ${active
                      ? 'bg-[var(--poe-gold)]/10 text-[var(--poe-gold)]'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                    }`}
                >
                  <Icon size={16} />
                  {label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
