import React, { useState, useEffect } from 'react';
import { driverApi } from '../api/client';
import { useDriverAuth } from '../context/AuthContext';
import StopActionButtons from '../components/StopActionButtons';
import {
  Truck,
  MapPin,
  Clock,
  Package,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Calendar,
} from 'lucide-react';

function formatMinutesToTime(min) {
  if (min == null) return '--:--';
  const h24 = Math.floor(min / 60) % 24;
  const m = Math.floor(min % 60);
  const period = h24 >= 12 ? 'PM' : 'AM';
  const h12 = h24 % 12 || 12;
  return `${h12}:${String(m).padStart(2, '0')} ${period}`;
}

export default function AssignedRoute() {
  const { user } = useDriverAuth();
  const [manifest, setManifest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stopStatuses, setStopStatuses] = useState({});

  const fetchManifest = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await driverApi.getManifest();
      setManifest(data);
      // Initialize local statuses
      const initialStatuses = {};
      data?.itinerary?.forEach((s) => {
        initialStatuses[s.parcel_id] = s.status || 'pending';
      });
      setStopStatuses((prev) => ({ ...initialStatuses, ...prev }));
    } catch (err) {
      setError(err.message || 'Failed to load route manifest.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchManifest();
  }, []);

  const handleStatusUpdated = (parcelId, newStatus) => {
    setStopStatuses((prev) => ({
      ...prev,
      [parcelId]: newStatus,
    }));
  };

  const itinerary = manifest?.itinerary || [];
  const totalStops = itinerary.length;
  const deliveredCount = Object.values(stopStatuses).filter((s) => s === 'delivered').length;
  const failedCount = Object.values(stopStatuses).filter((s) => s === 'failed').length;
  const remainingCount = totalStops - deliveredCount - failedCount;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '640px', margin: '0 auto', width: '100%' }}>
      {/* Driver & Shift Header Card */}
      <div className="glass-card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-sm)',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Truck size={18} color="#fff" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff', lineHeight: 1.1 }}>
                {manifest?.vehicle_label || user?.vehicle_label || 'Assigned Vehicle'}
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Driver: <strong>{user?.name || user?.username}</strong>
              </span>
            </div>
          </div>

          <button
            onClick={fetchManifest}
            className="btn-secondary"
            style={{ padding: '0.45rem 0.75rem', fontSize: '0.75rem' }}
            title="Refresh Route"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Sync</span>
          </button>
        </div>

        {/* Progress KPIs */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '0.5rem',
          paddingTop: '0.75rem',
          borderTop: '1px solid var(--border-card)',
        }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.5rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Remaining</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>{remainingCount}</div>
          </div>
          <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '0.5rem', borderRadius: 'var(--radius-sm)', textAlign: 'center', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
            <div style={{ fontSize: '0.7rem', color: '#34d399' }}>Delivered</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#34d399' }}>{deliveredCount}</div>
          </div>
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '0.5rem', borderRadius: 'var(--radius-sm)', textAlign: 'center', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <div style={{ fontSize: '0.7rem', color: '#f87171' }}>Failed</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f87171' }}>{failedCount}</div>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '0.75rem 1rem',
          color: '#f87171',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Ordered Stop List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 0.25rem' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Shift Delivery Sequence ({totalStops} Stops)
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>QPSO Timed Manifest</span>
        </div>

        {itinerary.map((stop, idx) => {
          const currentStatus = stopStatuses[stop.parcel_id] || stop.status || 'pending';
          const isPending = currentStatus === 'pending';

          return (
            <div
              key={`${stop.parcel_id}-${idx}`}
              className="glass-card"
              style={{
                padding: '1rem',
                borderLeft: isPending ? '4px solid var(--primary)' : currentStatus === 'delivered' ? '4px solid #10b981' : '4px solid #ef4444',
                opacity: isPending ? 1 : 0.85,
                transition: 'all 0.2s ease',
              }}
            >
              {/* Stop Header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    background: 'var(--primary)',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                  }}>
                    {stop.stop_index || idx + 1}
                  </span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>
                    {stop.parcel_id}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  <Package size={13} />
                  <span>{stop.weight_kg} kg</span>
                </div>
              </div>

              {/* Address */}
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.4rem', color: '#cbd5e1', fontSize: '0.85rem', marginBottom: '0.6rem' }}>
                <MapPin size={15} color="var(--primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <span>{stop.address}</span>
              </div>

              {/* SLA Deadlines */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '0.75rem',
                padding: '0.4rem 0.6rem',
                background: 'rgba(255, 255, 255, 0.02)',
                borderRadius: 'var(--radius-sm)',
                marginBottom: '0.75rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-muted)' }}>
                  <Clock size={13} color="#38bdf8" />
                  <span>Est. Arrival: <strong>{formatMinutesToTime(stop.scheduled_arrival_min)}</strong></span>
                </div>
                <div style={{ color: '#fbbf24', fontWeight: 600 }}>
                  Deadline: {formatMinutesToTime(stop.sla_deadline_min)}
                </div>
              </div>

              {/* Action Buttons */}
              <StopActionButtons
                stopId={stop.parcel_id}
                vehicleId={manifest.vehicle_label}
                sessionId={manifest.session_id}
                currentStatus={currentStatus}
                onStatusUpdated={handleStatusUpdated}
              />
            </div>
          );
        })}

        {!itinerary.length && !loading && (
          <div className="glass-card" style={{ padding: '3rem 1.5rem', textAlign: 'center' }}>
            <Calendar size={32} color="var(--text-dim)" style={{ margin: '0 auto 0.75rem' }} />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff', marginBottom: '0.35rem' }}>
              No Active Routes Assigned
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Your vehicle has no pending delivery schedules dispatched for this shift.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
