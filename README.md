# Abraxas: Hybrid QGA + QPSO Last-Mile Logistics Platform

Production-ready last-mile delivery routing and dynamic fleet dispatch platform for Pune, India. Powered by a hybrid Quantum-Inspired Genetic Algorithm (QGA) for combinatorial clustering & stop sequencing, Quantum-Behaved Particle Swarm Optimization (QPSO) for continuous departure scheduling & SLA timing, FastAPI REST API, and dedicated React 19 Admin & Driver web portals.

---

## 🚀 Key Platform Features

- **Hybrid Quantum Optimization Engine:**
  - **Leiden Graph Modularity Pre-Clustering:** Partitions delivery stops into contiguous delivery zones, reducing combinatorial search space by over $10^{165}\times$.
  - **Discrete QGA (Quantum-Inspired Genetic Algorithm):** Q-bit rotation gates ($\theta$), H-gate probabilistic mutation, and elite chromosome retention optimize stop ordering across multiple vehicle capacities.
  - **Continuous QPSO (Quantum-Behaved Particle Swarm Optimization):** Simulates wave-function $\delta$-potential well dynamics to optimize departure times and satisfy hard customer SLA delivery windows.
  - **Dynamic Bounce-Back Loop:** Automatically repairs infeasible chromosomes via QGA chromosome mutation and best-effort fallback tagging.
- **Three-Tiered Live Re-Optimization:**
  - *Tier 1 (Delivered):* Continuous QPSO re-tune on remaining stops (~18 ms).
  - *Tier 2 (Failed):* Greedy nearest-neighbor insertion into alternate vehicles with QPSO feasibility check (~58 ms).
  - *Tier 3 (Escalation):* Structural QGA+QPSO re-partitioning when no vehicle can absorb unserved stops (~330 ms).
- **TomTom Live Traffic Integration:** Representative arterial segment sampling with spatial decay propagation, 120-second staggered caching, and simulated rush-hour fallback curve.
- **Admin Fleet Management Portal (Port 5173):** Live Leaflet fleet maps, 4 business-priority preset selector cards (`balanced`, `minimize_distance`, `minimize_cost_fuel`, `prioritize_sla`), one-click dispatch, and pure SVG analytics dashboard (fuel trends, SLA gauges, violation audit log).
- **Driver Mobile Portal (Port 5174):** Role-isolated route manifests, live vehicle telemetry interpolation along real OSM road geometry, and delivery action logging (`Mark Delivered` / `Mark Failed`).

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
│   │   ├── routers/          # REST endpoints (CRUD, routing, driver, analytics)
│   │   ├── simulation/       # Accelerated-clock movement & lat/lon interpolator
│   │   └── traffic/          # TomTom traffic client, propagation & fallback curve
│   ├── scripts/              # Benchmark, seed, and pre-flight healthcheck utilities
│   └── tests/                # 112 pytest unit and integration test suite
├── frontend-admin/           # React 19 + Vite Admin Portal (Port 5173)
├── frontend-driver/          # React 19 + Vite Driver Portal (Port 5174)
├── docs/                     # Architectural design docs, benchmarks, and API specs
├── docker-compose.yml        # Multi-container deployment configuration
├── Development_Playbook.md   # Complete phase-wise development record
├── Makefile                  # Developer CLI shortcuts
└── README.md                 # System overview and quickstart guide
```

---

## 📚 Technical Documentation Directory

- 📐 **[API Contract](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/docs/api_contract.md):** Complete REST endpoint specification and request/response payloads.
- ⚡ **[Scalability & Benchmark Evidence](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/docs/scalability_evidence.md):** Empirical timing results across 30 to 120 delivery stops and re-optimization cost tiers.
- 🧪 **[End-to-End Regression Report](file:///Users/sharwilhodgar/Desktop/Abraxas%20P2/docs/regression_report.md):** 112-test QA suite summary and lifecycle validation.
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
In three separate terminal tabs:

```bash
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
| `make test-backend` | Execute full automated test suite (112 tests) |
| `make lint` | Run ruff and frontend linters |
| `make scale-benchmark` | Run 120-stop load test and performance sweep |
| `make healthcheck` | Verify MongoDB, graph cache, and TomTom connectivity |
| `make seed-data` | Idempotently seed parcels, hubs, vehicles, and sessions |

---

## 🔒 Demo Logins

- **Admin Portal (`http://localhost:5173`):** Username `admin` | Password `admin123`
- **Driver Portal (`http://localhost:5174`):** Username `driver1` | Password `driver123`
