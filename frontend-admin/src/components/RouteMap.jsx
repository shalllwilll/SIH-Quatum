import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

const PUNE_CENTER = [18.5204, 73.8567];

const ROUTE_PALETTE = [
  '#6366f1', // Indigo
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#ec4899', // Pink
  '#06b6d4', // Cyan
  '#8b5cf6', // Violet
  '#14b8a6', // Teal
  '#f97316', // Orange
];

export default function RouteMap({
  warehouses = [],
  assignments = [],
  stopsLookup = {},
  selectedVehicleId = null,
  onSelectVehicle = null,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layersRef = useRef({ polylines: [], markers: [] });

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: PUNE_CENTER,
      zoom: 12,
      zoomControl: true,
      preferCanvas: true, // Hardware-accelerated Canvas polyline rendering
    });

    // Dark-mode basemap: use CARTO if key is configured, otherwise high-contrast ESRI Dark Canvas (no watermark / no key needed)
    const cartoKey = import.meta.env.VITE_CARTO_API_KEY;
    const tileUrl = cartoKey
      ? `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?api_key=${cartoKey}`
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

  // Update Layers (Warehouses, Stops, Polylines)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear existing polylines and markers
    layersRef.current.polylines.forEach((p) => p.remove());
    layersRef.current.markers.forEach((m) => m.remove());
    layersRef.current.polylines = [];
    layersRef.current.markers = [];

    const bounds = L.latLngBounds([]);

    // 1. Warehouses
    warehouses.forEach((wh) => {
      const whLatLng = [wh.lat || 18.5204, wh.lon || 73.8567];
      bounds.extend(whLatLng);

      const whIcon = L.divIcon({
        className: 'custom-wh-map-icon',
        html: `
          <div style="
            background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%);
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.6);
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

      const whMarker = L.marker(whLatLng, { icon: whIcon }).addTo(map);
      whMarker.bindPopup(`
        <div style="padding: 4px;">
          <h4 style="font-weight: 700; color: #818cf8; margin-bottom: 2px;">${wh.name || 'Central Hub'}</h4>
          <p style="font-size: 11px; color: #cbd5e1;">${wh.address || 'Pune Dispatch Center'}</p>
        </div>
      `);
      layersRef.current.markers.push(whMarker);
    });

    // 2. Vehicle Routes & Stops
    assignments.forEach((assignment, vIdx) => {
      const color = ROUTE_PALETTE[vIdx % ROUTE_PALETTE.length];
      const isSelected = selectedVehicleId ? assignment.vehicle_id === selectedVehicleId : true;
      const isFallback = assignment.fallback_applied || !assignment.feasible;
      const routeColor = isFallback ? '#ef4444' : color;

      const whLatLng = warehouses.length > 0
        ? [warehouses[0].lat || 18.5204, warehouses[0].lon || 73.8567]
        : PUNE_CENTER;

      const pathCoords = [whLatLng];

      // Build sequence of stop coordinates
      const stops = assignment.stop_arrivals || assignment.stops || [];
      stops.forEach((stopItem, sIdx) => {
        const stopId = typeof stopItem === 'string' ? stopItem : stopItem.stop_id;
        const arrivalMin = typeof stopItem === 'object' ? stopItem.arrival_time_min : null;

        // Lookup stop lat/lon
        const stopData = stopsLookup[stopId];
        let lat = stopData?.lat;
        let lon = stopData?.lon;

        // Fallback coordinate offset if not in direct lookup
        if (!lat || !lon) {
          const hashVal = stopId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
          lat = 18.5204 + (((hashVal * 7) % 50) - 25) * 0.003;
          lon = 73.8567 + (((hashVal * 11) % 50) - 25) * 0.003;
        }

        const stopLatLng = [lat, lon];
        pathCoords.push(stopLatLng);
        bounds.extend(stopLatLng);

        // Marker for Stop
        const stopIcon = L.divIcon({
          className: 'custom-stop-map-icon',
          html: `
            <div style="
              background: ${routeColor};
              width: 22px;
              height: 22px;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              color: #ffffff;
              font-weight: 800;
              font-size: 10px;
              box-shadow: 0 2px 8px ${routeColor}88;
              border: 2px solid #ffffff;
              opacity: ${isSelected ? 1 : 0.4};
              transition: all 0.2s ease;
            ">
              ${sIdx + 1}
            </div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });

        const stopMarker = L.marker(stopLatLng, { icon: stopIcon }).addTo(map);
        const formatTime = (min) => {
          if (min == null) return '--:--';
          const h = Math.floor(min / 60) % 24;
          const m = Math.floor(min % 60);
          return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
        };

        stopMarker.bindPopup(`
          <div style="padding: 4px;">
            <div style="font-weight: 700; color: #fff; margin-bottom: 4px;">
              Stop #${sIdx + 1} (${stopId})
            </div>
            <div style="font-size: 11px; color: #cbd5e1; margin-bottom: 2px;">
              Vehicle: <strong style="color: ${routeColor}">${assignment.vehicle_id}</strong>
            </div>
            <div style="font-size: 11px; color: #94a3b8;">
              Est. Arrival: <strong>${formatTime(arrivalMin)}</strong>
            </div>
            ${isFallback ? '<div style="font-size: 10px; color: #f87171; font-weight: 700; margin-top: 4px;">⚠️ Best-Effort SLA Fallback</div>' : ''}
          </div>
        `);
        layersRef.current.markers.push(stopMarker);
      });

      // Complete loop back to warehouse
      pathCoords.push(whLatLng);

      // Draw Polyline
      const polyline = L.polyline(pathCoords, {
        color: routeColor,
        weight: isSelected ? 4 : 2,
        opacity: isSelected ? 0.9 : 0.25,
        dashArray: isFallback ? '6, 6' : undefined,
      }).addTo(map);

      polyline.on('click', () => {
        if (onSelectVehicle) {
          onSelectVehicle(assignment.vehicle_id);
        }
      });

      layersRef.current.polylines.push(polyline);
    });

    if (bounds.isValid() && (assignments.length > 0 || warehouses.length > 0)) {
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [warehouses, assignments, stopsLookup, selectedVehicleId, onSelectVehicle]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '450px' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%', borderRadius: 'var(--radius-md)' }} />

      {/* Floating Legend */}
      <div style={{
        position: 'absolute',
        bottom: '16px',
        left: '16px',
        background: 'rgba(9, 13, 22, 0.85)',
        backdropFilter: 'blur(10px)',
        border: '1px solid var(--border-card)',
        borderRadius: 'var(--radius-sm)',
        padding: '0.6rem 0.9rem',
        zIndex: 1000,
        fontSize: '0.75rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.4rem',
      }}>
        <div style={{ fontWeight: 700, color: '#fff', marginBottom: '0.2rem' }}>Route Map Legend</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#4f46e5' }} />
          <span style={{ color: 'var(--text-muted)' }}>Warehouse Hub</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '14px', height: '3px', background: '#10b981' }} />
          <span style={{ color: 'var(--text-muted)' }}>Feasible Route</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '14px', height: '3px', background: '#ef4444', borderTop: '1px dashed #ef4444' }} />
          <span style={{ color: '#f87171' }}>SLA Fallback (Flagged)</span>
        </div>
      </div>
    </div>
  );
}
