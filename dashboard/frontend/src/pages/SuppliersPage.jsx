import { useApi } from '../hooks/useApi';

export default function SuppliersPage() {
  const { data, loading, error } = useApi('/suppliers', { interval: 15000 });

  if (loading) return <div className="page-loading">Chargement...</div>;
  if (error) return <div className="page-error">Erreur: {error}</div>;

  const suppliers = data?.suppliers || [];

  return (
    <div className="page">
      <h1>Fournisseurs</h1>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Email</th>
              <th>Score QCDP Moyen</th>
              <th>Taux de Reponse</th>
              <th>Offres</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((s, i) => (
              <tr key={i}>
                <td className="td-title">{s.name}</td>
                <td>{s.email || '—'}</td>
                <td>
                  <div className="score-bar">
                    <div className="score-fill" style={{ width: `${(s.avg_score || 0)}%`, backgroundColor: scoreColor(s.avg_score) }} />
                    <span>{s.avg_score?.toFixed(1) || '—'}</span>
                  </div>
                </td>
                <td>{s.response_rate != null ? `${s.response_rate}%` : '—'}</td>
                <td>{s.total_offers ?? '—'}</td>
              </tr>
            ))}
            {suppliers.length === 0 && (
              <tr><td colSpan={5} className="empty-row">Aucun fournisseur</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function scoreColor(score) {
  if (!score) return '#95a5a6';
  if (score >= 75) return '#27ae60';
  if (score >= 50) return '#f39c12';
  return '#e74c3c';
}
