/**
 * frontend-admin/src/api/client.js — API client with auth token interceptor
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiRequest(endpoint, options = {}) {
  const token = sessionStorage.getItem('admin_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      sessionStorage.removeItem('admin_token');
      sessionStorage.removeItem('admin_user');
      window.dispatchEvent(new Event('auth_expired'));
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = data?.detail || data?.error || `HTTP ${response.status}`;
      throw new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
    }

    return data;
  } catch (err) {
    throw err;
  }
}

export const api = {
  // Auth
  login: (username, password) =>
    apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  getMe: () => apiRequest('/auth/me'),

  // Warehouses
  getWarehouses: () => apiRequest('/warehouses'),
  createWarehouse: (data) =>
    apiRequest('/warehouses', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Parcels
  getParcels: (page = 1, limit = 20, status = null) => {
    let q = `/parcels?page=${page}&limit=${limit}`;
    if (status) q += `&status=${status}`;
    return apiRequest(q);
  },

  // Vehicles
  getVehicles: () => apiRequest('/vehicles'),
  getVehiclePositions: () => apiRequest('/vehicles/positions'),
  getVehicle: (id) => apiRequest(`/vehicles/${id}`),
  createVehicle: (data) =>
    apiRequest('/vehicles', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateVehicle: (id, data) =>
    apiRequest(`/vehicles/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // Routing Sessions
  runRoutingSession: (params) =>
    apiRequest('/routing-sessions/run', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  getSessionStatus: (sessionId) => apiRequest(`/routing-sessions/${sessionId}/status`),
  getSessionDetails: (sessionId) => apiRequest(`/routing-sessions/${sessionId}`),
  assignSessionRoutes: (sessionId) =>
    apiRequest(`/routing-sessions/${sessionId}/assign`, {
      method: 'POST',
    }),

  // Delivery Events
  getDeliveryEvents: (sessionId = null, limit = 50) => {
    let q = `/delivery-events?limit=${limit}`;
    if (sessionId) q += `&session_id=${sessionId}`;
    return apiRequest(q);
  },

  // Analytics
  getFuelEfficiencyTrend: () => apiRequest('/analytics/fuel-efficiency'),
  getSlaCompliance: (groupBy = null) => {
    const q = groupBy ? `/analytics/sla-compliance?groupBy=${groupBy}` : '/analytics/sla-compliance';
    return apiRequest(q);
  },
  getViolations: () => apiRequest('/analytics/violations'),
  getVehiclePerformance: () => apiRequest('/analytics/vehicle-performance'),

  // Traffic & Diagnostics
  getTrafficStatus: () => apiRequest('/traffic/status'),
  refreshTraffic: () => apiRequest('/traffic/refresh', { method: 'POST' }),
  getHealth: () => apiRequest('/health'),
  getDbHealth: () => apiRequest('/health/db'),

  // Demo Scenario & Presets Comparison (SIH)
  seedScenario: (data) =>
    apiRequest('/demo/seed-scenario', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  injectTrafficSpike: (data) =>
    apiRequest('/demo/inject-traffic-spike', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  comparePresets: (data = {}) =>
    apiRequest('/routing-sessions/compare', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getDemoWarehouses: () => apiRequest('/demo/warehouses'),

  // OSRM Road Geometry Snapping
  getRoadGeometry: (waypoints) =>
    apiRequest('/routing/road-geometry', {
      method: 'POST',
      body: JSON.stringify({ waypoints }),
    }),
};

