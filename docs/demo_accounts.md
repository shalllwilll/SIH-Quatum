# Demo Accounts & Role-Based Access Control (RBAC)

This document records the demo-grade accounts, credentials, and role assignments for the Last-Mile Delivery Routing Platform, per spec §5, §8, and §10.

## 1. Credentials Catalog

| Username | Password | Role | Assigned Vehicle | Driver Name | Notes |
|---|---|---|---|---|---|
| `admin` | `admin123` | `admin` | Fleet-wide | Fleet Dispatcher | Full control: configure presets, trigger runs, assign routes, monitor fleet |
| `driver1` | `driver123` | `driver` | `Van-1` | Ramesh Pawar | Isolated driver view: itinerary, turn-by-turn simulation, delivery status updates |
| `driver2` | `driver223` | `driver` | `Van-2` | Suresh Gaikwad | Isolated driver view |
| `driver3` | `driver323` | `driver` | `Van-3` | Amit Kulkarni | Isolated driver view |

## 2. RBAC Policy & Permissions

- **Admin Role (`admin`)**:
  - Full CRUD on Warehouses, Parcels, Vehicles.
  - Triggering QGA+QPSO routing sessions (`POST /routing-sessions/run`).
  - Assigning optimized routes to fleet (`POST /routing-sessions/{id}/assign`).
  - Fleet-wide live position polling (`GET /vehicles/positions`).
  - Viewing all delivery event logs across sessions.

- **Driver Role (`driver`)**:
  - Authenticate to receive JWT token containing `driver_id` and assigned `vehicle_label`.
  - Query assigned vehicle's itinerary and current route (`GET /driver/manifest`).
  - Log delivery outcomes (`POST /delivery-events`).
  - Query own vehicle position.
  - **Forbidden (`403`)**: Accessing admin-only actions (triggering runs, modifying other vehicles/drivers, fleet-wide modifications).

## 3. Token Format & Header

Authentication uses standard Bearer tokens in the `Authorization` header:
```http
Authorization: Bearer <token>
```
Tokens are signed HMAC-SHA256 tokens containing claims:
- `sub`: User ID
- `username`: Username
- `role`: Role (`admin` | `driver`)
- `name`: Display name
- `vehicle_label`: Assigned vehicle (for drivers)
- `exp`: Expiration timestamp (seconds)
