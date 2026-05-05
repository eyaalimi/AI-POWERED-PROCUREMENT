import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { Search, ChevronRight, X, ExternalLink } from 'lucide-react';

const STATUS_CONFIG = {
  pending: { label: 'RECEIVED', color: '#3b82f6', bg: '#eff6ff' },
  analyzing: { label: 'ANALYZING', color: '#8b5cf6', bg: '#f5f3ff' },
  sourcing: { label: 'SOURCING', color: '#8b5cf6', bg: '#f5f3ff' },
  contacting: { label: 'CONTACTING', color: '#f59e0b', bg: '#fffbeb' },
  rfqs_sent: { label: 'RFQS SENT', color: '#f59e0b', bg: '#fffbeb' },
  awaiting_responses: { label: 'AWAITING OFFERS', color: '#ea580c', bg: '#fff7ed' },
  offers_received: { label: 'OFFERS IN', color: '#ea580c', bg: '#fff7ed' },
  evaluated: { label: 'EVALUATED', color: '#10b981', bg: '#ecfdf5' },
  evaluation_sent: { label: 'EVAL SENT', color: '#10b981', bg: '#ecfdf5' },
  awaiting_decision: { label: 'DECISION PENDING', color: '#9333ea', bg: '#faf5ff' },
  po_generated: { label: 'PO CREATED', color: '#10b981', bg: '#ecfdf5' },
  completed: { label: 'COMPLETED', color: '#10b981', bg: '#ecfdf5' },
  delivered: { label: 'DELIVERED', color: '#10b981', bg: '#ecfdf5' },
  failed: { label: 'FAILED', color: '#ef4444', bg: '#fef2f2' },
  rejected: { label: 'REJECTED', color: '#ef4444', bg: '#fef2f2' },
};

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || { label: status, color: '#64748b', bg: '#f1f5f9' };
  return (
    <span className="status-badge" style={{ background: cfg.bg, color: cfg.color }}>
      {cfg.label}
    </span>
  );
}

function timeAgo(dateStr) {
  if (!dateStr) return '—';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

export default function InboxPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [month, setMonth] = useState('');
  const [selectedId, setSelectedId] = useState(null);

  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (month) params.set('month', month);
  params.set('limit', '50');

  const { data, loading, error } = useApi(`/emails/inbox?${params}`, { interval: 10000 });
  const { data: detail } = useApi(selectedId ? `/emails/${selectedId}` : null, { enabled: !!selectedId });

  let emails = data?.data || [];
  if (statusFilter) emails = emails.filter(e => e.status === statusFilter);
  const emailDetail = detail?.data;

  if (loading && !data) return <div className="page-loading">Loading inbox...</div>;
  if (error) return <div className="page-error">Error: {error}</div>;

  return (
    <div className="page">
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
        <div className="search-wrapper" style={{ flex: 1 }}>
          <Search size={16} />
          <input
            type="text"
            placeholder="Search by product, requester..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <select
          className="filter-input"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          {Object.entries(STATUS_CONFIG).map(([k, v]) => (
            <option key={k} value={k}>{v.label}</option>
          ))}
        </select>
        <input
          type="month"
          className="filter-input"
          value={month}
          onChange={e => setMonth(e.target.value)}
        />
      </div>

      <div style={{ display: 'flex', gap: 20 }}>
        <div style={{ flex: selectedId ? '0 0 55%' : 1, transition: 'flex 0.2s ease' }}>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Received</th>
                  <th>Requester</th>
                  <th>Product</th>
                  <th>Status</th>
                  <th style={{ width: 30 }}></th>
                </tr>
              </thead>
              <tbody>
                {emails.length === 0 && (
                  <tr><td colSpan={5} className="empty-row">No emails found</td></tr>
                )}
                {emails.map(e => (
                  <tr
                    key={e.id}
                    className={selectedId === e.id ? 'selected' : ''}
                    onClick={() => setSelectedId(e.id)}
                  >
                    <td style={{ whiteSpace: 'nowrap', fontSize: 13, color: '#94a3b8' }}>
                      {timeAgo(e.created_at)}
                    </td>
                    <td style={{ fontSize: 13 }}>{e.requester_email}</td>
                    <td className="td-title">{e.product}</td>
                    <td><StatusBadge status={e.status} /></td>
                    <td><ChevronRight size={16} color="#94a3b8" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {selectedId && emailDetail && (
          <div style={{ flex: '0 0 43%' }}>
            <div className="detail-panel" style={{ position: 'sticky', top: 96 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                <div>
                  <h2 style={{ margin: 0 }}>{emailDetail.product}</h2>
                  <div style={{ marginTop: 8 }}><StatusBadge status={emailDetail.status} /></div>
                </div>
                <button
                  onClick={() => setSelectedId(null)}
                  className="btn btn-ghost btn-sm"
                >
                  <X size={16} />
                </button>
              </div>

              <div style={{ marginTop: 20 }}>
                <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 14, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  Analysis Result
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px 20px' }}>
                  <InfoItem label="Product" value={emailDetail.product} />
                  <InfoItem label="Category" value={emailDetail.category} />
                  <InfoItem label="Quantity" value={emailDetail.quantity ? `${emailDetail.quantity} ${emailDetail.unit || ''}` : '—'} />
                  <InfoItem label="Budget" value={emailDetail.budget_min || emailDetail.budget_max ? `${emailDetail.budget_min || '?'} - ${emailDetail.budget_max || '?'} TND` : '—'} />
                  <InfoItem label="Deadline" value={emailDetail.deadline || '—'} />
                  <InfoItem label="Valid" value={
                    emailDetail.is_valid
                      ? <span style={{ color: '#10b981', fontWeight: 600 }}>Yes</span>
                      : <span style={{ color: '#ef4444', fontWeight: 600 }}>No — {emailDetail.rejection_reason || ''}</span>
                  } />
                  <InfoItem label="Requester" value={emailDetail.requester_email} />
                  <InfoItem label="Received" value={emailDetail.created_at ? new Date(emailDetail.created_at).toLocaleString() : '—'} />
                </div>
              </div>

              {emailDetail.status === 'evaluation_sent' && (
                <div style={{ marginTop: 16 }}>
                  <a
                    href={`/select/${emailDetail.id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-primary btn-sm"
                    style={{ textDecoration: 'none' }}
                  >
                    <ExternalLink size={14} /> View Evaluation
                  </a>
                </div>
              )}

              {emailDetail.timeline && emailDetail.timeline.length > 0 && (
                <div style={{ marginTop: 24 }}>
                  <h3 style={{ fontSize: 12, fontWeight: 600, marginBottom: 14, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    Timeline
                  </h3>
                  <div style={{ maxHeight: 280, overflowY: 'auto' }}>
                    {emailDetail.timeline.map((ev, i) => (
                      <div key={i} style={{
                        display: 'flex', gap: 10, padding: '8px 0',
                        borderBottom: '1px solid #f1f5f9', fontSize: 13
                      }}>
                        <span style={{ color: '#94a3b8', fontSize: 11, whiteSpace: 'nowrap', fontFamily: 'monospace' }}>
                          {ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : ''}
                        </span>
                        <span style={{ fontWeight: 600, color: '#334155', minWidth: 80 }}>{ev.agent}</span>
                        <span style={{ color: '#64748b' }}>{ev.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', marginBottom: 3, letterSpacing: 0.3 }}>{label}</div>
      <div style={{ fontSize: 13.5, color: '#334155' }}>{value}</div>
    </div>
  );
}
