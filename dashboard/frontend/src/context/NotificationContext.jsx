import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';

const NotificationContext = createContext();

export function useNotifications() {
  return useContext(NotificationContext);
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

function authHeaders() {
  const token = localStorage.getItem('token');
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([]);
  const [toasts, setToasts] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const prevEmailIdsRef = useRef(new Set());
  const initialLoadRef = useRef(true);

  // Poll for new emails every 10 seconds
  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE}/emails/inbox?limit=20`, { headers: authHeaders() });
        if (!res.ok) return;
        const json = await res.json();
        const emails = json.data || [];

        if (initialLoadRef.current) {
          // First load — seed known IDs, don't notify
          prevEmailIdsRef.current = new Set(emails.map(e => e.id));
          initialLoadRef.current = false;
          return;
        }

        const prevIds = prevEmailIdsRef.current;
        const newEmails = emails.filter(e => !prevIds.has(e.id));

        if (newEmails.length > 0 && !cancelled) {
          const newNotifs = newEmails.map(e => ({
            id: e.id,
            type: 'email',
            title: `New request: ${e.product}`,
            description: `From ${e.requester_email}`,
            time: e.created_at,
            read: false,
            status: e.status,
          }));

          setNotifications(prev => [...newNotifs, ...prev].slice(0, 50));
          setUnreadCount(prev => prev + newEmails.length);

          // Show toast for each new email
          newEmails.forEach(e => {
            addToast({
              type: 'email',
              title: `New request received`,
              message: `${e.product} — from ${e.requester_email}`,
            });
          });
        }

        prevEmailIdsRef.current = new Set(emails.map(e => e.id));
      } catch {
        // ignore polling errors
      }
    };

    poll();
    const interval = setInterval(poll, 10000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  // Also poll for status changes (pipeline events)
  useEffect(() => {
    let cancelled = false;
    const lastEventRef = { current: null };

    const pollActivity = async () => {
      try {
        const res = await fetch(`${API_BASE}/dashboard/activity?limit=5`, { headers: authHeaders() });
        if (!res.ok) return;
        const json = await res.json();
        const events = json.events || [];

        if (events.length === 0) return;
        const latest = events[0];

        if (lastEventRef.current === null) {
          lastEventRef.current = latest.id;
          return;
        }

        if (latest.id !== lastEventRef.current && !cancelled) {
          const newEvents = [];
          for (const ev of events) {
            if (ev.id === lastEventRef.current) break;
            newEvents.push(ev);
          }

          if (newEvents.length > 0) {
            const newNotifs = newEvents.map(ev => ({
              id: ev.id,
              type: ev.event_type,
              title: `[${ev.agent}] ${ev.event_type}`,
              description: ev.message,
              time: ev.created_at,
              read: false,
            }));

            setNotifications(prev => [...newNotifs, ...prev].slice(0, 50));
            setUnreadCount(prev => prev + newEvents.length);

            // Toast only for important events
            newEvents
              .filter(ev => ev.event_type === 'success' || ev.event_type === 'error')
              .forEach(ev => {
                addToast({
                  type: ev.event_type,
                  title: ev.agent,
                  message: ev.message,
                });
              });
          }

          lastEventRef.current = latest.id;
        }
      } catch {
        // ignore
      }
    };

    pollActivity();
    const interval = setInterval(pollActivity, 10000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  const addToast = useCallback((toast) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { ...toast, id }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const markAllRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  }, []);

  const markRead = useCallback((id) => {
    setNotifications(prev =>
      prev.map(n => n.id === id && !n.read ? { ...n, read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, []);

  return (
    <NotificationContext.Provider value={{
      notifications, toasts, unreadCount,
      addToast, dismissToast, markAllRead, markRead,
    }}>
      {children}
    </NotificationContext.Provider>
  );
}
