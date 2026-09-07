import React, { useState } from 'react';
import { useDriverAuth } from '../context/AuthContext';
import { Navigation, Key, User, ArrowRight, Truck } from 'lucide-react';

export default function Login() {
  const { login, loading } = useDriverAuth();
  const [username, setUsername] = useState('driver1');
  const [password, setPassword] = useState('driver123');
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    const result = await login(username, password);
    if (!result.success) {
      setError(result.error);
    }
  };

  const fillDemoDriver = (u, p) => {
    setUsername(u);
    setPassword(p);
    setError(null);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem',
      background: 'radial-gradient(ellipse at top, #1e1b4b 0%, #090d16 70%)',
    }}>
      <div className="glass-card" style={{
        width: '100%',
        maxWidth: '400px',
        padding: '2rem',
        borderRadius: 'var(--radius-xl)',
        border: '1px solid rgba(99, 102, 241, 0.2)',
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{
            width: '54px',
            height: '54px',
            margin: '0 auto 0.75rem',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 25px rgba(16, 185, 129, 0.35)',
          }}>
            <Navigation size={28} color="#ffffff" />
          </div>
          <h1 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#ffffff' }}>
            Driver Mobile App
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
            On-Time Last-Mile Delivery Navigator
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem',
            marginBottom: '1.25rem',
            color: '#f87171',
            fontSize: '0.85rem',
          }}>
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              Driver Username
            </label>
            <div style={{ position: 'relative' }}>
              <User size={16} style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: '2.5rem' }}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="driver1"
                required
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Key size={16} style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
              <input
                type="password"
                className="form-input"
                style={{ paddingLeft: '2.5rem' }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-success"
            style={{ width: '100%', justifyContent: 'center', padding: '0.75rem', marginTop: '0.5rem' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In as Driver'}
            <ArrowRight size={16} />
          </button>
        </form>

        {/* Demo Accounts Presets */}
        <div style={{ marginTop: '1.75rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-card)' }}>
          <p style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', marginBottom: '0.5rem', textAlign: 'center', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Demo Driver Accounts
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <button
              type="button"
              className="btn-secondary"
              style={{ width: '100%', fontSize: '0.75rem', padding: '0.5rem 0.75rem', justifyContent: 'space-between' }}
              onClick={() => fillDemoDriver('driver1', 'driver123')}
            >
              <span>Driver 1 (Van-1 • Ramesh Pawar)</span>
              <Truck size={14} color="#34d399" />
            </button>
            <button
              type="button"
              className="btn-secondary"
              style={{ width: '100%', fontSize: '0.75rem', padding: '0.5rem 0.75rem', justifyContent: 'space-between' }}
              onClick={() => fillDemoDriver('driver2', 'driver223')}
            >
              <span>Driver 2 (Van-2 • Suresh Gaikwad)</span>
              <Truck size={14} color="#818cf8" />
            </button>
            <button
              type="button"
              className="btn-secondary"
              style={{ width: '100%', fontSize: '0.75rem', padding: '0.5rem 0.75rem', justifyContent: 'space-between' }}
              onClick={() => fillDemoDriver('driver3', 'driver323')}
            >
              <span>Driver 3 (Van-3 • Amit Kulkarni)</span>
              <Truck size={14} color="#fbbf24" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
