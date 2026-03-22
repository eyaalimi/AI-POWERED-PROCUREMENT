import { NavLink } from 'react-router-dom';
import { BarChart3, GitBranch, Activity, Truck, Shield } from 'lucide-react';

const links = [
  { to: '/', icon: BarChart3, label: 'KPIs' },
  { to: '/pipelines', icon: GitBranch, label: 'Pipelines' },
  { to: '/activity', icon: Activity, label: 'Activity Log' },
  { to: '/suppliers', icon: Truck, label: 'Suppliers' },
  { to: '/blacklist', icon: Shield, label: 'Blacklist' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Procurement AI</h2>
        <span className="sidebar-subtitle">Tour de Controle</span>
      </div>
      <nav>
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
