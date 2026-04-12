export default function KpiCard({ title, value, subtitle, color = '#6366f1', icon: Icon }) {
  return (
    <div className="kpi-card" style={{ '--kpi-color': color }}>
      {Icon && (
        <div className="kpi-icon" style={{ background: `${color}12` }}>
          <Icon size={20} color={color} />
        </div>
      )}
      <div className="kpi-value">{value}</div>
      <div className="kpi-title">{title}</div>
      {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
    </div>
  );
}
