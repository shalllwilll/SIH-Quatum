import React, { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function PerformanceTrends({ fuelPoints, slaDataPerVehicle }) {
  const [metric, setMetric] = useState('SLA Compliance'); // 'SLA Compliance', 'Fuel Consumption', 'Distance', 'CO2'

  const data = useMemo(() => {
    return fuelPoints.map((fp, idx) => {
      const co2 = fp.carbon_emissions_kg || (fp.estimated_fuel_liters * 2.64);
      const dayName = fp.day_label || `Day ${idx + 1}`;
      
      return {
        name: dayName,
        'SLA Compliance': fp.sla_compliance_pct ?? 95.0,
        'Fuel Consumption': fp.estimated_fuel_liters,
        'Distance': fp.total_distance_km,
        'CO2': Math.round(co2 * 10) / 10,
      };
    });
  }, [fuelPoints]);

  const colorMap = {
    'SLA Compliance': 'var(--success)',
    'Fuel Consumption': 'var(--primary)',
    'Distance': 'var(--text-main)',
    'CO2': 'var(--warning)',
  };

  const unitMap = {
    'SLA Compliance': '%',
    'Fuel Consumption': 'L',
    'Distance': 'km',
    'CO2': 'kg',
  };

  return (
    <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontWeight: 500, fontSize: '0.9rem', color: 'var(--text-main)' }}>Performance Trends</h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Day-wise operational evolution across 6 dispatch days</p>
        </div>
        <select 
          value={metric} 
          onChange={e => setMetric(e.target.value)}
          style={{ 
            background: 'var(--bg-active)', 
            border: '1px solid var(--border-card)', 
            color: 'var(--text-main)',
            padding: '0.35rem 0.6rem',
            borderRadius: '4px',
            fontSize: '0.8rem',
            outline: 'none',
            cursor: 'pointer'
          }}
        >
          <option>SLA Compliance</option>
          <option>Fuel Consumption</option>
          <option>Distance</option>
          <option>CO2</option>
        </select>
      </div>

      <div style={{ flex: 1, minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-card)" vertical={false} />
            <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis 
              stroke="var(--text-muted)" 
              fontSize={11} 
              tickLine={false} 
              axisLine={false}
              domain={metric === 'SLA Compliance' ? [80, 100] : ['auto', 'auto']}
              tickFormatter={val => `${val}${unitMap[metric]}`}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--bg-card-solid)', border: '1px solid var(--border-card)', borderRadius: '4px', color: 'var(--text-main)' }} 
              itemStyle={{ color: colorMap[metric], fontWeight: 600 }}
              formatter={(val) => [`${val} ${unitMap[metric]}`, metric]}
            />
            <Line 
              type="monotone" 
              dataKey={metric} 
              stroke={colorMap[metric]} 
              strokeWidth={2.5} 
              dot={{ r: 4, fill: colorMap[metric], strokeWidth: 2, stroke: '#0a0b0e' }} 
              activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }} 
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
