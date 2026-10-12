import React from 'react';
import { MapPin, Calendar, Clock, Pause, Play, CheckCircle2 } from 'lucide-react';

export default function TopHeader({ simTime, timeMultiplier, isPaused, togglePause, fleetCounts }) {
  const formatTime = (minutes) => {
    if (!minutes) return '00:00 AM';
    const hrs = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    const period = hrs >= 12 ? 'PM' : 'AM';
    const dispHrs = hrs % 12 === 0 ? 12 : hrs % 12;
    return `${dispHrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')} ${period}`;
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '1.25rem 2rem',
      borderBottom: '1px solid var(--border-card)',
      background: 'var(--bg-dark)'
    }}>
      {/* Left Area: Operations Context */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: 'var(--radius-md)' }}>
          <MapPin size={24} color="var(--text-muted)" />
        </div>
        <div>
          <h1 className="heading-1" style={{ fontSize: '1.1rem', marginBottom: '0.2rem' }}>Pune Operations</h1>
          <div className="text-label" style={{ display: 'flex', gap: '0.75rem' }}>
            <span>{fleetCounts?.warehouses || 3} Warehouses</span>
            <span>&bull;</span>
            <span>{fleetCounts?.vehicles || 11} Vehicles</span>
            <span>&bull;</span>
            <span>{fleetCounts?.deliveries || 56} Deliveries</span>
          </div>
        </div>
      </div>

      {/* Right Area: Simulation & Traffic Context */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        
        {/* Date */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', paddingRight: '1.5rem', borderRight: '1px solid var(--border-card)' }}>
          <Calendar size={20} color="var(--text-muted)" />
          <div>
            <div className="text-label" style={{ color: 'var(--text-main)' }}>Day 04 (Demo)</div>
            <div className="text-body" style={{ fontSize: '0.75rem' }}>Mon, 8 Sep 2026</div>
          </div>
        </div>

        {/* Sim Clock */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', paddingRight: '1.5rem', borderRight: '1px solid var(--border-card)' }}>
          <Clock size={20} color="var(--text-muted)" />
          <div>
            <div className="text-label">Simulation Time</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="heading-2" style={{ fontSize: '1.1rem' }}>{formatTime(simTime)}</span>
              <span style={{ fontSize: '0.65rem', background: 'rgba(99,102,241,0.2)', color: '#818cf8', padding: '0.1rem 0.4rem', borderRadius: '4px', fontWeight: 600 }}>{timeMultiplier}x</span>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button 
            onClick={togglePause}
            style={{
              width: '36px', height: '36px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-card)',
              background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', transition: 'all 0.2s'
            }}
          >
            {isPaused ? <Play size={16} color="#fff" /> : <Pause size={16} color="#fff" />}
          </button>
        </div>

        {/* Traffic Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', paddingLeft: '1rem' }}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)', zIndex: 2 }} />
            <div style={{ position: 'absolute', width: '100%', height: '100%', background: 'var(--success)', borderRadius: '50%', opacity: 0.4, animation: 'pulse 2s infinite' }} />
          </div>
          <div>
            <div className="text-body" style={{ fontSize: '0.75rem' }}>TomTom Traffic</div>
            <div style={{ color: 'var(--success)', fontSize: '0.75rem', fontWeight: 600 }}>Live</div>
          </div>
        </div>

      </div>
    </div>
  );
}
