import { useState } from 'react';

export default function LiveAIStrip({ agents = [], status = 'operational' }) {
  const [hoverKey, setHoverKey] = useState(null);
  const statusLabel = status === 'operational' ? 'Operational' : 'Degraded';
  const statusClass = status === 'operational' ? 'is-ok' : 'is-degraded';

  return (
    <div className="dash-live-strip" aria-hidden="true">
      <div className="dash-live-strip-label">LIVE AI</div>

      <div className="dash-live-flow">
        {agents.map((agent, idx) => (
          <div key={agent.key} className="dash-live-node-wrap">
            <div
              className={`dash-live-node ${agent.isCurrentlyActive ? 'is-active' : ''}`}
              onMouseEnter={() => setHoverKey(agent.key)}
              onMouseLeave={() => setHoverKey(null)}
            >
              <span className="dash-live-count dash-num">{agent.activeCount}</span>
              <span className="dash-live-name">{agent.name}</span>
              {hoverKey === agent.key && (
                <div className="dash-live-tooltip" role="tooltip">
                  p95 {agent.p95Ms}ms
                  <br />
                  {agent.tokensPerMin.toLocaleString()} tok/min
                </div>
              )}
            </div>
            {idx < agents.length - 1 && <div className="dash-live-link" />}
          </div>
        ))}
      </div>

      <div className={`dash-live-status ${statusClass}`}>
        <span className="dash-live-status-dot" />
        {statusLabel}
      </div>
    </div>
  );
}
