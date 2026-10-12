import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import ComparisonCards from '../components/ComparisonDashboard/ComparisonCards';
import ComparisonMap from '../components/ComparisonDashboard/ComparisonMap';
import StrategyInsights from '../components/ComparisonDashboard/StrategyInsights';
import VehicleAssignments from '../components/ComparisonDashboard/VehicleAssignments';

export default function ComparisonDashboard({ setActiveTab }) {
  const [metrics, setMetrics] = useState(null);
  const [selectedPreset, setSelectedPreset] = useState('balanced');
  const [previewSession, setPreviewSession] = useState(null);
  
  const [isComparing, setIsComparing] = useState(true);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isAssigning, setIsAssigning] = useState(false);
  const [error, setError] = useState(null);

  // 1. Fetch initial comparison matrix
  useEffect(() => {
    const fetchComparison = async () => {
      try {
        setIsComparing(true);
        const res = await api.comparePresets({});
        setMetrics(res);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsComparing(false);
      }
    };
    fetchComparison();
  }, []);

  // 2. When selectedPreset changes, load the session that /compare already computed for that preset
  useEffect(() => {
    if (!metrics) return;  // Wait for initial metrics to load

    const loadPresetSession = async () => {
      try {
        setIsSimulating(true);
        // Use the session_id that /compare already persisted for this preset
        const sessionId = metrics.session_ids?.[selectedPreset];
        if (!sessionId) {
          // Fallback: run a fresh session if session_ids not available
          const runRes = await api.runRoutingSession({
            preset: selectedPreset,
            async_run: false,
            seed: 42 + ['balanced', 'min_fuel', 'min_distance', 'prioritize_sla'].indexOf(selectedPreset),
          });
          const sessionDetails = await api.getSessionDetails(runRes.session_id);
          setPreviewSession(sessionDetails);
          return;
        }
        // Load the pre-computed session for this preset
        const sessionDetails = await api.getSessionDetails(sessionId);
        setPreviewSession(sessionDetails);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsSimulating(false);
      }
    };

    loadPresetSession();
  }, [selectedPreset, metrics]);


  const handleAssign = async () => {
    if (!previewSession) return;
    try {
      setIsAssigning(true);
      await api.assignSessionRoutes(previewSession.id);
      setActiveTab('active');
    } catch (err) {
      setError(err.message);
      setIsAssigning(false);
    }
  };

  if (isComparing && !metrics) {
    return (
      <div className="flex h-full items-center justify-center text-[var(--text-muted)]">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-4"></div>
          <p>Executing Quantum Optimization across all business presets...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return <div className="p-8 text-red-500">Error: {error}</div>;
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '1.5rem 2rem', gap: '1.5rem', overflow: 'hidden', position: 'relative' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <div>
          <h2 className="heading-1">Strategic Preset Comparison</h2>
          <p className="text-body" style={{ marginTop: '0.25rem' }}>Select an optimization strategy to evaluate projected operational metrics against narrow SLA windows.</p>
        </div>
        <button
          onClick={handleAssign}
          disabled={isAssigning || isSimulating || !previewSession}
          className="btn-primary"
          style={ (isAssigning || isSimulating || !previewSession) ? { opacity: 0.5, cursor: 'not-allowed' } : { backgroundColor: 'var(--primary)', color: '#fff', borderColor: 'var(--primary)' } }
        >
          {isAssigning ? 'Assigning...' : `Assign ${metrics?.presets[selectedPreset]?.name || 'Strategy'}`}
        </button>
      </div>

      <div style={{ flexShrink: 0 }}>
        {metrics && (
          <ComparisonCards 
            presets={metrics.presets} 
            selectedPreset={selectedPreset} 
            onSelect={setSelectedPreset} 
          />
        )}
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', minHeight: 0 }}>
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative' }}>
          <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border-card)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--bg-card-solid)' }}>
            <div>
              <h3 style={{ fontWeight: 500, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                Route Preview
                {previewSession && !isSimulating && (
                  <span style={{ marginLeft: '8px', fontSize: '0.72rem', color: 'var(--primary)', fontWeight: 400, opacity: 0.85 }}>
                    — {metrics?.presets[selectedPreset]?.name || selectedPreset}
                  </span>
                )}
              </h3>
            </div>
            {isSimulating && (
              <span style={{ fontSize: '0.75rem', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ height: '8px', width: '8px', backgroundColor: 'var(--primary)', borderRadius: '50%', animation: 'pulse 1.2s infinite' }}></span>
                Loading Routes...
              </span>
            )}
          </div>
          <div style={{ flex: 1, position: 'relative' }}>
            {previewSession && <ComparisonMap key={previewSession.id || selectedPreset} session={previewSession} />}
            {isSimulating && (
              <div style={{ position: 'absolute', inset: 0, backgroundColor: 'rgba(10, 11, 14, 0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, backdropFilter: 'blur(2px)' }}>
                 <div style={{ color: 'var(--text-muted)' }}>Simulating...</div>
              </div>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', minHeight: 0 }}>
          <StrategyInsights 
            tradeoffSummary={metrics?.tradeoff_summary} 
            selectedCard={metrics?.presets[selectedPreset]} 
          />
          <VehicleAssignments 
            assignments={previewSession?.vehicle_assignments || []} 
            isSimulating={isSimulating}
          />
        </div>
      </div>
    </div>
  );
}
