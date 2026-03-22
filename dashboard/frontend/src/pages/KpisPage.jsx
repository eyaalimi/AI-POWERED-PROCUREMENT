import { useApi } from '../hooks/useApi';
import KpiCard from '../components/KpiCard';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const STATUS_COLORS = {
  completed: '#27ae60',
  evaluated: '#2ecc71',
  pending: '#95a5a6',
  analyzing: '#3498db',
  sourcing: '#9b59b6',
  rfqs_sent: '#f39c12',
  offers_received: '#e67e22',
  failed: '#e74c3c',
};

export default function KpisPage() {
  const { data, loading, error } = useApi('/dashboard/kpis', { interval: 15000 });

  if (loading) return <div className="page-loading">Chargement...</div>;
  if (error) return <div className="page-error">Erreur: {error}</div>;

  const kpis = data;
  const statusData = Object.entries(kpis.status_breakdown || {}).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <div className="page">
      <h1>Tableau de Bord</h1>

      <div className="kpi-grid">
        <KpiCard title="Total Demandes" value={kpis.total_requests} color="#2C3E50" />
        <KpiCard title="Taux de Succes" value={`${kpis.success_rate}%`} color="#27ae60" />
        <KpiCard title="Volume Total (TND)" value={kpis.total_volume_tnd?.toLocaleString() || '0'} color="#2980b9" />
        <KpiCard title="Economies (TND)" value={kpis.savings_tnd?.toLocaleString() || '0'} color="#16a085" />
        <KpiCard title="Cycle Moyen" value={`${kpis.avg_cycle_hours?.toFixed(1) || '—'}h`} color="#8e44ad" />
        <KpiCard title="RFQs Envoyees" value={kpis.total_rfqs_sent} color="#f39c12" />
        <KpiCard title="Offres Recues" value={kpis.total_offers_received} color="#e67e22" />
      </div>

      <div className="charts-row">
        <div className="chart-card">
          <h3>Repartition par Statut</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, value }) => `${name}: ${value}`}>
                {statusData.map((entry) => (
                  <Cell key={entry.name} fill={STATUS_COLORS[entry.name] || '#95a5a6'} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Statuts</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={statusData}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#3498db" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
