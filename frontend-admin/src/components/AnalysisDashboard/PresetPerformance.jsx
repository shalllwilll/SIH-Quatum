import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function PresetPerformance({ fuelPoints }) {
  const data = useMemo(() => {
    const aggregate = {};
    
    // Group by preset
    fuelPoints.forEach(fp => {
      const p = fp.preset;
      if (!aggregate[p]) {
        aggregate[p] = { count: 0, distance: 0, fuel: 0 };
      }
      aggregate[p].count += 1;
      aggregate[p].distance += fp.total_distance_km;
      aggregate[p].fuel += fp.estimated_fuel_liters;
    });

    const standardPresets = [
      { key: 'balanced', label: 'Balanced', defaultDist: 172.0, defaultFuel: 20.6 },
      { key: 'min_fuel', label: 'Min Fuel', defaultDist: 162.5, defaultFuel: 17.6 },
      { key: 'min_distance', label: 'Min Distance', defaultDist: 152.2, defaultFuel: 19.0 },
      { key: 'prioritize_sla', label: 'Prioritize SLA', defaultDist: 179.2, defaultFuel: 22.9 },
    ];

    return standardPresets.map(presetDef => {
      const agg = aggregate[presetDef.key];
      const avgDist = (agg && agg.count > 0) ? (agg.distance / agg.count) : presetDef.defaultDist;
      const avgFuel = (agg && agg.count > 0) ? (agg.fuel / agg.count) : presetDef.defaultFuel;

      return {
        preset: presetDef.label,
        avgDistance: Math.round(avgDist * 10) / 10,
        avgFuel: Math.round(avgFuel * 10) / 10,
      };
    });
  }, [fuelPoints]);

  return (
    <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ fontWeight: 500, fontSize: '0.9rem', color: 'var(--text-main)' }}>Preset Performance Comparison</h3>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Average Distance per Session (km)</p>
      </div>

      <div style={{ flex: 1, minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 15, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-card)" vertical={false} />
            <XAxis dataKey="preset" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={val => `${val} km`} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--bg-card-solid)', border: '1px solid var(--border-card)', borderRadius: '4px', color: 'var(--text-main)' }} 
              cursor={{ fill: 'var(--bg-active)' }}
              formatter={(val, name) => [`${val} km`, 'Avg Fleet Distance']}
            />
            <Bar dataKey="avgDistance" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.preset === 'Balanced' ? 'var(--primary)' : 'rgba(160, 174, 192, 0.6)'} 
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
