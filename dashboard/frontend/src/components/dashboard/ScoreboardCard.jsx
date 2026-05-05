import { ArrowUp, ArrowDown } from 'lucide-react';

const ACCENT_HEX = {
  primary: '#6366F1',
  success: '#10B981',
  warning: '#F59E0B',
  danger:  '#EF4444',
};

export default function ScoreboardCard({
  label,
  value,
  delta,
  improvementDirection = 'higher',
  deltaSuffix = '%',
  accent = 'primary',
  visual,
  alertText,
}) {
  const accentColor = ACCENT_HEX[accent] || ACCENT_HEX.primary;
  const goingUp = (delta ?? 0) >= 0;
  const isImprovement = improvementDirection === 'higher' ? goingUp : !goingUp;
  const deltaColor = delta == null
    ? 'var(--dash-text-muted)'
    : isImprovement ? 'var(--dash-accent-success)' : 'var(--dash-accent-danger)';

  return (
    <div className="dash-card dash-scorecard" style={{ '--dash-card-accent': accentColor }}>
      <div className="dash-scorecard-accent-line" />
      <div className="dash-label">{label}</div>
      <div className="dash-scorecard-value dash-num">{value}</div>
      <div className="dash-scorecard-delta" style={{ color: deltaColor }}>
        {delta != null && (
          <>
            {goingUp ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
            <span className="dash-num">{Math.abs(delta)}{deltaSuffix}</span>
          </>
        )}
        {alertText && <span style={{ marginLeft: 8 }}>{alertText}</span>}
      </div>
      <div className="dash-scorecard-visual">{visual}</div>
    </div>
  );
}
