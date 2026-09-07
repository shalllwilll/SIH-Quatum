# Warehouse Locations — Pune Last-Mile Delivery Network

This document defines the physical locations, operational parameters, and graph snapping strategy for the 4 central distribution hubs (warehouses) in the Pune urban region.

---

## 1. Selected Hub Coordinates & Operational Profile

| Hub ID | Name | Suburb / Zone | Latitude | Longitude | Capacity / Day | Operating Hours |
|---|---|---|---|---|---|---|
| `WH-PUNE-001` | Central Logistics Hub | Shivajinagar | 18.5308 | 73.8475 | 500 parcels | 06:00 – 22:00 (360–1320 min) |
| `WH-PUNE-002` | East Logistics Hub | Hadapsar | 18.5089 | 73.9260 | 400 parcels | 06:00 – 22:00 (360–1320 min) |
| `WH-PUNE-003` | West Logistics Hub | Kothrud | 18.5074 | 73.8077 | 400 parcels | 06:00 – 22:00 (360–1320 min) |
| `WH-PUNE-004` | North Logistics Hub | Pimpri-Chinchwad | 18.6298 | 73.7997 | 400 parcels | 06:00 – 22:00 (360–1320 min) |

---

## 2. Selection Rationale

- **Geographic Coverage:** The 4 hubs form a balanced quadrilateral covering Central, Eastern industrial/tech corridors (Hadapsar/Kharadi), Western residential corridors (Kothrud/Bawdhan), and Northern industrial zone (Pimpri-Chinchwad).
- **Road Connectivity:** All 4 sites sit at major highway intersections (NH 48, Solapur Highway, Old Mumbai-Pune Highway, Karve Road) providing high-speed arterial connections to the road network.
- **Graph Snapping:** During dataset generation (`backend/scripts/generate_stops.py`), each warehouse coordinate is snapped to its nearest node in the largest strongly connected component (SCC) of the Pune OSM graph via `osmnx.distance.nearest_nodes`.

---

## 3. Database Schema

Each warehouse document stored in the `warehouses` collection follows the Pydantic model [`backend/app/models/warehouse.py`](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/backend/app/models/warehouse.py):

```json
{
  "warehouse_id": "WH-PUNE-001",
  "name": "Central Logistics Hub - Shivajinagar",
  "location": {
    "type": "Point",
    "coordinates": [73.8475, 18.5308]
  },
  "snapped_node_id": 245192834,
  "operating_hours": {
    "start_time": 360,
    "end_time": 1320
  },
  "active": true
}
```
