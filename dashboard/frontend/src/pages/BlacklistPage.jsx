import { useState } from 'react';
import { useApi, apiPost, apiDelete } from '../hooks/useApi';

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
    if (!confirm('Retirer ce fournisseur de la blacklist ?')) return;
    await apiDelete(`/suppliers/blacklist/${id}`);
    refetch();
  };

  if (loading) return <div className="page-loading">Chargement...</div>;
  if (error) return <div className="page-error">Erreur: {error}</div>;

  const blacklist = data?.blacklist || [];

  return (
    <div className="page">
      <h1>Blacklist Fournisseurs</h1>

      <form className="blacklist-form" onSubmit={handleAdd}>
        <input
          placeholder="Nom du fournisseur"
          value={form.supplier_name}
          onChange={(e) => setForm({ ...form, supplier_name: e.target.value })}
          required
        />
        <input
          placeholder="Email (optionnel)"
          value={form.supplier_email}
          onChange={(e) => setForm({ ...form, supplier_email: e.target.value })}
        />
        <input
          placeholder="Raison"
          value={form.reason}
          onChange={(e) => setForm({ ...form, reason: e.target.value })}
          required
        />
        <button type="submit" disabled={submitting}>
          {submitting ? 'Ajout...' : 'Ajouter'}
        </button>
      </form>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Fournisseur</th>
              <th>Email</th>
              <th>Raison</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {blacklist.map((b) => (
              <tr key={b.id}>
                <td className="td-title">{b.supplier_name}</td>
                <td>{b.supplier_email || '—'}</td>
                <td>{b.reason}</td>
                <td>{new Date(b.created_at).toLocaleDateString('fr-FR')}</td>
                <td>
                  <button className="btn-danger btn-sm" onClick={() => handleRemove(b.id)}>Retirer</button>
                </td>
              </tr>
            ))}
            {blacklist.length === 0 && (
              <tr><td colSpan={5} className="empty-row">Blacklist vide</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
