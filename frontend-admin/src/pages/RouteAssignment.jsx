import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import PresetSelector from '../components/PresetSelector';
import RouteMap from '../components/RouteMap';
import RouteResultsTable from '../components/RouteResultsTable';
import {
  Play,
  Send,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Layers,
} from 'lucide-react';

export default function RouteAssignment() {
  const [preset, setPreset] = useState('balanced');
  const [running, setRunning] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [error, setError] = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const [assigning, setAssigning] = useState(false);
  const [assignSuccess, setAssignSuccess] = useState(null);
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);

  const [warehouses, setWarehouses] = useState([]);
  const [stopsLookup, setStopsLookup] = useState({});

  // Fetch static warehouses and parcels on mount for map coordinates
  useEffect(() => {
    api.getWarehouses()
      .then((data) => setWarehouses(data || []))
      .catch((err) => console.warn('Could not load warehouses:', err));

    api.getParcels(1, 200)
      .then((res) => {
        const items = res?.items || res || [];
        const lookup = {};
        items.forEach((p) => {
          const key = p.parcel_id || p.tracking_number || p._id || p.id;
          lookup[key] = {
            lat: p.lat,
            lon: p.lon,
            address: p.address,
            weight_kg: p.weight_kg,
          };
        });
        setStopsLookup(lookup);
      })
      .catch((err) => console.warn('Could not load parcels:', err));
  }, []);

  const handleRunOptimization = async () => {
    setRunning(true);
    setError(null);
    setAssignSuccess(null);
    setProgressMsg('Initializing QGA + QPSO Optimization Engine...');

    try {
      // Trigger optimization run
      const res = await api.runRoutingSession({
        preset,
        max_bounceback_retries: 3,
        seed: 42,
        async_run: false, // execute synchronously or poll if needed
      });

      const sessionId = res.session_id;
      setProgressMsg('Optimizing discrete clustering & continuous timing...');

      // Fetch complete session details
      const details = await api.getSessionDetails(sessionId);
      setSessionData(details);
      setRunning(false);
      setProgressMsg('');
    } catch (err) {
      setError(err.message || 'Optimization pipeline encountered an error');
      setRunning(false);
      setProgressMsg('');
    }
  };

  const handleAssignRoutes = async () => {
    if (!sessionData?.id) return;
    setAssigning(true);
    setError(null);
    try {
      const res = await api.assignSessionRoutes(sessionData.id);
      setAssignSuccess(`Successfully assigned ${res.assigned_vehicles_count} vehicles across ${res.assigned_parcels_count} deliveries!`);
    } catch (err) {
      setError(err.message || 'Failed to assign routes to fleet');
    } finally {
      setAssigning(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner & Run Action */}
      <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <PresetSelector
          selectedPreset={preset}
          onSelect={setPreset}
          disabled={running}
        />

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '1rem', borderTop: '1px solid var(--border-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span className="badge badge-primary">
              <Sparkles size={12} /> Quantum-Inspired Genetic Algorithm + Particle Swarm
            </span>
            {running && (
              <span style={{ fontSize: '0.85rem', color: '#818cf8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <RefreshCw className="animate-spin" size={14} /> {progressMsg}
              </span>
            )}
          </div>

          <button
            onClick={handleRunOptimization}
            disabled={running}
            className="btn-primary"
            style={{ padding: '0.75rem 1.75rem', fontSize: '0.95rem' }}
          >
            {running ? (
              <>
                <RefreshCw className="animate-spin" size={18} />
                <span>Running Optimization...</span>
              </>
            ) : (
              <>
                <Play size={18} />
                <span>Run Optimization Pipeline</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '1rem',
          color: '#f87171',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Assign Success Alert */}
      {assignSuccess && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '1rem',
          color: '#34d399',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <CheckCircle2 size={20} />
            <span style={{ fontWeight: 600 }}>{assignSuccess}</span>
          </div>
          <span className="badge badge-success">FLEET DISPATCHED</span>
        </div>
      )}

      {/* Main Results View */}
      {sessionData ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Dispatch Action Bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(255, 255, 255, 0.02)',
            padding: '1rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-card)',
          }}>
            <div>
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff' }}>
                Optimization Solution Generated
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginLeft: '0.75rem' }}>
                Preset: <strong style={{ color: 'var(--primary)' }}>{sessionData.preset}</strong> • Session ID: {sessionData.id}
              </span>
            </div>

            <button
              onClick={handleAssignRoutes}
              disabled={assigning}
              className="btn-primary"
              style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', boxShadow: '0 4px 15px rgba(16, 185, 129, 0.3)' }}
            >
              <Send size={16} />
              <span>{assigning ? 'Dispatching to Fleet...' : 'Commit & Assign Routes'}</span>
            </button>
          </div>

          {/* Grid: Map + Table */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: '1.25rem', minHeight: '560px' }}>
            {/* Route Map */}
            <div className="glass-card" style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column' }}>
              <RouteMap
                warehouses={warehouses}
                assignments={sessionData.vehicle_assignments || []}
                stopsLookup={stopsLookup}
                selectedVehicleId={selectedVehicleId}
                onSelectVehicle={setSelectedVehicleId}
              />
            </div>

            {/* Results Table & Metrics */}
            <div style={{ display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
              <RouteResultsTable
                sessionData={sessionData}
                selectedVehicleId={selectedVehicleId}
                onSelectVehicle={setSelectedVehicleId}
              />
            </div>
          </div>
        </div>
      ) : (
        /* Empty State */
        !running && (
          <div className="glass-card" style={{ padding: '4rem 2rem', textAlign: 'center' }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: 'var(--radius-lg)',
              background: 'rgba(99, 102, 241, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.5rem',
            }}>
              <Layers size={32} color="#818cf8" />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fff', marginBottom: '0.5rem' }}>
              No Optimization Session Active
            </h3>
            <p style={{ color: 'var(--text-muted)', maxWidth: '480px', margin: '0 auto 1.5rem', fontSize: '0.9rem', lineHeight: 1.5 }}>
              Select an optimization objective preset above and click <strong>"Run Optimization Pipeline"</strong> to partition delivery clusters and compute quantum-inspired vehicle schedules.
            </p>
          </div>
        )
      )}
    </div>
  );
}
