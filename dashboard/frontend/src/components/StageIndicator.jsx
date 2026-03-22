import { CheckCircle, Clock, AlertCircle, Circle } from 'lucide-react';

const stageConfig = {
  done: { icon: CheckCircle, color: '#27ae60', label: 'Done' },
  active: { icon: Clock, color: '#f39c12', label: 'In progress' },
  pending: { icon: Circle, color: '#95a5a6', label: 'Pending' },
  error: { icon: AlertCircle, color: '#e74c3c', label: 'Error' },
  skipped: { icon: Circle, color: '#bdc3c7', label: 'Skipped' },
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
