import { CheckCircle, Clock, AlertCircle, Circle } from 'lucide-react';

const stageConfig = {
  done:    { icon: CheckCircle, color: '#10b981', bg: '#ecfdf5', label: 'Done' },
  active:  { icon: Clock,       color: '#f59e0b', bg: '#fffbeb', label: 'In progress' },
  pending: { icon: Circle,      color: '#94a3b8', bg: '#f1f5f9', label: 'Pending' },
  error:   { icon: AlertCircle, color: '#ef4444', bg: '#fef2f2', label: 'Error' },
  skipped: { icon: Circle,      color: '#cbd5e1', bg: '#f8fafc', label: 'Skipped' },
};

export default function StageIndicator({ stages }) {
  const stageNames = {
    analysis: 'Analysis',
    sourcing: 'Sourcing',
    rfqs: 'RFQs',
    offers: 'Offers',
    evaluation: 'Evaluation',
  };

  return (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexWrap: 'wrap' }}>
      {Object.entries(stages).map(([key, status]) => {
        const { icon: Icon, color, bg } = stageConfig[status] || stageConfig.pending;
        return (
          <div
            key={key}
            title={`${stageNames[key]}: ${status}`}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 3,
              padding: '2px 8px',
              borderRadius: 12,
              background: bg,
              border: `1px solid ${color}33`,
            }}
          >
            <Icon size={12} color={color} />
            <span style={{ fontSize: 11, fontWeight: 500, color }}>{stageNames[key]}</span>
          </div>
        );
      })}
    </div>
  );
}
