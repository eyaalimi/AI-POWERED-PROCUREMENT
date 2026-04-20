import { useState } from 'react';
import { useApi } from '../hooks/useApi';

const TYPE_COLORS = {
  info: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
};

export default function ActivityPage() {
  const [agentFilter, setAgentFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const path = agentFilter ? `/dashboard/activity?agent=${agentFilter}` : '/dashboard/activity';
  const { data, loading, error } = useApi(path, { interval: 10000 });

  if (loading) return <div className="page-loading">Loading activity...</div>;
  if (error) return <div className="page-error">Error: {error}</div>;

  let events = data?.events || [];
  const agents = [...new Set(events.map((e) => e.agent))];

  if (typeFilter) events = events.filter(e => e.event_type === typeFilter);

  return (
    <div className="page">
      <div className="filters">
        <select className="filter-input" value={agentFilter} onChange={(e) => setAgentFilter(e.target.value)}>
          <option value="">All Agents</option>
          {agents.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        <select className="filter-input" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All Types</option>
          <option value="info">Info</option>
          <option value="success">Success</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
        </select>
      </div>

      <div className="table-wrapper" style={{ padding: '8px 0' }}>
        <div className="activity-timeline" style={{ padding: '0 20px' }}>
          {events.map((ev, i) => (
            <div key={i} className="activity-item">
              <div className="activity-dot" style={{ backgroundColor: TYPE_COLORS[ev.event_type] || '#94a3b8' }} />
              <div className="activity-content">
                <div className="activity-header">
                  <span className="activity-agent">{ev.agent}</span>
                  <span className={`activity-type type-${ev.event_type}`}>{ev.event_type}</span>
                  <span className="activity-time">{new Date(ev.created_at).toLocaleString('fr-FR')}</span>
                </div>
                <p className="activity-message">{ev.message}</p>
                {ev.request_id && <span className="activity-request">Request: {ev.request_id.slice(0, 8)}...</span>}
              </div>
            </div>
          ))}
          {events.length === 0 && <p className="empty-text">No activity recorded</p>}
        </div>
      </div>
    </div>
  );
}
