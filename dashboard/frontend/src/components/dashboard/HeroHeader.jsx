import { useEffect, useState } from 'react';
import { RotateCw, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const PERIODS = [
  { id: '7d',  label: 'Last 7 days' },
  { id: '30d', label: 'Last 30 days' },
  { id: '90d', label: 'Last 90 days' },
];

function formatRelative(date) {
  const seconds = Math.max(0, Math.round((Date.now() - date) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

export default function HeroHeader({ period, onPeriodChange, lastUpdated }) {
  const { user } = useAuth();
  const [, setTick] = useState(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const monthLabel = new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const currentPeriod = PERIODS.find(p => p.id === period) || PERIODS[1];

  return (
    <div className="dash-hero-header">
      <div className="dash-hero-header-left">
        <div className="dash-hero-greeting">
          Welcome back{user?.name ? `, ${user.name}` : ''}
          <span className="dash-hero-month"> · {monthLabel}</span>
        </div>
      </div>
      <div className="dash-hero-header-right">
        <div className="dash-period-selector">
          <button
            className="dash-period-btn"
            onClick={() => setOpen(o => !o)}
            aria-haspopup="listbox"
            aria-expanded={open}
          >
            {currentPeriod.label}
            <ChevronDown size={14} />
          </button>
          {open && (
            <ul className="dash-period-menu" role="listbox">
              {PERIODS.map(p => (
                <li
                  key={p.id}
                  role="option"
                  aria-selected={p.id === period}
                  className={`dash-period-option ${p.id === period ? 'is-active' : ''}`}
                  onClick={() => { onPeriodChange?.(p.id); setOpen(false); }}
                >
                  {p.label}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="dash-live-pill" title="Auto-refresh">
          <RotateCw size={12} className="dash-live-icon" />
          Updated {lastUpdated ? formatRelative(lastUpdated) : '—'}
        </div>
      </div>
    </div>
  );
}
