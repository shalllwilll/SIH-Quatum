import React from 'react';

export default function StrategyInsights({ tradeoffSummary, selectedCard }) {
  if (!selectedCard) return null;

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border-card)', backgroundColor: 'var(--bg-card-solid)' }}>
        <h3 style={{ fontWeight: 500, fontSize: '0.9rem', color: 'var(--text-main)' }}>Strategy Insights</h3>
      </div>
      <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem', flex: 1, overflowY: 'auto' }}>
        
        {/* Selected Preset Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {selectedCard?.name}
          </h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
            <span style={{ color: 'var(--primary)', marginRight: '0.5rem' }}>•</span>
            {selectedCard?.key_tradeoff}
          </p>
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)', marginTop: '0.25rem' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: 500 }}>Verdict</p>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{selectedCard?.verdict}</p>
          </div>
        </div>

        {/* Network Wide Trade-offs */}
        <div style={{ marginTop: '0.5rem' }}>
          <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
            Overall Network Trade-offs
          </h4>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {tradeoffSummary.map((insight, idx) => (
              <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
                <span style={{ color: 'var(--primary)', marginTop: '0.1rem' }}>•</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
