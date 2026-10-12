import React from 'react';

export default function FleetStatusCard({ metrics }) {
  const { totalVehicles = 11, activeVehicles = 11, parcels = { total: 56, completed: 0, enRoute: 56, returning: 0, pending: 0 } } = metrics || {};

  return (
    <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 className="heading-2" style={{ fontSize: '1rem' }}>Fleet Status</h3>
      </div>
      
      <div style={{ marginBottom: '1.5rem' }}>
        <div className="heading-1">{activeVehicles} / {totalVehicles}</div>
        <div className="text-body" style={{ fontSize: '0.8rem' }}>Active Vehicles</div>
      </div>

      <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
        {/* Simple Ring Mockup */}
        <div style={{ position: 'relative', width: '80px', height: '80px', borderRadius: '50%', border: '8px solid rgba(255,255,255,0.05)', borderTopColor: 'var(--primary)', borderRightColor: 'var(--success)' }}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <span className="heading-2" style={{ fontSize: '1.1rem' }}>{parcels.total}</span>
            <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Parcels</span>
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--success)' }}/>
              <span style={{ color: 'var(--text-muted)' }}>Completed</span>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{parcels.completed}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--primary)' }}/>
              <span style={{ color: 'var(--text-muted)' }}>En Route</span>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{parcels.enRoute}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--warning)' }}/>
              <span style={{ color: 'var(--text-muted)' }}>Returning</span>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{parcels.returning}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--text-dim)' }}/>
              <span style={{ color: 'var(--text-muted)' }}>Pending</span>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{parcels.pending}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
