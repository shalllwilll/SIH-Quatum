import React from 'react';

export default function SlaComplianceCard({ metrics }) {
  const { compliancePercent = 100, onTime = 0, late = 0, upcoming = 56 } = metrics || {};

  return (
    <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1rem' }}>
      <h3 className="heading-2" style={{ fontSize: '1rem', marginBottom: '1.25rem' }}>SLA Compliance (So Far)</h3>
      
      <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
        <div style={{ position: 'relative', width: '80px', height: '80px', borderRadius: '50%', border: '8px solid rgba(255,255,255,0.05)', borderTopColor: 'var(--success)', borderRightColor: 'var(--success)', borderBottomColor: compliancePercent > 75 ? 'var(--success)' : 'transparent' }}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span className="heading-2" style={{ fontSize: '1.1rem' }}>{compliancePercent}%</span>
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--success)' }}/>
              <span style={{ color: 'var(--text-muted)' }}>On Time</span>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{onTime}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--danger)' }}/>
              <span style={{ color: 'var(--text-muted)' }}>Late</span>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: late > 0 ? 'var(--danger)' : 'inherit' }}>{late}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--text-dim)' }}/>
              <span style={{ color: 'var(--text-muted)' }}>Upcoming</span>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{upcoming}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
