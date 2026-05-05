import { useParams, useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { ArrowLeft, FileText, Clock, Package, Mail, Award, Download, AlertCircle, CheckCircle, Truck, Star } from 'lucide-react';

const STATUS_COLORS = {
  pending: '#3b82f6', analyzing: '#8b5cf6', sourcing: '#8b5cf6',
  rfqs_sent: '#f59e0b', awaiting_responses: '#ea580c', offers_received: '#ea580c',
  evaluated: '#10b981', evaluation_sent: '#10b981', po_generated: '#10b981',
  completed: '#27AE60', failed: '#E74C3C', rejected: '#E74C3C',
};

function ScoreBar({ value, color = 'var(--turq)', max = 100 }) {
  const pct = Math.min((value || 0) / max * 100, 100);
  const barColor = color || (pct >= 75 ? '#27AE60' : pct >= 50 ? '#F5A623' : '#E74C3C');
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 6, borderRadius: 3, background: '#E0F5F3', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', borderRadius: 3, background: barColor, transition: 'width 0.5s ease' }} />
      </div>
      <span style={{ fontSize: 12, fontWeight: 600, color: barColor, minWidth: 40 }}>{value?.toFixed(1) || '—'}/100</span>
    </div>
  );
}

function InfoRow({ label, value, color }) {
  return (
    <tr>
      <td style={{ width: '38%', color: '#95A5A6', fontSize: 13, padding: '10px 16px' }}>{label}</td>
      <td style={{ padding: '10px 16px', fontWeight: 600, color: color || 'var(--text-primary)' }}>{value || 'N/A'}</td>
    </tr>
  );
}

export default function RequestDetailPage() {
  const { requestId } = useParams();
  const navigate = useNavigate();
  const { data, loading, error } = useApi(`/requests/${requestId}`, { interval: 15000 });
  const { data: timelineData } = useApi(`/requests/${requestId}/timeline`, { interval: 15000 });

  if (loading) return <div className="page-loading">Loading request details...</div>;
  if (error) return <div className="page-error"><AlertCircle size={20} /> Error: {error}</div>;

  const req = data?.data;
  if (!req) return <div className="page-error">Request not found</div>;

  const timeline = timelineData?.data || [];
  const statusColor = STATUS_COLORS[req.status] || '#94a3b8';

  return (
    <div className="page">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 }}>
        <button onClick={() => navigate(-1)} className="detail-back-btn">
          <ArrowLeft size={18} />
        </button>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, color: 'var(--text-primary)' }}>{req.product}</h2>
          <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--turq)' }}>{requestId}</span>
        </div>
        <span className="status-badge" style={{ background: `${statusColor}18`, color: statusColor, fontSize: 13, padding: '6px 14px' }}>
          {req.status?.replace(/_/g, ' ').toUpperCase()}
        </span>
      </div>

      {/* Info + Timeline Row */}
      <div className="detail-row">
        <div className="detail-col" style={{ flex: '0 0 45%' }}>
          <div className="detail-card">
            <div className="detail-card-header">
              <h3><FileText size={16} /> Request Information</h3>
            </div>
            <table className="detail-info-table">
              <tbody>
                <InfoRow label="Product" value={req.product} />
                <InfoRow label="Category" value={req.category} />
                <InfoRow label="Quantity" value={req.quantity ? `${req.quantity} ${req.unit || 'units'}` : null} />
                <InfoRow label="Budget" value={
                  req.budget_min || req.budget_max
                    ? `${req.budget_min || '?'} — ${req.budget_max || '?'} TND`
                    : null
                } color="var(--blue)" />
                <InfoRow label="Deadline" value={req.deadline} />
                <InfoRow label="Requester" value={req.requester_email} />
                <InfoRow label="Valid" value={
                  req.is_valid
                    ? <span style={{ color: '#27AE60' }}>Yes</span>
                    : <span style={{ color: '#E74C3C' }}>No — {req.rejection_reason}</span>
                } />
                <InfoRow label="Created" value={req.created_at ? new Date(req.created_at).toLocaleString('fr-FR') : null} />
              </tbody>
            </table>
          </div>
        </div>

        <div className="detail-col" style={{ flex: 1 }}>
          {/* Timeline */}
          <div className="detail-card" style={{ marginBottom: 16 }}>
            <div className="detail-card-header">
              <h3><Clock size={16} /> Timeline</h3>
              <span className="stat-badge">{timeline.length} events</span>
            </div>
            <div style={{ maxHeight: 220, overflowY: 'auto', padding: 16 }}>
              {timeline.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#95A5A6', padding: 20 }}>No events yet</div>
              ) : (
                <div className="timeline">
                  {timeline.map((ev, i) => (
                    <div key={i} className="timeline-item">
                      <div className={`timeline-dot ${ev.event_type === 'error' ? 'error' : ev.event_type === 'warning' ? 'warning' : 'done'}`} />
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                          <span style={{ fontWeight: 700, color: 'var(--blue)', fontSize: 13 }}>[{ev.agent}]</span>
                          <span style={{ color: '#2C3E50', fontSize: 13 }}>{ev.message}</span>
                        </div>
                        <span style={{ fontSize: 11, color: '#BDC3C7' }}>
                          {ev.created_at ? new Date(ev.created_at).toLocaleString('fr-FR') : ''}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* PDF Download Card */}
          {req.evaluations?.length > 0 && (
            <div className="detail-card" style={{ border: '2px solid var(--turq)', textAlign: 'center', padding: 20 }}>
              <div style={{ fontSize: 32 }}>📄</div>
              <div style={{ fontWeight: 700, color: 'var(--blue)', margin: '8px 0' }}>Evaluation Report Available</div>
              <div style={{ fontSize: 13, color: '#95A5A6', marginBottom: 14 }}>PDF comparison report with supplier scores</div>
              <a href={`/select/${requestId}`} className="btn-download">
                <Download size={14} /> View Report & Select Supplier
              </a>
            </div>
          )}
        </div>
      </div>

      {/* Evaluations */}
      {req.evaluations?.length > 0 && (
        <div className="detail-card" style={{ marginTop: 20 }}>
          <div className="detail-card-header">
            <h3><Award size={16} /> Evaluations</h3>
            <span className="stat-badge" style={{ background: '#D5F5E3', color: '#1E8449' }}>
              {req.evaluations.length} evaluated
            </span>
          </div>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Supplier</th>
                  <th>Overall Score</th>
                  <th>Quality</th>
                  <th>Cost</th>
                  <th>Delivery</th>
                  <th>Performance</th>
                </tr>
              </thead>
              <tbody>
                {req.evaluations.map((ev, i) => (
                  <tr key={ev.id} style={i === 0 ? { background: '#F0FFF4' } : i === 1 ? { background: '#EBF5FB' } : {}}>
                    <td>
                      <span style={{ fontSize: 18, marginRight: 4 }}>
                        {ev.rank === 1 ? '🥇' : ev.rank === 2 ? '🥈' : ev.rank === 3 ? '🥉' : ''}
                      </span>
                      <strong>#{ev.rank}</strong>
                    </td>
                    <td>
                      <strong>{ev.supplier_name}</strong>
                      {ev.rank === 1 && <span className="stat-badge" style={{ marginLeft: 8, background: '#D5F5E3', color: '#1E8449', fontSize: 10 }}>Recommended</span>}
                    </td>
                    <td><ScoreBar value={ev.overall_score} color="#27AE60" /></td>
                    <td><ScoreBar value={ev.qualite_score} color="#9B59B6" /></td>
                    <td><ScoreBar value={ev.cout_score} color="#F5A623" /></td>
                    <td><ScoreBar value={ev.delais_score} color="#4A90D9" /></td>
                    <td><ScoreBar value={ev.performance_score} color="#E74C3C" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Offers */}
      {req.offers?.length > 0 && (
        <div className="detail-card" style={{ marginTop: 20 }}>
          <div className="detail-card-header">
            <h3><Package size={16} /> Offers Received</h3>
            <span className="stat-badge" style={{ background: '#E0F9F7', color: '#0d7377' }}>
              {req.offers.length} offers
            </span>
          </div>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Supplier</th>
                  <th>Unit Price</th>
                  <th>Total Price</th>
                  <th>Delivery</th>
                  <th>Warranty</th>
                  <th>Payment Terms</th>
                </tr>
              </thead>
              <tbody>
                {req.offers.map((o) => {
                  const supplier = req.suppliers?.find(s => s.id === o.supplier_id);
                  return (
                    <tr key={o.id}>
                      <td className="td-title">{supplier?.name || o.supplier_id?.slice(0, 8)}</td>
                      <td><strong style={{ color: 'var(--blue)' }}>{o.unit_price ? `${o.unit_price.toFixed(2)} ${o.currency || 'TND'}` : 'N/A'}</strong></td>
                      <td><strong>{o.total_price ? `${o.total_price.toFixed(2)} ${o.currency || 'TND'}` : 'N/A'}</strong></td>
                      <td><span style={{ color: 'var(--turq)', fontWeight: 600 }}>{o.delivery_days ? `${o.delivery_days} days` : 'N/A'}</span></td>
                      <td style={{ fontSize: 13 }}>{o.warranty || 'N/A'}</td>
                      <td style={{ fontSize: 13 }}>{o.payment_terms || 'N/A'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Suppliers Found */}
      {req.suppliers?.length > 0 && (
        <div className="detail-card" style={{ marginTop: 20 }}>
          <div className="detail-card-header">
            <h3><Truck size={16} /> Suppliers Found</h3>
            <span className="stat-badge" style={{ background: '#E0F9F7', color: '#0d7377' }}>
              {req.suppliers.length} suppliers
            </span>
          </div>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Country</th>
                  <th>Relevance Score</th>
                </tr>
              </thead>
              <tbody>
                {req.suppliers.map((s, i) => (
                  <tr key={s.id}>
                    <td><strong style={{ color: 'var(--blue)' }}>#{i + 1}</strong></td>
                    <td className="td-title">{s.name}</td>
                    <td style={{ fontSize: 13 }}>{s.email || 'N/A'}</td>
                    <td>{s.country || 'N/A'}</td>
                    <td><ScoreBar value={s.relevance_score} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Logs */}
      {timeline.length > 0 && (
        <div className="detail-card" style={{ marginTop: 20 }}>
          <div className="detail-card-header">
            <h3><FileText size={16} /> Pipeline Logs</h3>
            <span className="stat-badge">{timeline.length} entries</span>
          </div>
          <div className="logs-viewer">
            {timeline.map((log, i) => (
              <div key={i} className="log-line">
                <span className="log-time">
                  {log.created_at ? new Date(log.created_at).toLocaleTimeString('fr-FR') : ''}
                </span>
                <span className={`log-agent ${log.event_type === 'error' ? 'log-error' : log.event_type === 'warning' ? 'log-warning' : 'log-info'}`}>
                  [{log.agent}]
                </span>
                <span className="log-message">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
