import { MOCK_CATEGORY_SPEND } from '../../mocks/dashboardMocks';

function formatTND(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M TND`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K TND`;
  return `${n} TND`;
}

export default function CategoryBreakdown({ rows = MOCK_CATEGORY_SPEND }) {
  const max = Math.max(...rows.map(r => r.amount), 1);
  return (
    <div className="dash-card dash-cats">
      <div className="dash-card-header">
        <span className="dash-label">Spend by category</span>
      </div>
      <ul className="dash-cats-list">
        {rows.map(r => {
          const pct = (r.amount / max) * 100;
          return (
            <li key={r.category} className="dash-cats-row">
              <span className="dash-cats-name">{r.category}</span>
              <span className="dash-cats-bar-track">
                <span className="dash-cats-bar-fill" style={{ width: `${pct}%` }} />
              </span>
              <span className="dash-cats-amount dash-num">{formatTND(r.amount)}</span>
            </li>
          );
        })}
      </ul>
      <div className="dash-card-footer">
        <a className="dash-link" href="#" onClick={e => e.preventDefault()}>View all categories →</a>
      </div>
    </div>
  );
}
