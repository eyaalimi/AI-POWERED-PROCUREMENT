import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import StageIndicator from '../components/StageIndicator';

export default function PipelinesPage() {
  const { data, loading, error } = useApi('/dashboard/pipelines', { interval: 10000 });
  const [selectedId, setSelectedId] = useState(null);
  const detail = useApi(`/dashboard/pipelines/${selectedId}`, { enabled: !!selectedId });

  if (loading) return <div className="page-loading">Chargement...</div>;
  if (error) return <div className="page-error">Erreur: {error}</div>;

  const pipelines = data?.pipelines || [];

  return (
    <div className="page">
      <h1>Pipelines Live</h1>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Demande</th>
              <th>Statut</th>
              <th>Etapes</th>
              <th>Budget</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {pipelines.map((p) => (
              <tr key={p.id} className={selectedId === p.id ? 'selected' : ''} onClick={() => setSelectedId(p.id)}>
                <td className="td-title">{p.title || p.id.slice(0, 8)}</td>
                <td><span className={`status-badge status-${p.status}`}>{p.status}</span></td>
                <td><StageIndicator stages={p.stages} /></td>
                <td>{p.budget ? `${p.budget.toLocaleString()} TND` : '—'}</td>
                <td>{p.created_at ? new Date(p.created_at).toLocaleDateString('fr-FR') : '—'}</td>
              </tr>
            ))}
            {pipelines.length === 0 && (
              <tr><td colSpan={5} className="empty-row">Aucun pipeline</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {selectedId && detail.data && (
        <div className="detail-panel">
          <h2>Detail: {detail.data.title || selectedId.slice(0, 8)}</h2>
          <div className="detail-grid">
            {detail.data.suppliers?.length > 0 && (
              <div className="detail-section">
                <h3>Fournisseurs ({detail.data.suppliers.length})</h3>
                <ul>{detail.data.suppliers.map((s, i) => <li key={i}>{s.name} — {s.email}</li>)}</ul>
              </div>
            )}
            {detail.data.evaluations?.length > 0 && (
              <div className="detail-section">
                <h3>Evaluations QCDP</h3>
                <table className="data-table small">
                  <thead>
                    <tr><th>Fournisseur</th><th>Q</th><th>C</th><th>D</th><th>P</th><th>Total</th><th>Rang</th></tr>
                  </thead>
                  <tbody>
                    {detail.data.evaluations.map((e) => (
                      <tr key={e.id}>
                        <td>{e.supplier_name}</td>
                        <td>{e.qualite_score?.toFixed(1)}</td>
                        <td>{e.cout_score?.toFixed(1)}</td>
                        <td>{e.delais_score?.toFixed(1)}</td>
                        <td>{e.performance_score?.toFixed(1)}</td>
                        <td><strong>{e.overall_score?.toFixed(1)}</strong></td>
                        <td>#{e.rank}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {detail.data.events?.length > 0 && (
              <div className="detail-section">
                <h3>Evenements</h3>
                <ul className="event-list">
                  {detail.data.events.slice(0, 10).map((ev, i) => (
                    <li key={i} className={`event-${ev.event_type}`}>
                      <span className="event-time">{new Date(ev.created_at).toLocaleTimeString('fr-FR')}</span>
                      <span className="event-agent">[{ev.agent}]</span>
                      {ev.message}
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
