import React from 'react';

export default function SessionHistory({ sessions }) {
  // Sort by created_at descending if not already sorted
  const sortedSessions = [...sessions].sort((a, b) => b.created_at - a.created_at);

  const getStatusColor = (status) => {
    switch(status.toLowerCase()) {
      case 'completed': return 'var(--success)';
      case 'running': return 'var(--warning)';
      case 'failed': return 'var(--danger)';
      default: return 'var(--text-muted)';
    }
  };

  const getPresetLabel = (preset) => {
    return preset.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-card)', backgroundColor: 'var(--bg-card-solid)' }}>
        <h3 style={{ fontWeight: 500, fontSize: '0.9rem', color: 'var(--text-main)' }}>Session History</h3>
      </div>
      
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <table className="data-table" style={{ width: '100%' }}>
          <thead style={{ position: 'sticky', top: 0, backgroundColor: 'var(--bg-card-solid)', zIndex: 10 }}>
            <tr>
              <th>Day / Session</th>
              <th>Date</th>
              <th>Preset</th>
              <th style={{ textAlign: 'right' }}>Parcels</th>
              <th style={{ textAlign: 'right' }}>Distance</th>
              <th style={{ textAlign: 'right' }}>Fuel</th>
              <th style={{ textAlign: 'right' }}>CO₂</th>
              <th style={{ textAlign: 'right' }}>SLA</th>
              <th style={{ textAlign: 'right' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {sortedSessions.length === 0 ? (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No historical sessions found.
                </td>
              </tr>
            ) : (
              sortedSessions.map((session, idx) => {
                const dateObj = new Date(session.created_at * 1000);
                const dateStr = dateObj.toLocaleDateString([], { day: '2-digit', month: 'short', year: 'numeric' });
                const dayLabel = session.day_label || `Session ${sortedSessions.length - idx}`;
                
                return (
                  <tr key={session.session_id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.85rem' }}>
                      <span style={{ 
                        display: 'inline-block', 
                        padding: '0.15rem 0.5rem', 
                        borderRadius: '4px', 
                        backgroundColor: session.day_label?.includes('Today') ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                        color: session.day_label?.includes('Today') ? 'var(--primary)' : 'var(--text-main)',
                        border: session.day_label?.includes('Today') ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid var(--border-card)'
                      }}>
                        {dayLabel}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{dateStr}</td>
                    <td style={{ fontWeight: 500 }}>{getPresetLabel(session.preset)}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{session.completed_parcels} / {session.parcel_count}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                      {session.total_distance_km ? `${session.total_distance_km.toFixed(1)} km` : '-'}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {session.estimated_fuel_liters ? `${session.estimated_fuel_liters.toFixed(1)} L` : '-'}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--warning)' }}>
                      {session.carbon_emissions_kg ? `${session.carbon_emissions_kg.toFixed(1)} kg` : '-'}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--success)', fontWeight: 600 }}>
                      {session.sla_compliance_pct ? `${session.sla_compliance_pct.toFixed(1)}%` : '-'}
                    </td>
                    <td style={{ textAlign: 'right', color: getStatusColor(session.status) }}>
                      {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
