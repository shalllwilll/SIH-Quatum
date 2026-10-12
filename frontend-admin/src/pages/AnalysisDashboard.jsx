import React, { useState, useEffect } from 'react';
import TopKPISummary from '../components/AnalysisDashboard/TopKPISummary';
import PerformanceTrends from '../components/AnalysisDashboard/PerformanceTrends';
import PresetPerformance from '../components/AnalysisDashboard/PresetPerformance';
import SessionHistory from '../components/AnalysisDashboard/SessionHistory';
import KeyInsights from '../components/AnalysisDashboard/KeyInsights';

export default function AnalysisDashboard() {
  const [sessions, setSessions] = useState([]);
  const [slaSummary, setSlaSummary] = useState(null);
  const [fuelPoints, setFuelPoints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch historical sessions
        const sessionRes = await fetch('http://localhost:8000/routing-sessions/');
        const sessionData = await sessionRes.json();
        
        // Fetch analytics
        const slaRes = await fetch('http://localhost:8000/analytics/sla-compliance');
        const slaData = await slaRes.json();

        const fuelRes = await fetch('http://localhost:8000/analytics/fuel-efficiency');
        const fuelData = await fuelRes.json();

        setSessions(sessionData || []);
        setSlaSummary(slaData || null);
        setFuelPoints(fuelData || []);
      } catch (err) {
        console.error("Error fetching analysis data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
        Loading historical data...
      </div>
    );
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '1.5rem', overflowY: 'auto' }}>
      
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 500, color: 'var(--text-main)', marginBottom: '0.5rem' }}>Analysis Dashboard</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Historical KPIs, trends, and strategic insights</p>
      </div>

      {/* Top KPIs */}
      <TopKPISummary sessions={sessions} slaSummary={slaSummary} fuelPoints={fuelPoints} />

      {/* Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginBottom: '1.5rem', minHeight: '320px' }}>
        <PerformanceTrends fuelPoints={fuelPoints} />
        <PresetPerformance fuelPoints={fuelPoints} />
      </div>

      {/* Bottom Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem', minHeight: '300px' }}>
        <KeyInsights sessions={sessions} />
        <SessionHistory sessions={sessions} />
      </div>

    </div>
  );
}
