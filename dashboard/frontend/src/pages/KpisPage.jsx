import { useApi } from '../hooks/useApi';
import { useNavigate } from 'react-router-dom';
import KpiCard from '../components/KpiCard';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area, CartesianGrid } from 'recharts';
import { FileText, CheckCircle, DollarSign, TrendingDown, Clock, Send, Inbox, Eye, Award } from 'lucide-react';

function formatNumber(n) {
  if (!n) return '0';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

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

const WORKFLOW_PHASES = [
  {
    name: 'Preparation',
    color: '#40E0D0',
    statuses: ['pending', 'analyzing'],
    labels: ['Received', 'Analyzing'],
  },
  {
    name: 'Execution',
    color: '#1B3A6B',
    statuses: ['sourcing', 'rfqs_sent', 'awaiting_responses', 'offers_received'],
    labels: ['Sourcing', 'RFQs Sent', 'Awaiting Offers', 'Offers In'],
  },
  {
    name: 'Finalisation',
    color: '#27AE60',
    statuses: ['evaluated', 'evaluation_sent', 'po_generated', 'completed'],
    labels: ['Evaluated', 'Eval Sent', 'PO Created', 'Completed'],
  },
];

export default function KpisPage() {
  const { data, loading, error } = useApi('/dashboard/kpis', { interval: 15000 });
  const { data: recsData } = useApi('/dashboard/recommendations', { interval: 30000 });
  const navigate = useNavigate();

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
        <KpiCard icon={DollarSign} title="Total Volume" value={`${formatNumber(kpis.total_volume_tnd)} TND`} color="#3b82f6" />
        <KpiCard icon={TrendingDown} title="Savings" value={`${formatNumber(kpis.savings_tnd)} TND`} color="#0d9488" />
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

      {/* Workflow Visualization */}
      <div className="detail-card" style={{ marginTop: 24 }}>
        <div className="detail-card-header">
          <h3>Procurement Workflow</h3>
        </div>
        <div className="workflow-grid">
          {WORKFLOW_PHASES.map(phase => {
            const phaseTotal = phase.statuses.reduce((sum, s) => sum + (kpis.status_breakdown?.[s] || 0), 0);
            const pct = kpis.total_requests > 0 ? Math.round(phaseTotal / kpis.total_requests * 100) : 0;
            return (
              <div key={phase.name} className="workflow-card" style={{ '--wf-color': phase.color }}>
                <div className="workflow-card-header">
                  <span className="workflow-phase-name">{phase.name}</span>
                  <span className="workflow-phase-count">{phaseTotal}</span>
                </div>
                <div className="workflow-progress-bar">
                  <div className="workflow-progress-fill" style={{ width: `${pct}%`, background: phase.color }} />
                </div>
                <div className="workflow-states">
                  {phase.statuses.map((s, i) => {
                    const count = kpis.status_breakdown?.[s] || 0;
                    return (
                      <div key={s} className="workflow-state-row">
                        <span className="workflow-state-dot" style={{ background: phase.color }} />
                        <span className="workflow-state-label">{phase.labels[i]}</span>
                        <span className="workflow-state-count">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recommendations Table */}
      {(recsData?.recommendations?.length > 0) && (
        <div className="detail-card" style={{ marginTop: 24 }}>
          <div className="detail-card-header">
            <h3><Award size={16} /> Top Recommendations</h3>
            <span className="stat-badge" style={{ background: '#D5F5E3', color: '#1E8449' }}>
              {recsData.recommendations.length} evaluated
            </span>
          </div>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Best Supplier</th>
                  <th>Score</th>
                  <th>Date</th>
                  <th style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recsData.recommendations.map(r => (
                  <tr key={r.request_id}>
                    <td className="td-title">{r.product}</td>
                    <td><strong>{r.supplier_name}</strong></td>
                    <td>
                      <strong style={{ color: '#27AE60' }}>{r.overall_score?.toFixed(1)}</strong>
                      <span style={{ color: '#95A5A6', fontSize: 12 }}>/100</span>
                    </td>
                    <td style={{ fontSize: 12, color: '#95A5A6' }}>
                      {r.created_at ? new Date(r.created_at).toLocaleDateString('fr-FR') : '—'}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        className="btn-sm-action"
                        onClick={() => navigate(`/request/${r.request_id}`)}
                      >
                        <Eye size={13} /> Detail
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
