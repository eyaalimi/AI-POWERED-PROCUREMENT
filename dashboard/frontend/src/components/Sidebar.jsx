import { NavLink, useNavigate } from 'react-router-dom';
import { BarChart3, GitBranch, Activity, Truck, Shield, Mail, Package, Zap, LogOut, User, Users, FilePlus, DollarSign } from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';
import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
  const { unreadCount } = useNotifications();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const NAV_SECTIONS = [
    {
      label: 'Overview',
      links: [
        { to: '/', icon: BarChart3, label: 'Dashboard' },
        { to: '/inbox', icon: Mail, label: 'Inbox', badge: true },
        { to: '/new-request', icon: FilePlus, label: 'New Request' },
      ],
    },
    {
      label: 'Operations',
      links: [
        { to: '/pipelines', icon: GitBranch, label: 'Pipelines' },
        { to: '/orders', icon: Package, label: 'Orders' },
        { to: '/activity', icon: Activity, label: 'Activity Log' },
      ],
    },
    {
      label: 'Management',
      links: [
        { to: '/suppliers', icon: Truck, label: 'Suppliers' },
        { to: '/budget', icon: DollarSign, label: 'Budget' },
        ...(user?.role === 'admin' ? [
          { to: '/blacklist', icon: Shield, label: 'Blacklist' },
          { to: '/users', icon: Users, label: 'Team Members' },
        ] : []),
      ],
    },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon"><Zap size={20} /></div>
          <div>
            <h2>Procurement AI</h2>
            <span className="sidebar-subtitle">Control Tower</span>
          </div>
        </div>
      </div>
      <nav>
        {NAV_SECTIONS.map(section => (
          <div key={section.label}>
            <div className="nav-section-label">{section.label}</div>
            {section.links.map(({ to, icon: Icon, label, badge }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                end={to === '/'}
              >
                <Icon size={18} />
                <span>{label}</span>
                {badge && unreadCount > 0 && (
                  <span className="nav-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <div className="sidebar-footer">
        {user && (
          <div className="sidebar-user">
            <div className="sidebar-user-avatar">
              <User size={16} />
            </div>
            <div className="sidebar-user-info">
              <span className="sidebar-user-name">{user.name}</span>
              <span className="sidebar-user-role">
                {user.role === 'admin' ? 'Admin' : 'Employee'} — {user.company_name}
              </span>
            </div>
            <button className="sidebar-logout" onClick={handleLogout} title="Logout">
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
