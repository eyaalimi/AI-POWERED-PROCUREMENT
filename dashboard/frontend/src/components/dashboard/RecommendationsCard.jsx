import { useNavigate } from 'react-router-dom';
import { Award } from 'lucide-react';

function scoreColor(score) {
  if (score >= 80) return 'var(--dash-accent-success)';
  if (score >= 60) return 'var(--dash-accent-warning)';
  return 'var(--dash-accent-danger)';
}

export default function RecommendationsCard({ recommendations = [] }) {
  const navigate = useNavigate();
  const top3 = recommendations.slice(0, 3);

  return (
    <div className="dash-card dash-recos">
      <div className="dash-card-header">
        <span className="dash-label">
          <Award size={12} style={{ marginRight: 4, verticalAlign: -1 }} />
          Top recommendations · this week
        </span>
      </div>

      {top3.length === 0 ? (
        <div className="dash-attention-empty">
          <p style={{ color: 'var(--dash-text-secondary)', fontSize: 13 }}>No evaluations yet.</p>
        </div>
      ) : (
        <ul className="dash-recos-list">
          {top3.map((r, idx) => (
            <li
              key={r.request_id || idx}
              className="dash-recos-row"
              onClick={() => navigate(`/request/${r.request_id}`)}
              tabIndex={0}
              role="button"
              onKeyDown={(e) => { if (e.key === 'Enter') navigate(`/request/${r.request_id}`); }}
            >
              <span className="dash-recos-rank">{idx + 1}</span>
              <div className="dash-recos-body">
                <div className="dash-recos-supplier">{r.supplier_name}</div>
                <div className="dash-recos-product">{r.product}</div>
              </div>
              <div className="dash-recos-score dash-num" style={{ color: scoreColor(r.overall_score || 0) }}>
                {(r.overall_score ?? 0).toFixed(0)}
                <span className="dash-recos-score-suffix">/100</span>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="dash-card-footer">
        <a className="dash-link" onClick={(e) => { e.preventDefault(); navigate('/reports'); }} href="/reports">
          View all evaluations →
        </a>
      </div>
    </div>
  );
}
