export default function KpiCard({ title, value, subtitle, color = '#40E0D0', icon: Icon }) {
  return (
    <div className="kpi-card" style={{ '--kpi-color': color }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="kpi-value">{value}</div>
          <div className="kpi-title">{title}</div>
          {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
        </div>
        {Icon && (
          <div className="kpi-icon" style={{ background: `linear-gradient(135deg, ${color}22, rgba(27,58,107,0.08))` }}>
            <Icon size={22} color={color} />
          </div>
        )}
      </div>
    </div>
  );
}
