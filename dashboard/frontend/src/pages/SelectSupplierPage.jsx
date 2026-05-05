import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useApi, apiPost } from '../hooks/useApi';
import { Award, CheckCircle, Package } from 'lucide-react';

export default function SelectSupplierPage() {
  const { requestId } = useParams();
  const [selectedEval, setSelectedEval] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [poResult, setPoResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    quantity: '', delivery_address: '', cost_center: '',
    department: '', requester_name: '', notes: '',
  });

  const { data, loading, error } = useApi(`/requests/${requestId}`);
  const req = data?.data;

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#f8fafc' }}>
      <div style={{ textAlign: 'center', color: '#94a3b8' }}>
        <div style={{ width: 40, height: 40, border: '3px solid #e2e8f0', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
        Loading evaluation...
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    </div>
  );

  if (error || !req) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#f8fafc' }}>
      <div style={{ textAlign: 'center', color: '#ef4444', maxWidth: 400 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>!</div>
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Unable to load evaluation</h2>
        <p style={{ color: '#94a3b8', fontSize: 14 }}>Please check the link in your email or try again later.</p>
      </div>
    </div>
  );

  const evaluations = req.evaluations || [];

  const handleSelect = (ev) => {
    setSelectedEval(ev);
    setShowForm(true);
    setFormData(f => ({ ...f, quantity: req.quantity || '' }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const result = await apiPost(`/orders/requests/${requestId}/purchase-order`, {
        evaluation_id: selectedEval.id,
        ...formData,
        quantity: formData.quantity ? Number(formData.quantity) : null,
      });
      setPoResult(result.data);
    } catch {
      alert('Error creating purchase order');
    }
    setSubmitting(false);
  };

  // Confirmation page
  if (poResult) {
    return (
      <div style={{ minHeight: '100vh', background: '#f8fafc', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ maxWidth: 560, width: '100%', padding: '0 20px', textAlign: 'center' }}>
          <div style={{ width: 72, height: 72, borderRadius: '50%', background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
            <CheckCircle size={36} color="#10b981" />
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, color: '#0f172a' }}>Purchase Order Created</h1>
          <p style={{ color: '#94a3b8', marginBottom: 28, fontSize: 15 }}>Your order has been submitted successfully.</p>

          <div style={{ background: '#fff', borderRadius: 12, padding: 28, textAlign: 'left', boxShadow: '0 1px 3px rgba(0,0,0,0.06)', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              <InfoItem label="PO Reference" value={<span style={{ fontFamily: "'SF Mono', monospace", fontWeight: 700, fontSize: 16, color: '#6366f1' }}>{poResult.po_reference}</span>} />
              <InfoItem label="Product" value={poResult.product} />
              <InfoItem label="Supplier" value={poResult.supplier_name} />
              <InfoItem label="Total" value={`${poResult.total_price || '—'} ${poResult.currency}`} />
              <InfoItem label="Quantity" value={`${poResult.quantity || '—'} ${poResult.unit || ''}`} />
              <InfoItem label="Status" value={
                <span style={{ background: '#fffbeb', color: '#f59e0b', padding: '4px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600 }}>
                  AWAITING DELIVERY
                </span>
              } />
            </div>
          </div>

          <div style={{ marginTop: 24 }}>
            <a href="/orders" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '12px 24px', background: '#6366f1', color: '#fff', borderRadius: 8,
              textDecoration: 'none', fontWeight: 600, fontSize: 14, transition: '0.2s',
            }}>
              <Package size={16} /> Track Your Order
            </a>
          </div>
        </div>
      </div>
    );
  }

  // PO form
  if (showForm && selectedEval) {
    const offer = req.offers?.find(o => o.supplier_id && selectedEval.supplier_email);
    return (
      <div style={{ minHeight: '100vh', background: '#f8fafc', padding: '40px 20px' }}>
        <div style={{ maxWidth: 700, margin: '0 auto' }}>
          <h1 style={{ fontSize: 22, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 10, color: '#0f172a' }}>
            <Package size={22} color="#6366f1" />
            Purchase Order
          </h1>
          <p style={{ color: '#94a3b8', marginBottom: 28 }}>Complete the form for <strong style={{ color: '#334155' }}>{selectedEval.supplier_name}</strong></p>

          <form onSubmit={handleSubmit} style={{ background: '#fff', borderRadius: 12, padding: 28, boxShadow: '0 1px 3px rgba(0,0,0,0.06)', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20, paddingBottom: 20, borderBottom: '1px solid #f1f5f9' }}>
              <FieldReadonly label="Product" value={req.product} />
              <FieldReadonly label="Supplier" value={selectedEval.supplier_name} />
              <FieldReadonly label="Supplier Email" value={selectedEval.supplier_email} />
              <FieldReadonly label="Unit Price" value={offer?.unit_price ? `${offer.unit_price} TND` : '—'} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <FormField label="Quantity" value={formData.quantity} onChange={v => setFormData(f => ({ ...f, quantity: v }))} type="number" />
              <FormField label="Requester Name" value={formData.requester_name} onChange={v => setFormData(f => ({ ...f, requester_name: v }))} />
              <FormField label="Delivery Address" value={formData.delivery_address} onChange={v => setFormData(f => ({ ...f, delivery_address: v }))} />
              <FormField label="Cost Center" value={formData.cost_center} onChange={v => setFormData(f => ({ ...f, cost_center: v }))} />
              <FormField label="Department" value={formData.department} onChange={v => setFormData(f => ({ ...f, department: v }))} />
            </div>

            <div style={{ marginTop: 16 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.3 }}>Notes</label>
              <textarea value={formData.notes} onChange={e => setFormData(f => ({ ...f, notes: e.target.value }))}
                rows={3} style={{ width: '100%', padding: '10px 14px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 14, resize: 'vertical', fontFamily: 'inherit' }} />
            </div>

            <div style={{ marginTop: 24, display: 'flex', gap: 12 }}>
              <button type="button" onClick={() => { setShowForm(false); setSelectedEval(null); }}
                style={{ padding: '10px 20px', background: '#f1f5f9', border: 'none', borderRadius: 8, fontSize: 14, cursor: 'pointer', fontFamily: 'inherit', fontWeight: 500, color: '#64748b' }}>
                Back
              </button>
              <button type="submit" disabled={submitting}
                style={{ padding: '10px 28px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, fontSize: 14, cursor: 'pointer', opacity: submitting ? 0.6 : 1, fontFamily: 'inherit', transition: '0.2s' }}>
                {submitting ? 'Submitting...' : 'Submit Purchase Order'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // Evaluation cards
  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', padding: '40px 20px' }}>
      <div style={{ maxWidth: 940, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{ width: 56, height: 56, borderRadius: 14, background: 'linear-gradient(135deg, #6366f1, #818cf8)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <Award size={28} color="#fff" />
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 6, color: '#0f172a' }}>
            Supplier Evaluation
          </h1>
          <p style={{ color: '#64748b', fontSize: 15 }}>
            <strong style={{ color: '#334155' }}>{req.product}</strong> — {evaluations.length} supplier(s) evaluated
          </p>
        </div>

        {evaluations.length === 0 && (
          <div style={{ background: '#fff', borderRadius: 12, padding: 60, textAlign: 'center', color: '#94a3b8', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>...</div>
            <p style={{ fontSize: 15 }}>No evaluations available yet.</p>
            <p style={{ fontSize: 13, marginTop: 4 }}>Evaluations will appear here once the analysis is complete.</p>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {evaluations.map(ev => {
            const isRecommended = ev.rank === 1;
            const score = ev.overall_score || 0;
            return (
              <div key={ev.id} style={{
                background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                border: isRecommended ? '2px solid #10b981' : '1px solid #e2e8f0',
                position: 'relative', transition: '0.2s',
              }}>
                {isRecommended && (
                  <div style={{ position: 'absolute', top: -11, right: 16, background: 'linear-gradient(135deg, #10b981, #34d399)', color: '#fff', padding: '3px 12px', borderRadius: 20, fontSize: 10, fontWeight: 700, letterSpacing: 0.5, textTransform: 'uppercase' }}>
                    Recommended
                  </div>
                )}
                <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4, color: '#0f172a' }}>{ev.supplier_name}</h3>
                <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 16 }}>{ev.supplier_email}</p>

                <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 20 }}>
                  <div style={{
                    width: 64, height: 64, borderRadius: '50%', position: 'relative',
                    background: `conic-gradient(${scoreColor(score)} ${score * 3.6}deg, #f1f5f9 0deg)`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 15, color: '#0f172a' }}>
                      {score?.toFixed(0) || '—'}
                    </div>
                  </div>
                  <div style={{ fontSize: 13, display: 'grid', gap: 4 }}>
                    <ScoreLine label="Quality" value={ev.qualite_score} />
                    <ScoreLine label="Cost" value={ev.cout_score} />
                    <ScoreLine label="Delivery" value={ev.delais_score} />
                    <ScoreLine label="Performance" value={ev.performance_score} />
                  </div>
                </div>

                {ev.recommendation && (
                  <p style={{ fontSize: 12, color: '#64748b', marginBottom: 16, fontStyle: 'italic', lineHeight: 1.5, padding: '8px 12px', background: '#f8fafc', borderRadius: 8 }}>
                    {ev.recommendation}
                  </p>
                )}

                <button onClick={() => handleSelect(ev)} style={{
                  width: '100%', padding: '11px 0',
                  background: isRecommended ? '#10b981' : '#6366f1',
                  color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, fontSize: 14,
                  cursor: 'pointer', transition: '0.2s', fontFamily: 'inherit',
                }}>
                  Select This Supplier
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ScoreLine({ label, value }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ color: '#94a3b8', fontSize: 12, minWidth: 80 }}>{label}</span>
      <div style={{ width: 48, height: 4, borderRadius: 2, background: '#f1f5f9', overflow: 'hidden' }}>
        <div style={{ width: `${value || 0}%`, height: '100%', borderRadius: 2, background: scoreColor(value), transition: 'width 0.6s ease' }} />
      </div>
      <span style={{ fontWeight: 600, fontSize: 12, color: '#334155', minWidth: 24 }}>{value?.toFixed(0) || '—'}</span>
    </div>
  );
}

function scoreColor(score) {
  if (!score) return '#94a3b8';
  if (score >= 75) return '#10b981';
  if (score >= 50) return '#f59e0b';
  return '#ef4444';
}

function FieldReadonly({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.3 }}>{label}</div>
      <div style={{ padding: '10px 14px', background: '#f8fafc', borderRadius: 8, fontSize: 14, color: '#334155', border: '1px solid #f1f5f9' }}>{value}</div>
    </div>
  );
}

function FormField({ label, value, onChange, type = 'text' }) {
  return (
    <div>
      <label style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.3 }}>{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)}
        style={{ width: '100%', padding: '10px 14px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', transition: '0.2s' }} />
    </div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', marginBottom: 3, letterSpacing: 0.3 }}>{label}</div>
      <div style={{ fontSize: 14, color: '#334155' }}>{value}</div>
    </div>
  );
}
