import React from 'react';
import { ShieldAlert, AlertTriangle, Scale, Clock } from 'lucide-react';

export default function ViolationHistory({ violations = [] }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(239, 68, 68, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <ShieldAlert size={16} color="#f87171" />
          </div>
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>Constraint Violation Audit Log</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Historical capacity overruns & SLA window breaches</span>
          </div>
        </div>

        <span className="badge badge-warning">
          {violations.length} Events Logged
        </span>
      </div>

      {/* Violation Cards Timeline */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '280px', overflowY: 'auto' }}>
        {violations.map((v, idx) => {
          const isCapacity = v.violation_type === 'CAPACITY_OVERRUN';

          return (
            <div
              key={`${v.session_id}-${idx}`}
              style={{
                padding: '0.75rem 1rem',
                background: 'rgba(255, 255, 255, 0.02)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-card)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: 'var(--radius-sm)',
                  background: isCapacity ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  {isCapacity ? <Scale size={14} color="#fbbf24" /> : <Clock size={14} color="#f87171" />}
                </div>

                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff' }}>
                    {v.details}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                    Session: {v.session_id.slice(-6)} • Count: <strong>{v.count}</strong>
                  </div>
                </div>
              </div>

              <span className={`badge ${isCapacity ? 'badge-warning' : 'badge-danger'}`} style={{ fontSize: '0.65rem' }}>
                {v.violation_type.replace(/_/g, ' ')}
              </span>
            </div>
          );
        })}

        {!violations.length && (
          <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
            🎉 Zero constraint violations recorded. Fleet operating with 100% capacity and SLA adherence!
          </div>
        )}
      </div>
    </div>
  );
}
