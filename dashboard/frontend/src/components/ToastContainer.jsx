import { Mail, CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';

const TOAST_ICONS = {
  email: { icon: Mail, color: '#3b82f6', bg: '#eff6ff' },
  success: { icon: CheckCircle, color: '#10b981', bg: '#ecfdf5' },
  warning: { icon: AlertTriangle, color: '#f59e0b', bg: '#fffbeb' },
  error: { icon: AlertCircle, color: '#ef4444', bg: '#fef2f2' },
};

export default function ToastContainer() {
  const { toasts, dismissToast } = useNotifications();

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map(t => {
        const cfg = TOAST_ICONS[t.type] || TOAST_ICONS.email;
        const Icon = cfg.icon;
        return (
          <div key={t.id} className="toast" onClick={() => dismissToast(t.id)}>
            <div className="toast-icon" style={{ background: cfg.bg }}>
              <Icon size={18} color={cfg.color} />
            </div>
            <div className="toast-body">
              <div className="toast-title">{t.title}</div>
              <div className="toast-message">{t.message}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
