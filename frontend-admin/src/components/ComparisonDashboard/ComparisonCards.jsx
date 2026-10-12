import React from 'react';

export default function ComparisonCards({ presets, selectedPreset, onSelect }) {
  // Preset order from API
  const presetKeys = ['balanced', 'min_fuel', 'min_distance', 'prioritize_sla'];
  
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
      {presetKeys.map(key => {
        const card = presets[key];
        if (!card) return null;
        const isSelected = selectedPreset === key;
        
        return (
          <div 
            key={key}
            onClick={() => onSelect(key)}
            className={`glass-card ${!isSelected ? 'glass-card-hover' : ''}`}
            style={{ 
              cursor: 'pointer', 
              padding: '1.25rem', 
              borderColor: isSelected ? 'var(--primary)' : 'var(--border-card)',
              boxShadow: isSelected ? '0 0 15px var(--primary-glow)' : undefined,
              backgroundColor: isSelected ? 'rgba(18, 20, 24, 0.95)' : undefined
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ fontWeight: 600, fontSize: '0.95rem', color: isSelected ? 'var(--primary)' : 'var(--text-main)', marginBottom: '0.15rem' }}>
                  {card.name}
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{card.tagline}</span>
              </div>
              {card.is_recommended && (
                <span className="status-pill" style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem', color: 'var(--primary)', backgroundColor: 'var(--primary-glow)' }}>
                  Recommended
                </span>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.25rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Distance</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-main)' }}>{card.total_distance_km.toFixed(1)} km</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.25rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Fuel</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-main)' }}>{card.estimated_fuel_litres.toFixed(1)} L</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.25rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Time (Sim)</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-main)' }}>{Math.round(card.total_duration_min / 60)}h {Math.round(card.total_duration_min % 60)}m</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.25rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Est. CO₂</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-main)' }}>{card.estimated_co2_kg.toFixed(1)} kg</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.25rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>SLA Compliance</span>
                <span style={{ 
                  fontFamily: 'var(--font-mono)', 
                  fontWeight: 600,
                  color: card.sla_compliance_pct === 100 ? 'var(--success)' : 
                         card.sla_compliance_pct > 95 ? 'var(--warning)' : 'var(--danger)'
                }}>
                  {card.sla_compliance_pct.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
