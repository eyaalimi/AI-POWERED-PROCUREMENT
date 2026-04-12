import { CheckCircle, Clock, AlertCircle, Circle } from 'lucide-react';

const stageConfig = {
  done: { icon: CheckCircle, color: '#10b981', label: 'Done' },
  active: { icon: Clock, color: '#f59e0b', label: 'In progress' },
  pending: { icon: Circle, color: '#94a3b8', label: 'Pending' },
  error: { icon: AlertCircle, color: '#ef4444', label: 'Error' },
  skipped: { icon: Circle, color: '#cbd5e1', label: 'Skipped' },
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
    <div className="stage-row">
      {Object.entries(stages).map(([key, status]) => {
        const { icon: Icon, color } = stageConfig[status] || stageConfig.pending;
        return (
          <div key={key} className="stage-item" title={`${stageNames[key]}: ${status}`}>
            <Icon size={16} color={color} />
            <span className="stage-label">{stageNames[key]}</span>
          </div>
        );
      })}
    </div>
  );
}
