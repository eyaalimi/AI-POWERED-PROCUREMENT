import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import StageIndicator from '../components/StageIndicator';
import { Search } from 'lucide-react';

export default function PipelinesPage() {
  const { data, loading, error } = useApi('/dashboard/pipelines', { interval: 10000 });
  const [selectedId, setSelectedId] = useState(null);
  const [search, setSearch] = useState('');
  const detail = useApi(`/dashboard/pipelines/${selectedId}`, { enabled: !!selectedId });

  if (loading) return <div className="page-loading">Loading pipelines...</div>;
  if (error) return <div className="page-error">Error: {error}</div>;

  let pipelines = data?.pipelines || [];
  if (search) {
    const q = search.toLowerCase();
    pipelines = pipelines.filter(p =>
      (p.title || '').toLowerCase().includes(q) || (p.status || '').toLowerCase().includes(q)
    );
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <div className="search-wrapper" style={{ flex: 1 }}>
          <Search size={16} />
          <input
            type="text"
            placeholder="Search pipelines..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Request</th>
              <th>Status</th>
              <th>Stages</th>
              <th>Budget</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {pipelines.map((p) => (
              <tr key={p.id} className={selectedId === p.id ? 'selected' : ''} onClick={() => setSelectedId(p.id)}>
                <td className="td-title">{p.title || p.id.slice(0, 8)}</td>
                <td><span className={`status-badge status-${p.status}`}>{p.status?.replace(/_/g, ' ')}</span></td>
                <td><StageIndicator stages={p.stages} /></td>
                <td style={{ fontWeight: 500 }}>{p.budget ? `${p.budget.toLocaleString()} TND` : '—'}</td>
                <td style={{ color: '#94a3b8', fontSize: 13 }}>{p.created_at ? new Date(p.created_at).toLocaleDateString('fr-FR') : '—'}</td>
              </tr>
            ))}
            {pipelines.length === 0 && (
              <tr><td colSpan={5} className="empty-row">No pipelines found</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {selectedId && detail.data && (
        <div className="detail-panel" style={{ marginTop: 20 }}>
          <h2>{detail.data.title || selectedId.slice(0, 8)}</h2>
          <div className="detail-grid">
            {detail.data.suppliers?.length > 0 && (
              <div className="detail-section">
                <h3>Suppliers ({detail.data.suppliers.length})</h3>
                <ul>{detail.data.suppliers.map((s, i) => <li key={i}>{s.name} — <span style={{ color: '#6366f1' }}>{s.email}</span></li>)}</ul>
              </div>
            )}
            {detail.data.evaluations?.length > 0 && (
              <div className="detail-section">
                <h3>QCDP Evaluations</h3>
                <table className="data-table small">
                  <thead>
                    <tr><th>Supplier</th><th>Q</th><th>C</th><th>D</th><th>P</th><th>Overall</th><th>Rank</th></tr>
                  </thead>
                  <tbody>
                    {detail.data.evaluations.map((e) => (
                      <tr key={e.id}>
                        <td className="td-title">{e.supplier_name}</td>
                        <td>{e.qualite_score?.toFixed(1)}</td>
                        <td>{e.cout_score?.toFixed(1)}</td>
                        <td>{e.delais_score?.toFixed(1)}</td>
                        <td>{e.performance_score?.toFixed(1)}</td>
                        <td><strong style={{ color: '#6366f1' }}>{e.overall_score?.toFixed(1)}</strong></td>
                        <td>#{e.rank}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {detail.data.events?.length > 0 && (
              <div className="detail-section">
                <h3>Events</h3>
                <ul className="event-list">
                  {detail.data.events.slice(0, 10).map((ev, i) => (
                    <li key={i}>
                      <span className="event-time">{new Date(ev.created_at).toLocaleTimeString('fr-FR')}</span>
                      <span className="event-agent">[{ev.agent}]</span>
                      <span style={{ color: '#64748b' }}>{ev.message}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
