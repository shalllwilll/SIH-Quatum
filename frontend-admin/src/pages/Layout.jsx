import React from 'react';
import { useAuth } from '../context/AuthContext';
import {
  MapPin,
  Route,
  Truck,
  Activity,
  BarChart3,
  LogOut,
  Radio,
} from 'lucide-react';

export default function Layout({ activeTab, onTabChange, children }) {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'overview', label: 'Fleet Overview', icon: MapPin },
    { id: 'routing', label: 'Route Assignment', icon: Route },
    { id: 'vehicles', label: 'Vehicles & Drivers', icon: Truck },
    { id: 'analytics', label: 'Analytics & Trends', icon: BarChart3 },
    { id: 'diagnostics', label: 'Live Traffic & Engine', icon: Activity },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-dark)' }}>
      {/* Left Sidebar */}
      <aside style={{
        width: '260px',
        background: 'var(--bg-card-solid)',
        borderRight: '1px solid var(--border-card)',
        display: 'flex',
        flexDirection: 'column',
        padding: '1.5rem 1rem',
        zIndex: 20,
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0 0.5rem 1.5rem', borderBottom: '1px solid var(--border-card)' }}>
          <div style={{
            width: '40px',
            height: '40px',
            background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px var(--primary-glow)',
          }}>
            <Truck size={22} color="#fff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff', lineHeight: 1.1 }}>Abraxas</h2>
            <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--primary)', letterSpacing: '0.05em' }}>
              QGA·QPSO DISPATCH
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1.5rem', flex: 1 }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid transparent',
                  background: isActive ? 'linear-gradient(90deg, rgba(99, 102, 241, 0.15) 0%, rgba(99, 102, 241, 0.05) 100%)' : 'transparent',
                  color: isActive ? '#818cf8' : 'var(--text-muted)',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease',
                }}
              >
                <Icon size={18} color={isActive ? '#818cf8' : 'var(--text-dim)'} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Dispatcher Status Card */}
        <div style={{
          padding: '1rem',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-card)',
          marginBottom: '1rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#34d399' }}>Live Dispatcher</span>
          </div>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>{user?.name || 'Dispatcher'}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Role: {user?.role || 'admin'}</div>
        </div>

        {/* Logout */}
        <button
          onClick={logout}
          className="btn-secondary"
          style={{ width: '100%', justifyContent: 'center', fontSize: '0.85rem' }}
        >
          <LogOut size={16} />
          Sign Out
        </button>
      </aside>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Top Header */}
        <header style={{
          height: '64px',
          background: 'rgba(18, 26, 43, 0.6)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid var(--border-card)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 2rem',
          zIndex: 10,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff' }}>
              {navItems.find((n) => n.id === activeTab)?.label || 'Dashboard'}
            </h1>
            <span className="badge badge-primary">Pune Operational Zone</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <Radio size={14} color="#10b981" />
              <span>Engine Status: <strong style={{ color: '#10b981' }}>ONLINE</strong></span>
            </div>
          </div>
        </header>

        {/* Body View */}
        <main style={{ flex: 1, padding: '1.5rem', overflowY: 'auto' }}>
          {children}
        </main>
      </div>
    </div>
  );
}
