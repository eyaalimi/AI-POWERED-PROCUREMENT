export default function KpiCard({ title, value, subtitle, color = '#2C3E50' }) {
  return (
    <div className="kpi-card">
      <div className="kpi-value" style={{ color }}>{value}</div>
      <div className="kpi-title">{title}</div>
      {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
    </div>
  );
}
