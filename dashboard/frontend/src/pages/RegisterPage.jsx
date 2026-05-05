import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Zap, User, Mail, Lock, Building2, Briefcase, AlertCircle } from 'lucide-react';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '', email: '', password: '', department: '', company_name: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(form);
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <Zap size={28} />
          </div>
          <h1>Procurement AI</h1>
          <p>Create your account</p>
        </div>

        {error && (
          <div className="auth-error">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label>Full Name</label>
            <div className="auth-input-wrapper">
              <User size={16} />
              <input type="text" value={form.name} onChange={set('name')} placeholder="John Doe" required />
            </div>
          </div>

          <div className="auth-field">
            <label>Email</label>
            <div className="auth-input-wrapper">
              <Mail size={16} />
              <input type="email" value={form.email} onChange={set('email')} placeholder="you@company.com" required />
            </div>
          </div>

          <div className="auth-field">
            <label>Password</label>
            <div className="auth-input-wrapper">
              <Lock size={16} />
              <input type="password" value={form.password} onChange={set('password')} placeholder="Min 6 characters" required minLength={6} />
            </div>
          </div>

          <div className="auth-field">
            <label>Company Name</label>
            <div className="auth-input-wrapper">
              <Building2 size={16} />
              <input type="text" value={form.company_name} onChange={set('company_name')} placeholder="Your company" required />
            </div>
          </div>

          <div className="auth-field">
            <label>Department</label>
            <div className="auth-input-wrapper">
              <Briefcase size={16} />
              <input type="text" value={form.department} onChange={set('department')} placeholder="e.g. Procurement, IT, Operations" />
            </div>
          </div>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="auth-role-hint">
          First person to register for a company becomes the Admin.
        </p>

        <div className="auth-footer">
          Already have an account? <Link to="/login">Sign In</Link>
        </div>
      </div>
    </div>
  );
}
