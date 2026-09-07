import React, { useState } from 'react';
import { Fuel, TrendingUp, Calendar, Zap } from 'lucide-react';

export default function FuelTrendChart({ data = [] }) {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-dim)' }}>
        No fuel efficiency sessions recorded yet.
      </div>
    );
  }

  // SVG Chart dimensions
  const width = 600;
  const height = 240;
  const padding = { top: 30, right: 30, bottom: 40, left: 45 };

  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Compute Scales
  const scores = data.map((d) => d.fuel_efficiency_score);
  const minScore = Math.max(0, Math.min(...scores) - 10);
  const maxScore = Math.min(100, Math.max(...scores) + 10);

  const getX = (idx) => {
    if (data.length <= 1) return padding.left + chartWidth / 2;
    return padding.left + (idx / (data.length - 1)) * chartWidth;
  };

  const getY = (val) => {
    const range = maxScore - minScore || 1;
    return padding.top + chartHeight - ((val - minScore) / range) * chartHeight;
  };

  // Build SVG Path
  const points = data.map((d, i) => [getX(i), getY(d.fuel_efficiency_score)]);
  const pathD = points.reduce((acc, curr, i) => {
    return i === 0 ? `M ${curr[0]},${curr[1]}` : `${acc} L ${curr[0]},${curr[1]}`;
  }, '');

  const areaD = points.length > 0
    ? `${pathD} L ${points[points.length - 1][0]},${padding.top + chartHeight} L ${points[0][0]},${padding.top + chartHeight} Z`
    : '';

  // Trend computation
  const firstVal = data[0]?.fuel_efficiency_score || 0;
  const lastVal = data[data.length - 1]?.fuel_efficiency_score || 0;
  const delta = lastVal - firstVal;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Chart Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(16, 185, 129, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Fuel size={16} color="#34d399" />
          </div>
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>Fuel Efficiency & Green Routing Trend</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>QPSO Congestion Avoidance Index (0–100)</span>
          </div>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          background: 'rgba(16, 185, 129, 0.1)',
          padding: '0.35rem 0.75rem',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
        }}>
          <TrendingUp size={14} color="#34d399" />
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#34d399' }}>
            {delta >= 0 ? `+${delta.toFixed(1)}%` : `${delta.toFixed(1)}%`} Optimization Gain
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', maxHeight: '260px' }}>
          <defs>
            <linearGradient id="fuelGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio, idx) => {
            const y = padding.top + chartHeight * ratio;
            const val = Math.round(maxScore - ratio * (maxScore - minScore));
            return (
              <g key={idx}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="rgba(255, 255, 255, 0.05)"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  fill="#64748b"
                  fontSize="10"
                  textAnchor="end"
                >
                  {val}
                </text>
              </g>
            );
          })}

          {/* Area Fill */}
          <path d={areaD} fill="url(#fuelGradient)" />

          {/* Trend Line */}
          <path
            d={pathD}
            fill="none"
            stroke="#10b981"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data Points */}
          {data.map((d, i) => {
            const cx = getX(i);
            const cy = getY(d.fuel_efficiency_score);
            const isHovered = hoveredPoint === i;

            return (
              <g key={d.session_id || i}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 6 : 4}
                  fill="#10b981"
                  stroke="#ffffff"
                  strokeWidth="2"
                  style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
                  onMouseEnter={() => setHoveredPoint(i)}
                  onMouseLeave={() => setHoveredPoint(null)}
                />
                {/* X-axis Label */}
                <text
                  x={cx}
                  y={padding.top + chartHeight + 18}
                  fill="#94a3b8"
                  fontSize="10"
                  textAnchor="middle"
                  fontWeight="600"
                >
                  S#{i + 1}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Floating Tooltip */}
        {hoveredPoint !== null && data[hoveredPoint] && (
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '16px',
            background: 'rgba(18, 26, 43, 0.95)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.6rem 0.85rem',
            fontSize: '0.75rem',
            boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
            pointerEvents: 'none',
          }}>
            <div style={{ fontWeight: 700, color: '#fff', marginBottom: '0.2rem' }}>
              Session {data[hoveredPoint].session_id.slice(-6)} ({data[hoveredPoint].preset})
            </div>
            <div style={{ color: '#34d399', fontWeight: 600 }}>
              Efficiency Score: {data[hoveredPoint].fuel_efficiency_score} / 100
            </div>
            <div style={{ color: '#cbd5e1' }}>
              Fleet Distance: {data[hoveredPoint].total_distance_km} km ({data[hoveredPoint].estimated_fuel_liters} L fuel)
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
