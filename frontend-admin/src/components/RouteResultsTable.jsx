import React, { useState } from 'react';
import {
  Truck,
  Clock,
  Navigation,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Zap,
  Activity,
} from 'lucide-react';

function formatMinutes(min) {
  if (min == null) return '--:--';
  const h = Math.floor(min / 60) % 24;
  const m = Math.floor(min % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

export default function RouteResultsTable({
  sessionData,
  selectedVehicleId,
  onSelectVehicle,
}) {
  const [expandedVehicle, setExpandedVehicle] = useState(null);

  if (!sessionData) return null;

  const {
    total_distance_km,
    sla_compliance_pct,
    vehicle_assignments = [],
    cluster_count,
    metadata = {},
  } = sessionData;

  const {
    execution_time_ms = 0,
    bounceback_count = 0,
    feasible = true,
    fallback_applied = false,
  } = metadata;

  const toggleExpand = (vehId) => {
    setExpandedVehicle(expandedVehicle === vehId ? null : vehId);
    if (onSelectVehicle) {
      onSelectVehicle(vehId);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Top Level Metric KPIs */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: '0.75rem',
      }}>
        {/* SLA Compliance */}
        <div style={{
          background: sla_compliance_pct >= 90 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
          border: `1px solid ${sla_compliance_pct >= 90 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
          borderRadius: 'var(--radius-sm)',
          padding: '0.85rem 1rem',
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Clock size={13} /> SLA Compliance
          </div>
          <div style={{
            fontSize: '1.4rem',
            fontWeight: 800,
            color: sla_compliance_pct >= 90 ? '#34d399' : '#fbbf24',
            marginTop: '0.2rem',
          }}>
            {sla_compliance_pct != null ? `${sla_compliance_pct}%` : 'N/A'}
          </div>
        </div>

        {/* Total Distance */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-card)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.85rem 1rem',
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Navigation size={13} /> Total Distance
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fff', marginTop: '0.2rem' }}>
            {total_distance_km != null ? `${total_distance_km.toFixed(1)} km` : 'N/A'}
          </div>
        </div>

        {/* Leiden Clusters */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-card)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.85rem 1rem',
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Activity size={13} /> Active Clusters
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#818cf8', marginTop: '0.2rem' }}>
            {cluster_count || vehicle_assignments.length}
          </div>
        </div>

        {/* QGA-QPSO Iterations / Execution */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-card)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.85rem 1rem',
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Zap size={13} /> Optimization Time
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#38bdf8', marginTop: '0.2rem' }}>
            {execution_time_ms ? `${(execution_time_ms / 1000).toFixed(2)}s` : '< 1s'}
          </div>
        </div>
      </div>

      {/* SLA Fallback Warning Banner if applicable */}
      {fallback_applied && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '0.75rem 1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}>
          <AlertTriangle size={20} color="#f87171" style={{ flexShrink: 0 }} />
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f87171' }}>
              Best-Effort SLA Fallback Applied
            </div>
            <div style={{ fontSize: '0.75rem', color: '#fca5a5', marginTop: '0.15rem' }}>
              One or more over-constrained stops could not satisfy strict SLA windows after {bounceback_count} bounce-back iterations. Routes have been assigned with minimal SLA penalty without dropping parcels.
            </div>
          </div>
        </div>
      )}

      {/* Vehicle Routes Table */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid var(--border-card)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
      }}>
        <div style={{
          padding: '0.75rem 1rem',
          borderBottom: '1px solid var(--border-card)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>
            Vehicle Schedules & Dispatch Plans ({vehicle_assignments.length})
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Click row to expand stop timeline</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {vehicle_assignments.map((assignment) => {
            const isSelected = selectedVehicleId === assignment.vehicle_id;
            const isExpanded = expandedVehicle === assignment.vehicle_id;
            const isVehicleFallback = assignment.fallback_applied || !assignment.feasible;
            const stops = assignment.stop_arrivals || assignment.stops || [];

            return (
              <div
                key={assignment.vehicle_id}
                style={{
                  borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                  background: isSelected ? 'rgba(99, 102, 241, 0.08)' : 'transparent',
                }}
              >
                {/* Header Row */}
                <div
                  onClick={() => toggleExpand(assignment.vehicle_id)}
                  style={{
                    padding: '0.85rem 1rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    userSelect: 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {isExpanded ? <ChevronDown size={16} color="var(--text-muted)" /> : <ChevronRight size={16} color="var(--text-muted)" />}
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--radius-sm)',
                      background: isVehicleFallback ? 'rgba(239, 68, 68, 0.15)' : 'rgba(99, 102, 241, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}>
                      <Truck size={16} color={isVehicleFallback ? '#f87171' : '#818cf8'} />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff' }}>
                        {assignment.vehicle_id}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        Cluster #{assignment.cluster_id ?? 1} • {stops.length} Deliveries
                      </div>
                    </div>
                  </div>

                  {/* Timing & Feasibility Badges */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#fff' }}>
                        {formatMinutes(assignment.departure_time_min)} → {formatMinutes(assignment.return_arrival_time_min)}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                        {assignment.total_duration_min ? `${Math.round(assignment.total_duration_min)} min route` : ''}
                      </div>
                    </div>

                    {isVehicleFallback ? (
                      <span className="badge badge-danger" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <AlertTriangle size={11} /> SLA Fallback
                      </span>
                    ) : (
                      <span className="badge badge-success" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <CheckCircle2 size={11} /> Feasible
                      </span>
                    )}
                  </div>
                </div>

                {/* Expanded Stops Timeline */}
                {isExpanded && (
                  <div style={{
                    padding: '0.75rem 1rem 1rem 3.5rem',
                    background: 'rgba(0, 0, 0, 0.2)',
                    borderTop: '1px solid rgba(255, 255, 255, 0.03)',
                  }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-dim)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                      Stop Execution Sequence
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                      {stops.map((stopItem, sIdx) => {
                        const stopId = typeof stopItem === 'string' ? stopItem : stopItem.stop_id;
                        const arrivalMin = typeof stopItem === 'object' ? stopItem.arrival_time_min : null;
                        const depMin = typeof stopItem === 'object' ? stopItem.departure_time_min : null;

                        return (
                          <div
                            key={`${stopId}-${sIdx}`}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              fontSize: '0.75rem',
                              padding: '0.4rem 0.6rem',
                              background: 'rgba(255, 255, 255, 0.02)',
                              borderRadius: 'var(--radius-sm)',
                              border: '1px solid rgba(255, 255, 255, 0.03)',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span style={{ fontWeight: 800, color: 'var(--primary)' }}>#{sIdx + 1}</span>
                              <span style={{ color: '#fff', fontWeight: 600 }}>{stopId}</span>
                            </div>
                            <div style={{ color: 'var(--text-muted)' }}>
                              Arrival: <strong style={{ color: '#cbd5e1' }}>{formatMinutes(arrivalMin)}</strong>
                              {depMin && ` • Dep: ${formatMinutes(depMin)}`}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
