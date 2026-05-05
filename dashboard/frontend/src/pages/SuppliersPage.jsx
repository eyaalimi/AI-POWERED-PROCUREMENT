import { useState } from 'react';
import { useApi, exportCsv } from '../hooks/useApi';
import { Search, Download, Star, AlertTriangle, TrendingUp, Users, ShieldOff, Mail, Globe, Award } from 'lucide-react';

export default function SuppliersPage() {
  const { data, loading, error } = useApi('/suppliers?limit=200', { interval: 15000 });
  const [search, setSearch] = useState('');
  const [tab, setTab] = useState('all'); // all | reviews

  if (loading) return <div className="page-loading">Loading suppliers...</div>;
  if (error) return <div className="page-error">Error: {error}</div>;

  let suppliers = data?.suppliers || [];

  // Compute stats from full data before filtering
  const totalSuppliers = suppliers.length;
  const withScores = suppliers.filter(s => s.avg_qcdp_score != null);
  const avgScore = withScores.length ? (withScores.reduce((a, s) => a + s.avg_qcdp_score, 0) / withScores.length) : 0;
  const withRate = suppliers.filter(s => s.response_rate != null);
  const avgResponseRate = withRate.length ? (withRate.reduce((a, s) => a + s.response_rate, 0) / withRate.length) : 0;
  const blacklistedCount = suppliers.filter(s => s.is_blacklisted).length;

  // Reviews data
  const nonResponsive = suppliers.filter(s => s.rfqs_received > 0 && s.response_rate === 0).sort((a, b) => b.rfqs_received - a.rfqs_received);
  const topRated = [...withScores].sort((a, b) => b.avg_qcdp_score - a.avg_qcdp_score).slice(0, 10);
  const frequentlySourced = [...suppliers].sort((a, b) => b.times_sourced - a.times_sourced).slice(0, 10);
  const lowPerformers = withScores.filter(s => s.avg_qcdp_score < 40).sort((a, b) => a.avg_qcdp_score - b.avg_qcdp_score);

  if (search) {
    const q = search.toLowerCase();
    suppliers = suppliers.filter(s =>
      (s.name || '').toLowerCase().includes(q) || (s.email || '').toLowerCase().includes(q)
      || (s.country || '').toLowerCase().includes(q) || (s.category || '').toLowerCase().includes(q)
    );
  }

  return (
    <div className="page">
      {/* KPI Cards */}
      <div className="supplier-kpi-grid">
        <div className="supplier-kpi-card">
          <div className="supplier-kpi-icon" style={{ background: 'rgba(64,224,208,0.12)', color: 'var(--turq3)' }}><Users size={20} /></div>
          <div className="supplier-kpi-info">
            <span className="supplier-kpi-value">{totalSuppliers}</span>
            <span className="supplier-kpi-label">Total Suppliers</span>
          </div>
        </div>
        <div className="supplier-kpi-card">
          <div className="supplier-kpi-icon" style={{ background: 'rgba(27,58,107,0.1)', color: 'var(--blue)' }}><Star size={20} /></div>
          <div className="supplier-kpi-info">
            <span className="supplier-kpi-value">{avgScore.toFixed(1)}<span className="supplier-kpi-unit">/100</span></span>
            <span className="supplier-kpi-label">Avg QCDP Score</span>
          </div>
        </div>
        <div className="supplier-kpi-card">
          <div className="supplier-kpi-icon" style={{ background: 'rgba(39,174,96,0.1)', color: 'var(--success)' }}><TrendingUp size={20} /></div>
          <div className="supplier-kpi-info">
            <span className="supplier-kpi-value">{avgResponseRate.toFixed(0)}<span className="supplier-kpi-unit">%</span></span>
            <span className="supplier-kpi-label">Avg Response Rate</span>
          </div>
        </div>
        <div className="supplier-kpi-card">
          <div className="supplier-kpi-icon" style={{ background: 'rgba(231,76,60,0.1)', color: 'var(--danger)' }}><ShieldOff size={20} /></div>
          <div className="supplier-kpi-info">
            <span className="supplier-kpi-value">{blacklistedCount}</span>
            <span className="supplier-kpi-label">Blacklisted</span>
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="supplier-tabs">
        <button className={`supplier-tab ${tab === 'all' ? 'active' : ''}`} onClick={() => setTab('all')}>
          <Users size={15} /> All Suppliers
        </button>
        <button className={`supplier-tab ${tab === 'reviews' ? 'active' : ''}`} onClick={() => setTab('reviews')}>
          <Award size={15} /> Supplier Reviews
        </button>
      </div>

      {tab === 'all' && (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            <div className="search-wrapper" style={{ flex: 1 }}>
              <Search size={16} />
              <input type="text" placeholder="Search by name, email, country or category..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <button onClick={() => exportCsv('/export/suppliers')} className="btn-export">
              <Download size={15} /> Export CSV
            </button>
          </div>

          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Supplier</th>
                  <th>Category</th>
                  <th>Country</th>
                  <th>QCDP Score</th>
                  <th>Response Rate</th>
                  <th>RFQs / Offers</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((s, i) => (
                  <tr key={i} className={s.is_blacklisted ? 'row-blacklisted' : ''}>
                    <td>
                      <div className="supplier-cell">
                        <div className="supplier-avatar">{(s.name || '?')[0].toUpperCase()}</div>
                        <div>
                          <div className="td-title">{s.name}</div>
                          <div className="td-subtitle">{s.email || '—'}</div>
                        </div>
                      </div>
                    </td>
                    <td><span className="tag-pill">{s.category || '—'}</span></td>
                    <td style={{ fontSize: 13 }}>{s.country || '—'}</td>
                    <td>
                      <div className="score-bar-inline">
                        <div className="score-bar-track">
                          <div className="score-bar-fill" style={{ width: `${s.avg_qcdp_score || 0}%`, background: scoreColor(s.avg_qcdp_score) }} />
                        </div>
                        <span className="score-bar-val">{s.avg_qcdp_score?.toFixed(1) || '—'}</span>
                      </div>
                    </td>
                    <td>
                      <div className="score-bar-inline">
                        <div className="score-bar-track">
                          <div className="score-bar-fill" style={{ width: `${s.response_rate || 0}%`, background: rateColor(s.response_rate) }} />
                        </div>
                        <span className="score-bar-val">{s.response_rate != null ? `${s.response_rate}%` : '—'}</span>
                      </div>
                    </td>
                    <td style={{ fontSize: 13, fontWeight: 500 }}>
                      {s.rfqs_received ?? 0} / {s.offers_sent ?? 0}
                    </td>
                    <td>
                      {s.is_blacklisted
                        ? <span className="status-badge status-blacklisted">Blacklisted</span>
                        : s.response_rate === 0 && s.rfqs_received > 0
                          ? <span className="status-badge status-no-response">No Response</span>
                          : <span className="status-badge status-active">Active</span>
                      }
                    </td>
                  </tr>
                ))}
                {suppliers.length === 0 && (
                  <tr><td colSpan={7} className="empty-row">No suppliers found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'reviews' && (
        <div className="reviews-grid">
          {/* Non-responsive suppliers */}
          <div className="review-card review-card-warn">
            <div className="review-card-header">
              <AlertTriangle size={18} />
              <h3>Non-Responsive Suppliers</h3>
              <span className="review-count">{nonResponsive.length}</span>
            </div>
            <p className="review-desc">Suppliers who received RFQs but never replied with an offer.</p>
            {nonResponsive.length > 0 ? (
              <div className="review-list">
                {nonResponsive.slice(0, 8).map((s, i) => (
                  <div key={i} className="review-item">
                    <div className="supplier-avatar small">{(s.name || '?')[0].toUpperCase()}</div>
                    <div className="review-item-info">
                      <span className="review-item-name">{s.name}</span>
                      <span className="review-item-detail">{s.rfqs_received} RFQs sent — 0 replies</span>
                    </div>
                    <Mail size={14} style={{ color: 'var(--text-muted)' }} />
                  </div>
                ))}
              </div>
            ) : <p className="review-empty">All suppliers have responded at least once.</p>}
          </div>

          {/* Top rated */}
          <div className="review-card review-card-success">
            <div className="review-card-header">
              <Star size={18} />
              <h3>Top Rated Suppliers</h3>
              <span className="review-count">{topRated.length}</span>
            </div>
            <p className="review-desc">Best QCDP scores from evaluated suppliers.</p>
            {topRated.length > 0 ? (
              <div className="review-list">
                {topRated.map((s, i) => (
                  <div key={i} className="review-item">
                    <div className="review-rank">{i < 3 ? ['🥇','🥈','🥉'][i] : `#${i+1}`}</div>
                    <div className="review-item-info">
                      <span className="review-item-name">{s.name}</span>
                      <span className="review-item-detail">{s.email}</span>
                    </div>
                    <div className="review-score" style={{ color: scoreColor(s.avg_qcdp_score) }}>{s.avg_qcdp_score.toFixed(1)}</div>
                  </div>
                ))}
              </div>
            ) : <p className="review-empty">No evaluated suppliers yet.</p>}
          </div>

          {/* Frequently sourced */}
          <div className="review-card review-card-info">
            <div className="review-card-header">
              <Globe size={18} />
              <h3>Most Frequently Sourced</h3>
              <span className="review-count">{frequentlySourced.filter(s => s.times_sourced > 1).length}</span>
            </div>
            <p className="review-desc">Suppliers who appear most often across procurement requests.</p>
            {frequentlySourced.length > 0 ? (
              <div className="review-list">
                {frequentlySourced.map((s, i) => (
                  <div key={i} className="review-item">
                    <div className="supplier-avatar small">{(s.name || '?')[0].toUpperCase()}</div>
                    <div className="review-item-info">
                      <span className="review-item-name">{s.name}</span>
                      <span className="review-item-detail">{s.times_sourced} times sourced • {s.offers_sent} offers</span>
                    </div>
                    <TrendingUp size={14} style={{ color: 'var(--turq3)' }} />
                  </div>
                ))}
              </div>
            ) : <p className="review-empty">No sourcing data yet.</p>}
          </div>

          {/* Low performers */}
          <div className="review-card review-card-danger">
            <div className="review-card-header">
              <ShieldOff size={18} />
              <h3>Low Performance</h3>
              <span className="review-count">{lowPerformers.length}</span>
            </div>
            <p className="review-desc">Suppliers scoring below 40/100 — consider reviewing or blacklisting.</p>
            {lowPerformers.length > 0 ? (
              <div className="review-list">
                {lowPerformers.slice(0, 8).map((s, i) => (
                  <div key={i} className="review-item">
                    <div className="supplier-avatar small">{(s.name || '?')[0].toUpperCase()}</div>
                    <div className="review-item-info">
                      <span className="review-item-name">{s.name}</span>
                      <span className="review-item-detail">Score: {s.avg_qcdp_score.toFixed(1)} / 100</span>
                    </div>
                    <div className="review-score" style={{ color: 'var(--danger)' }}>{s.avg_qcdp_score.toFixed(1)}</div>
                  </div>
                ))}
              </div>
            ) : <p className="review-empty">No low-performing suppliers.</p>}
          </div>
        </div>
      )}
    </div>
  );
}

function scoreColor(score) {
  if (!score) return '#94a3b8';
  if (score >= 75) return '#27AE60';
  if (score >= 50) return '#F5A623';
  return '#E74C3C';
}

function rateColor(rate) {
  if (rate == null) return '#94a3b8';
  if (rate >= 70) return '#27AE60';
  if (rate >= 40) return '#F5A623';
  return '#E74C3C';
}
