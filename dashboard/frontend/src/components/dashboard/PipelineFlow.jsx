import { useNavigate } from 'react-router-dom';

const STAGES = [
  { key: 'received',           label: 'Received',  statuses: ['pending'] },
  { key: 'analyzing',          label: 'Analysis',  statuses: ['analyzing'] },
  { key: 'sourcing',           label: 'Sourcing',  statuses: ['sourcing'] },
  { key: 'rfqs_sent',          label: 'RFQs',      statuses: ['rfqs_sent'] },
  { key: 'awaiting_responses', label: 'Awaiting',  statuses: ['awaiting_responses', 'offers_received'] },
  { key: 'evaluated',          label: 'Evaluated', statuses: ['evaluated', 'evaluation_sent'] },
  { key: 'completed',          label: 'Done',      statuses: ['completed', 'po_generated'] },
];

export default function PipelineFlow({ statusBreakdown = {} }) {
  const navigate = useNavigate();
  const counts = STAGES.map(s => ({
    ...s,
    count: s.statuses.reduce((sum, st) => sum + (statusBreakdown[st] || 0), 0),
  }));

  const total = counts.reduce((sum, s) => sum + s.count, 0);
  const bottleneck = counts.reduce((max, s) => (s.count > max.count ? s : max), counts[0]);

  return (
    <div className="dash-card dash-pipeline">
      <div className="dash-card-header">
        <span className="dash-label">Procurement pipeline</span>
        <span className="dash-pill">{total} active flows</span>
      </div>

      <div className="dash-pipeline-flow">
        {counts.map((stage, idx) => {
          const isBottleneck = stage.count > 0 && stage.key === bottleneck.key;
          return (
            <div key={stage.key} className="dash-pipeline-stage-wrap">
              <button
                className={`dash-pipeline-stage ${isBottleneck ? 'is-bottleneck' : ''}`}
                onClick={() => navigate(`/pipelines?status=${stage.key}`)}
              >
                <span className="dash-pipeline-stage-count dash-num">{stage.count}</span>
                <span className="dash-pipeline-stage-label">{stage.label}</span>
              </button>
              {idx < counts.length - 1 && <div className="dash-pipeline-track" />}
            </div>
          );
        })}
      </div>

      {bottleneck.count > 0 && total > 0 && (
        <div className="dash-pipeline-callout">
          ↑ bottleneck: <strong>{bottleneck.label}</strong> ({bottleneck.count} pending)
        </div>
      )}
    </div>
  );
}
