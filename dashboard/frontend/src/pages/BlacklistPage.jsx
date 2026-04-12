import { useState } from 'react';
import { useApi, apiPost, apiDelete } from '../hooks/useApi';
import { ShieldOff } from 'lucide-react';

export default function BlacklistPage() {
  const { data, loading, error, refetch } = useApi('/suppliers/blacklist', { interval: 15000 });
  const [form, setForm] = useState({ supplier_name: '', supplier_email: '', reason: '' });
  const [submitting, setSubmitting] = useState(false);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.supplier_name || !form.reason) return;
    setSubmitting(true);
    await apiPost('/suppliers/blacklist', form);
    setForm({ supplier_name: '', supplier_email: '', reason: '' });
    setSubmitting(false);
    refetch();
  };

  const handleRemove = async (id) => {
    if (!confirm('Remove this supplier from the blacklist?')) return;
    await apiDelete(`/suppliers/blacklist/${id}`);
    refetch();
  };

  if (loading) return <div className="page-loading">Loading blacklist...</div>;
  if (error) return <div className="page-error">Error: {error}</div>;

  const blacklist = data?.blacklist || [];

  return (
    <div className="page">
      <form className="blacklist-form" onSubmit={handleAdd}>
        <input
          placeholder="Supplier name"
          value={form.supplier_name}
          onChange={(e) => setForm({ ...form, supplier_name: e.target.value })}
          required
        />
        <input
          placeholder="Email (optional)"
          value={form.supplier_email}
          onChange={(e) => setForm({ ...form, supplier_email: e.target.value })}
        />
        <input
          placeholder="Reason"
          value={form.reason}
          onChange={(e) => setForm({ ...form, reason: e.target.value })}
          required
        />
        <button type="submit" disabled={submitting}>
          {submitting ? 'Adding...' : 'Add to Blacklist'}
        </button>
      </form>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Supplier</th>
              <th>Email</th>
              <th>Reason</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {blacklist.map((b) => (
              <tr key={b.id}>
                <td className="td-title">{b.supplier_name}</td>
                <td>{b.supplier_email || '—'}</td>
                <td style={{ color: '#64748b' }}>{b.reason}</td>
                <td style={{ color: '#94a3b8', fontSize: 13 }}>{new Date(b.created_at).toLocaleDateString('fr-FR')}</td>
                <td>
                  <button className="btn btn-danger btn-sm" onClick={() => handleRemove(b.id)}>
                    <ShieldOff size={14} /> Remove
                  </button>
                </td>
              </tr>
            ))}
            {blacklist.length === 0 && (
              <tr><td colSpan={5} className="empty-row">Blacklist is empty</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
