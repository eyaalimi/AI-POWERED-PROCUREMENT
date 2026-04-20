import { useState } from 'react';
import { useApi, apiPost } from '../hooks/useApi';
import { Users, Shield, User, UserPlus, X } from 'lucide-react';

const ROLE_STYLES = {
  admin: { bg: '#fef3c7', color: '#92400e', icon: Shield },
  employee: { bg: '#dbeafe', color: '#1e40af', icon: User },
};

export default function UsersPage() {
  const { data: users, loading, error, refetch } = useApi('/auth/users');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '', department: '', role: 'employee' });
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState('');

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setFormError('');
    try {
      const res = await apiPost('/auth/users/create', form);
      if (res.id) {
        setShowForm(false);
        setForm({ name: '', email: '', password: '', department: '', role: 'employee' });
        refetch();
      } else {
        setFormError(res.detail || 'Failed to create user');
      }
    } catch {
      setFormError('Failed to create user');
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <div style={{ padding: 32 }}>Loading...</div>;
  if (error) return <div style={{ padding: 32, color: '#ef4444' }}>Error: {error}</div>;

  return (
    <div style={{ padding: '24px 32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Users size={24} />
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>Team Members</h1>
          <span style={{
            background: '#e2e8f0', borderRadius: 12, padding: '2px 10px',
            fontSize: 13, color: '#475569',
          }}>
            {users?.length || 0}
          </span>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 8,
            padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}
        >
          {showForm ? <X size={16} /> : <UserPlus size={16} />}
          {showForm ? 'Cancel' : 'Add User'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} style={{
          background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
          padding: 20, marginBottom: 20, display: 'grid', gridTemplateColumns: '1fr 1fr',
          gap: 12,
        }}>
          <input
            placeholder="Full name" required value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            style={inputStyle}
          />
          <input
            placeholder="Email" type="email" required value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            style={inputStyle}
          />
          <input
            placeholder="Password" type="password" required minLength={6} value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            style={inputStyle}
          />
          <input
            placeholder="Department" value={form.department}
            onChange={(e) => setForm({ ...form, department: e.target.value })}
            style={inputStyle}
          />
          <select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
            style={inputStyle}
          >
            <option value="employee">Employee</option>
            <option value="admin">Admin</option>
          </select>
          <button type="submit" disabled={creating} style={{
            background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 8,
            padding: '10px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}>
            {creating ? 'Creating...' : 'Create User'}
          </button>
          {formError && <div style={{ gridColumn: '1/-1', color: '#ef4444', fontSize: 13 }}>{formError}</div>}
        </form>
      )}

      <div style={{
        background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
        overflow: 'hidden',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <th style={thStyle}>Name</th>
              <th style={thStyle}>Email</th>
              <th style={thStyle}>Department</th>
              <th style={thStyle}>Role</th>
              <th style={thStyle}>Joined</th>
            </tr>
          </thead>
          <tbody>
            {(users || []).map((u) => {
              const s = ROLE_STYLES[u.role] || ROLE_STYLES.employee;
              const RoleIcon = s.icon;
              return (
                <tr key={u.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{
                        width: 32, height: 32, borderRadius: '50%',
                        background: '#e0e7ff', display: 'flex', alignItems: 'center',
                        justifyContent: 'center', fontWeight: 600, fontSize: 13, color: '#4338ca',
                      }}>
                        {u.name?.charAt(0).toUpperCase()}
                      </div>
                      {u.name}
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#64748b' }}>{u.email}</td>
                  <td style={{ padding: '12px 16px', color: '#64748b' }}>{u.department || '-'}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      background: s.bg, color: s.color,
                      padding: '3px 10px', borderRadius: 8, fontSize: 12, fontWeight: 600,
                    }}>
                      <RoleIcon size={12} />
                      {u.role}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#64748b' }}>
                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const inputStyle = {
  padding: '10px 12px', borderRadius: 8, border: '1px solid #e2e8f0',
  fontSize: 14, outline: 'none',
};

const thStyle = { padding: '12px 16px', textAlign: 'left', fontWeight: 600 };
