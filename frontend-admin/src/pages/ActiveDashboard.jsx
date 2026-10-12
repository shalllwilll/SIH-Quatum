import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import TopHeader from '../components/ActiveDashboard/TopHeader';
import FleetStatusCard from '../components/ActiveDashboard/FleetStatusCard';
import SlaComplianceCard from '../components/ActiveDashboard/SlaComplianceCard';
import NextStopsTable from '../components/ActiveDashboard/NextStopsTable';
import BottomKPIStrip from '../components/ActiveDashboard/BottomKPIStrip';
import LiveMap from '../components/ActiveDashboard/LiveMap';

export default function ActiveDashboard() {
  const [warehouses, setWarehouses] = useState([]);
  const [simVehicles, setSimVehicles] = useState([]);   // live positions from WS telemetry
  const [parcels, setParcels] = useState([]);
  const [activeSession, setActiveSession] = useState(null); // session with route_geometry

  const [simTime, setSimTime] = useState(540); // 9:00 AM
  const [timeMultiplier, setTimeMultiplier] = useState(60);
  const [isPaused, setIsPaused] = useState(false);
  const [simComplete, setSimComplete] = useState(false);
  const [simStatus, setSimStatus] = useState('idle'); // 'idle' | 'running' | 'complete'

  const wsRef = useRef(null);

  // ── Fetch static data (warehouses, parcels) ──────────────────────────────
  const fetchStaticData = useCallback(async () => {
    try {
      const [whRes, parRes] = await Promise.all([
        fetch('http://localhost:8000/demo/warehouses'),
        fetch('http://localhost:8000/parcels'),
      ]);
      if (whRes.ok) setWarehouses(await whRes.json());
      if (parRes.ok) {
        const pData = await parRes.json();
        setParcels(pData.items || []);
      }
    } catch (err) {
      console.error('Failed to fetch static data', err);
    }
  }, []);

  // ── On mount: fetch static data + check if simulation already running ────
  useEffect(() => {
    fetchStaticData();

    // Check if there's already an active simulation running
    fetch('http://localhost:8000/simulation/state')
      .then(r => r.ok ? r.json() : null)
      .then(state => {
        if (state?.has_active_session && state?.session_id) {
          setSimStatus('running');
          // Fetch that session so map can show routes
          return fetch(`http://localhost:8000/routing-sessions/${state.session_id}`)
            .then(r => r.ok ? r.json() : null)
            .then(sess => { if (sess) setActiveSession(sess); });
        }
      })
      .catch(() => {});
  }, [fetchStaticData]);

  // ── WebSocket: connect once, handle incoming telemetry ───────────────────
  useEffect(() => {
    const connectWS = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/fleet');
      wsRef.current = ws;

      ws.onopen = () => console.log('[ActiveDashboard] WS connected');

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'telemetry_update') {
            // Update live vehicle positions from simulation engine
            setSimVehicles(data.vehicles || []);
            if (data.clock) {
              setSimTime(data.clock.time_min);
              setTimeMultiplier(data.clock.multiplier);
              setIsPaused(data.clock.paused);
            }
            setSimStatus('running');
            setSimComplete(false);
          } else if (data.type === 'routes_assigned') {
            // Routes were just assigned — fetch the session doc and mark running
            const sessionId = data.session_id;
            if (sessionId) {
              fetch(`http://localhost:8000/routing-sessions/${sessionId}`)
                .then(r => r.ok ? r.json() : null)
                .then(sess => {
                  if (sess) setActiveSession(sess);
                })
                .catch(() => {});
            }
            setSimStatus('running');
            setSimComplete(false);
          } else if (data.type === 'simulation_complete') {
            setSimStatus('complete');
            setSimComplete(true);
            if (data.vehicles) setSimVehicles(data.vehicles);
          }
        } catch (err) {
          console.error('WS parse error', err);
        }
      };

      ws.onclose = () => {
        console.log('[ActiveDashboard] WS closed — reconnecting in 3s...');
        setTimeout(connectWS, 3000);
      };

      ws.onerror = (e) => console.error('[ActiveDashboard] WS error', e);
    };

    connectWS();

    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect loop on unmount
        wsRef.current.close();
      }
    };
  }, []);

  // ── Pause/resume ─────────────────────────────────────────────────────────
  const togglePause = async () => {
    try {
      const endpoint = isPaused ? 'resume' : 'pause';
      await fetch(`http://localhost:8000/simulation/${endpoint}`, { method: 'POST' });
      setIsPaused(!isPaused);
    } catch (err) {
      console.error('Failed to toggle pause', err);
    }
  };

  // ── Metrics from live vehicle states ─────────────────────────────────────
  const metrics = useMemo(() => {
    const totalVehicles = simVehicles.length || 3;
    const activeVehicles = simVehicles.filter(v => v.status === 'en_route').length;
    const deliveringVehicles = simVehicles.filter(v => v.status === 'delivering').length;
    const completedVehicles = simVehicles.filter(v => v.status === 'complete').length;

    const totalStops = simVehicles.reduce((sum, v) => sum + (v.total_stops || 0), 0);
    const doneStops = simVehicles.reduce((sum, v) => sum + (v.current_stop_index || 0), 0);

    const compliancePercent = totalStops > 0 ? Math.round((doneStops / totalStops) * 100) : 0;

    const nextStops = simVehicles
      .filter(v => v.status === 'en_route' && v.total_stops > v.current_stop_index)
      .map(v => ({
        vehicleId: v.vehicle_id,
        stopId: `Stop ${v.current_stop_index + 1} of ${v.total_stops}`,
        etaFormatted: 'En Route',
      }))
      .slice(0, 5);

    return {
      fleet: {
        totalVehicles,
        activeVehicles: activeVehicles + deliveringVehicles,
        parcels: {
          total: parcels.length,
          completed: doneStops,
          enRoute: activeVehicles,
          returning: completedVehicles,
          pending: Math.max(0, parcels.length - doneStops),
        },
      },
      sla: {
        compliancePercent,
        onTime: doneStops,
        late: 0,
        upcoming: Math.max(0, totalStops - doneStops),
      },
      kpis: {
        totalDistance: 184.2,
        fuelConsumed: 32.4,
        timeFormatted: `${Math.floor(simTime / 60)}:${String(Math.floor(simTime % 60)).padStart(2, '0')}`,
        carbonEmissions: 71.2,
        deliveriesCompleted: doneStops,
        totalDeliveries: totalStops || parcels.length,
      },
      nextStops,
    };
  }, [simVehicles, parcels, simTime]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', position: 'relative' }}>
      {/* Top Header */}
      <TopHeader
        simTime={simTime}
        timeMultiplier={timeMultiplier}
        isPaused={isPaused}
        togglePause={togglePause}
        fleetCounts={{ warehouses: warehouses.length, vehicles: simVehicles.length, deliveries: parcels.length }}
      />

      {/* Simulation Status Banner */}
      {simStatus === 'idle' && (
        <div style={{
          background: 'linear-gradient(90deg, rgba(99,102,241,0.15), rgba(99,102,241,0.05))',
          borderBottom: '1px solid rgba(99,102,241,0.3)',
          padding: '0.5rem 2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.8rem',
          color: '#94a3b8',
        }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#475569', display: 'inline-block' }} />
          No active simulation. Assign routes from the <strong style={{ color: '#818CF8', marginLeft: 4 }}>Comparison Panel</strong> to start live vehicle tracking.
        </div>
      )}
      {simStatus === 'running' && (
        <div style={{
          background: 'linear-gradient(90deg, rgba(16,185,129,0.15), rgba(16,185,129,0.05))',
          borderBottom: '1px solid rgba(16,185,129,0.3)',
          padding: '0.5rem 2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.8rem',
          color: '#6EE7B7',
        }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: '#10B981', display: 'inline-block',
            boxShadow: '0 0 6px #10B981',
            animation: 'pulse 1.2s ease-in-out infinite',
          }} />
          <strong>Live Simulation Active</strong> — 1 min real-time = 1 hour simulated • Vehicles moving along assigned routes
          {isPaused && <span style={{ color: '#F59E0B', marginLeft: 8 }}>⏸ Paused</span>}
        </div>
      )}
      {simStatus === 'complete' && (
        <div style={{
          background: 'linear-gradient(90deg, rgba(99,102,241,0.15), rgba(99,102,241,0.05))',
          borderBottom: '1px solid rgba(99,102,241,0.3)',
          padding: '0.5rem 2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.8rem',
          color: '#818CF8',
        }}>
          <span style={{ fontSize: '1rem' }}>✅</span>
          <strong>Simulation Complete</strong> — All vehicles have returned to base. Assign new routes to re-run.
        </div>
      )}

      {/* Main Content Area */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Left: Map Container */}
        <div style={{ flex: 1, padding: '1.25rem', paddingRight: '0.625rem', display: 'flex', flexDirection: 'column' }}>
          <LiveMap
            warehouses={warehouses}
            simVehicles={simVehicles}
            parcels={parcels}
            session={activeSession}
            simStatus={simStatus}
          />
        </div>

        {/* Right: Telemetry & KPIs */}
        <div style={{ width: '380px', padding: '1.25rem', paddingLeft: '0.625rem', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
          <FleetStatusCard metrics={metrics.fleet} />
          <SlaComplianceCard metrics={metrics.sla} />
          <NextStopsTable nextStops={metrics.nextStops} />
        </div>

      </div>

      {/* Bottom KPI Strip */}
      <BottomKPIStrip kpis={metrics.kpis} />
    </div>
  );
}
