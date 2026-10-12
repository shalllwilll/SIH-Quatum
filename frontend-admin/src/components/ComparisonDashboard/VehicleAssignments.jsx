import React from 'react';

export default function VehicleAssignments({ assignments, isSimulating }) {
  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border-card)', backgroundColor: 'var(--bg-card-solid)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontWeight: 500, fontSize: '0.9rem', color: 'var(--text-main)' }}>Vehicle Assignments</h3>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{assignments.length} Vehicles</span>
      </div>
      
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <table className="data-table">
          <thead style={{ position: 'sticky', top: 0, backgroundColor: 'var(--bg-card-solid)', zIndex: 10 }}>
            <tr>
              <th>Vehicle</th>
              <th>Warehouse</th>
              <th style={{ textAlign: 'right' }}>Stops</th>
              <th style={{ textAlign: 'right' }}>Distance</th>
              <th style={{ textAlign: 'right' }}>Est. Time</th>
            </tr>
          </thead>
          <tbody>
            {assignments.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  {isSimulating ? 'Simulating assignments...' : 'No data available'}
                </td>
              </tr>
            ) : (
              assignments.map((assignment, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 500 }}>{assignment.vehicle_id}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{assignment.warehouse_id}</td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{assignment.stops?.length || 0}</td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{assignment.repositioning_distance_km ? `${assignment.repositioning_distance_km.toFixed(1)} km` : '-'}</td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{assignment.total_duration_min ? `${Math.round(assignment.total_duration_min)}m` : '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
