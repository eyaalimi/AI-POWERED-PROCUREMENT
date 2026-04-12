import { useApi } from '../hooks/useApi';
import KpiCard from '../components/KpiCard';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area, CartesianGrid } from 'recharts';
import { FileText, CheckCircle, DollarSign, TrendingDown, Clock, Send, Inbox } from 'lucide-react';

const STATUS_COLORS = {
  completed: '#10b981',
  evaluated: '#10b981',
  evaluation_sent: '#8b5cf6',
  pending: '#94a3b8',
  analyzing: '#3b82f6',
  sourcing: '#8b5cf6',
  rfqs_sent: '#f59e0b',
  awaiting_responses: '#f59e0b',
  offers_received: '#ea580c',
  failed: '#ef4444',
};

const RADIAN = Math.PI / 180;
function renderCustomLabel({ cx, cy, midAngle, innerRadius, outerRadius, name, value }) {
  const radius = outerRadius + 20;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="#64748b" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={12} fontWeight={500}>
      {name} ({value})
    </text>
  );
}

export default function KpisPage() {
  const { data, loading, error } = useApi('/dashboard/kpis', { interval: 15000 });

  if (loading) return <div className="page-loading">Loading dashboard...</div>;
  if (error) return <div className="page-error">Error: {error}</div>;

  const kpis = data;
  const statusData = Object.entries(kpis.status_breakdown || {}).map(([name, value]) => ({
    name: name.replace(/_/g, ' '),
    value,
    fill: STATUS_COLORS[name] || '#94a3b8',
  }));

  return (
    <div className="page">
      <div className="kpi-grid">
        <KpiCard icon={FileText} title="Total Requests" value={kpis.total_requests} color="#6366f1" />
        <KpiCard icon={CheckCircle} title="Success Rate" value={`${kpis.success_rate}%`} color="#10b981" />
        <KpiCard icon={DollarSign} title="Total Volume" value={`${(kpis.total_volume_tnd || 0).toLocaleString()} TND`} color="#3b82f6" />
        <KpiCard icon={TrendingDown} title="Savings" value={`${(kpis.savings_tnd || 0).toLocaleString()} TND`} color="#0d9488" />
        <KpiCard icon={Clock} title="Avg Cycle" value={`${kpis.avg_cycle_hours?.toFixed(1) || '—'}h`} color="#8b5cf6" />
        <KpiCard icon={Send} title="RFQs Sent" value={kpis.total_rfqs_sent} color="#f59e0b" />
        <KpiCard icon={Inbox} title="Offers Received" value={kpis.total_offers_received} color="#ea580c" />
      </div>

      <div className="charts-row">
        <div className="chart-card">
          <h3>Status Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={65}
                outerRadius={100}
                paddingAngle={3}
                label={renderCustomLabel}
              >
                {statusData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} stroke="none" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', boxShadow: '0 4px 6px rgba(0,0,0,0.06)', fontSize: 13 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Requests by Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={statusData} barSize={32}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', boxShadow: '0 4px 6px rgba(0,0,0,0.06)', fontSize: 13 }}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {statusData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
