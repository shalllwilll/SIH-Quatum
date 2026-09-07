import React from 'react';
import { Scale, Compass, Fuel, Clock, Check } from 'lucide-react';

export const PRESETS = [
  {
    id: 'balanced',
    name: 'Balanced Dispatch',
    tagline: 'Standard Multi-Objective',
    description: 'Equally balances fleet mileage, fuel consumption, and strict on-time SLA fulfillment.',
    icon: Scale,
    color: '#6366f1',
    weights: '40% SLA • 30% Distance • 30% Fuel',
  },
  {
    id: 'min_distance',
    name: 'Minimize Distance',
    tagline: 'Route Compactness',
    description: 'Prioritizes shortest overall road network distance, ideal for urban density clustering.',
    icon: Compass,
    color: '#3b82f6',
    weights: '60% Distance • 25% SLA • 15% Fuel',
  },
  {
    id: 'min_fuel',
    name: 'Minimum Fuel & Cost',
    tagline: 'Green & Cost-Efficient',
    description: 'Steers routes away from congested corridors to reduce idling fuel burn and vehicle wear.',
    icon: Fuel,
    color: '#10b981',
    weights: '50% Fuel/Congestion • 30% SLA • 20% Distance',
  },
  {
    id: 'prioritize_sla',
    name: 'Strict SLA Priority',
    tagline: 'Zero-Tolerance Deadlines',
    description: 'Heavy penalty on delayed arrivals, optimizing departure times for time-critical express parcels.',
    icon: Clock,
    color: '#f59e0b',
    weights: '70% SLA • 15% Distance • 15% Fuel',
  },
];

export default function PresetSelector({ selectedPreset, onSelect, disabled }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Optimization Objective Preset
        </label>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>QGA-QPSO Multi-Objective Function</span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
        gap: '1rem',
      }}>
        {PRESETS.map((preset) => {
          const Icon = preset.icon;
          const isSelected = selectedPreset === preset.id;
          return (
            <div
              key={preset.id}
              onClick={() => !disabled && onSelect(preset.id)}
              style={{
                background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                border: isSelected ? `2px solid ${preset.color}` : '1px solid var(--border-card)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
                cursor: disabled ? 'not-allowed' : 'pointer',
                opacity: disabled ? 0.6 : 1,
                transition: 'all 0.2s ease',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxShadow: isSelected ? `0 0 20px ${preset.color}33` : 'none',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <div style={{
                    width: '38px',
                    height: '38px',
                    borderRadius: 'var(--radius-sm)',
                    background: `${preset.color}22`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: `1px solid ${preset.color}44`,
                  }}>
                    <Icon size={20} color={preset.color} />
                  </div>
                  {isSelected && (
                    <div style={{
                      width: '22px',
                      height: '22px',
                      borderRadius: '50%',
                      background: preset.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}>
                      <Check size={14} color="#fff" />
                    </div>
                  )}
                </div>

                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '0.25rem' }}>
                  {preset.name}
                </div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: preset.color, marginBottom: '0.5rem' }}>
                  {preset.tagline}
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.4, margin: 0 }}>
                  {preset.description}
                </p>
              </div>

              <div style={{
                marginTop: '1rem',
                paddingTop: '0.75rem',
                borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                fontSize: '0.7rem',
                color: 'var(--text-dim)',
                fontWeight: 600,
              }}>
                {preset.weights}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
