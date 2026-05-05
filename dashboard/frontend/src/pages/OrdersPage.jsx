import { useState } from 'react';
import { useApi, apiPost, apiPatch, exportCsv } from '../hooks/useApi';
import { Search, Download } from 'lucide-react';
import KpiCard from '../components/KpiCard';
import { Package, Truck, CheckCircle, Clock } from 'lucide-react';

const DELIVERY_STATUS = {
  awaiting_delivery: { label: 'AWAITING DELIVERY', color: '#f59e0b', bg: '#fffbeb' },
  shipped: { label: 'SHIPPED', color: '#3b82f6', bg: '#eff6ff' },
  delivered: { label: 'DELIVERED', color: '#10b981', bg: '#ecfdf5' },
  cancelled: { label: 'CANCELLED', color: '#ef4444', bg: '#fef2f2' },
};

function DeliveryBadge({ status }) {
  const cfg = DELIVERY_STATUS[status] || { label: status, color: '#64748b', bg: '#f1f5f9' };
  return (
    <span className="status-badge" style={{ background: cfg.bg, color: cfg.color }}>
      {cfg.label}
    </span>
  );
}

export default function OrdersPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [month, setMonth] = useState('');
  const [selectedId, setSelectedId] = useState(null);

  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (statusFilter) params.set('delivery_status', statusFilter);
  if (month) params.set('month', month);
  params.set('limit', '50');

  const { data, loading, error, refetch } = useApi(`/orders?${params}`, { interval: 30000 });
  const { data: stats } = useApi('/orders/stats');
  const { data: detail, refetch: refetchDetail } = useApi(
    selectedId ? `/orders/${selectedId}` : null,
    { enabled: !!selectedId }
  );

  const orders = data?.data || [];
  const orderStats = stats?.data || {};
  const orderDetail = detail?.data;

  const handleStatusUpdate = async (poId, newStatus) => {
    if (newStatus === 'delivered') {
      if (!confirm('Confirm that goods have been received?')) return;
      await apiPost(`/orders/${poId}/confirm-delivery`, { confirmed_by: 'dashboard_user' });
    } else {
      await apiPatch(`/orders/${poId}/status`, { delivery_status: newStatus });
    }
    refetch();
    if (selectedId === poId) refetchDetail();
  };

  if (loading && !data) return <div className="page-loading">Loading orders...</div>;
  if (error) return <div className="page-error">Error: {error}</div>;

  return (
    <div className="page">
      <div className="kpi-grid" style={{ marginBottom: 24 }}>
        <KpiCard icon={Package} title="Total Orders" value={orderStats.total_orders ?? '—'} color="#3b82f6" />
        <KpiCard icon={Clock} title="Active Orders" value={orderStats.active_orders ?? '—'} color="#f59e0b" />
        <KpiCard icon={CheckCircle} title="Delivered This Month" value={orderStats.delivered_this_month ?? '—'} color="#10b981" />
        <KpiCard icon={Truck} title="Avg Delivery (days)" value={orderStats.avg_delivery_days ?? '—'} color="#8b5cf6" />
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <div className="search-wrapper" style={{ flex: 1 }}>
          <Search size={16} />
          <input
            type="text"
            placeholder="Search PO, product, supplier..."
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
          <option value="awaiting_delivery">Awaiting Delivery</option>
          <option value="shipped">Shipped</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <input
          type="month"
          className="filter-input"
          value={month}
          onChange={e => setMonth(e.target.value)}
        />
        <button onClick={() => exportCsv('/export/orders')} style={{
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
              <th>PO Reference</th>
              <th>Product</th>
              <th>Supplier</th>
              <th>Total (TND)</th>
              <th>Created</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 && (
              <tr><td colSpan={7} className="empty-row">No purchase orders found</td></tr>
            )}
            {orders.map(o => (
              <tr key={o.id} className={selectedId === o.id ? 'selected' : ''} onClick={() => setSelectedId(o.id)}>
                <td style={{ fontWeight: 600, fontFamily: "'SF Mono', 'Fira Code', monospace", fontSize: 13 }}>{o.po_reference}</td>
                <td className="td-title">{o.product}</td>
                <td>{o.supplier_name}</td>
                <td style={{ fontWeight: 500 }}>{o.total_price != null ? o.total_price.toLocaleString() : '—'}</td>
                <td style={{ fontSize: 13, color: '#94a3b8' }}>{o.created_at ? new Date(o.created_at).toLocaleDateString() : '—'}</td>
                <td><DeliveryBadge status={o.delivery_status} /></td>
                <td onClick={e => e.stopPropagation()}>
                  {o.delivery_status === 'awaiting_delivery' && (
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn btn-sm" style={{ background: '#eff6ff', color: '#3b82f6' }} onClick={() => handleStatusUpdate(o.id, 'shipped')}>
                        Shipped
                      </button>
                      <button className="btn btn-sm btn-success" onClick={() => handleStatusUpdate(o.id, 'delivered')}>
                        Delivered
                      </button>
                    </div>
                  )}
                  {o.delivery_status === 'shipped' && (
                    <button className="btn btn-sm btn-success" onClick={() => handleStatusUpdate(o.id, 'delivered')}>
                      Confirm Delivery
                    </button>
                  )}
                  {o.delivery_status === 'delivered' && (
                    <span style={{ fontSize: 12, color: '#10b981', fontWeight: 600 }}>Delivered</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedId && orderDetail && (
        <div className="detail-panel" style={{ marginTop: 20 }}>
          <h2>PO: {orderDetail.po_reference}</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px 24px', marginTop: 16 }}>
            <InfoItem label="Product" value={orderDetail.product} />
            <InfoItem label="Supplier" value={orderDetail.supplier_name} />
            <InfoItem label="Supplier Email" value={orderDetail.supplier_email} />
            <InfoItem label="Quantity" value={`${orderDetail.quantity || '—'} ${orderDetail.unit || ''}`} />
            <InfoItem label="Unit Price" value={orderDetail.unit_price != null ? `${orderDetail.unit_price} ${orderDetail.currency}` : '—'} />
            <InfoItem label="Total Price" value={orderDetail.total_price != null ? `${orderDetail.total_price} ${orderDetail.currency}` : '—'} />
            <InfoItem label="Delivery Address" value={orderDetail.delivery_address || '—'} />
            <InfoItem label="Cost Center" value={orderDetail.cost_center || '—'} />
            <InfoItem label="Department" value={orderDetail.department || '—'} />
            <InfoItem label="Requester" value={`${orderDetail.requester_name || ''} (${orderDetail.requester_email})`} />
            <InfoItem label="Status" value={<DeliveryBadge status={orderDetail.delivery_status} />} />
            <InfoItem label="Delivered At" value={orderDetail.delivered_at ? new Date(orderDetail.delivered_at).toLocaleString() : '—'} />
            {orderDetail.confirmed_by && <InfoItem label="Confirmed By" value={orderDetail.confirmed_by} />}
            {orderDetail.notes && <InfoItem label="Notes" value={orderDetail.notes} />}
          </div>
        </div>
      )}
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
