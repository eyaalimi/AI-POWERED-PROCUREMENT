import { useState } from 'react';
import { useApi, exportCsv } from '../hooks/useApi';
import { Search, Download } from 'lucide-react';

export default function SuppliersPage() {
  const { data, loading, error } = useApi('/suppliers', { interval: 15000 });
  const [search, setSearch] = useState('');

  if (loading) return <div className="page-loading">Loading suppliers...</div>;
  if (error) return <div className="page-error">Error: {error}</div>;

  let suppliers = data?.suppliers || [];
  if (search) {
    const q = search.toLowerCase();
    suppliers = suppliers.filter(s =>
      (s.name || '').toLowerCase().includes(q) || (s.email || '').toLowerCase().includes(q)
    );
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <div className="search-wrapper" style={{ flex: 1 }}>
          <Search size={16} />
          <input
            type="text"
            placeholder="Search suppliers..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <button onClick={() => exportCsv('/export/suppliers')} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8,
          padding: '8px 14px', fontSize: 13, color: '#475569', cursor: 'pointer', fontWeight: 500,
        }}>
          <Download size={15} /> Export CSV
        </button>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Supplier</th>
              <th>Email</th>
              <th>Avg QCDP Score</th>
              <th>Response Rate</th>
              <th>Offers</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((s, i) => (
              <tr key={i}>
                <td className="td-title">{s.name}</td>
                <td style={{ color: '#6366f1' }}>{s.email || '—'}</td>
                <td>
                  <div className="score-bar">
                    <div style={{ width: 80, height: 6, borderRadius: 3, background: '#f1f5f9', overflow: 'hidden' }}>
                      <div className="score-fill" style={{ width: `${(s.avg_score || 0)}%`, backgroundColor: scoreColor(s.avg_score) }} />
                    </div>
                    <span>{s.avg_score?.toFixed(1) || '—'}</span>
                  </div>
                </td>
                <td style={{ fontWeight: 500 }}>{s.response_rate != null ? `${s.response_rate}%` : '—'}</td>
                <td>{s.total_offers ?? '—'}</td>
              </tr>
            ))}
            {suppliers.length === 0 && (
              <tr><td colSpan={5} className="empty-row">No suppliers found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function scoreColor(score) {
  if (!score) return '#94a3b8';
  if (score >= 75) return '#10b981';
  if (score >= 50) return '#f59e0b';
  return '#ef4444';
}
