# Known Duplication & Shared Architectural Patterns

This document catalogues intentionally duplicated or adapted components across frontends (`frontend-admin` and `frontend-driver`) per Development Playbook Phase 8 guidance.

## 1. Authentication & API Client
- **Files**: `frontend-admin/src/api/client.js` & `frontend-driver/src/api/client.js`
- **Rationale**: Both apps use Bearer JWT authentication against the FastAPI backend, but `frontend-driver` operates under strict role-based data isolation (`/driver/manifest`, `/driver/position`, `/delivery-events`) and isolated session storage keys (`driver_token` vs `admin_token`).
- **Maintenance**: Both clients share the same error parsing, base URL configuration (`VITE_API_BASE_URL`), and 401 expiration event handling pattern.

## 2. Design Tokens & Styling
- **Files**: `frontend-admin/src/index.css` & `frontend-driver/src/index.css`
- **Rationale**: Admin portal uses a wide desktop multi-column dashboard layout, while the Driver portal uses a compact mobile-first layout with bottom sticky navigation. Both share identical glassmorphic dark-theme tokens (`--bg-dark`, `--bg-card`, `--primary`, `--border-card`, `--radius-md`).

## 3. Leaflet Mapping & Tile Layer
- **Files**: `frontend-admin/src/pages/FleetOverview.jsx` / `RouteMap.jsx` & `frontend-driver/src/pages/LiveMap.jsx`
- **Rationale**: Admin renders fleet-wide vehicle telemetry and multi-vehicle route polylines; Driver renders single-vehicle isolated position and assigned shift stop sequence using CartoDB dark matter tiles.
