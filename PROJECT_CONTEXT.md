# Abraxas: Complete System Architecture, Mathematical Foundation & Implementation Context

> **Document Purpose:** Master context document designed for transferring the complete state, architectural specifications, mathematical formulations, codebase topology, and operational workflows of the **Abraxas Hybrid QGA + QPSO Last-Mile Delivery Routing Platform** to any external tool, developer, or AI agent without loss of context.

---

## 1. Executive Overview & Mission Statement

**Abraxas** is an enterprise-grade, last-mile logistics routing and dynamic fleet dispatch platform built specifically for the complex metropolitan road network of **Pune, India** (~18.5204° N, 73.8567° E).

Traditional Vehicle Routing Problems with Time Windows (VRPTW) scale with factorial complexity ($O(N!)$). For a realistic metropolitan fleet handling 120 delivery stops across 20 vehicles, the unconstrained search space reaches $120! \approx 6.68 \times 10^{198}$, rendering exact integer programming (MILP) or standard metaheuristics computationally infeasible for sub-second real-time dispatch.

Abraxas solves this by decoupling the problem into a **two-phase hybrid quantum-inspired optimization framework** with **submodular pre-clustering** and **three-tiered live re-optimization**:
1. **Topological Pre-Clustering (Leiden Graph Modularity):** Partitions stops into geographically and topologically contiguous delivery zones on the OpenStreetMap road graph, reducing search space by **$>10^{165}\times$**.
2. **Phase 1: Discrete Combinatorial Optimization (QGA):** A Quantum-Inspired Genetic Algorithm uses qubit probability vectors and quantum rotation gates ($R(\theta)$) to optimize discrete parcel-to-vehicle assignments and stop orderings under strict vehicle capacity limits.
3. **Phase 2: Continuous Temporal Optimization (QPSO):** A Quantum-Behaved Particle Swarm Optimization engine treats vehicle departure times as wave-function positions trapped in a delta-potential well, solving continuous schedule timing to satisfy strict customer Service Level Agreement (SLA) time windows.
4. **Dynamic Infeasibility Bounce-Back:** If QPSO detects unavoidable SLA violations, targeted feedback mutates the discrete QGA chromosomes to re-order stops until global feasibility is achieved.
5. **Real-Time Dynamic Dispatch & Re-Optimization:** Driver delivery updates (`DELIVERED`, `FAILED`) trigger hierarchical live re-solves (Tier 1 QPSO re-tune in ~12ms, Tier 2 local repair + 2-opt smoothing in ~42ms, Tier 3 structural escalation in ~240ms).

---

## 2. Core Mathematical & Algorithmic Formulations

### 2.1 Leiden Community Pre-Clustering
Instead of routing all $N$ stops across all $K$ vehicles simultaneously, the road network graph $G = (V, E)$ is partitioned using the **Leiden graph modularity maximization** algorithm:
$$\mathcal{H} = \frac{1}{2m} \sum_{ij} \left( A_{ij} - \gamma \frac{k_i k_j}{2m} \right) \delta(\sigma_i, \sigma_j)$$
- **Resolution Parameter ($\gamma$):** 1.0 (balances cluster cohesion and vehicle capacity absorption).
- **Result:** $N = 120$ stops are partitioned into $C \approx 4$ distinct territorial clusters of $\approx 30$ stops each, reducing combinatorial permutations from $120! \approx 6.68 \times 10^{198}$ to $4 \times 30! \approx 1.06 \times 10^{33}$ (a $> 10^{165}\times$ search space reduction).

### 2.2 Discrete QGA (Quantum-Inspired Genetic Algorithm)
- **Q-bit Chromosome Encoding:** Each stop decision is represented as a qubit state $|\psi_i\rangle = \alpha_i |0\rangle + \beta_i |1\rangle$, parametrized by probability angle $\theta_i \in [0, \pi/2]$ where:
  $$\alpha_i = \cos(\theta_i), \quad \beta_i = \sin(\theta_i), \quad |\alpha_i|^2 + |\beta_i|^2 = 1$$
- **State Collapse / Observation:** A priority value is sampled: $p_i = \sin^2(\theta_i) + \epsilon \cdot \text{Uniform}(0, 0.05)$. Stops sorted by priority are partitioned into vehicle routes with warehouse break-genes.
- **Quantum Rotation Gate Update ($R(\Delta\theta)$):**
  $$\begin{bmatrix} \cos(\theta_i^{t+1}) \\ \sin(\theta_i^{t+1}) \end{bmatrix} = \begin{bmatrix} \cos(\Delta\theta_i) & -\sin(\Delta\theta_i) \\ \sin(\Delta\theta_i) & \cos(\Delta\theta_i) \end{bmatrix} \begin{bmatrix} \cos(\theta_i^t) \\ \sin(\theta_i^t) \end{bmatrix}$$
  $$\theta_i^{t+1} = \text{clip}\left(\theta_i^t + S(\alpha_i, \beta_i) \cdot \Delta\theta, 0, \frac{\pi}{2}\right)$$
  Where rotation step $\Delta\theta \in [0.01\pi, 0.05\pi]$ is steered toward the elite chromosome found so far.
- **SIMD Vectorization:** Trigonometric angle evaluations and coordinate clipping are vectorized in NumPy using C-contiguous arrays.

### 2.3 Continuous QPSO (Quantum-Behaved Particle Swarm Optimization)
In classical PSO, particles follow Newtonian trajectories with position $x$ and velocity $v$. In QPSO, particles move in a quantum $\delta$-potential well centered at local attractor $p_{i,j}$:
$$p_{i,j}^t = \phi \cdot pbest_{i,j}^t + (1 - \phi) \cdot gbest_j^t, \quad \phi \sim \text{Uniform}(0, 1)$$
The mean best position of the swarm ($mbest$) is calculated by vector averaging:
$$mbest(t) = \frac{1}{M} \sum_{i=1}^M pbest_i(t)$$
Particle position updates follow wave-function collapse:
$$x_{i,j}^{t+1} = p_{i,j}^t \pm \beta \cdot |mbest_j(t) - x_{i,j}^t| \cdot \ln\left(\frac{1}{u}\right), \quad u \sim \text{Uniform}(0, 1)$$
- **Contraction-Expansion Coefficient ($\beta$):** Dynamically decays from $\beta_{\max} = 1.0$ to $\beta_{\min} = 0.5$ over swarm iterations $t = 1 \dots T_{\max}$:
  $$\beta(t) = \beta_{\max} - \frac{t}{T_{\max}} (\beta_{\max} - \beta_{\min})$$
- **Monotonic Departure Arrival Timing:** Arrival time at stop $k$ with travel time $\Delta t_{k-1, k}$ and service dwell time $\tau_{dwell} = 5.0\text{ min}$:
  $$T_{arr}(k) = T_{arr}(k-1) + \tau_{dwell} + \Delta t_{k-1, k} \cdot c_{k-1, k}$$
  Where $c_{k-1, k} \ge 1.0$ is the dynamic traffic congestion multiplier.

### 2.4 Multi-Objective Cost & Business Preset Formulations
Global fitness evaluates a normalized convex combination of four distinct operational objectives:
$$F(R) = w_1 \cdot D_{norm} + w_2 \cdot T_{norm} + w_3 \cdot P_{cap} + w_4 \cdot P_{sla}$$
- **$D_{norm}$ (Distance):** Total route length in km normalized by fleet baseline.
- **$T_{norm}$ (Fuel & Congestion):** Energy consumed incorporating congestion multipliers $c_e = \frac{v_{free}}{v_{actual}}$.
- **$P_{cap}$ (Capacity Penalty):** Strict quadratic penalty for overloaded vehicles:
  $$P_{cap} = \sum_{k=1}^K \max\left(0, \frac{\text{Load}_k - \text{Cap}_k}{\text{Cap}_k}\right)^2 \times 1000$$
- **$P_{sla}$ (SLA Lateness Penalty):** Penalty for deliveries outside $[SLA_{start}, SLA_{deadline}]$:
  $$P_{sla} = \sum_{i=1}^N \left( \max(0, SLA_{start, i} - T_{arr, i}) \cdot 0.5 + \max(0, T_{arr, i} - SLA_{deadline, i}) \cdot 2.0 \right)$$

#### The 4 Business Presets:
| Preset Name | $w_1$ (Dist) | $w_2$ (Fuel/Congestion) | $w_3$ (Capacity) | $w_4$ (SLA Window) | Primary Operational Target |
|:---|:---:|:---:|:---:|:---:|:---|
| `balanced` | 0.25 | 0.25 | 0.25 | 0.25 | Default balanced operational trade-off |
| `min_distance` | 0.50 | 0.15 | 0.20 | 0.15 | Minimizes total route odometer km |
| `min_fuel` | 0.15 | 0.50 | 0.20 | 0.15 | Reroutes around jammed corridors |
| `prioritize_sla` | 0.15 | 0.15 | 0.20 | 0.50 | Eliminates late customer delivery penalties |

### 2.5 Infeasibility Bounce-Back Loop
When QPSO determines that a chromosome cannot achieve 100% SLA compliance due to temporal bottlenecks:
1. Feasibility failure is flagged and passed back to QGA.
2. The offending cluster's genetic temperature and mutation rate are boosted:
   $$\mu_{retry} = \mu_{base} + k \cdot 0.05, \quad G_{max} = G_{base} + k \cdot 20$$
3. Random seed is perturbed: $\text{seed}_{retry} = \text{seed} + k \times 100$.
4. If the retry cap (default: 3) is reached without full feasibility, **best-effort fallback** is applied, tagging unfulfilled constraints explicitly in metadata without dropping any parcels.

### 2.6 Three-Tier Live Dynamic Re-Optimization
When vehicles are executing deliveries on live roads:
- **Tier 1 (Delivered Event):** Continuous QPSO re-tune on remaining pending stops. Stop order is fixed; only departure velocity and remaining arrival times are updated (~12 ms).
- **Tier 2 (Failed Event):** Greedy nearest-neighbor re-insertion of the failed parcel into alternate vehicles within the same cluster, followed by a **2-Opt geometric path uncrossing heuristic** and QPSO feasibility check (~42 ms).
- **Tier 3 (Structural Escalation):** If no vehicle in the cluster can absorb the failed stop without capacity or SLA violation, structural Leiden re-partitioning and QGA re-solve are executed (~240 ms).

---

## 3. Technology Stack & Component Specifications

```
                                +-----------------------------------------------+
                                |              Browser User Agent               |
                                +-----------------------------------------------+
                                        |                               |
                   HTTP/REST (Port 5173)|            HTTP/REST (Port 5174)|
                   WebSocket /ws/fleet  |            WebSocket /ws/driver |
                                        v                               v
                        +-------------------------------+ +-------------------------------+
                        |   Admin Portal (React 19)     | |   Driver Portal (React 19)    |
                        |   - Leaflet Canvas Maps       | |   - Mobile Delivery Manifest  |
                        |   - SVG Analytics Dashboard   | |   - Real-time GPS Interpolator|
                        |   - Preset Selector & Dispatch| |   - Action Logger (Delivered) |
                        +-------------------------------+ +-------------------------------+
                                        \                               /
                                         \                             /
                                          v                           v
                                +-----------------------------------------------+
                                |         FastAPI REST & WebSocket Gateway      |
                                |         - Python 3.11+ / Uvicorn (Port 8000)  |
                                |         - JWT Auth & Role-Based Access        |
                                |         - ConnectionManager (Live Streaming)  |
                                +-----------------------------------------------+
                                        |               |               |
             +--------------------------+               |               +--------------------------+
             |                                          |                                          |
             v                                          v                                          v
+-----------------------------+        +-----------------------------+        +-----------------------------+
|   Database Layer (MongoDB)  |        |  Quantum Routing Pipeline   |        |  Traffic & Routing Engines  |
|  - mongo:7.0 (Port 27017)   |        |  - Leiden Community Detector|        |  - TomTom Live Flow API     |
|  - $jsonSchema Validation   |        |  - Vectorized QGA Engine    |        |  - cKDTree Spatial Index    |
|  - 5 Core Collections       |        |  - Vectorized QPSO Swarm    |        |  - Valhalla C++ Engine:8002 |
|  - Motor Async Driver       |        |  - 2-Opt Geometric Repair   |        |  - Simulated Fallback Curve |
+-----------------------------+        +-----------------------------+        +-----------------------------+
```

### Backend (Python 3.11+)
- **Framework:** FastAPI with Uvicorn async ASGI server.
- **Math & Algorithms:** NumPy (SIMD vectorization), SciPy (`scipy.spatial.cKDTree`), NetworkX, python-igraph (Leiden clustering).
- **Database Driver:** `motor` (AsyncIO driver for MongoDB 7.0) with `pydantic` v2 schema validation.
- **Routing Engine Client:** `httpx` async client communicating with local/containerized Valhalla C++ engine (`http://localhost:8002`) with in-memory graph fallback.
- **External Traffic:** TomTom Traffic Flow Segment API (`https://api.tomtom.com/traffic/services/4/flowSegmentData/...`).

### Frontend Admin Portal (Port 5173)
- **Framework:** React 19, Vite, React Router DOM.
- **Mapping:** Leaflet with HTML5 Canvas hardware acceleration (`preferCanvas: true`) and CARTO Dark Matter authenticated tile layer (`https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=...`) with Esri Dark Canvas fallback.
- **Icons & Visuals:** `lucide-react`, pure SVG mathematical charts (fuel curves, violation logs, SLA donut gauges).
- **Streaming:** Native WebSocket client connected to `/ws/fleet` with auto-reconnecting HTTP polling fallback.

### Frontend Driver Mobile Portal (Port 5174)
- **Framework:** React 19, Vite, responsive mobile layout (viewport max-width 480px optimized).
- **Features:** Stop sequence checklist, SLA countdown timers, one-click action logging (`Mark Delivered`, `Mark Failed` with modal reason selector), animated GPS position interpolator following real OSM road linestrings.
- **Streaming:** Native WebSocket client connected to `/ws/driver/{driver_id}`.

---

## 4. Complete Directory & File Manifest

```
/Users/sharwilhodgar/Desktop/Abraxas P2/
├── backend/
│   ├── app/
│   │   ├── auth/                     # Authentication & security
│   │   │   ├── __init__.py
│   │   │   ├── jwt.py                # JWT creation, decoding, token validation
│   │   │   └── rbac.py               # Role-based access control (Admin vs Driver)
│   │   ├── clustering/               # Territorial pre-clustering
│   │   │   ├── __init__.py
│   │   │   └── leiden.py             # NetworkX/igraph Leiden graph modularity partitioner
│   │   ├── costing/                  # Objective evaluation
│   │   │   ├── __init__.py
│   │   │   ├── cost_function.py      # Distance, fuel, capacity, SLA lateness formulation
│   │   │   ├── fitness.py            # Normalized global route fitness aggregator
│   │   │   └── presets.py            # Weights for balanced, min_dist, min_fuel, prioritize_sla
│   │   ├── graph/                    # Spatial Pune road graph
│   │   │   ├── __init__.py
│   │   │   └── loader.py             # OSMnx MultiDiGraph loader, cache manager, lat/lon distance
│   │   ├── models/                   # Pydantic schemas & MongoDB documents
│   │   │   ├── __init__.py
│   │   │   ├── delivery_event.py     # Event schema (DELIVERED, FAILED, ATTEMPTED)
│   │   │   ├── parcel.py             # Parcel schema (weight, address, SLA window, coordinates)
│   │   │   ├── routing_session.py    # Complete session optimization log, routes, fitness history
│   │   │   ├── vehicle.py            # Vehicle schema (capacity, driver assignment, telemetry)
│   │   │   └── warehouse.py          # Distribution hub schema (operating hours, coordinates)
│   │   ├── pipeline/                 # Hybrid engine orchestrators
│   │   │   ├── __init__.py
│   │   │   ├── local_repair.py       # Tier-2 nearest neighbor insertion + 2-Opt smoothing
│   │   │   ├── orchestrator.py       # Leiden -> QGA -> QPSO -> Bounce-back orchestrator
│   │   │   ├── retrigger.py          # Three-tier live event dispatcher
│   │   │   └── retune.py             # Tier-1 QPSO fast arrival time retuning
│   │   ├── qga/                      # Discrete Quantum Genetic Algorithm
│   │   │   ├── __init__.py
│   │   │   ├── chromosome.py         # Classical Chromosome, Gene, StopGene, BreakGene
│   │   │   ├── decoder.py            # Vehicle route decoding & capacity partitioning
│   │   │   ├── qubit_encoding.py     # QubitChromosome, rotation gates R(theta), observe()
│   │   │   └── run_qga.py            # Generational loop, elite retention, plateau termination
│   │   ├── qpso/                     # Continuous Quantum Particle Swarm Optimization
│   │   │   ├── __init__.py
│   │   │   ├── arrival_time.py       # Monotonic cumulative schedule timeline evaluator
│   │   │   ├── fitness.py            # Continuous SLA violation & lateness calculator
│   │   │   ├── particle.py           # QPSO Particle, delta-well update, mbest vectorizer
│   │   │   └── run_qpso.py           # Swarm execution loop, contraction-expansion beta decay
│   │   ├── routers/                  # FastAPI REST Endpoints
│   │   │   ├── __init__.py
│   │   │   ├── analytics.py          # SVG analytics, fuel efficiency, violations, trends
│   │   │   ├── auth.py               # /auth/login, /auth/me, /auth/token
│   │   │   ├── delivery_events.py    # POST /delivery-events, live stream audit
│   │   │   ├── driver.py             # GET /driver/manifest, action endpoints
│   │   │   ├── parcels.py            # CRUD /parcels with filtering & pagination
│   │   │   ├── routing_sessions.py   # POST /routing-sessions/run, /status, /assign
│   │   │   ├── traffic.py            # GET /traffic/status, POST /traffic/refresh
│   │   │   ├── vehicles.py           # CRUD /vehicles, GET /vehicles/positions
│   │   │   ├── warehouses.py         # CRUD /warehouses
│   │   │   └── websocket.py          # /ws/fleet and /ws/driver/{driver_id} streams
│   │   ├── routing/                  # High-Performance Routing
│   │   │   ├── __init__.py
│   │   │   └── valhalla.py           # Valhalla C++ engine client (/sources_to_targets, /route)
│   │   ├── simulation/               # Real-time Movement Engine
│   │   │   ├── __init__.py
│   │   │   ├── clock.py              # Accelerated simulation clock (1x to 60x ratio)
│   │   │   ├── interpolator.py       # Slerp & piecewise lat/lon path interpolator
│   │   │   └── runner.py             # Multi-vehicle position simulator
│   │   ├── traffic/                  # Live Traffic Subsystem
│   │   │   ├── __init__.py           # get_traffic_manager() singleton
│   │   │   ├── cache.py              # 120s TTL cache with cold start & fallback tracking
│   │   │   ├── fallback_curve.py     # Pune rush-hour time-of-day simulation curve
│   │   │   ├── propagate.py          # scipy.spatial.cKDTree O(|E| log |S|) spatial propagator
│   │   │   ├── refresh_loop.py       # Staggered 8 QPS background polling manager
│   │   │   └── tomtom_client.py      # TomTom Flow Segment API async client
│   │   ├── db.py                     # Motor client, $jsonSchema validator initializer, ping_db
│   │   └── main.py                   # FastAPI app, lifespan background tasks, CORS, routes
│   ├── data/
│   │   ├── pune_network_osm.graphml  # Full Pune metropolitan road network graph
│   │   └── representative_segments.json # 70 representative Pune arterial road corridors
│   ├── scripts/
│   │   ├── benchmark_scale.py        # 30-to-120 stop scale benchmark harness
│   │   ├── preflight_check.py        # Healthcheck script for DB, graph, APIs
│   │   └── seed_dev_data.py          # Idempotent parcel, hub, vehicle, & session seeder
│   ├── tests/                        # 119 automated pytest unit & integration tests
│   │   ├── test_valhalla_and_vectorization.py # Enterprise tests for Valhalla, cKDTree, 2-Opt, NumPy
│   │   └── ... (19 total test suites)
│   ├── Dockerfile                    # Python 3.11-slim container image definition
│   ├── pyproject.toml                # Dependencies & package build config
│   └── .env                          # Local credentials (TOMTOM_API_KEY, JWT_SECRET, MONGO_URI)
├── frontend-admin/                   # React 19 Admin Portal (Port 5173)
│   ├── src/
│   │   ├── api/client.js             # Centralized API fetch client with auth & error interceptors
│   │   ├── components/
│   │   │   ├── Navbar.jsx            # Top bar with live time, WebSocket badge, sign-out
│   │   │   ├── RouteMap.jsx          # Leaflet Canvas route visualization with animated polylines
│   │   │   └── Sidebar.jsx           # Nav menu (Fleet, Routes, Analytics, Traffic, Vehicles)
│   │   ├── pages/
│   │   │   ├── Analytics.jsx         # Fuel trend charts, SLA violation breakdown, gauges
│   │   │   ├── Diagnostics.jsx       # Live Traffic & Engine status, TomTom corridor speeds
│   │   │   ├── FleetOverview.jsx     # Live GPS tracking map with real-time van markers
│   │   │   ├── Layout.jsx            # Main app shell & router outlet
│   │   │   ├── Login.jsx             # Admin authentication screen
│   │   │   ├── RouteAssignment.jsx   # 4 Preset cards, 1-click optimization run & dispatch
│   │   │   └── VehiclesDrivers.jsx   # Fleet & driver CRUD management
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css                 # Premium dark-mode glassmorphic design system
│   ├── Dockerfile                    # Nginx multi-stage build container definition
│   └── .env                          # Frontend environment (VITE_API_BASE_URL, VITE_CARTO_API_KEY)
├── frontend-driver/                  # React 19 Driver Mobile Portal (Port 5174)
│   ├── src/
│   │   ├── api/client.js             # Driver API fetch client
│   │   ├── pages/
│   │   │   ├── DeliveryDetail.jsx    # Stop detail modal, notes, SLA window status
│   │   │   ├── LiveMap.jsx           # Turn-by-turn map with real road geometry & driver GPS
│   │   │   ├── Login.jsx             # Driver authentication screen
│   │   │   └── Manifest.jsx          # Interactive stop sequence, Mark Delivered / Failed
│   │   ├── App.jsx
│   │   └── index.css
│   ├── Dockerfile                    # Nginx multi-stage build container definition
│   └── .env                          # Driver frontend environment
├── docs/                             # Engineering documentation
│   ├── api_contract.md               # Full REST endpoint request/response specification
│   ├── demo_accounts.md              # Seed credentials for admin and driver logins
│   ├── deployment.md                 # Production deployment & containerization guide
│   ├── historical_seed_story.md      # 5-session improvement trajectory for demo analytics
│   ├── regression_report.md          # 119-test QA pass report
│   ├── scalability_evidence.md       # Empirical benchmark results across 30 to 120 stops
│   └── warehouse_locations.md        # Pune distribution hub coordinates & catchment zones
├── docker-compose.yml                # Multi-container stack (MongoDB, Valhalla, Backend, Frontends)
├── Development_Playbook.md           # Master phase-by-phase implementation record
├── Makefile                          # Developer CLI commands
└── README.md                         # Quickstart & architectural summary
```

---

## 5. API Contract & Communication Endpoints

### 5.1 Authentication (`/auth`)
- `POST /auth/login`: Authenticate with `{ username, password }`. Returns `{ access_token, token_type, role, user_id }`.
- `GET /auth/me`: Validates JWT Bearer token and returns authenticated user metadata.

### 5.2 Core Entities (`/warehouses`, `/parcels`, `/vehicles`)
- `GET /warehouses`: Returns all Pune distribution hubs (`Viman Nagar`, `Hadapsar`, `Hinjawadi`, `Swargate`).
- `GET /parcels?page=1&limit=50&status=pending`: Paginated parcels list.
- `POST /parcels`: Ingest new delivery stop with SLA deadlines and weight.
- `GET /vehicles`: Returns fleet list with driver assignments, capacities, and active route statuses.
- `GET /vehicles/positions`: High-frequency endpoint returning interpolated GPS coordinates (`lat`, `lon`, `speed_kmh`, `bearing`, `status`) for all active vehicles.

### 5.3 Routing & Quantum Optimization (`/routing-sessions`)
- `POST /routing-sessions/run`: Triggers full hybrid pipeline with payload:
  ```json
  {
    "preset": "balanced",
    "max_bounceback_retries": 3,
    "seed": 42,
    "async_run": false
  }
  ```
- `GET /routing-sessions/{session_id}/status`: Polling status endpoint returning `{ status, progress_percent, elapsed_seconds }`.
- `GET /routing-sessions/{session_id}`: Full result payload including cluster assignments, vehicle routes, polyline geometries, and SLA compliance metrics.
- `POST /routing-sessions/{session_id}/assign`: Commits session routes to vehicles and dispatches them to driver mobile manifests.

### 5.4 Driver & Delivery Actions (`/driver`, `/delivery-events`)
- `GET /driver/manifest`: Returns assigned stop sequence and customer addresses for the authenticated driver.
- `POST /delivery-events`: Logs delivery actions:
  ```json
  {
    "event_type": "DELIVERED",
    "parcel_id": "PCL-10492",
    "vehicle_id": "VAN-PUNE-03",
    "driver_id": "driver1",
    "timestamp_epoch": 1788789000,
    "failure_reason": null
  }
  ```
  Automatically triggers Tier-1 or Tier-2 live re-optimization in the background.

### 5.5 Live Traffic & Telemetry (`/traffic`, `/ws`)
- `GET /traffic/status`: Returns TomTom connectivity, active source (`live` vs `simulated_fallback`), cache age, and live speed measurements for 70 Pune arterial corridors.
- `POST /traffic/refresh`: Forces an immediate on-demand TomTom API refresh cycle.
- `WebSocket /ws/fleet`: Bi-directional stream broadcasting fleet coordinates to the Admin Portal every 1.5s.
- `WebSocket /ws/driver/{driver_id}`: Dedicated low-latency stream for active driver mobile telemetry.

---

## 6. MongoDB Database Schema & `$jsonSchema` Constraints

The database `logistics_db` uses strict schema validation applied idempotently on server startup:

1. **`warehouses`:**
   - Required: `warehouse_id` (string), `name` (string), `lat` (double), `lon` (double), `address` (string).
2. **`parcels`:**
   - Required: `address` (string), `lat` (double), `lon` (double), `weight_kg` (double > 0), `sla_start_min` (int $\ge 0$), `sla_deadline_min` (int $\le 1440$), `status` (`pending`, `assigned`, `in_transit`, `delivered`, `failed`).
3. **`vehicles`:**
   - Required: `label` (string), `capacity_kg` (double > 0), `status` (`idle`, `en_route`, `delivering`, `maintenance`).
4. **`routing_sessions`:**
   - Required: `preset` (`balanced`, `min_distance`, `min_fuel`, `prioritize_sla`), `status` (`pending`, `running`, `completed`, `failed`, `assigned`), `created_at` (date).
5. **`delivery_events`:**
   - Required: `parcel_id` (string), `vehicle_id` (string), `event_type` (`DELIVERED`, `FAILED`, `ATTEMPTED`), `timestamp` (date).

---

## 7. Active External API Credentials & Configuration

### 7.1 TomTom Live Traffic API
- **Active Key:** `DLn3hC3bv7T4JfDa7yUOhebWB0RVHFkT`
- **Config Location:** `backend/.env` under `TOMTOM_API_KEY`.
- **Verified Status:** Returning live Pune arterial flow speeds (e.g., Nagar Road: 30 km/h vs 38 km/h free flow, 1.27x congestion ratio).
- **Fallback Mechanism:** Built-in simulated rush-hour curve (`backend/app/traffic/fallback_curve.py`) activates seamlessly if key is missing or quota is exhausted.

### 7.2 CARTO Dark Matter Basemaps
- **Active Key:** `cb1_30dp_1_cc75fba3ffbcd1d1e9225d5e`
- **Config Location:** `frontend-admin/.env` and `frontend-driver/.env` under `VITE_CARTO_API_KEY`.
- **Verified Status:** Directly serving authenticated, watermark-free Dark Matter map tiles via:
  `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=cb1_30dp_1_cc75fba3ffbcd1d1e9225d5e`
- **Fallback Mechanism:** Automatic fallback to Esri World Dark Gray Canvas if no key is configured.

### 7.3 Default Demonstration Accounts
- **Admin Dispatcher:** Username: `admin` | Password: `admin123` (Access: `http://localhost:5173/`)
- **Fleet Driver 1:** Username: `driver1` | Password: `driver123` (Access: `http://localhost:5174/`)
- **Fleet Driver 2:** Username: `driver2` | Password: `driver123` (Access: `http://localhost:5174/`)

---

## 8. Verified Performance Benchmarks & Empirical Evidence

From empirical sweeps documented in `docs/scalability_evidence.md`:
- **Full Scale Optimization (120 stops, 20 vans, 4 hubs):** **336.92 ms** total execution time (< 3.0s demo ceiling).
- **Leiden Graph Modularity Pre-Clustering:** Scales sub-linearly from 3.56 ms (60 stops) to 8.81 ms (120 stops).
- **Initial Feasibility Rate:** Raised from **42.8%** (flat unclustered QGA) to **97.4%** (Leiden-partitioned QGA).
- **Three-Tier Re-Optimization Latency Hierarchy:**
  - *Tier 1 (Delivered):* **12.4 ms** (QPSO arrival time retune).
  - *Tier 2 (Failed):* **41.8 ms** (Local repair + 2-Opt geometric path smoothing).
  - *Tier 3 (Escalation):* **238.5 ms** (Structural re-clustering + full re-solve).
- **Automated Test Suite:** **119 / 119 tests passing (100% pass rate)** across 19 test modules in `backend/tests/`.
- **Linter Status:** 0 Ruff errors, 0 warnings across entire backend.

---

## 9. Developer CLI & Operational Commands

All primary actions are automated via the root `Makefile`:

```bash
# 1. Install dependencies & preflight check
cd backend && source .venv/bin/activate && pip install -e . && cd ..
make preflight-check

# 2. Seed development database (idempotent)
make seed-data

# 3. Run automated test suite (119 tests)
backend/.venv/bin/pytest backend/tests/ -v

# 4. Run linter
backend/.venv/bin/ruff check backend/app/ backend/scripts/ backend/tests/

# 5. Launch development services
# Terminal 1: Backend API
backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# Terminal 2: Admin Portal
cd frontend-admin && npm run dev -- --port 5173
# Terminal 3: Driver Portal
cd frontend-driver && npm run dev -- --port 5174

# 6. Containerized Deployment (Full Stack)
docker compose up --build -d
```

---

## 10. Summary of Most Recent Completed Updates

1. **Auto-Start TomTom Background Loop:** Registered `TrafficRefreshManager.start_loop()` in FastAPI's startup `lifespan` in `app/main.py`. The background worker polls TomTom every 120s staggered at 8 QPS, updating the in-memory cache continuously.
2. **Live Diagnostics Endpoint (`/traffic/status`):** Created `backend/app/routers/traffic.py` returning real-time connectivity, latency, and sample Pune arterial speeds. Wired directly into `frontend-admin/src/pages/Diagnostics.jsx` with an interactive "Poll Live API Now" button.
3. **Valhalla C++ Matrix & 2-Opt Smoothing Integration:** Embedded native C++ distance matrix lookups with automatic spatial graph fallback and integrated post-insertion 2-opt geometric route uncrossing into Tier-2 local repair.
4. **Hardware-Accelerated Canvas Basemaps:** Applied `preferCanvas: true` and configured the user's authenticated CARTO API key across all Leaflet maps.

---
*Context file generated autonomously on September 7, 2026. Certified ready for immediate handoff or cross-tool transfer.*
