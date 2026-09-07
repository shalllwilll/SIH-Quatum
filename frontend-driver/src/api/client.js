/**
 * frontend-driver/src/api/client.js — Driver API Client with auth token interceptor
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiRequest(endpoint, options = {}) {
  const token = sessionStorage.getItem('driver_token');
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
      sessionStorage.removeItem('driver_token');
      sessionStorage.removeItem('driver_user');
      window.dispatchEvent(new Event('driver_auth_expired'));
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

export const driverApi = {
  // Auth
  login: (username, password) =>
    apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  getMe: () => apiRequest('/auth/me'),

  // Driver Isolated Manifest & Route Itinerary
  getManifest: () => apiRequest('/driver/manifest'),

  // Driver's Assigned Vehicle Position
  getDriverPosition: () => apiRequest('/driver/position'),

  // Delivery Event Logger
  logDeliveryEvent: (eventData) =>
    apiRequest('/delivery-events', {
      method: 'POST',
      body: JSON.stringify(eventData),
    }),

  // Delivery Events for this driver
  getMyEvents: (limit = 50) => apiRequest(`/delivery-events?limit=${limit}`),
};
