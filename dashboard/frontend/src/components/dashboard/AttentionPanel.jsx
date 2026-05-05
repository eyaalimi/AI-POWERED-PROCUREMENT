import { AlertTriangle, Clock, DollarSign, RefreshCw, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const CATEGORY_META = {
  APPROVAL:  { Icon: AlertTriangle, severityClass: 'is-warning' },
  STUCK:     { Icon: Clock,         severityClass: 'is-danger'  },
  BUDGET:    { Icon: DollarSign,    severityClass: 'is-danger'  },
  RELAUNCH:  { Icon: RefreshCw,     severityClass: 'is-warning' },
};

export default function AttentionPanel({ items = [] }) {
  const navigate = useNavigate();

  return (
    <div className="dash-card dash-attention">
      <div className="dash-card-header">
        <span className="dash-label">Needs your attention</span>
        <span className="dash-pill">{items.length} {items.length === 1 ? 'item' : 'items'}</span>
      </div>

      {items.length === 0 ? (
        <div className="dash-attention-empty">
          <CheckCircle size={28} color="var(--dash-accent-success)" />
          <p>Everything is on track. Nothing requires your attention.</p>
        </div>
      ) : (
        <ul className="dash-attention-list">
          {items.map(item => {
            const meta = CATEGORY_META[item.category] || CATEGORY_META.APPROVAL;
            const { Icon } = meta;
            return (
              <li key={item.id} className={`dash-attention-row ${meta.severityClass}`}>
                <div className="dash-attention-tag">
                  <Icon size={14} />
                  <span>{item.category}</span>
                </div>
                <div className="dash-attention-body">
                  <div className="dash-attention-title">{item.title}</div>
                  <div className="dash-attention-sub">{item.subtitle}</div>
                </div>
                <button
                  className="dash-attention-action"
                  onClick={() => navigate(item.actionHref)}
                >
                  {item.actionLabel} →
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
