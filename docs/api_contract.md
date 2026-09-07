# API Contract Specification

This document defines the complete REST API contract for the Last-Mile Delivery Routing Platform backend (FastAPI), per spec §10.

Canonical Unit Rules (spec §3a):
- **Coordinates**: Decimal degrees (`float`): `lat` [-90.0, 90.0], `lon` [-180.0, 180.0]
- **Time**: Minutes since midnight (`int` or `float`): `[0, 1439]` (e.g., `540` = 09:00 AM, `1080` = 06:00 PM)
- **Distance**: Kilometres (`float`)
- **Speed**: Kilometres per hour (`km/h`, `float`)
- **Weight / Load**: Kilograms (`kg`, `float`)
- **Conversion Policy**: All backend storage and API request/response payloads preserve canonical typed units. Time formatting (e.g., "09:00 AM") is performed exclusively at the UI/presentation layer.

Error Response Format:
All error responses consistently return JSON:
```json
{
  "error": "Error Category / Type",
  "detail": "Descriptive explanation of the error."
}
```

---

## 1. Authentication Endpoints (`/auth`)

### `POST /auth/login`
- **Description**: Authenticate admin or driver user (demo-grade RBAC).
- **Request Body**:
  ```json
  {
    "username": "admin",
    "password": "password123"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "demo_jwt_token_...",
    "token_type": "bearer",
    "user": {
      "id": "USR-001",
      "username": "admin",
      "role": "admin",
      "name": "Fleet Dispatcher"
    }
  }
  ```
- **Errors**: `401 Unauthorized` for bad credentials, `422 Unprocessable Entity` for invalid body.

---

## 2. Warehouse Endpoints (`/warehouses`)

### `GET /warehouses`
- **Description**: List all operational warehouse distribution hubs.
- **Response `200 OK`**:
  ```json
  [
    {
      "id": "64f1a2b3c4d5e6f7a8b9c0d1",
      "name": "Kothrud Depot",
      "lat": 18.5074,
      "lon": 73.8077,
      "address": "Paud Road, Kothrud, Pune",
      "node_id": 12345678
    }
  ]
  ```

### `POST /warehouses`
- **Description**: Create a new warehouse hub.
- **Request Body**:
  ```json
  {
    "name": "Hadapsar Hub",
    "lat": 18.5089,
    "lon": 73.9259,
    "address": "Magarpatta Road, Hadapsar, Pune",
    "node_id": 87654321
  }
  ```
- **Response `201 Created`**: Returns created `Warehouse` object.

### `GET /warehouses/{id}`
- **Description**: Fetch single warehouse by MongoDB ObjectId.
- **Response `200 OK`**: Single `Warehouse` object.
- **Errors**: `404 Not Found`.

---

## 3. Parcel Endpoints (`/parcels`)

### `GET /parcels`
- **Description**: List delivery parcels with pagination and status filtering.
- **Query Parameters**:
  - `page`: `int` (default: 1, ge=1)
  - `limit`: `int` (default: 20, ge=1, le=200)
  - `status`: `string` (`pending` | `assigned` | `en_route` | `delivered` | `failed`, optional)
- **Response `200 OK`**:
  ```json
  {
    "items": [
      {
        "id": "64f1a2b3c4d5e6f7a8b9c0d2",
        "address": "FC Road, Deccan Gymkhana, Pune",
        "lat": 18.5196,
        "lon": 73.8436,
        "node_id": 23456789,
        "weight_kg": 4.5,
        "sla_start_min": 540,
        "sla_deadline_min": 720,
        "status": "pending"
      }
    ],
    "total": 120,
    "page": 1,
    "limit": 20,
    "pages": 6
  }
  ```

### `POST /parcels`
- **Description**: Create a single parcel delivery stop.
- **Request Body**:
  ```json
  {
    "address": "Viman Nagar Central, Pune",
    "lat": 18.5679,
    "lon": 73.9143,
    "node_id": 34567890,
    "weight_kg": 8.0,
    "sla_start_min": 600,
    "sla_deadline_min": 840,
    "status": "pending"
  }
  ```
- **Response `201 Created`**: Returns created `Parcel` object.
- **Errors**: `422 Unprocessable Entity` (e.g. `sla_deadline_min <= sla_start_min`).

### `GET /parcels/{id}`
- **Description**: Fetch single parcel by ObjectId.
- **Response `200 OK`**: Single `Parcel` object.
- **Errors**: `404 Not Found`.

---

## 4. Vehicle Endpoints (`/vehicles`)

### `GET /vehicles`
- **Description**: List all fleet vehicles.
- **Response `200 OK`**:
  ```json
  [
    {
      "id": "64f1a2b3c4d5e6f7a8b9c0d3",
      "label": "Van-1",
      "capacity_kg": 250.0,
      "status": "idle",
      "driver_id": "driver1",
      "current_warehouse_id": "64f1a2b3c4d5e6f7a8b9c0d1"
    }
  ]
  ```

### `POST /vehicles`
- **Description**: Register a new fleet vehicle.
- **Request Body**:
  ```json
  {
    "label": "Van-4",
    "capacity_kg": 300.0,
    "status": "idle",
    "driver_id": "driver4",
    "current_warehouse_id": "64f1a2b3c4d5e6f7a8b9c0d1"
  }
  ```
- **Response `201 Created`**: Returns created `Vehicle` object.

### `GET /vehicles/{id}`
- **Description**: Fetch single vehicle by ObjectId.
- **Response `200 OK`**: Single `Vehicle` object.
- **Errors**: `404 Not Found`.

### `PATCH /vehicles/{id}`
- **Description**: Update vehicle status, driver assignment, or current location.
- **Request Body**:
  ```json
  {
    "status": "en_route",
    "driver_id": "driver1"
  }
  ```
- **Response `200 OK`**: Updated `Vehicle` object.
- **Errors**: `404 Not Found`, `422 Unprocessable Entity`.

### `GET /vehicles/positions`
- **Description**: Bulk endpoint for Fleet Overview map polling (spec §6).
- **Response `200 OK`**:
  ```json
  [
    {
      "vehicle_id": "64f1a2b3c4d5e6f7a8b9c0d3",
      "label": "Van-1",
      "lat": 18.5204,
      "lon": 73.8567,
      "heading_deg": 45.0,
      "speed_kmh": 28.5,
      "status": "en_route",
      "current_stop_index": 3,
      "total_stops": 12,
      "active_route_id": "route_v1_trip1"
    }
  ]
  ```

### `GET /vehicles/{id}/position`
- **Description**: Single vehicle position polling endpoint (driver/admin specific).
- **Response `200 OK`**: Single vehicle position object.

---

## 5. Routing Optimization Sessions (`/routing-sessions`)

### `POST /routing-sessions/run`
- **Description**: Trigger QGA + QPSO optimization run with a business priority preset.
- **Request Body**:
  ```json
  {
    "preset": "balanced",
    "warehouse_id": "64f1a2b3c4d5e6f7a8b9c0d1",
    "start_time_min": 540.0,
    "max_bounceback_retries": 3
  }
  ```
- **Supported Presets**: `balanced`, `min_distance`, `min_time`, `prioritize_sla`, `smooth_speed`
- **Response `202 Accepted`**:
  ```json
  {
    "session_id": "64f1a2b3c4d5e6f7a8b9c0d9",
    "status": "running",
    "message": "Optimization pipeline started."
  }
  ```
- **Errors**: `422 Unprocessable Entity` for invalid preset.

### `GET /routing-sessions/{id}/status`
- **Description**: Lightweight polling endpoint for execution status.
- **Response `200 OK`**:
  ```json
  {
    "session_id": "64f1a2b3c4d5e6f7a8b9c0d9",
    "status": "completed",
    "progress_percent": 100,
    "elapsed_seconds": 1.45,
    "error_message": null
  }
  ```

### `GET /routing-sessions/{id}`
- **Description**: Retrieve full routing solution and evaluation metrics.
- **Response `200 OK`**:
  ```json
  {
    "session_id": "64f1a2b3c4d5e6f7a8b9c0d9",
    "preset": "balanced",
    "status": "completed",
    "overall_feasibility": true,
    "bounceback_retries": 0,
    "combined_fitness": 0.428,
    "routes": [
      {
        "vehicle_id": "Van-1",
        "trip_id": 1,
        "stops": [
          {
            "stop_index": 0,
            "parcel_id": "64f1a2b3c4d5e6f7a8b9c0d2",
            "lat": 18.5196,
            "lon": 73.8436,
            "arrival_time_min": 565.2,
            "departure_time_min": 570.2,
            "sla_start_min": 540,
            "sla_deadline_min": 720,
            "is_sla_violated": false
          }
        ],
        "total_distance_km": 14.8,
        "total_time_min": 42.5,
        "total_load_kg": 185.0
      }
    ],
    "created_at": "2026-09-07T12:00:00Z"
  }
  ```

### `POST /routing-sessions/{id}/assign`
- **Description**: Confirm and commit route assignment to active vehicles.
- **Response `200 OK`**:
  ```json
  {
    "session_id": "64f1a2b3c4d5e6f7a8b9c0d9",
    "status": "assigned",
    "assigned_vehicles_count": 3,
    "assigned_parcels_count": 48
  }
  ```

---

## 6. Delivery Events Endpoints (`/delivery-events`)

### `POST /delivery-events`
- **Description**: Driver logs delivery attempt result (delivered / failed).
- **Request Body**:
  ```json
  {
    "parcel_id": "64f1a2b3c4d5e6f7a8b9c0d2",
    "vehicle_id": "Van-1",
    "driver_id": "driver1",
    "session_id": "64f1a2b3c4d5e6f7a8b9c0d9",
    "status": "delivered",
    "timestamp_min": 568.0,
    "notes": "Delivered to reception",
    "proof_photo_url": null
  }
  ```
- **Response `201 Created`**: Returns created `DeliveryEvent` object.
- **Errors**: `404 Not Found` if parcel/session invalid, `422 Unprocessable Entity`.

### `GET /delivery-events`
- **Description**: Query logged delivery events by session or vehicle.
- **Query Parameters**:
  - `session_id`: `string` (optional)
  - `vehicle_id`: `string` (optional)
  - `limit`: `int` (default: 50)
- **Response `200 OK`**: List of `DeliveryEvent` objects.

---

## 7. Driver Manifest Endpoints (`/driver`)

### `GET /driver/manifest`
- **Description**: Fetch assigned itinerary for the logged-in driver.
- **Response `200 OK`**:
  ```json
  {
    "driver_id": "driver1",
    "vehicle_label": "Van-1",
    "session_id": "64f1a2b3c4d5e6f7a8b9c0d9",
    "itinerary": [
      {
        "stop_index": 1,
        "parcel_id": "64f1a2b3c4d5e6f7a8b9c0d2",
        "address": "FC Road, Deccan Gymkhana, Pune",
        "lat": 18.5196,
        "lon": 73.8436,
        "weight_kg": 4.5,
        "sla_start_min": 540,
        "sla_deadline_min": 720,
        "scheduled_arrival_min": 565.2,
        "status": "pending"
      }
    ]
  }
  ```

---

## 8. Live Traffic Status Endpoints (`/traffic`)

### `GET /traffic/status`
- **Description**: Diagnostic data source freshness and cache health for Admin UI.
- **Response `200 OK`**:
  ```json
  {
    "traffic_source": "live",
    "cached_segment_count": 70,
    "consecutive_cycle_failures": 0,
    "fallback_threshold": 3,
    "last_refresh_timestamp": 1788780000.0
  }
  ```
