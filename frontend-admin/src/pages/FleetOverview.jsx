import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import { api } from '../api/client';
import {
  Truck,
  Building,
  Navigation,
  RefreshCw,
  AlertTriangle,
  Clock,
} from 'lucide-react';

const POSITION_POLL_MS = 3000;
const PUNE_CENTER = [18.5204, 73.8567];

export default function FleetOverview() {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef({ warehouses: {}, vehicles: {} });

  const [warehouses, setWarehouses] = useState([]);
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pollError, setPollError] = useState(null);
  const [isWebSocketActive, setIsWebSocketActive] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Initialize Leaflet Map with Canvas Acceleration
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: PUNE_CENTER,
      zoom: 12,
      zoomControl: true,
      preferCanvas: true, // Hardware-accelerated 60 FPS Canvas rendering
    });

    // Dark-mode basemap: use CARTO if key is configured, otherwise high-contrast ESRI Dark Canvas (no watermark / no key needed)
    const cartoKey = import.meta.env.VITE_CARTO_API_KEY;
    const tileUrl = cartoKey
      ? `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=${cartoKey}`
      : 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
    const attribution = cartoKey
      ? '&copy; <a href="https://carto.com/">CARTO</a> | &copy; OpenStreetMap'
      : '&copy; Esri &mdash; Esri, DeLorme, NAVTEQ';

    L.tileLayer(tileUrl, {
      attribution,
      subdomains: cartoKey ? 'abcd' : '',
      maxZoom: 18,
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Fetch static warehouses once
  useEffect(() => {
    api.getWarehouses()
      .then((data) => {
        setWarehouses(data || []);
      })
      .catch((err) => {
        console.warn('Could not load warehouses:', err);
      });
  }, []);

  // Render Warehouse Markers on Map
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !warehouses.length) return;

    Object.values(markersRef.current.warehouses).forEach((m) => m.remove());
    markersRef.current.warehouses = {};

    warehouses.forEach((wh) => {
      const whIcon = L.divIcon({
        className: 'custom-warehouse-icon',
        html: `
          <div style="
            background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%);
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.6);
            border: 2px solid #ffffff;
          ">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
              <path d="M3 21h18M3 7l9-4 9 4v14H3V7z"/>
            </svg>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const marker = L.marker([wh.lat, wh.lon], { icon: whIcon }).addTo(map);
      marker.bindPopup(`
        <div style="padding: 4px;">
          <h4 style="font-weight: 700; color: #818cf8; margin-bottom: 4px;">${wh.name}</h4>
          <p style="font-size: 12px; color: #cbd5e1; margin-bottom: 2px;">${wh.address}</p>
          <span style="font-size: 10px; color: #94a3b8;">Distribution Hub</span>
        </div>
      `);
      markersRef.current.warehouses[wh.id || wh.name] = marker;
    });
  }, [warehouses]);

  // Real-Time Telemetry: WebSocket Connection with Polling Fallback
  useEffect(() => {
    let isMounted = true;
    let ws = null;
    let pollInterval = null;

    const fetchPositions = async () => {
      try {
        const data = await api.getVehiclePositions();
        if (!isMounted) return;
        setPositions(data || []);
        setLastUpdated(new Date());
        setPollError(null);
        setLoading(false);
      } catch (err) {
        if (!isMounted) return;
        setPollError('Live position sync temporarily unavailable.');
        setLoading(false);
      }
    };

    fetchPositions();

    const wsUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')
      .replace(/^http/, 'ws') + '/ws/fleet';

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (isMounted) setIsWebSocketActive(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (Array.isArray(payload)) {
            if (isMounted) {
              setPositions(payload);
              setLastUpdated(new Date());
              setPollError(null);
              setLoading(false);
            }
          }
        } catch {
          // ignore non-json
        }
      };

      ws.onerror = () => {
        if (isMounted) setIsWebSocketActive(false);
      };

      ws.onclose = () => {
        if (isMounted) {
          setIsWebSocketActive(false);
          if (!pollInterval) {
            pollInterval = setInterval(fetchPositions, POSITION_POLL_MS);
          }
        }
      };
    } catch {
      setIsWebSocketActive(false);
      pollInterval = setInterval(fetchPositions, POSITION_POLL_MS);
    }

    pollInterval = setInterval(fetchPositions, isWebSocketActive ? 10000 : POSITION_POLL_MS);

    return () => {
      isMounted = false;
      if (ws) ws.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, []);

  // Update Vehicle Markers on Map
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    positions.forEach((veh) => {
      const isEnRoute = veh.status === 'en_route' || veh.status === 'delivering';
      const color = isEnRoute ? '#10b981' : '#64748b';
      const glow = isEnRoute ? 'rgba(16, 185, 129, 0.7)' : 'rgba(100, 116, 139, 0.3)';

      const vehIcon = L.divIcon({
        className: 'custom-vehicle-icon',
        html: `
          <div style="
            background: ${color};
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 14px ${glow};
            border: 2px solid #ffffff;
            transition: all 0.5s ease;
          ">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5">
              <path d="M1 3h15v13H1zM16 8h4l3 3v5h-7V8zM5.5 18a2.5 2.5 0 100-5 2.5 2.5 0 000 5zM18.5 18a2.5 2.5 0 100-5 2.5 2.5 0 000 5z"/>
            </svg>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const vKey = veh.vehicle_id || veh.label;
      if (markersRef.current.vehicles[vKey]) {
        markersRef.current.vehicles[vKey].setLatLng([veh.lat, veh.lon]);
        markersRef.current.vehicles[vKey].setIcon(vehIcon);
      } else {
        const marker = L.marker([veh.lat, veh.lon], { icon: vehIcon }).addTo(map);
        marker.bindPopup(`
          <div style="padding: 4px;">
            <h4 style="font-weight: 700; color: #fff;">${veh.label}</h4>
            <div style="font-size: 12px; margin: 4px 0; color: #cbd5e1;">
              Status: <strong style="color: ${color}; text-transform: uppercase;">${veh.status}</strong>
            </div>
            <div style="font-size: 11px; color: #94a3b8;">
              Driver: ${veh.driver_id || 'Unassigned'} • Speed: ${veh.speed_kmh} km/h
            </div>
          </div>
        `);
        markersRef.current.vehicles[vKey] = marker;
      }
    });
  }, [positions]);

  // Statistics
  const totalVehicles = positions.length;
  const enRouteCount = positions.filter((v) => v.status === 'en_route' || v.status === 'delivering').length;
  const idleCount = totalVehicles - enRouteCount;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '1rem' }}>
      {/* Top Notification / Polling State */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className={`badge ${isWebSocketActive ? 'badge-success' : 'badge-info'}`}>
            {isWebSocketActive ? '⚡ Live WebSocket Push' : '🔄 Polling Mode'}
          </span>
          {lastUpdated && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Clock size={13} /> Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>

        {pollError && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'rgba(245, 158, 11, 0.15)',
            color: '#fbbf24',
            padding: '0.4rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.8rem',
            border: '1px solid rgba(245, 158, 11, 0.3)',
          }}>
            <AlertTriangle size={14} />
            <span>{pollError} (Serving Stale Cache)</span>
          </div>
        )}
      </div>

      {/* Main Grid: Map + Side Stat Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '1rem', flex: 1, minHeight: '520px' }}>
        {/* Leaflet Map Canvas */}
        <div className="glass-card" style={{ padding: '0.5rem', position: 'relative', overflow: 'hidden' }}>
          <div ref={mapContainerRef} style={{ width: '100%', height: '100%', borderRadius: 'var(--radius-md)' }} />
          {loading && (
            <div style={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(9, 13, 22, 0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              color: 'var(--text-muted)',
              zIndex: 1000,
            }}>
              <RefreshCw className="animate-spin" size={20} />
              <span>Initializing Live Map...</span>
            </div>
          )}
        </div>

        {/* Right Info & Metric Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Summary Metric Card */}
          <div className="glass-card" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Fleet Status
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Total Fleet</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>{totalVehicles}</div>
              </div>
              <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                <div style={{ fontSize: '0.75rem', color: '#34d399' }}>Active / En Route</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#34d399' }}>{enRouteCount}</div>
              </div>
            </div>

            <div style={{ marginTop: '0.75rem', background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Idle Staged</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-muted)' }}>{idleCount}</div>
            </div>
          </div>

          {/* Active Vehicles List */}
          <div className="glass-card" style={{ padding: '1.25rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Live Telemetry
            </h3>

            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {positions.map((veh) => {
                const isEnRoute = veh.status === 'en_route' || veh.status === 'delivering';
                return (
                  <div
                    key={veh.vehicle_id || veh.label}
                    style={{
                      padding: '0.65rem 0.75rem',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-card)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>{veh.label}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{veh.driver_id || 'No Driver'}</div>
                    </div>
                    <span className={`badge ${isEnRoute ? 'badge-success' : 'badge-primary'}`} style={{ fontSize: '0.65rem' }}>
                      {veh.status}
                    </span>
                  </div>
                );
              })}

              {!positions.length && !loading && (
                <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '2rem 0', fontSize: '0.85rem' }}>
                  No vehicles currently reporting telemetry.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
