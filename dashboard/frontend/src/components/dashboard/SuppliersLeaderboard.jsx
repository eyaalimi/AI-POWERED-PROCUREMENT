import { useNavigate } from 'react-router-dom';
import { MOCK_TOP_SUPPLIERS } from '../../mocks/dashboardMocks';

function scoreColor(score) {
  if (score >= 80) return 'var(--dash-accent-success)';
  if (score >= 60) return 'var(--dash-accent-warning)';
  return 'var(--dash-accent-danger)';
}

function relativeDays(days) {
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  return `${days}d ago`;
}

export default function SuppliersLeaderboard({ rows = MOCK_TOP_SUPPLIERS }) {
  const navigate = useNavigate();
  return (
    <div className="dash-card dash-suppliers">
      <div className="dash-card-header">
        <span className="dash-label">Top suppliers · last 30 days</span>
        <a className="dash-link" href="/suppliers" onClick={(e) => { e.preventDefault(); navigate('/suppliers'); }}>
          View all →
        </a>
      </div>

      <table className="dash-suppliers-table">
        <thead>
          <tr>
            <th style={{ width: 36 }}>#</th>
            <th>Supplier</th>
            <th style={{ width: 140 }}>Category</th>
            <th style={{ width: 140 }}>Response rate</th>
            <th style={{ width: 80, textAlign: 'right' }}>Score</th>
            <th style={{ width: 100 }}>Last seen</th>
            <th style={{ width: 32 }}></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((s, i) => (
            <tr key={s.id}>
              <td className="dash-num">{i + 1}</td>
              <td>
                <div className="dash-suppliers-name">{s.name}</div>
                <div className="dash-suppliers-email">{s.email}</div>
              </td>
              <td>
                <span className="dash-tag">{s.category}</span>
              </td>
              <td>
                <div className="dash-suppliers-bar-track">
                  <div className="dash-suppliers-bar-fill" style={{ width: `${s.responseRate}%` }} />
                </div>
                <div className="dash-suppliers-bar-label dash-num">{s.responseRate}%</div>
              </td>
              <td className="dash-num" style={{ textAlign: 'right', fontSize: 16, fontWeight: 700, color: scoreColor(s.avgScore) }}>
                {s.avgScore.toFixed(1)}
              </td>
              <td className="dash-suppliers-last">{relativeDays(s.lastInteractionDays)}</td>
              <td>
                <button className="dash-suppliers-chev" onClick={() => navigate('/suppliers')} aria-label="Open supplier">→</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
