import React, { useMemo, useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// The 3 Strategic Planned Warehouses in Pune
const STRATEGIC_WAREHOUSES = [
  {
    id: 'WH-PUNE-001',
    name: 'Central Logistics Hub - Shivajinagar',
    pt: [18.5308, 73.8475],
    region: 'Central Hub',
    address: 'FP 12, Shivajinagar Commercial Complex, Pune'
  },
  {
    id: 'WH-PUNE-002',
    name: 'East Logistics Hub - Viman Nagar / Kharadi',
    pt: [18.5529, 73.9242],
    region: 'East Hub',
    address: 'Plot 8, EON Tech Corridor, Kharadi-Viman Nagar, Pune'
  },
  {
    id: 'WH-PUNE-003',
    name: 'West Logistics Hub - Kothrud / Baner',
    pt: [18.5074, 73.8077],
    region: 'West Hub',
    address: 'Sector B, Paud Road, Kothrud-Baner Link, Pune'
  },
];

// Parse coords: handles [lat,lon], [lon,lat], {lat,lon}
function parseLatLng(coord) {
  if (!coord) return null;
  if (Array.isArray(coord)) {
    const a = parseFloat(coord[0]);
    const b = parseFloat(coord[1]);
    if (isNaN(a) || isNaN(b)) return null;
    // For Pune/India: lon ~73, lat ~18 — if first value > 40 it is longitude
    if (a > 40) return [b, a];
    return [a, b];
  }
  if (typeof coord === 'object') {
    if (coord.lat !== undefined && coord.lon !== undefined) return [parseFloat(coord.lat), parseFloat(coord.lon)];
    if (coord.latitude !== undefined && coord.longitude !== undefined) return [parseFloat(coord.latitude), parseFloat(coord.longitude)];
  }
  return null;
}

// Route color palette
const ROUTE_COLORS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
  '#8B5CF6', '#EC4899', '#06B6D4', '#F97316',
  '#84CC16', '#A855F7',
];

// Auto-fit bounds inside map
function FitBounds({ bounds, sessionKey }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length > 1) {
      const timer = setTimeout(() => {
        map.invalidateSize();
        try { map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 }); } catch (e) {}
      }, 80);
      return () => clearTimeout(timer);
    }
  }, [bounds, sessionKey, map]);
  return null;
}

// Warehouse divIcon with distinct glowing badge
const createWhIcon = (name) => L.divIcon({
  html: `<div style="
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(15, 23, 42, 0.95);
    border: 2px solid #6366F1;
    border-radius: 8px;
    padding: 3px 8px 3px 4px;
    box-shadow: 0 0 14px rgba(99,102,241,0.7), 0 4px 12px rgba(0,0,0,0.8);
    transform: translate(-50%, -50%);
    cursor: pointer;
    white-space: nowrap;
  ">
    <div style="
      width: 24px; height: 24px;
      background: linear-gradient(135deg,#6366F1,#4F46E5);
      border-radius: 6px;
      display: flex; align-items: center; justify-content: center;
      border: 1.5px solid #fff;
    ">
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
        fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
    </div>
    <span style="color: #fff; font-size: 11px; font-weight: 700; letter-spacing: 0.3px;">${name}</span>
  </div>`,
  className: '',
  iconSize: [0, 0],
});

// Delivery Stop divIcon with numbered indicator ("Deliver 1", "Deliver 2", ...)
const createDeliveryStopIcon = (seq, color) => L.divIcon({
  html: `<div style="
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(10, 11, 14, 0.94);
    border: 1.5px solid ${color};
    border-radius: 12px;
    padding: 2px 7px 2px 3px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.75), 0 0 10px ${color}88;
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
    transform: translate(-50%, -50%);
    transition: transform 0.15s ease;
  ">
    <div style="
      width: 17px;
      height: 17px;
      background: ${color};
      border-radius: 50%;
      color: #ffffff;
      font-size: 10px;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 1px 3px rgba(0,0,0,0.5);
    ">${seq}</div>
    <span style="color: #ffffff; font-size: 10.5px; font-weight: 600; letter-spacing: 0.2px;">Deliver ${seq}</span>
  </div>`,
  className: '',
  iconSize: [0, 0],
});

export default function ComparisonMap({ session }) {
  const [parcelLookup, setParcelLookup] = useState({});
  const [dbWarehouses, setDbWarehouses] = useState([]);

  // Fetch full parcel directory to map stop IDs to actual delivery locations
  useEffect(() => {
    async function loadData() {
      try {
        const [pRes, whRes] = await Promise.all([
          fetch('http://localhost:8000/parcels?limit=150'),
          fetch('http://localhost:8000/demo/warehouses'),
        ]);
        if (pRes.ok) {
          const pData = await pRes.json();
          const pList = pData.items || (Array.isArray(pData) ? pData : []);
          const map = {};
          pList.forEach(p => {
            const key = p.parcel_id || p.tracking_number || p.id;
            if (key) {
              map[key] = {
                lat: p.lat,
                lon: p.lon,
                address: p.address,
                recipient: p.recipient,
                weight_kg: p.weight_kg,
              };
            }
          });
          setParcelLookup(map);
        }
        if (whRes.ok) {
          const whData = await whRes.json();
          if (Array.isArray(whData) && whData.length > 0) {
            setDbWarehouses(whData);
          }
        }
      } catch (err) {
        console.warn('ComparisonMap: could not fetch parcel/warehouse catalog', err);
      }
    }
    loadData();
  }, []);

  // Merge default planned warehouses with DB warehouses
  const allWarehouses = useMemo(() => {
    const merged = new Map();
    STRATEGIC_WAREHOUSES.forEach(w => merged.set(w.id, w));
    dbWarehouses.forEach(w => {
      const id = w.warehouse_id || w.id;
      if (id && w.lat && w.lon) {
        merged.set(id, {
          id,
          name: w.name || id,
          pt: [w.lat, w.lon],
          region: w.region || 'Hub',
          address: w.address || '',
        });
      }
    });
    return Array.from(merged.values());
  }, [dbWarehouses]);

  const { lines, bounds, deliveryStops, sessionKey } = useMemo(() => {
    if (!session || !session.vehicle_assignments) {
      return { lines: [], bounds: [], deliveryStops: [], sessionKey: 'empty' };
    }

    const newLines = [];
    const newBounds = [];
    const newDeliveryStops = [];

    // Always include the 3 strategic warehouses in bounds
    allWarehouses.forEach(w => newBounds.push(w.pt));

    session.vehicle_assignments.forEach((assignment, idx) => {
      const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];
      const vehicleId = assignment.vehicle_id || `Vehicle ${idx + 1}`;

      // Polyline from OSRM geometry
      if (assignment.route_geometry && assignment.route_geometry.length > 1) {
        const latLngs = assignment.route_geometry.map(parseLatLng).filter(Boolean);
        if (latLngs.length > 1) {
          newLines.push({ id: assignment.vehicle_id || idx, latLngs, color, vehicleId });
          latLngs.forEach(ll => newBounds.push(ll));

          // Delivery stops for this vehicle
          const stopsList = assignment.stops || (assignment.stop_arrivals ? assignment.stop_arrivals.map(s => s.stop_id) : []);
          const arrivalsMap = {};
          if (assignment.stop_arrivals) {
            assignment.stop_arrivals.forEach(a => {
              arrivalsMap[a.stop_id] = a;
            });
          }

          stopsList.forEach((stopId, sIdx) => {
            const seq = sIdx + 1; // 1-based delivery index for this vehicle
            const arr = arrivalsMap[stopId] || {};
            const pInfo = parcelLookup[stopId] || {};

            // Determine stop coordinate: 1) arr coordinates, 2) parcelLookup, 3) geometry interpolation
            let pt = null;
            if (arr.lat && arr.lon) {
              pt = [arr.lat, arr.lon];
            } else if (pInfo.lat && pInfo.lon) {
              pt = [pInfo.lat, pInfo.lon];
            } else if (latLngs.length > 2) {
              const inner = latLngs.slice(1, latLngs.length - 1);
              pt = inner[sIdx % inner.length];
            }

            if (pt) {
              const arrivalMin = arr.arrival_time_min;
              const etaFormatted = arrivalMin
                ? `${String(Math.floor(arrivalMin / 60)).padStart(2, '0')}:${String(Math.floor(arrivalMin % 60)).padStart(2, '0')}`
                : null;

              newDeliveryStops.push({
                seq,
                stopId,
                pt,
                color,
                vehicleId,
                etaFormatted,
                address: pInfo.address || arr.address || 'Pune Destination',
                recipient: pInfo.recipient,
              });
              newBounds.push(pt);
            }
          });
        }
      }
    });

    // Unique key per session so MapContainer fully remounts
    const key = session.id || session.session_id
      || `${session.preset || ''}${session.vehicle_assignments.length}`;

    return {
      lines: newLines,
      bounds: newBounds,
      deliveryStops: newDeliveryStops,
      sessionKey: key,
    };
  }, [session, parcelLookup, allWarehouses]);

  const mapCenter = bounds.length > 0
    ? bounds[Math.floor(bounds.length / 2)]
    : [18.5204, 73.8567];

  // CARTO basemap URL with API key to eliminate watermark
  const cartoApiKey = import.meta.env.VITE_CARTO_API_KEY || 'cb1_30dp_1_cc75fba3ffbcd1d1e9225d5e';
  const tileUrl = cartoApiKey
    ? `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png?key=${cartoApiKey}`
    : `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png`;

  return (
    <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: '#0a0a0a' }}>
      {/* key={sessionKey} forces full Leaflet remount when preset changes */}
      <MapContainer
        key={sessionKey}
        center={mapCenter}
        zoom={12}
        style={{ height: '100%', width: '100%', background: '#0a0a0a' }}
        zoomControl={true}
        attributionControl={false}
      >
        <TileLayer url={tileUrl} subdomains="abcd" maxZoom={19} />

        {bounds.length > 1 && <FitBounds bounds={bounds} sessionKey={sessionKey} />}

        {/* Vehicle route polylines */}
        {lines.map((line, idx) => (
          <Polyline
            key={`line-${line.id}-${idx}`}
            positions={line.latLngs}
            color={line.color}
            weight={3.5}
            opacity={0.88}
          >
            <Tooltip sticky>{line.vehicleId || `Vehicle ${idx + 1}`}</Tooltip>
          </Polyline>
        ))}

        {/* Delivery stop indicators ("Deliver 1", "Deliver 2", ...) */}
        {deliveryStops.map((stop, idx) => (
          <Marker
            key={`stop-${stop.vehicleId}-${stop.stopId}-${idx}`}
            position={stop.pt}
            icon={createDeliveryStopIcon(stop.seq, stop.color)}
            zIndexOffset={500}
          >
            <Tooltip direction="top" offset={[0, -14]}>
              <div style={{ lineHeight: 1.4, fontSize: '0.78rem' }}>
                <div style={{ fontWeight: 700, color: stop.color, marginBottom: '2px' }}>
                  📍 Deliver #{stop.seq} • {stop.stopId}
                </div>
                <div style={{ color: '#e2e8f0' }}><strong>Vehicle:</strong> {stop.vehicleId}</div>
                {stop.etaFormatted && (
                  <div style={{ color: '#94a3b8' }}><strong>ETA:</strong> {stop.etaFormatted}</div>
                )}
                {stop.address && (
                  <div style={{ color: '#94a3b8', maxWidth: '200px', whiteSpace: 'normal', marginTop: '2px' }}>
                    {stop.address}
                  </div>
                )}
              </div>
            </Tooltip>
          </Marker>
        ))}

        {/* All 3 Planned Strategic Warehouses */}
        {allWarehouses.map((wh) => (
          <Marker
            key={`wh-${wh.id}`}
            position={wh.pt}
            icon={createWhIcon(wh.region || wh.id)}
            zIndexOffset={1000}
          >
            <Tooltip direction="top" offset={[0, -20]}>
              <div style={{ lineHeight: 1.4, fontSize: '0.78rem' }}>
                <div style={{ fontWeight: 700, color: '#818CF8', marginBottom: '2px' }}>
                  🏭 {wh.name}
                </div>
                <div style={{ color: '#94a3b8' }}><strong>Code:</strong> {wh.id}</div>
                {wh.address && (
                  <div style={{ color: '#94a3b8', maxWidth: '220px', whiteSpace: 'normal', marginTop: '2px' }}>
                    {wh.address}
                  </div>
                )}
              </div>
            </Tooltip>
          </Marker>
        ))}
      </MapContainer>

      {/* In-map Legend */}
      <div style={{
        position: 'absolute', bottom: '12px', left: '12px', zIndex: 1000,
        backgroundColor: 'rgba(10,11,14,0.92)', backdropFilter: 'blur(8px)',
        border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px',
        padding: '10px 14px', fontSize: '0.72rem',
        color: 'rgba(255,255,255,0.85)',
        display: 'flex', flexDirection: 'column', gap: '6px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
        pointerEvents: 'none',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '18px', height: '18px',
            background: 'linear-gradient(135deg,#6366F1,#4F46E5)',
            borderRadius: '5px', border: '1.5px solid #fff', flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{ fontSize: '10px' }}>🏭</span>
          </div>
          <span><strong>3 Planned Hubs</strong> (Central, East, West)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            padding: '1px 5px', borderRadius: '10px',
            background: '#1E293B', border: '1px solid #3B82F6',
            color: '#fff', fontSize: '9.5px', fontWeight: 700, flexShrink: 0,
          }}>
            Deliver 1, 2...
          </div>
          <span>Delivery Stops (Sequence indicator)</span>
        </div>
        <div style={{ height: '1px', background: 'rgba(255,255,255,0.1)', margin: '2px 0' }} />
        {lines.slice(0, 5).map((line, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '18px', height: '3.5px',
              background: line.color, borderRadius: '2px', flexShrink: 0,
            }} />
            <span style={{ opacity: 0.85 }}>{line.vehicleId || `Vehicle ${i + 1}`}</span>
          </div>
        ))}
        {lines.length > 5 && <div style={{ opacity: 0.5, fontSize: '0.68rem' }}>+{lines.length - 5} more vehicles</div>}
      </div>
    </div>
  );
}
