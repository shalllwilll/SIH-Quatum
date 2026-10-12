import React from 'react';
import { Route, MapPin, Clock, Droplets, Leaf, Package } from 'lucide-react';

export default function BottomKPIStrip({ kpis }) {
  const {
    totalDistance = 184.2,
    fuelConsumed = 32.4,
    timeFormatted = '5 h 12 min',
    carbonEmissions = 71.2,
    deliveriesCompleted = 24,
    totalDeliveries = 56
  } = kpis || {};

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '1.25rem 2rem',
      borderTop: '1px solid var(--border-card)',
      background: 'var(--bg-dark)'
    }}>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Route size={18} color="var(--text-muted)" />
        <div>
          <div className="text-label">Total Distance</div>
          <div className="heading-2" style={{ fontSize: '1.1rem', marginTop: '0.2rem' }}>{totalDistance.toFixed(1)} km</div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Droplets size={18} color="var(--text-muted)" />
        <div>
          <div className="text-label">Fuel Consumed</div>
          <div className="heading-2" style={{ fontSize: '1.1rem', marginTop: '0.2rem' }}>{fuelConsumed.toFixed(1)} L</div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Clock size={18} color="var(--text-muted)" />
        <div>
          <div className="text-label">Total Time (Sim)</div>
          <div className="heading-2" style={{ fontSize: '1.1rem', marginTop: '0.2rem' }}>{timeFormatted}</div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Leaf size={18} color="var(--text-muted)" />
        <div>
          <div className="text-label">Carbon Emissions</div>
          <div className="heading-2" style={{ fontSize: '1.1rem', marginTop: '0.2rem' }}>{carbonEmissions.toFixed(1)} kg CO₂</div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Package size={18} color="var(--text-muted)" />
        <div>
          <div className="text-label">Deliveries Completed</div>
          <div className="heading-2" style={{ fontSize: '1.1rem', marginTop: '0.2rem' }}>{deliveriesCompleted} / {totalDeliveries}</div>
        </div>
      </div>

    </div>
  );
}
