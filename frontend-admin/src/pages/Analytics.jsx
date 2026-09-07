import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import FuelTrendChart from '../components/FuelTrendChart';
import SlaComplianceView from '../components/SlaComplianceView';
import ViolationHistory from '../components/ViolationHistory';
import VehiclePerformanceTable from '../components/VehiclePerformanceTable';
import {
  BarChart3,
  RefreshCw,
  TrendingUp,
  Clock,
  Fuel,
  ShieldCheck,
  AlertCircle,
} from 'lucide-react';

export default function Analytics() {
  const [fuelData, setFuelData] = useState([]);
  const [slaSummary, setSlaSummary] = useState(null);
  const [vehicleSla, setVehicleSla] = useState([]);
  const [violations, setViolations] = useState([]);
  const [vehicleStats, setVehicleStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const [fuel, sla, vehSla, viol, stats] = await Promise.all([
        api.getFuelEfficiencyTrend(),
        api.getSlaCompliance(),
        api.getSlaCompliance('vehicle'),
        api.getViolations(),
        api.getVehiclePerformance(),
      ]);

      setFuelData(fuel || []);
      setSlaSummary(sla);
      setVehicleSla(vehSla || []);
      setViolations(viol || []);
      setVehicleStats(stats || []);
    } catch (err) {
      setError(err.message || 'Failed to load analytics dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BarChart3 size={22} color="var(--primary)" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff' }}>
              Fleet Performance & Predictive Analytics
            </h2>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
            Historical multi-session trends demonstrating progressive optimization of fuel, mileage, and SLA precision.
          </p>
        </div>

        <button
          onClick={fetchAnalytics}
          className="btn-secondary"
          style={{ padding: '0.6rem 1rem' }}
          title="Refresh Analytics"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '0.85rem 1rem',
          color: '#f87171',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Analytics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem' }}>
        {/* Left Column: Fuel Efficiency & Vehicle Performance */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Fuel Trend Card */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <FuelTrendChart data={fuelData} />
          </div>

          {/* Vehicle Performance Table Card */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <VehiclePerformanceTable stats={vehicleStats} />
          </div>
        </div>

        {/* Right Column: SLA Compliance & Violations Log */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* SLA Compliance View Card */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <SlaComplianceView summary={slaSummary} vehicleBreakdown={vehicleSla} />
          </div>

          {/* Violations History Card */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <ViolationHistory violations={violations} />
          </div>
        </div>
      </div>
    </div>
  );
}
