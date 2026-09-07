# Abraxas: Hybrid QGA + QPSO Last-Mile Logistics Platform

Production-ready last-mile delivery routing and dynamic fleet dispatch platform for Pune, India. Powered by a hybrid Quantum-Inspired Genetic Algorithm (QGA) for combinatorial clustering & stop sequencing, Quantum-Behaved Particle Swarm Optimization (QPSO) for continuous departure scheduling & SLA timing, FastAPI REST API, and dedicated React 19 Admin & Driver web portals.

---

## 🚀 Key Platform Features

- **Hybrid Quantum Optimization Engine:**
  - **Leiden Graph Modularity Pre-Clustering:** Partitions delivery stops into contiguous delivery zones, reducing combinatorial search space by over $10^{165}\times$.
  - **Vectorized Discrete QGA (NumPy Acceleration):** Q-bit rotation gates ($\theta$), H-gate probabilistic mutation, and elite chromosome retention optimize stop ordering across multiple vehicle capacities with SIMD-vectorized angle calculations.
  - **Continuous QPSO (Quantum-Behaved Particle Swarm Optimization):** Simulates wave-function $\delta$-potential well dynamics with vectorized velocity & position updates to optimize departure times and satisfy customer SLA delivery windows.
  - **Dynamic Bounce-Back Loop & 2-Opt Local Repair:** Automatically repairs infeasible chromosomes and applies 2-opt geometric smoothing to uncross intersecting route segments.
- **Enterprise Routing & Spatial Acceleration:**
  - **Valhalla C++ High-Performance Routing Engine:** Native matrix computation (`/sources_to_targets`) and multi-stop turn-by-turn geometry generation (`/route`) running containerized via Docker on port 8002 with automatic spatial graph fallback.
  - **cKDTree Batch Congestion Propagation:** $O(|E| \log |S|)$ spatial indexing via `scipy.spatial.cKDTree` over 3D Cartesian coordinates on the unit sphere for ultra-fast traffic propagation across tens of thousands of edges.
  - **Real-Time WebSocket Streaming:** Bi-directional telemetry streaming via FastAPI WebSockets (`/ws/fleet`, `/ws/driver/{id}`) eliminating HTTP polling overhead.
  - **Hardware-Accelerated Canvas Map Rendering:** Leaflet maps configured with `preferCanvas: true` for 60 FPS GPU-accelerated rendering of dense fleet routes.
- **Three-Tiered Live Re-Optimization:**
  - *Tier 1 (Delivered):* Continuous QPSO re-tune on remaining stops (~12 ms).
  - *Tier 2 (Failed):* Greedy nearest-neighbor insertion with 2-Opt smoothing and QPSO feasibility check (~42 ms).
  - *Tier 3 (Escalation):* Structural QGA+QPSO re-partitioning when no vehicle can absorb unserved stops (~240 ms).
- **TomTom Live Traffic Integration:** Representative arterial segment sampling with spatial decay propagation, 120-second staggered caching, and simulated rush-hour fallback curve.
- **Admin Fleet Management Portal (Port 5173):** Live Leaflet fleet maps, 4 business-priority preset selector cards (`balanced`, `minimize_distance`, `minimize_cost_fuel`, `prioritize_sla`), one-click dispatch, pure SVG analytics dashboard (fuel trends, SLA gauges, violation audit log), and real-time WebSocket telemetry badge.
- **Driver Mobile Portal (Port 5174):** Role-isolated route manifests, live vehicle telemetry interpolation along real OSM road geometry, WebSocket synchronization, and delivery action logging (`Mark Delivered` / `Mark Failed`).

---

## 📁 Repository Structure

```
├── backend/                  # FastAPI backend service (Python 3.11+)
│   ├── app/
│   │   ├── auth/             # JWT authentication & role-based access control
│   │   ├── clustering/       # Leiden graph community pre-clustering
│   │   ├── costing/          # 4 business priority presets & cost functions
│   │   ├── graph/            # Pune OSM road network loader & spatial indexing
│   │   ├── pipeline/         # QGA+QPSO orchestrator, retune & local repair
│   │   ├── qga/              # Quantum-Inspired Genetic Algorithm engine
│   │   ├── qpso/             # Quantum-Behaved Particle Swarm Optimization engine
│   │   ├── routers/          # REST endpoints (CRUD, routing, driver, analytics, websocket)
│   │   ├── routing/          # Valhalla C++ routing engine client & fallback
│   │   ├── simulation/       # Accelerated-clock movement & lat/lon interpolator
│   │   └── traffic/          # TomTom traffic client, cKDTree propagation & fallback
│   ├── scripts/              # Benchmark, seed, and pre-flight healthcheck utilities
│   └── tests/                # 119 pytest unit and integration test suite
├── frontend-admin/           # React 19 + Vite Admin Portal (Port 5173)
├── frontend-driver/          # React 19 + Vite Driver Portal (Port 5174)
├── docs/                     # Architectural design docs, benchmarks, and API specs
├── docker-compose.yml        # Multi-container deployment configuration (Valhalla + MongoDB)
├── Development_Playbook.md   # Complete phase-wise development record
├── Makefile                  # Developer CLI shortcuts
└── README.md                 # System overview and quickstart guide
```

---

## 📚 Technical Documentation Directory

- 📐 **[API Contract](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/docs/api_contract.md):** Complete REST endpoint specification and request/response payloads.
- ⚡ **[Scalability & Benchmark Evidence](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/docs/scalability_evidence.md):** Empirical timing results across 30 to 120 delivery stops and re-optimization cost tiers.
- 🧪 **[End-to-End Regression Report](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/docs/regression_report.md):** 119-test QA suite summary and lifecycle validation.
- 🚀 **[Deployment Guide](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/docs/deployment.md):** Step-by-step local and containerized deployment instructions.
- 🔑 **[Demo Account Credentials](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/docs/demo_accounts.md):** Pre-configured Admin and Driver login accounts.
- 📈 **[Historical Seed Data Story](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/docs/historical_seed_story.md):** 5-session improvement trajectory for the analytics dashboard.
- 🗺️ **[Warehouse Locations](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/docs/warehouse_locations.md):** Pune distribution hub coordinates and catchment areas.

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+** / npm
- **MongoDB 7.0+** (running on `mongodb://localhost:27017`)
- **Docker & Docker Compose** (for Valhalla C++ routing engine)

### 2. Setup & Seed Data
```bash
# Clone repository and navigate to root
cd "Abraxas P2"

# Setup Python environment & install backend dependencies
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
cd ..

# Seed delivery parcels, distribution hubs, and historical analytics sessions
make seed-data

# Run pre-flight health check
make healthcheck
```

### 3. Launch Platform Services
In separate terminal tabs:

```bash
# (Optional) Start Valhalla C++ Engine via Docker:
docker compose up valhalla -d

# Terminal 1: Backend API (http://localhost:8000)
make run-backend

# Terminal 2: Admin Web Portal (http://localhost:5173)
make run-frontend-admin

# Terminal 3: Driver Web Portal (http://localhost:5174)
make run-frontend-driver
```

---

## 🛠️ Developer CLI Commands

| Command | Description |
|---|---|
| `make test-backend` | Execute full automated test suite (119 tests) |
| `make lint` | Run ruff and frontend linters |
| `make scale-benchmark` | Run 120-stop load test and performance sweep |
| `make healthcheck` | Verify MongoDB, graph cache, and TomTom connectivity |
| `make seed-data` | Idempotently seed parcels, hubs, vehicles, and sessions |

---

## 🔒 Demo Logins

- **Admin Portal (`http://localhost:5173`):** Username `admin` | Password `admin123`
- **Driver Portal (`http://localhost:5174`):** Username `driver1` | Password `driver123`
