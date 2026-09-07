import React from 'react';
import { Clock, CheckCircle2, AlertTriangle, XCircle, Truck } from 'lucide-react';

export default function SlaComplianceView({ summary = null, vehicleBreakdown = [] }) {
  if (!summary) return null;

  const {
    overall_compliance_pct = 100,
    total_events = 0,
    delivered_count = 0,
    late_count = 0,
    failed_count = 0,
    on_time_count = 0,
  } = summary;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(99, 102, 241, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Clock size={16} color="#818cf8" />
          </div>
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>SLA Compliance & Delivery Outcomes</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Across all historical and active dispatch shifts</span>
          </div>
        </div>

        <div style={{
          fontSize: '1.5rem',
          fontWeight: 800,
          color: overall_compliance_pct >= 90 ? '#34d399' : '#fbbf24',
        }}>
          {overall_compliance_pct}%
        </div>
      </div>

      {/* Outcome Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
        gap: '0.6rem',
      }}>
        <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-card)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Total Deliveries</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', marginTop: '0.15rem' }}>{total_events}</div>
        </div>

        <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
          <div style={{ fontSize: '0.7rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <CheckCircle2 size={11} /> On-Time
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#34d399', marginTop: '0.15rem' }}>{on_time_count}</div>
        </div>

        <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
          <div style={{ fontSize: '0.7rem', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <AlertTriangle size={11} /> Late
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fbbf24', marginTop: '0.15rem' }}>{late_count}</div>
        </div>

        <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
          <div style={{ fontSize: '0.7rem', color: '#f87171', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <XCircle size={11} /> Failed
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f87171', marginTop: '0.15rem' }}>{failed_count}</div>
        </div>
      </div>

      {/* Per-Vehicle SLA Breakdown Progress Bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Per-Vehicle SLA Performance
        </div>

        {vehicleBreakdown.map((veh) => {
          const pct = veh.compliance_pct;
          const color = pct >= 90 ? '#10b981' : pct >= 80 ? '#f59e0b' : '#ef4444';

          return (
            <div key={veh.vehicle_id} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#fff', fontWeight: 600 }}>
                  <Truck size={13} color={color} />
                  <span>{veh.vehicle_id}</span>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>({veh.total_deliveries} stops)</span>
                </div>
                <div style={{ fontWeight: 700, color }}>{pct}%</div>
              </div>

              {/* Progress Bar Track */}
              <div style={{
                height: '6px',
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '9999px',
                overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%',
                  width: `${pct}%`,
                  background: color,
                  borderRadius: '9999px',
                  transition: 'width 0.5s ease',
                }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
