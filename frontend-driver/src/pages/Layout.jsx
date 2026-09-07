import React from 'react';
import { useDriverAuth } from '../context/AuthContext';
import {
  ListOrdered,
  MapPin,
  LogOut,
  Navigation,
  Truck,
} from 'lucide-react';

export default function Layout({ activeTab, onTabChange, children }) {
  const { user, logout } = useDriverAuth();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: 'var(--bg-dark)' }}>
      {/* Top Mobile App Header */}
      <header style={{
        height: '56px',
        background: 'var(--bg-card-solid)',
        borderBottom: '1px solid var(--border-card)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1rem',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            width: '32px',
            height: '32px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Navigation size={18} color="#fff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff', lineHeight: 1.1 }}>Abraxas Driver</h1>
            <span style={{ fontSize: '0.65rem', color: '#34d399', fontWeight: 600 }}>
              {user?.vehicle_label || 'Assigned Shift'}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={logout}
            className="btn-secondary"
            style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
            title="Sign Out"
          >
            <LogOut size={13} />
            <span>Sign Out</span>
          </button>
        </div>
      </header>

      {/* Main Body */}
      <main style={{ flex: 1, padding: '1rem', paddingBottom: '76px', overflowY: 'auto' }}>
        {children}
      </main>

      {/* Bottom Sticky Mobile Navigation Bar */}
      <nav style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: '60px',
        background: 'rgba(18, 26, 43, 0.95)',
        backdropFilter: 'blur(16px)',
        borderTop: '1px solid var(--border-card)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-around',
        zIndex: 100,
        padding: '0 1rem',
      }}>
        <button
          onClick={() => onTabChange('itinerary')}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.2rem',
            background: 'none',
            border: 'none',
            color: activeTab === 'itinerary' ? '#34d399' : 'var(--text-dim)',
            cursor: 'pointer',
            padding: '0.4rem 1.5rem',
            borderRadius: 'var(--radius-sm)',
            transition: 'all 0.15s ease',
          }}
        >
          <ListOrdered size={20} />
          <span style={{ fontSize: '0.7rem', fontWeight: activeTab === 'itinerary' ? 700 : 500 }}>Itinerary</span>
        </button>

        <button
          onClick={() => onTabChange('map')}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.2rem',
            background: 'none',
            border: 'none',
            color: activeTab === 'map' ? '#34d399' : 'var(--text-dim)',
            cursor: 'pointer',
            padding: '0.4rem 1.5rem',
            borderRadius: 'var(--radius-sm)',
            transition: 'all 0.15s ease',
          }}
        >
          <MapPin size={20} />
          <span style={{ fontSize: '0.7rem', fontWeight: activeTab === 'map' ? 700 : 500 }}>Live Map</span>
        </button>
      </nav>
    </div>
  );
}
