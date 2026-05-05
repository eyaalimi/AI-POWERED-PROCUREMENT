import { useState } from 'react';
import { apiPost } from '../hooks/useApi';
import { useAuth } from '../context/AuthContext';
import { Send, FileText, Mail, CheckCircle } from 'lucide-react';

const CATEGORIES = [
  'Raw Materials', 'Electronic Components', 'Cables & Connectors',
  'Packaging', 'Tools & Equipment', 'Office Supplies', 'IT Equipment',
  'Safety Equipment', 'Maintenance Parts', 'Other',
];

export default function NewRequestPage() {
  const { user } = useAuth();
  const [form, setForm] = useState({
    product: '', category: '', quantity: '', unit: 'pcs',
    budget_min: '', budget_max: '', deadline: '', department: user?.department || '', notes: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const payload = {
        ...form,
        quantity: form.quantity ? parseFloat(form.quantity) : null,
        budget_min: form.budget_min ? parseFloat(form.budget_min) : null,
        budget_max: form.budget_max ? parseFloat(form.budget_max) : null,
      };
      const res = await apiPost('/requests', payload);
      if (res.id) {
        setResult(res);
      } else {
        setError(res.detail || 'Failed to create request');
      }
    } catch {
      setError('Failed to create request');
    } finally {
      setSubmitting(false);
    }
  };

  const openGmail = () => {
    if (!result) return;
    const to = 'test@procurement-ai.click';
    const subject = encodeURIComponent(result.mailto_subject);
    const body = encodeURIComponent(result.mailto_body);
    window.open(`https://mail.google.com/mail/?view=cm&to=${to}&su=${subject}&body=${body}`, '_blank');
  };

  const resetForm = () => {
    setResult(null);
    setForm({
      product: '', category: '', quantity: '', unit: 'pcs',
      budget_min: '', budget_max: '', deadline: '', department: user?.department || '', notes: '',
    });
  };

  if (result) {
    return (
      <div style={{ padding: '24px 32px', maxWidth: 600 }}>
        <div style={{
          background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
          padding: 32, textAlign: 'center',
        }}>
          <div style={{
            width: 56, height: 56, borderRadius: '50%', background: '#dcfce7',
            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px',
          }}>
            <CheckCircle size={28} color="#16a34a" />
          </div>
          <h2 style={{ margin: '0 0 8px', fontSize: 20 }}>Request Created!</h2>
          <p style={{ color: '#64748b', margin: '0 0 24px', fontSize: 14 }}>
            Your procurement request has been saved. Send an email notification to the procurement team.
          </p>
          <button onClick={openGmail} style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: '#ea4335', color: '#fff', border: 'none', borderRadius: 8,
            padding: '12px 24px', fontSize: 14, fontWeight: 600, cursor: 'pointer', marginBottom: 12,
          }}>
            <Mail size={18} />
            Open Gmail & Send Notification
          </button>
          <br />
          <button onClick={resetForm} style={{
            background: 'none', border: '1px solid #e2e8f0', borderRadius: 8,
            padding: '10px 20px', fontSize: 13, color: '#64748b', cursor: 'pointer', marginTop: 8,
          }}>
            Create Another Request
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px 32px', maxWidth: 720 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}>
        <FileText size={24} />
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>New Procurement Request</h1>
      </div>

      {error && (
        <div style={{ background: '#fef2f2', color: '#dc2626', padding: '10px 16px', borderRadius: 8, marginBottom: 16, fontSize: 13 }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{
        background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: 24,
      }}>
        <div style={gridStyle}>
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={labelStyle}>Product / Service *</label>
            <input value={form.product} onChange={set('product')} required placeholder="e.g. Copper Wire 2.5mm" style={inputStyle} />
          </div>

          <div>
            <label style={labelStyle}>Category</label>
            <select value={form.category} onChange={set('category')} style={inputStyle}>
              <option value="">Select category...</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label style={labelStyle}>Department</label>
            <input value={form.department} onChange={set('department')} placeholder="e.g. Engineering" style={inputStyle} />
          </div>

          <div>
            <label style={labelStyle}>Quantity</label>
            <input type="number" value={form.quantity} onChange={set('quantity')} placeholder="100" min="0" step="any" style={inputStyle} />
          </div>

          <div>
            <label style={labelStyle}>Unit</label>
            <select value={form.unit} onChange={set('unit')} style={inputStyle}>
              {['pcs', 'kg', 'm', 'L', 'sets', 'rolls', 'boxes'].map(u => <option key={u} value={u}>{u}</option>)}
            </select>
          </div>

          <div>
            <label style={labelStyle}>Budget Min (TND)</label>
            <input type="number" value={form.budget_min} onChange={set('budget_min')} placeholder="0" min="0" step="any" style={inputStyle} />
          </div>

          <div>
            <label style={labelStyle}>Budget Max (TND)</label>
            <input type="number" value={form.budget_max} onChange={set('budget_max')} placeholder="10000" min="0" step="any" style={inputStyle} />
          </div>

          <div>
            <label style={labelStyle}>Deadline</label>
            <input type="date" value={form.deadline} onChange={set('deadline')} style={inputStyle} />
          </div>

          <div style={{ gridColumn: '1 / -1' }}>
            <label style={labelStyle}>Notes</label>
            <textarea value={form.notes} onChange={set('notes')} rows={3} placeholder="Additional requirements or specifications..." style={{ ...inputStyle, resize: 'vertical' }} />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 20 }}>
          <button type="submit" disabled={submitting} style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 8,
            padding: '10px 24px', fontSize: 14, fontWeight: 600, cursor: 'pointer',
          }}>
            <Send size={16} />
            {submitting ? 'Submitting...' : 'Submit Request'}
          </button>
        </div>
      </form>
    </div>
  );
}

const gridStyle = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 };
const labelStyle = { display: 'block', fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 6 };
const inputStyle = {
  width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid #e2e8f0',
  fontSize: 14, outline: 'none', boxSizing: 'border-box',
};
