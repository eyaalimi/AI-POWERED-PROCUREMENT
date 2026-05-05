import { useState } from 'react';
import { Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Bar, ComposedChart } from 'recharts';
import { MOCK_TREND, MOCK_TREND_PREVIOUS } from '../../mocks/dashboardMocks';

const METRICS = [
  { id: 'savings', label: 'Savings',    suffix: ' TND', color: '#10B981' },
  { id: 'cycle',   label: 'Cycle time', suffix: 'h',    color: '#6366F1' },
  { id: 'volume',  label: 'Volume',     suffix: ' TND', color: '#A78BFA' },
];

const PERIODS = [
  { id: '7d',  label: '7d' },
  { id: '30d', label: '30d' },
  { id: '90d', label: '90d' },
];

function formatNumber(v) {
  if (v == null) return '—';
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000)     return `${(v / 1_000).toFixed(1)}K`;
  return v.toFixed(1);
}

function CustomTooltip({ active, payload, suffix }) {
  if (!active || !payload || !payload.length) return null;
  const p = payload[0].payload;
  return (
    <div className="dash-trend-tooltip">
      <div className="dash-trend-tooltip-date">{p.date}</div>
      <div className="dash-trend-tooltip-value dash-num">
        {formatNumber(p.value)}{suffix}
      </div>
      <div className="dash-trend-tooltip-meta dash-num">
        {p.requests} requests
      </div>
    </div>
  );
}

export default function TrendChart() {
  const [metricId, setMetricId] = useState('savings');
  const [periodId, setPeriodId] = useState('30d');

  const metric = METRICS.find(m => m.id === metricId);
  const data = MOCK_TREND[metricId][periodId];
  const previous = MOCK_TREND_PREVIOUS[metricId][periodId];
  const current = data.reduce((acc, p) => acc + p.value, 0);
  const deltaPct = previous ? Math.round((current - previous) / previous * 100) : 0;

  return (
    <div className="dash-card dash-trend">
      <div className="dash-trend-header">
        <span className="dash-label">Performance trend</span>
        <div className="dash-trend-tabs" role="tablist">
          {METRICS.map(m => (
            <button
              key={m.id}
              role="tab"
              aria-selected={m.id === metricId}
              className={`dash-trend-tab ${m.id === metricId ? 'is-active' : ''}`}
              onClick={() => setMetricId(m.id)}
            >
              {m.label}
            </button>
          ))}
        </div>
        <div className="dash-trend-periods" role="tablist">
          {PERIODS.map(p => (
            <button
              key={p.id}
              role="tab"
              aria-selected={p.id === periodId}
              className={`dash-trend-period ${p.id === periodId ? 'is-active' : ''}`}
              onClick={() => setPeriodId(p.id)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="dash-trend-summary">
        <span className="dash-trend-summary-value dash-num">{formatNumber(current)}{metric.suffix}</span>
        <span className="dash-trend-summary-delta dash-num" style={{ color: deltaPct >= 0 ? 'var(--dash-accent-success)' : 'var(--dash-accent-danger)' }}>
          {deltaPct >= 0 ? '▲' : '▼'} {Math.abs(deltaPct)}% vs previous {periodId}
        </span>
      </div>

      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer>
          <ComposedChart data={data} margin={{ top: 10, right: 16, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={metric.color} stopOpacity={0.4} />
                <stop offset="100%" stopColor={metric.color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#1F2533" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: '#5A6275' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(d) => d.slice(5)}
            />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11, fill: '#5A6275' }}
              axisLine={false}
              tickLine={false}
              width={40}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11, fill: '#5A6275' }}
              axisLine={false}
              tickLine={false}
              width={30}
            />
            <Tooltip content={<CustomTooltip suffix={metric.suffix} />} cursor={{ stroke: '#2A3142', strokeWidth: 1 }} />
            <Bar yAxisId="right" dataKey="requests" fill="#1F2533" barSize={6} radius={[2, 2, 0, 0]} />
            <Area yAxisId="left" type="monotone" dataKey="value" stroke={metric.color} strokeWidth={2} fill="url(#trendGradient)" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
