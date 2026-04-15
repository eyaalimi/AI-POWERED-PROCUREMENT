import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useNavigate } from 'react-router-dom';
import KpiCard from '../components/KpiCard';
import { FileText, CheckCircle, HardDrive, Search, Download, Eye, Info } from 'lucide-react';

export default function ReportsPage() {
  const { data, loading, error } = useApi('/dashboard/reports', { interval: 30000 });
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  if (loading) return <div className="page-loading">Loading reports...</div>;
  if (error) return <div className="page-error">Error: {error}</div>;

  const reports = data?.reports || [];
  const filtered = search
    ? reports.filter(r =>
        r.product?.toLowerCase().includes(search.toLowerCase()) ||
        r.request_id?.toLowerCase().includes(search.toLowerCase()) ||
        r.supplier_name?.toLowerCase().includes(search.toLowerCase())
      )
    : reports;

  return (
    <div className="page">
      {/* KPI Row */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 24 }}>
        <KpiCard icon={FileText} title="Total Reports" value={reports.length} color="#40E0D0" />
        <KpiCard icon={CheckCircle} title="Available" value={reports.length} color="#27AE60" subtitle="Ready for download" />
        <KpiCard icon={HardDrive} title="Requests Evaluated" value={reports.length} color="#F5A623" subtitle="With PDF reports" />
      </div>

      {/* Table Card */}
      <div className="detail-card">
        <div className="detail-card-header">
          <h3><FileText size={16} /> RFQ PDF Reports</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div className="search-wrapper" style={{ minWidth: 220 }}>
              <Search size={14} />
              <input
                type="text"
                placeholder="Search reports..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <span className="stat-badge" style={{ background: 'var(--blue)', color: 'white' }}>
              {filtered.length}
            </span>
          </div>
        </div>

        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 20px' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
            <div style={{ fontWeight: 700, color: 'var(--blue)', marginBottom: 8, fontSize: 16 }}>
              No RFQ Reports Yet
            </div>
            <div style={{ fontSize: 14, color: '#95A5A6', marginBottom: 24, maxWidth: 400, margin: '0 auto 24px' }}>
              RFQ reports are generated automatically when the system evaluates supplier offers for a procurement request.
            </div>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Request ID</th>
                  <th>Product</th>
                  <th>Best Supplier</th>
                  <th>Score</th>
                  <th>Date</th>
                  <th style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r, i) => (
                  <tr key={r.request_id}>
                    <td><span style={{ color: 'var(--turq)', fontWeight: 700 }}>{i + 1}</span></td>
                    <td>
                      <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--blue)', fontWeight: 700 }}>
                        {r.request_id.slice(0, 8)}...
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 18 }}>📄</span>
                        <div>
                          <div className="td-title">{r.product}</div>
                          <div style={{ fontSize: 11, color: '#BDC3C7' }}>Evaluation Report PDF</div>
                        </div>
                      </div>
                    </td>
                    <td><strong>{r.supplier_name || 'N/A'}</strong></td>
                    <td>
                      <strong style={{ color: '#27AE60' }}>{r.overall_score?.toFixed(1) || '—'}</strong>
                      <span style={{ color: '#95A5A6', fontSize: 12 }}>/100</span>
                    </td>
                    <td style={{ fontSize: 12, color: '#95A5A6' }}>
                      {r.created_at ? new Date(r.created_at).toLocaleDateString('fr-FR') : 'N/A'}
                    </td>
                    <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                      <button
                        className="btn-sm-action"
                        onClick={() => navigate(`/request/${r.request_id}`)}
                        title="View Details"
                      >
                        <Eye size={13} /> Detail
                      </button>
                      <a
                        href={`/select/${r.request_id}`}
                        className="btn-sm-action primary"
                        style={{ marginLeft: 6 }}
                      >
                        <Download size={13} /> Report
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="detail-card" style={{ marginTop: 20 }}>
        <div className="detail-card-header">
          <h3><Info size={16} /> About RFQ Reports</h3>
        </div>
        <div className="info-grid">
          <div className="info-box" style={{ borderLeftColor: 'var(--turq)' }}>
            <div className="info-box-title">📄 What is a RFQ Report?</div>
            <div className="info-box-text">
              A PDF document containing the evaluation and comparison of all supplier offers for a procurement request, including QCDP scores and recommendations.
            </div>
          </div>
          <div className="info-box" style={{ borderLeftColor: '#27AE60' }}>
            <div className="info-box-title">⚙ When is it generated?</div>
            <div className="info-box-text">
              Automatically by the Evaluation Engine after collecting and scoring supplier offers. One report is generated per procurement request.
            </div>
          </div>
          <div className="info-box" style={{ borderLeftColor: '#F5A623' }}>
            <div className="info-box-title">💾 Storage Location</div>
            <div className="info-box-text">
              All reports are stored in AWS S3 and linked to the corresponding evaluation record in the database.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
