import { useState } from 'react';
import { useApi } from '../hooks/useApi';

const TYPE_COLORS = {
  info: '#3498db',
  success: '#27ae60',
  warning: '#f39c12',
  error: '#e74c3c',
};

export default function ActivityPage() {
  const [agentFilter, setAgentFilter] = useState('');
  const path = agentFilter ? `/dashboard/activity?agent=${agentFilter}` : '/dashboard/activity';
  const { data, loading, error } = useApi(path, { interval: 10000 });

  if (loading) return <div className="page-loading">Chargement...</div>;
  if (error) return <div className="page-error">Erreur: {error}</div>;

  const events = data?.events || [];
  const agents = [...new Set(events.map((e) => e.agent))];

  return (
    <div className="page">
      <h1>Journal d'Activite</h1>

      <div className="filters">
        <select value={agentFilter} onChange={(e) => setAgentFilter(e.target.value)}>
          <option value="">Tous les agents</option>
          {agents.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      <div className="activity-timeline">
        {events.map((ev, i) => (
          <div key={i} className="activity-item">
            <div className="activity-dot" style={{ backgroundColor: TYPE_COLORS[ev.event_type] || '#95a5a6' }} />
            <div className="activity-content">
              <div className="activity-header">
                <span className="activity-agent">{ev.agent}</span>
                <span className={`activity-type type-${ev.event_type}`}>{ev.event_type}</span>
                <span className="activity-time">{new Date(ev.created_at).toLocaleString('fr-FR')}</span>
              </div>
              <p className="activity-message">{ev.message}</p>
              {ev.request_id && <span className="activity-request">Demande: {ev.request_id.slice(0, 8)}</span>}
            </div>
          </div>
        ))}
        {events.length === 0 && <p className="empty-text">Aucune activite enregistree</p>}
      </div>
    </div>
  );
}
