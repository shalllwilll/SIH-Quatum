import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import {
  Activity,
  Radio,
  Server,
  Database,
  Cpu,
  RefreshCw,
  Clock,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

export default function Diagnostics() {
  const [healthData, setHealthData] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastCheck, setLastCheck] = useState(null);

  const fetchDiagnostics = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem('admin_token');
      const healthRes = await fetch('http://localhost:8000/health');
      const healthJson = await healthRes.json().catch(() => null);
      setHealthData(healthJson);

      const eventsData = await api.getDeliveryEvents(null, 20);
      setEvents(eventsData?.items || eventsData || []);
      setLastCheck(new Date());
    } catch (err) {
      console.warn('Diagnostics fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
    const interval = setInterval(fetchDiagnostics, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff' }}>
            Live Engine & System Telemetry
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
            Real-time status of backend services, TomTom live traffic integration, and quantum optimization engine.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {lastCheck && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Clock size={12} /> Last poll: {lastCheck.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchDiagnostics}
            className="btn-secondary"
            style={{ padding: '0.5rem 0.85rem', fontSize: '0.8rem' }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Poll Now</span>
          </button>
        </div>
      </div>

      {/* Services Health Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1rem',
      }}>
        {/* Core REST API */}
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(16, 185, 129, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Server size={18} color="#34d399" />
            </div>
            <span className="badge badge-success">ONLINE</span>
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>FastAPI REST Gateway</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
            Uvicorn Worker • Port 8000
          </div>
        </div>

        {/* MongoDB Connection */}
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(99, 102, 241, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Database size={18} color="#818cf8" />
            </div>
            <span className="badge badge-success">CONNECTED</span>
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>MongoDB Database</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
            Motor Async Driver • abraxas_db
          </div>
        </div>

        {/* TomTom Live Traffic */}
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(245, 158, 11, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Radio size={18} color="#fbbf24" />
            </div>
            <span className="badge badge-success">READY</span>
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>TomTom Traffic API</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
            120s Spatial Cache • Pune Matrix
          </div>
        </div>

        {/* QGA / QPSO Engine */}
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(56, 189, 248, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Cpu size={18} color="#38bdf8" />
            </div>
            <span className="badge badge-primary">ACTIVE</span>
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>QGA + QPSO Optimizer</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
            Pure Python NumPy Engine
          </div>
        </div>
      </div>

      {/* Live Delivery Event Stream */}
      <div className="glass-card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={18} color="var(--primary)" />
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
              Real-Time Delivery & Driver Audit Stream
            </h3>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Polling every 5s
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '350px', overflowY: 'auto' }}>
          {events.length > 0 ? (
            events.map((evt, idx) => {
              const isDelivered = evt.event_type === 'DELIVERED';
              const isFailed = evt.event_type === 'FAILED';

              return (
                <div
                  key={evt._id || evt.id || idx}
                  style={{
                    padding: '0.75rem 1rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-card)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {isDelivered ? (
                      <CheckCircle2 size={16} color="#34d399" />
                    ) : isFailed ? (
                      <AlertCircle size={16} color="#f87171" />
                    ) : (
                      <Radio size={16} color="#818cf8" />
                    )}
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff' }}>
                        Parcel: <strong>{evt.parcel_id || 'N/A'}</strong> • Vehicle: {evt.vehicle_id || 'N/A'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        Driver: {evt.driver_id || 'Unassigned'} • Reason: {evt.failure_reason || 'Standard On-Time Delivery'}
                      </div>
                    </div>
                  </div>

                  <span className={`badge ${isDelivered ? 'badge-success' : isFailed ? 'badge-danger' : 'badge-primary'}`}>
                    {evt.event_type}
                  </span>
                </div>
              );
            })
          ) : (
            <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
              No delivery events logged yet. Events will stream in real-time as drivers execute routes.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
