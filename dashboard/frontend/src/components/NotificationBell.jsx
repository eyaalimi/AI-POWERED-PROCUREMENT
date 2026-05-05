import { useState, useRef, useEffect } from 'react';
import { Bell, Mail, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';

const TYPE_CONFIG = {
  email: { icon: Mail, color: '#3b82f6', bg: '#eff6ff' },
  success: { icon: CheckCircle, color: '#10b981', bg: '#ecfdf5' },
  warning: { icon: AlertTriangle, color: '#f59e0b', bg: '#fffbeb' },
  error: { icon: AlertCircle, color: '#ef4444', bg: '#fef2f2' },
  info: { icon: Info, color: '#6366f1', bg: '#eef2ff' },
};

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function NotificationBell() {
  const { notifications, unreadCount, markAllRead, markRead } = useNotifications();
  const [open, setOpen] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button className="notification-bell" onClick={() => setOpen(!open)}>
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="notification-count">{unreadCount > 9 ? '9+' : unreadCount}</span>
        )}
      </button>

      {open && (
        <div className="notification-dropdown">
          <div className="notification-dropdown-header">
            <span>Notifications {unreadCount > 0 && `(${unreadCount})`}</span>
            {unreadCount > 0 && (
              <button onClick={markAllRead}>Mark all read</button>
            )}
          </div>

          <div className="notification-list">
            {notifications.length === 0 && (
              <div className="notification-empty">No notifications yet</div>
            )}
            {notifications.map(n => {
              const cfg = TYPE_CONFIG[n.type] || TYPE_CONFIG.info;
              const Icon = cfg.icon;
              return (
                <div
                  key={n.id}
                  className={`notification-item ${!n.read ? 'unread' : ''}`}
                  onClick={() => markRead(n.id)}
                >
                  <div style={{ width: 32, height: 32, borderRadius: 8, background: cfg.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Icon size={16} color={cfg.color} />
                  </div>
                  <div className="notification-item-content">
                    <div className="notification-item-title">{n.title}</div>
                    <div className="notification-item-desc">{n.description}</div>
                  </div>
                  <div className="notification-item-time">{timeAgo(n.time)}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
