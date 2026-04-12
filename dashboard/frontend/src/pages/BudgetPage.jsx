import { useApi } from '../hooks/useApi';
import { DollarSign, TrendingUp, AlertTriangle, PieChart as PieIcon } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

function formatTND(v) {
  return `${Number(v || 0).toLocaleString()} TND`;
}

function ProgressBar({ spent, pending, allocated, color }) {
  const spentPct = (spent / allocated) * 100;
  const pendingPct = (pending / allocated) * 100;
  return (
    <div style={{ background: '#f1f5f9', borderRadius: 6, height: 10, overflow: 'hidden', width: '100%' }}>
      <div style={{ display: 'flex', height: '100%' }}>
        <div style={{ width: `${spentPct}%`, background: color, transition: 'width 0.3s' }} />
        <div style={{ width: `${pendingPct}%`, background: color, opacity: 0.4, transition: 'width 0.3s' }} />
      </div>
    </div>
  );
}

export default function BudgetPage() {
  const { data, loading, error } = useApi('/dashboard/budget');

  if (loading) return <div className="page-loading">Loading budget data...</div>;
  if (error) return <div className="page-error">Error: {error}</div>;

  const { summary, departments, monthly_trend } = data;

  return (
    <div className="page">
      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        <SummaryCard icon={DollarSign} label="Total Allocated" value={formatTND(summary.total_allocated)} color="#6366f1" />
        <SummaryCard icon={TrendingUp} label="Total Spent" value={formatTND(summary.total_spent)} color="#10b981" />
        <SummaryCard icon={PieIcon} label="Utilization" value={`${summary.overall_utilization}%`} color="#f59e0b" />
        <SummaryCard icon={AlertTriangle} label="Remaining" value={formatTND(summary.total_remaining)} color="#3b82f6" />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ background: '#fef3c7', color: '#92400e', padding: '3px 10px', borderRadius: 8, fontSize: 11, fontWeight: 600 }}>
          DEMO DATA
        </span>
        <span style={{ fontSize: 12, color: '#94a3b8' }}>Budget figures are simulated for demonstration</span>
      </div>

      {/* Department Breakdown */}
      <div style={{
        background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
        padding: 20, marginBottom: 24,
      }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>Budget by Department</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {departments.map((d) => (
            <div key={d.name} style={{ display: 'grid', gridTemplateColumns: '140px 1fr 120px 80px', alignItems: 'center', gap: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 10, height: 10, borderRadius: 3, background: d.color }} />
                <span style={{ fontSize: 14, fontWeight: 500 }}>{d.name}</span>
              </div>
              <ProgressBar spent={d.spent} pending={d.pending} allocated={d.allocated} color={d.color} />
              <span style={{ fontSize: 13, color: '#64748b', textAlign: 'right' }}>
                {formatTND(d.spent + d.pending)}
              </span>
              <span style={{
                fontSize: 12, fontWeight: 600, textAlign: 'right',
                color: d.utilization > 85 ? '#ef4444' : d.utilization > 65 ? '#f59e0b' : '#10b981',
              }}>
                {d.utilization}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Monthly Trend Chart */}
      <div className="chart-card">
        <h3>Monthly Budget vs Actual</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthly_trend} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
            <Tooltip
              formatter={(v) => `${Number(v).toLocaleString()} TND`}
              contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 13 }}
            />
            <Legend />
            <Bar dataKey="budget" name="Budget" fill="#6366f1" radius={[4, 4, 0, 0]} />
            <Bar dataKey="actual" name="Actual Spend" fill="#10b981" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Department Table */}
      <div style={{
        background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
        overflow: 'hidden', marginTop: 24,
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <th style={th}>Department</th>
              <th style={th}>Allocated</th>
              <th style={th}>Spent</th>
              <th style={th}>Pending</th>
              <th style={th}>Remaining</th>
              <th style={th}>Utilization</th>
            </tr>
          </thead>
          <tbody>
            {departments.map((d) => (
              <tr key={d.name} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 8, height: 8, borderRadius: 2, background: d.color }} />
                    {d.name}
                  </div>
                </td>
                <td style={td}>{formatTND(d.allocated)}</td>
                <td style={td}>{formatTND(d.spent)}</td>
                <td style={td}>{formatTND(d.pending)}</td>
                <td style={td}>{formatTND(d.remaining)}</td>
                <td style={td}>
                  <span style={{
                    padding: '2px 8px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                    background: d.utilization > 85 ? '#fef2f2' : d.utilization > 65 ? '#fffbeb' : '#f0fdf4',
                    color: d.utilization > 85 ? '#ef4444' : d.utilization > 65 ? '#f59e0b' : '#10b981',
                  }}>
                    {d.utilization}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, color }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
      padding: 20, display: 'flex', alignItems: 'center', gap: 14,
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: 10, background: `${color}15`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon size={20} color={color} />
      </div>
      <div>
        <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#0f172a' }}>{value}</div>
      </div>
    </div>
  );
}

const th = { padding: '12px 16px', textAlign: 'left', fontWeight: 600, fontSize: 13 };
const td = { padding: '12px 16px', color: '#64748b' };
