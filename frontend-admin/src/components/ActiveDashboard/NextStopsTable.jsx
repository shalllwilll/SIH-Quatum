import React from 'react';
import { Truck } from 'lucide-react';

export default function NextStopsTable({ nextStops = [] }) {
  // nextStops: array of { vehicleId, stopId, etaFormatted }
  
  // Provide some mock data if empty for layout visualization
  const displayStops = nextStops.length > 0 ? nextStops : [
    { vehicleId: 'Van-3', stopId: '#28', etaFormatted: '12:14 PM' },
    { vehicleId: 'Van-7', stopId: '#12', etaFormatted: '12:27 PM' },
    { vehicleId: 'Van-1', stopId: '#31', etaFormatted: '12:31 PM' },
    { vehicleId: 'Van-5', stopId: '#07', etaFormatted: '12:46 PM' },
    { vehicleId: 'Van-9', stopId: '#22', etaFormatted: '01:03 PM' }
  ];

  return (
    <div className="glass-card" style={{ padding: '1.25rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 className="heading-2" style={{ fontSize: '1rem' }}>Next Stop Events</h3>
        <a href="#" style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 600 }}>View All &rarr;</a>
      </div>
      
      <div style={{ overflowY: 'auto', flex: 1 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Vehicle</th>
              <th>Next Stop</th>
              <th>ETA (Sim)</th>
            </tr>
          </thead>
          <tbody>
            {displayStops.map((stop, i) => (
              <tr key={i}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Truck size={14} color="var(--primary)" />
                    <span style={{ fontWeight: 500 }}>{stop.vehicleId}</span>
                  </div>
                </td>
                <td style={{ color: 'var(--text-muted)' }}>{stop.stopId}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{stop.etaFormatted}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
