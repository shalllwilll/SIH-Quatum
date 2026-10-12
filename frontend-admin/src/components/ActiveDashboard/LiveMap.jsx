import React, { useEffect, useMemo, useRef } from 'react';
import {
  MapContainer, TileLayer, Marker, Polyline, Tooltip, useMap, Circle
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default Leaflet icon paths in Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// ── Strategic Warehouses ───────────────────────────────────────────────────
const STRATEGIC_WAREHOUSES = [
  { warehouse_id: 'WH-PUNE-001', name: 'Central Logistics Hub - Shivajinagar', lat: 18.5308, lon: 73.8475, region: 'Central Hub', address: 'FP 12, Shivajinagar Commercial Complex, Pune' },
  { warehouse_id: 'WH-PUNE-002', name: 'East Logistics Hub - Viman Nagar / Kharadi', lat: 18.5529, lon: 73.9242, region: 'East Hub', address: 'Plot 8, EON Tech Corridor, Kharadi-Viman Nagar, Pune' },
  { warehouse_id: 'WH-PUNE-003', name: 'West Logistics Hub - Kothrud / Baner', lat: 18.5074, lon: 73.8077, region: 'West Hub', address: 'Sector B, Paud Road, Kothrud-Baner Link, Pune' },
];

// ── Color palette ─────────────────────────────────────────────────────────
const ROUTE_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#3b82f6', '#84cc16'];

// ── Warehouse icon ─────────────────────────────────────────────────────────
const createWarehouseIcon = (label) => L.divIcon({
  html: `<div style="
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(15,23,42,0.96); border:2px solid #6366F1;
    border-radius:8px; padding:3px 8px 3px 4px;
    box-shadow:0 0 14px rgba(99,102,241,0.7),0 4px 12px rgba(0,0,0,0.8);
    transform:translate(-50%,-50%); cursor:pointer; white-space:nowrap;">
    <div style="width:24px;height:24px;background:linear-gradient(135deg,#6366F1,#4F46E5);border-radius:6px;
      display:flex;align-items:center;justify-content:center;border:1.5px solid #fff;">
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
        fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
    </div>
    <span style="color:#fff;font-size:11px;font-weight:700;letter-spacing:0.3px;">${label}</span>
  </div>`,
  className: '',
  iconSize: [0, 0],
});

// ── Delivery stop icon ─────────────────────────────────────────────────────
const createDeliveryStopIcon = (seq, color) => L.divIcon({
  html: `<div style="
    display:inline-flex; align-items:center; gap:4px;
    background:rgba(10,11,14,0.94); border:1.5px solid ${color};
    border-radius:12px; padding:2px 7px 2px 3px;
    box-shadow:0 2px 8px rgba(0,0,0,0.75); cursor:pointer;
    white-space:nowrap; transform:translate(-50%,-50%);">
    <div style="width:16px;height:16px;background:${color};border-radius:50%;color:#fff;
      font-size:10px;font-weight:800;display:flex;align-items:center;justify-content:center;">${seq}</div>
    <span style="color:#fff;font-size:10px;font-weight:600;">Deliver ${seq}</span>
  </div>`,
  className: '',
  iconSize: [0, 0],
});

// ── Animated vehicle truck icon ────────────────────────────────────────────
const createVehicleIcon = (color, status, heading = 0, vehicleLabel = '') => {
  const isDelivering = status === 'delivering';
  const isComplete = status === 'complete' || status === 'idle';
  const opacity = isComplete ? 0.55 : 1;

  // Delivery pulse ring for delivering state
  const pulseRing = isDelivering
    ? `<div style="position:absolute;inset:-6px;border-radius:50%;border:2px solid ${color};opacity:0.5;animation:pingAnim 1.2s ease-in-out infinite;"></div>`
    : '';

  // Speed indicator dot
  const speedDot = status === 'en_route'
    ? `<div style="position:absolute;bottom:-3px;right:-3px;width:8px;height:8px;background:#10B981;border-radius:50%;border:1.5px solid #0a0b0e;"></div>`
    : '';

  return L.divIcon({
    html: `
    <div style="position:relative;opacity:${opacity};transform:rotate(${heading}deg);">
      ${pulseRing}
      <div style="
        width:36px;height:36px;background:${color};border-radius:50%;
        display:flex;align-items:center;justify-content:center;
        border:2.5px solid #fff;
        box-shadow:0 0 0 2px ${color}66,0 4px 12px ${color}88;
        position:relative;
      ">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
          fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="1" y="3" width="15" height="13"/>
          <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
          <circle cx="5.5" cy="18.5" r="2.5"/>
          <circle cx="18.5" cy="18.5" r="2.5"/>
        </svg>
        ${speedDot}
      </div>
      ${vehicleLabel ? `<div style="
        position:absolute;top:-20px;left:50%;transform:translateX(-50%);
        background:rgba(15,23,42,0.9);border:1px solid ${color};
        border-radius:4px;padding:1px 5px;
        color:#fff;font-size:9px;font-weight:700;white-space:nowrap;
      ">${vehicleLabel}</div>` : ''}
    </div>`,
    className: '',
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    tooltipAnchor: [0, -22],
  });
};

// ── Map auto-bounds component ─────────────────────────────────────────────
function MapBounds({ bounds, hasAnimation }) {
  const map = useMap();
  const didFitRef = useRef(false);

  useEffect(() => {
    // Only auto-fit once on initial data load, not on every vehicle update
    if (bounds && bounds.length > 0 && !hasAnimation && !didFitRef.current) {
      map.fitBounds(bounds, { padding: [50, 50] });
      didFitRef.current = true;
    }
  }, [map, bounds, hasAnimation]);

  return null;
}

// ── Trail dots for recent path ─────────────────────────────────────────────
// Not needed for now — keep map clean

// ── Main LiveMap component ─────────────────────────────────────────────────
export default function LiveMap({
  warehouses = [],
  simVehicles = [],      // live vehicle states from WS telemetry
  parcels = [],
  session = null,        // the assigned session (for route_geometry fallback)
  simStatus = 'idle',
}) {
  const defaultCenter = [18.5204, 73.8567];

  // Always show all 3 strategic warehouses
  const displayWarehouses = useMemo(() => {
    const map = new Map();
    STRATEGIC_WAREHOUSES.forEach(w => map.set(w.warehouse_id, w));
    warehouses.forEach(w => {
      const id = w.warehouse_id || w.id;
      if (id && w.lat && w.lon) map.set(id, { ...w, warehouse_id: id });
    });
    return Array.from(map.values());
  }, [warehouses]);

  // Build routes to draw:
  // Priority: from live simVehicles (which have route_geometry), then from session assignments
  const routes = useMemo(() => {
    // If we have live vehicle data with route_geometry, use that
    if (simVehicles.length > 0) {
      return simVehicles
        .filter(v => v.route_geometry && v.route_geometry.length > 1)
        .map((v, idx) => {
          const positions = v.route_geometry.map(pt => {
            if (Array.isArray(pt)) return (pt[0] > 40 && pt[1] < 40) ? [pt[1], pt[0]] : [pt[0], pt[1]];
            if (pt && typeof pt === 'object') return [pt.lat ?? pt.latitude, pt.lon ?? pt.longitude];
            return null;
          }).filter(Boolean);
          return {
            vehicleId: v.vehicle_id,
            color: v.color || ROUTE_COLORS[idx % ROUTE_COLORS.length],
            positions,
            status: v.status,
          };
        });
    }

    // Fallback: use session assignments for static preview when sim not started yet
    if (session?.vehicle_assignments) {
      return session.vehicle_assignments
        .filter(a => a.route_geometry?.length > 1)
        .map((a, idx) => ({
          vehicleId: a.vehicle_id,
          color: ROUTE_COLORS[idx % ROUTE_COLORS.length],
          positions: a.route_geometry.map(pt => {
            if (Array.isArray(pt)) return (pt[0] > 40 && pt[1] < 40) ? [pt[1], pt[0]] : [pt[0], pt[1]];
            if (pt && typeof pt === 'object') return [pt.lat ?? pt.latitude, pt.lon ?? pt.longitude];
            return null;
          }).filter(Boolean),
          status: 'idle',
        }));
    }

    return [];
  }, [simVehicles, session]);

  // Delivery stop markers
  const deliveryStops = useMemo(() => {
    const stops = [];

    // Prefer stop_arrivals from live vehicles (has lat/lon baked in)
    if (simVehicles.length > 0) {
      simVehicles.forEach((v, vIdx) => {
        const color = v.color || ROUTE_COLORS[vIdx % ROUTE_COLORS.length];
        (v.stop_arrivals || []).forEach((stop, sIdx) => {
          const lat = stop.lat || stop.latitude;
          const lon = stop.lon || stop.longitude;
          if (lat && lon) {
            stops.push({
              key: `${v.vehicle_id}-${sIdx}`,
              lat, lon,
              seq: sIdx + 1,
              color,
              label: stop.address || stop.stop_id || `Stop ${sIdx + 1}`,
              vehicleId: v.vehicle_id,
              delivered: v.current_stop_index > sIdx,
            });
          }
        });
      });
    } else if (parcels.length > 0) {
      // Fallback to parcels list
      parcels.slice(0, 30).forEach((p, idx) => {
        if (!p.lat || !p.lon) return;
        let color = '#3B82F6';
        if (p.status === 'completed') color = '#10B981';
        else if (p.status === 'failed') color = '#EF4444';
        stops.push({
          key: `p-${p.parcel_id || idx}`,
          lat: p.lat, lon: p.lon,
          seq: idx + 1,
          color,
          label: p.address || p.parcel_id,
          delivered: p.status === 'completed',
        });
      });
    }

    return stops;
  }, [simVehicles, parcels]);

  // Initial map bounds (only for first load)
  const initialBounds = useMemo(() => {
    const pts = displayWarehouses.map(w => [w.lat, w.lon]);
    parcels.slice(0, 10).forEach(p => { if (p.lat && p.lon) pts.push([p.lat, p.lon]); });
    return pts;
  }, [displayWarehouses, parcels]);

  const cartoApiKey = import.meta.env.VITE_CARTO_API_KEY || 'cb1_30dp_1_cc75fba3ffbcd1d1e9225d5e';
  const tileUrl = `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png?key=${cartoApiKey}`;

  const hasSimulation = simVehicles.length > 0;

  return (
    <div className="map-container" style={{
      flex: 1, height: '100%', minHeight: '400px', background: '#0a0b0e', position: 'relative', borderRadius: '12px', overflow: 'hidden',
    }}>
      {/* Ping animation keyframes injected inline */}
      <style>{`
        @keyframes pingAnim {
          0% { transform: scale(1); opacity: 0.5; }
          70% { transform: scale(2.2); opacity: 0; }
          100% { transform: scale(2.2); opacity: 0; }
        }
      `}</style>

      {/* Idle overlay */}
      {simStatus === 'idle' && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 500,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          background: 'rgba(10, 11, 14, 0.65)', backdropFilter: 'blur(4px)',
          pointerEvents: 'none',
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🚚</div>
          <div style={{ color: '#94a3b8', fontSize: '0.9rem', fontWeight: 500, textAlign: 'center', maxWidth: '260px' }}>
            <strong style={{ color: '#c7d2fe' }}>No Active Simulation</strong><br/>
            <span style={{ fontSize: '0.8rem' }}>Assign routes from the Comparison Panel to start live vehicle tracking</span>
          </div>
        </div>
      )}

      <MapContainer center={defaultCenter} zoom={12} style={{ height: '100%', width: '100%', background: '#0a0b0e' }}>
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">Carto</a>'
          url={tileUrl}
          subdomains="abcd"
        />

        {!hasSimulation && initialBounds.length > 0 && (
          <MapBounds bounds={initialBounds} hasAnimation={false} />
        )}

        {/* ── Route Polylines ──────────────────────────────────────────── */}
        {routes.map((route, idx) => (
          <Polyline
            key={`route-${idx}`}
            positions={route.positions}
            pathOptions={{
              color: route.color,
              weight: route.status === 'complete' ? 2 : 3.5,
              opacity: route.status === 'complete' ? 0.35 : 0.75,
              dashArray: route.status === 'idle' ? '8 6' : undefined,
            }}
          />
        ))}

        {/* ── Delivery Stop Markers ────────────────────────────────────── */}
        {deliveryStops.map((stop) => (
          <Marker
            key={stop.key}
            position={[stop.lat, stop.lon]}
            icon={createDeliveryStopIcon(stop.seq, stop.delivered ? '#10B981' : stop.color)}
            zIndexOffset={400}
          >
            <Tooltip direction="top" offset={[0, -14]}>
              <div style={{ lineHeight: 1.4, fontSize: '0.78rem' }}>
                <div style={{ fontWeight: 700, color: stop.color, marginBottom: '2px' }}>
                  📍 Deliver #{stop.seq}
                  {stop.delivered && <span style={{ color: '#10B981', marginLeft: 4 }}>✓ Done</span>}
                </div>
                <div style={{ color: '#94a3b8', maxWidth: '180px', whiteSpace: 'normal' }}>{stop.label}</div>
                {stop.vehicleId && <div><strong>Vehicle:</strong> {stop.vehicleId}</div>}
              </div>
            </Tooltip>
          </Marker>
        ))}

        {/* ── Warehouse Markers ─────────────────────────────────────────── */}
        {displayWarehouses.map((wh) => (
          <Marker
            key={`wh-${wh.warehouse_id}`}
            position={[wh.lat, wh.lon]}
            icon={createWarehouseIcon(wh.region || wh.name)}
            zIndexOffset={800}
          >
            <Tooltip direction="top" offset={[0, -20]}>
              <div style={{ lineHeight: 1.4, fontSize: '0.78rem' }}>
                <div style={{ fontWeight: 700, color: '#818CF8', marginBottom: '2px' }}>
                  🏭 {wh.name}
                </div>
                <div style={{ color: '#94a3b8' }}>{wh.address || wh.warehouse_id}</div>
              </div>
            </Tooltip>
          </Marker>
        ))}

        {/* ── Live Animated Vehicle Markers ────────────────────────────── */}
        {simVehicles.map((v, idx) => {
          const lat = v.location?.lat;
          const lon = v.location?.lon;
          if (!lat || !lon) return null;

          const color = v.color || ROUTE_COLORS[idx % ROUTE_COLORS.length];
          const heading = v.heading_deg || 0;

          return (
            <Marker
              key={`v-${v.vehicle_id}`}
              position={[lat, lon]}
              icon={createVehicleIcon(color, v.status, heading, v.vehicle_id)}
              zIndexOffset={1000}
            >
              <Tooltip direction="top" offset={[0, -22]} permanent={false}>
                <div style={{ lineHeight: 1.5, fontSize: '0.78rem', minWidth: '150px' }}>
                  <div style={{ fontWeight: 700, color, marginBottom: '3px' }}>
                    🚚 {v.vehicle_id}
                  </div>
                  <div>
                    <strong>Status:</strong>{' '}
                    <span style={{
                      color: v.status === 'en_route' ? '#10B981'
                        : v.status === 'delivering' ? '#F59E0B'
                        : v.status === 'complete' ? '#6366F1'
                        : '#94a3b8'
                    }}>
                      {v.status?.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  {v.speed_kmh > 0 && <div><strong>Speed:</strong> {v.speed_kmh} km/h</div>}
                  {v.total_stops > 0 && (
                    <div><strong>Stops:</strong> {v.current_stop_index} / {v.total_stops}</div>
                  )}
                  {heading > 0 && <div><strong>Heading:</strong> {Math.round(heading)}°</div>}
                </div>
              </Tooltip>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Live Legend Overlay */}
      {simStatus === 'running' && simVehicles.length > 0 && (
        <div style={{
          position: 'absolute', bottom: '1rem', left: '1rem', zIndex: 500,
          background: 'rgba(10, 11, 14, 0.92)', border: '1px solid rgba(99,102,241,0.3)',
          borderRadius: '10px', padding: '0.65rem 0.9rem',
          display: 'flex', flexDirection: 'column', gap: '0.4rem',
          backdropFilter: 'blur(8px)',
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
          maxWidth: '200px',
        }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, letterSpacing: '0.05em', marginBottom: '0.2rem' }}>
            VEHICLE STATUS
          </div>
          {simVehicles.map((v, idx) => {
            const color = v.color || ROUTE_COLORS[idx % ROUTE_COLORS.length];
            return (
              <div key={v.vehicle_id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
                <span style={{ fontSize: '0.72rem', color: '#cbd5e1', flex: 1 }}>{v.vehicle_id}</span>
                <span style={{
                  fontSize: '0.65rem',
                  color: v.status === 'en_route' ? '#10B981'
                    : v.status === 'delivering' ? '#F59E0B'
                    : v.status === 'complete' ? '#818CF8'
                    : '#64748b',
                  fontWeight: 600,
                }}>
                  {v.status === 'en_route' ? '▶ Moving'
                    : v.status === 'delivering' ? '📦 Stop'
                    : v.status === 'complete' ? '✓ Done'
                    : '◼ Idle'}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
