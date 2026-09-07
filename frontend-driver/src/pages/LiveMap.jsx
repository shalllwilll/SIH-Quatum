import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import { driverApi } from '../api/client';
import { useDriverAuth } from '../context/AuthContext';
import {
  Navigation,
  MapPin,
  Clock,
  RefreshCw,
  Compass,
  AlertTriangle,
} from 'lucide-react';

const PUNE_CENTER = [18.5204, 73.8567];
const POSITION_POLL_MS = 3000;

export default function LiveMap() {
  const { user } = useDriverAuth();
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const vehicleMarkerRef = useRef(null);
  const routePolylineRef = useRef(null);
  const stopMarkersRef = useRef([]);

  const [position, setPosition] = useState(null);
  const [manifest, setManifest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pollError, setPollError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: PUNE_CENTER,
      zoom: 13,
      zoomControl: true,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; CARTO &copy; OpenStreetMap',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Fetch Manifest
  useEffect(() => {
    driverApi.getManifest()
      .then((data) => setManifest(data))
      .catch((err) => console.warn('Could not load driver manifest:', err));
  }, []);

  // Polling driver vehicle position
  useEffect(() => {
    let isMounted = true;

    const fetchPos = async () => {
      try {
        const data = await driverApi.getDriverPosition();
        if (!isMounted) return;
        setPosition(data);
        setLastUpdated(new Date());
        setPollError(null);
        setLoading(false);
      } catch (err) {
        if (!isMounted) return;
        setPollError('Position update unavailable');
        setLoading(false);
      }
    };

    fetchPos();
    const interval = setInterval(fetchPos, POSITION_POLL_MS);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Update Route Polyline & Stops on Map
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !manifest?.itinerary) return;

    // Clear old stops
    stopMarkersRef.current.forEach((m) => m.remove());
    stopMarkersRef.current = [];
    if (routePolylineRef.current) {
      routePolylineRef.current.remove();
      routePolylineRef.current = null;
    }

    const stops = manifest.itinerary || [];
    const coords = [];

    stops.forEach((stop, idx) => {
      const latLng = [stop.lat || 18.5204 + idx * 0.005, stop.lon || 73.8567 + idx * 0.004];
      coords.push(latLng);

      const stopIcon = L.divIcon({
        className: 'custom-driver-stop-icon',
        html: `
          <div style="
            background: #6366f1;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 10px;
            font-weight: 800;
            border: 2px solid #ffffff;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.6);
          ">
            ${idx + 1}
          </div>
        `,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      });

      const m = L.marker(latLng, { icon: stopIcon }).addTo(map);
      m.bindPopup(`
        <div style="padding: 4px;">
          <h4 style="font-weight: 700; color: #818cf8; margin-bottom: 2px;">Stop #${idx + 1}: ${stop.parcel_id}</h4>
          <p style="font-size: 11px; color: #cbd5e1;">${stop.address}</p>
        </div>
      `);
      stopMarkersRef.current.push(m);
    });

    if (coords.length > 0) {
      const poly = L.polyline(coords, {
        color: '#10b981',
        weight: 4,
        opacity: 0.85,
        dashArray: '6, 6',
      }).addTo(map);
      routePolylineRef.current = poly;
    }
  }, [manifest]);

  // Update Vehicle Marker
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !position) return;

    const lat = position.lat || 18.5204;
    const lon = position.lon || 73.8567;
    const latLng = [lat, lon];

    const driverIcon = L.divIcon({
      className: 'custom-driver-pos-icon',
      html: `
        <div style="
          background: #10b981;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 3px solid #ffffff;
          box-shadow: 0 0 18px rgba(16, 185, 129, 0.8);
          animation: pulse 2s infinite;
        ">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3">
            <polygon points="12 2 19 21 12 17 5 21 12 2"/>
          </svg>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    if (vehicleMarkerRef.current) {
      vehicleMarkerRef.current.setLatLng(latLng);
    } else {
      const marker = L.marker(latLng, { icon: driverIcon }).addTo(map);
      marker.bindPopup(`
        <div style="padding: 4px;">
          <h4 style="font-weight: 700; color: #34d399;">Your Vehicle: ${position.label || 'Van'}</h4>
          <p style="font-size: 11px; color: #cbd5e1;">Status: ${position.status || 'En Route'}</p>
        </div>
      `);
      vehicleMarkerRef.current = marker;
      map.setView(latLng, 14);
    }
  }, [position]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)', minHeight: '480px', gap: '0.75rem', position: 'relative' }}>
      {/* Top Floating Status Overlay */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(9, 13, 22, 0.85)',
        backdropFilter: 'blur(10px)',
        border: '1px solid var(--border-card)',
        borderRadius: 'var(--radius-sm)',
        padding: '0.6rem 1rem',
        zIndex: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#fff' }}>
            {manifest?.vehicle_label || user?.vehicle_label || 'My Vehicle'} GPS Live
          </span>
        </div>

        {lastUpdated && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Map Canvas */}
      <div className="glass-card" style={{ flex: 1, padding: '0.25rem', position: 'relative', overflow: 'hidden' }}>
        <div ref={mapContainerRef} style={{ width: '100%', height: '100%', borderRadius: 'var(--radius-md)' }} />

        {loading && (
          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(9, 13, 22, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            color: 'var(--text-muted)',
            zIndex: 1000,
          }}>
            <RefreshCw className="animate-spin" size={20} />
            <span>Connecting GPS Stream...</span>
          </div>
        )}
      </div>
    </div>
  );
}
