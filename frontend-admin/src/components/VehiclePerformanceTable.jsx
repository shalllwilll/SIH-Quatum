import React from 'react';
import { Truck, Navigation, CheckCircle2, Clock } from 'lucide-react';

export default function VehiclePerformanceTable({ stats = [] }) {
  if (!stats || stats.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-dim)' }}>
        No historical vehicle performance data recorded yet.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>Vehicle Performance & Fleet Utilization</h3>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Aggregated historical metrics</span>
      </div>

      <div style={{
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid var(--border-card)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: 'rgba(255, 255, 255, 0.03)', borderBottom: '1px solid var(--border-card)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Vehicle</th>
              <th style={{ padding: '0.75rem 1rem' }}>Total Routes</th>
              <th style={{ padding: '0.75rem 1rem' }}>Total Distance</th>
              <th style={{ padding: '0.75rem 1rem' }}>Stops Fulfilled</th>
              <th style={{ padding: '0.75rem 1rem' }}>SLA Compliance</th>
              <th style={{ padding: '0.75rem 1rem' }}>Avg Duration</th>
            </tr>
          </thead>
          <tbody>
            {stats.map((s) => {
              const compliance = s.compliance_pct || 90.0;
              const color = compliance >= 90 ? '#34d399' : compliance >= 80 ? '#fbbf24' : '#f87171';

              return (
                <tr
                  key={s.vehicle_id}
                  style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}
                >
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{
                        width: '26px',
                        height: '26px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(99, 102, 241, 0.15)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}>
                        <Truck size={13} color="#818cf8" />
                      </div>
                      <span style={{ fontWeight: 700, color: '#fff' }}>{s.vehicle_id}</span>
                    </div>
                  </td>

                  <td style={{ padding: '0.75rem 1rem', color: '#cbd5e1' }}>
                    {s.total_routes}
                  </td>

                  <td style={{ padding: '0.75rem 1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#fff' }}>
                      <Navigation size={12} color="var(--text-dim)" />
                      <span>{s.total_distance_km} km</span>
                    </div>
                  </td>

                  <td style={{ padding: '0.75rem 1rem', color: '#cbd5e1' }}>
                    {s.total_stops_completed} deliveries
                  </td>

                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span style={{ fontWeight: 700, color }}>{compliance}%</span>
                  </td>

                  <td style={{ padding: '0.75rem 1rem', color: 'var(--text-dim)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <Clock size={12} />
                      <span>{s.avg_trip_duration_min} min</span>
                    </div>
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
