# Applied Logistics Platform — Phase-Wise Development Playbook

**Source spec:** Project2_Finalized_Spec.md
**Engine:** QIGA (Quantum-inspired Genetic Algorithm) + QPSO hybrid, Leiden pre-clustering
**Stack:** React (admin + driver) · Python/FastAPI · MongoDB · Leaflet · OSMnx · TomTom Traffic API

---

## How to use this playbook

- Work top-to-bottom. A milestone's "Depends on" field lists hard prerequisites — do not start it until those are DONE.
- Every milestone ends in a **Git Checkpoint** — only push after all test cases and the verification checklist pass.
- Each Phase ends in a **Phase Completion Checkpoint** — this is a Go/No-Go gate before starting the next phase.
- Suggested branch model: `main` (always deployable) ← `develop` ← `feature/<phase>.<milestone>-<short-name>`. Merge to `develop` at each milestone checkpoint, merge to `main` at each phase checkpoint.

---

## Missing information I need from you (please confirm before/while building)

These are called out in spec §10 as "decide during build," but a few affect early scaffolding decisions, so flag your choices when you reach the relevant milestone (defaults noted so you're never blocked):

1. Exact warehouse coordinates in Pune (default: pick 3 real intersections you choose in Milestone 1.2).
2. Number/naming of driver demo accounts (default: 3 drivers, `driver1`/`driver2`/`driver3`).
3. Whether pre-generated sessions should show a deliberate improvement trend (default: yes, vary one constraint per session to tell a story).
4. Exact FastAPI endpoint list/schema (default: drafted in Milestone 6.1 after wireframes in Phase 7).
5. TomTom API key — you must obtain this yourself (free tier signup) before Phase 5.

I will not silently assume anything beyond these defaults; each is called out again at the relevant milestone.

---

# Phase 0 – Project Setup & Baseline

### Milestone 0.1 — Repository & Environment Scaffolding
**Depends on:** nothing (first milestone)

**2. Objective**
Establish a working monorepo (or two linked repos) with backend and frontend skeletons, environment separation, and a passing "hello world" for each, so every later milestone has a stable base to build on.

**3. Tasks to Complete**
- [ ] Create root repo `logistics-platform/` with `backend/`, `frontend-admin/`, `frontend-driver/` (or a single `frontend/` with two route trees — decide now, see guidance) and `docs/`.
- [ ] Initialize git, add `.gitignore` (Python + Node + OS + IDE + `.env*` + `*.graphml` cache files).
- [ ] Backend: Python 3.11+ virtualenv, `requirements.txt` with `fastapi`, `uvicorn`, `pymongo`, `python-dotenv`, `pydantic`.
- [ ] Backend: minimal FastAPI app with `GET /health` returning `{"status": "ok"}`.
- [ ] Frontend: `create-vite` React app(s) with a placeholder home route.
- [ ] Add root `README.md` describing repo layout and how to run each service.
- [ ] Add `.env.example` files (backend) listing required variables without values (`MONGO_URI`, `TOMTOM_API_KEY`, `JWT_SECRET` or similar).

**4. Files / Modules Affected**
`backend/app/main.py`, `backend/requirements.txt`, `backend/.env.example`, `frontend-admin/src/App.jsx`, `frontend-driver/src/App.jsx`, `.gitignore`, `README.md`

**5. Implementation Guidance**
- Two-frontend-app approach (admin/driver as separate Vite apps) is simpler to reason about for a hackathon timeline than one app with route-based role-splitting, and matches spec §5's "Two Interfaces" framing directly. If you'd rather have one app, that's a valid alternative — just be consistent through Phase 7/8.
- FastAPI chosen over Flask per spec §8 rationale (async support helps later with polling-heavy live-update endpoints in Phase 9).
- Do not add MongoDB connection code yet — that's Milestone 0.3.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-0.1-01 | Backend health check | Backend running locally | `curl http://localhost:8000/health` | Returns `200` with `{"status":"ok"}` | Pending |
| TC-0.1-02 | Admin frontend boots | `npm install` run in frontend-admin | `npm run dev`, open browser | Placeholder page renders, no console errors | Pending |
| TC-0.1-03 | Driver frontend boots | `npm install` run in frontend-driver | `npm run dev`, open browser | Placeholder page renders, no console errors | Pending |
| TC-0.1-04 | `.env` never tracked | `.env` created locally with dummy value | `git status` | `.env` does not appear as trackable file | Pending |
| TC-0.1-05 (negative) | Missing env var handled | `.env` absent | Start backend | App fails with a clear error message, not a silent crash/hang | Pending |

**7. Verification Checklist**
- [ ] `backend/app/main.py` runs with `uvicorn app.main:app --reload` without errors.
- [ ] Both frontend apps start on distinct ports without conflict.
- [ ] `.gitignore` verified to exclude `.env`, `node_modules/`, `__pycache__/`, `*.graphml`.
- [ ] README instructions followed exactly by a second run-through (self-check) and they work.

**8. Milestone Completion Criteria**
All test cases pass; both frontends and backend boot cleanly from a fresh clone using only README instructions.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 0.1: repo scaffolding, backend health check, frontend skeletons"
git push origin main
```
Do NOT commit: `.env`, `node_modules/`, Python `venv/`/`__pycache__/`, any `.graphml` cache files (none exist yet, but keep the rule in mind going forward).

**10. Rollback / Recovery**
This is the first commit — if something is broken, use `git reset --hard HEAD~1` locally before ever pushing further, or `git revert <commit-hash>` if already pushed and shared.

---

### Milestone 0.2 — CI Sanity & Code Quality Baseline
**Depends on:** 0.1

**2. Objective**
Add minimal automated checks (lint + basic test runner) so every future milestone's "tests pass" claim is machine-verifiable, not just manual.

**3. Tasks to Complete**
- [ ] Backend: add `pytest` to `requirements.txt`; create `backend/tests/test_health.py` testing `GET /health`.
- [ ] Backend: add `ruff` or `flake8` config for basic linting.
- [ ] Frontend: add `eslint` config (Vite default is fine) to both apps.
- [ ] Add a simple `Makefile` or `scripts/` folder with `run-backend`, `run-frontend-admin`, `run-frontend-driver`, `test-backend` shortcuts.
- [ ] (Optional but recommended) Add a GitHub Actions workflow `.github/workflows/ci.yml` running lint + pytest on push.

**4. Files / Modules Affected**
`backend/tests/test_health.py`, `backend/pyproject.toml` or `.flake8`, `.github/workflows/ci.yml`, `Makefile`

**5. Implementation Guidance**
GitHub Actions is optional given hackathon time pressure — if skipped, substitute a documented manual pre-push checklist in README ("run `make test-backend` and `make lint` before every push"). Don't over-invest here; the goal is a safety net, not enterprise CI.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-0.2-01 | pytest discovers and passes health test | 0.1 complete | `pytest backend/tests` | 1 test passes | Pending |
| TC-0.2-02 | Lint passes on clean code | Fresh scaffold | `ruff check backend/` | No errors | Pending |
| TC-0.2-03 (negative) | Lint catches an intentional error | Add unused import temporarily | Run linter | Error reported, then remove and re-verify clean | Pending |

**7. Verification Checklist**
- [ ] `pytest` runs green from repo root.
- [ ] Lint runs clean on both backend and frontend.
- [ ] Makefile/scripts documented in README.

**8. Milestone Completion Criteria**
All checks above pass locally (and in CI, if configured).

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 0.2: CI sanity checks, pytest + lint baseline"
git push origin main
```
Do NOT commit: CI secrets/tokens (none needed yet since no external services are called).

**10. Rollback / Recovery**
`git revert <commit-hash>` — this milestone touches only tooling, so reverting has no functional risk.

---

### Milestone 0.3 — MongoDB Connection & Core Schema Stubs
**Depends on:** 0.1

**2. Objective**
Stand up a MongoDB connection (local or Atlas) and create the five core collections from spec §7 with validated stub schemas, so all later backend work has a real data layer instead of mocks.

**3. Tasks to Complete**
- [ ] Choose MongoDB deployment: local `mongod` for dev, or free-tier Atlas cluster (recommended for team demo consistency).
- [ ] Add `MONGO_URI` to `.env.example` and real `.env` (never committed).
- [ ] Implement `backend/app/db.py` with a Motor or PyMongo client singleton.
- [ ] Define Pydantic models for `Warehouse`, `Parcel`, `Vehicle`, `RoutingSession`, `DeliveryEvent` matching spec §7 draft schema, using the canonical units from spec §3a (km, minutes, minutes-since-midnight — never store display strings like "2:00 PM").
- [ ] Add JSON Schema validators on each MongoDB collection (Mongo's `$jsonSchema` validation) enforcing required fields and types.
- [ ] Write a seed script `backend/scripts/seed_dev_data.py` inserting 1 dummy warehouse, 2 dummy parcels, 1 dummy vehicle — for connectivity testing only (not the real Pune data, that's Phase 1).

**4. Files / Modules Affected**
`backend/app/db.py`, `backend/app/models/warehouse.py`, `.../parcel.py`, `.../vehicle.py`, `.../routing_session.py`, `.../delivery_event.py`, `backend/scripts/seed_dev_data.py`

**5. Implementation Guidance**
- Use Motor (async) if FastAPI routes will be async throughout (recommended, since Phase 9 polling endpoints benefit from async I/O); otherwise PyMongo (sync) is simpler to reason about for a hackathon team unfamiliar with async — pick one and be consistent.
- Store all times as integers (minutes since midnight) and all distances as floats (km) per spec §3a — this is a hard rule enforced from day one to avoid the exact unit-mismatch bugs the spec explicitly calls out.
- `congestion_type` field on relevant models should be a string enum (`"multiplicative"` / `"additive"`) per spec §3b, not a boolean — leaves room for future modes.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-0.3-01 | DB connects successfully | `.env` has valid `MONGO_URI` | Start backend, call a `/health/db` endpoint | Returns `200`, confirms ping success | Pending |
| TC-0.3-02 | Seed script inserts records | Empty dev DB | Run `seed_dev_data.py` | 1 warehouse, 2 parcels, 1 vehicle present in DB | Pending |
| TC-0.3-03 | Schema validation rejects bad parcel | DB validators active | Insert parcel missing `sla_deadline_min` | Insert rejected with validation error | Pending |
| TC-0.3-04 (negative) | Wrong-type field rejected | DB validators active | Insert parcel with `weight_kg` as string | Insert rejected | Pending |
| TC-0.3-05 | Connection failure handled | `.env` has invalid `MONGO_URI` | Start backend | Clear startup error, not a silent hang or crash with stack trace only | Pending |
| TC-0.3-06 (integration) | Pydantic model round-trips to Mongo doc | Seed data present | Fetch parcel via Pydantic model, serialize, compare to raw doc | Fields match exactly, units unchanged | Pending |

**7. Verification Checklist**
- [ ] All 5 collections exist with `$jsonSchema` validators applied.
- [ ] Seed script is idempotent (re-running doesn't duplicate — either checks existence or drops+reseeds explicitly).
- [ ] `/health/db` endpoint confirms live connectivity.
- [ ] No time/distance field anywhere stores a display-formatted string.

**8. Milestone Completion Criteria**
DB connects, all 5 collections validated and seeded, all test cases pass, unit-standardization rule confirmed by code review (self-check against spec §3a table).

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 0.3: MongoDB connection, core collection schemas, dev seed script"
git push origin main
```
Do NOT commit: `.env` with real `MONGO_URI`, any Atlas credentials, seeded data dumps.

**10. Rollback / Recovery**
If schema validators are too strict and block later legitimate inserts, adjust validators in a new commit rather than dropping them — never disable validation silently. To roll back entirely: `git revert <commit-hash>` and drop/recreate the dev database from scratch (safe since it's dev-only seed data).

---

## Phase 0 Completion Checkpoint
- **Completed milestones:** 0.1, 0.2, 0.3
- **Tests passed:** All TC-0.1-*, TC-0.2-*, TC-0.3-* (16 total)
- **Known issues:** _(fill in during actual build — e.g. "Atlas free tier cold-start latency ~2s on first request")_
- **Git commit/hash:** _(record the hash of the 0.3 push)_
- **Overall phase verification:** Backend boots, both frontends boot, DB connected and schema-validated, CI/lint green.
- **Go/No-Go for Phase 1:** GO if all above hold; otherwise fix before proceeding — nothing in Phase 1 can be tested without this foundation.

---

# Phase 1 – Graph Construction & OSM Data Layer

### Milestone 1.1 — OSMnx Graph Fetch & Disk Caching
**Depends on:** 0.3

**2. Objective**
Build the Pune road network graph via OSMnx exactly per spec §1/§8, fetched once and cached to disk — never live-fetched during demo — establishing the foundational data structure every routing computation depends on.

**3. Tasks to Complete**
- [ ] Add `osmnx`, `networkx` to `requirements.txt`.
- [ ] Write `backend/scripts/build_graph.py`: calls `osmnx.graph_from_place("Pune, India", network_type='drive')`.
- [ ] Save graph via `ox.save_graphml()` to `backend/data/pune_graph.graphml` (gitignored — regenerable, not a source file).
- [ ] Write `backend/app/graph_loader.py`: loads cached graphml at backend startup; raises a clear error if cache file is missing (with instructions to run the build script) rather than silently trying to fetch live.
- [ ] Tag each edge with `distance_km` and `base_travel_time_min` (from OSM speed data, per spec §1) as a post-processing step after load.
- [ ] Add a placeholder `congestion_ratio` (default 1.0) and `congestion_type` (default `"multiplicative"`) to every edge — real values come in Phase 5.
- [ ] Document in README how/when to regenerate the cache (e.g. if Overpass data changes or graph area needs adjusting).

**4. Files / Modules Affected**
`backend/scripts/build_graph.py`, `backend/app/graph_loader.py`, `backend/data/pune_graph.graphml` (generated, gitignored), `requirements.txt`, `README.md`

**5. Implementation Guidance**
- This must be a one-time, explicit, developer-run script — not something that runs automatically on backend startup, per spec §8's resilience requirement ("never re-fetched live during the demo").
- `base_travel_time_min = distance_km / speed_kmh * 60`, using OSM speed limit tags where present, falling back to a reasonable per-road-type default (document your fallback table) where missing — OSM speed data is frequently incomplete.
- Keep the raw `.graphml` out of git (it's large and regenerable) but commit the build script itself, so any teammate can regenerate identically.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-1.1-01 | Graph builds successfully | Internet access, Overpass API reachable | Run `build_graph.py` | `.graphml` file created, non-empty | Pending |
| TC-1.1-02 | Graph loads from cache | `.graphml` exists | Start backend | Graph loaded into memory, node/edge counts logged | Pending |
| TC-1.1-03 (negative) | Missing cache handled | Delete `.graphml` | Start backend | Clear error message with regeneration instructions, no crash-with-traceback-only | Pending |
| TC-1.1-04 | Edge attributes present | Graph loaded | Sample 10 random edges | All have `distance_km`, `base_travel_time_min`, `congestion_ratio`, `congestion_type` | Pending |
| TC-1.1-05 (edge case) | Missing OSM speed data handled | Graph loaded | Find an edge with no `maxspeed` tag in raw OSM data | Fallback default applied, no `None`/`NaN` in `base_travel_time_min` | Pending |
| TC-1.1-06 | Graph connectivity sanity | Graph loaded | Check largest strongly-connected component size vs total nodes | Largest component covers the vast majority of nodes (flag if not — indicates a bad fetch) | Pending |

**7. Verification Checklist**
- [ ] `.graphml` cache exists and loads in under a few seconds at backend startup.
- [ ] No edge has `None`/`NaN` in `distance_km` or `base_travel_time_min`.
- [ ] Graph node/edge counts are sane for a city the size of Pune (sanity-check against OSMnx docs/examples, not an exact number).
- [ ] `.gitignore` confirmed to exclude `*.graphml`.

**8. Milestone Completion Criteria**
Graph builds once, caches correctly, loads reliably from cache, all edges carry required attributes with no missing/invalid values, all test cases pass.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 1.1: OSMnx graph build script, disk caching, edge attribute tagging"
git push origin main
```
Do NOT commit: `pune_graph.graphml` itself (large, regenerable, gitignored) — only the script that builds it.

**10. Rollback / Recovery**
If a bad graph build corrupts local dev state, simply delete `pune_graph.graphml` and rerun `build_graph.py` — it's a pure function of the OSM data, no manual state to restore. Code rollback: `git revert <commit-hash>`.

---

### Milestone 1.2 — Warehouse & Delivery Stop Seeding on the Real Graph
**Depends on:** 1.1, 0.3

**2. Objective**
Place 3–4 warehouses and generate/import 100–120 realistic delivery stop locations, each snapped to actual graph nodes, replacing the dummy dev seed data from Milestone 0.3 with the real problem instance.

**3. Tasks to Complete**
- [ ] **Decide and record** exact coordinates for 3–4 warehouses within Pune, spread across the demo region (per spec §9 — this is one of the "decide during build" items; document your chosen coordinates in `docs/warehouse_locations.md`).
- [ ] Write `backend/scripts/generate_stops.py`: generates 100–120 delivery points (either sampled from real Pune addresses/POIs, or randomly sampled graph nodes within city bounds — document which approach and why).
- [ ] Snap every warehouse and delivery point to its nearest graph node via `osmnx.distance.nearest_nodes`.
- [ ] Assign each parcel: random weight (within realistic range, e.g. 1–15 kg), a random SLA window (e.g. one of several 2-hour slots spanning the simulated day), `status="pending"`.
- [ ] Insert warehouses and parcels into MongoDB via the models from Milestone 0.3, replacing dev seed data (keep the dev seed script separate/renamed so it's not confused with real data).
- [ ] Add a sanity script `backend/scripts/validate_stops.py` confirming every stop node exists in the loaded graph and is reachable from at least one warehouse.

**4. Files / Modules Affected**
`backend/scripts/generate_stops.py`, `backend/scripts/validate_stops.py`, `docs/warehouse_locations.md`, MongoDB `warehouses`/`parcels` collections

**5. Implementation Guidance**
- Reachability matters more than randomness here — a delivery point with no path from any warehouse silently breaks every later milestone. Validate this explicitly, don't assume OSMnx graphs are always fully connected (they often have small disconnected components).
- SLA windows should be spread across the simulated day (not all clustered at once) to make later SLA-conflict testing (Phase 4) meaningful.
- Keep parcel generation seeded (`random.seed(...)`) so the "same" 100–120 stops can be regenerated deterministically for repeatable testing.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-1.2-01 | Warehouses seeded | Graph loaded | Run seeding script | 3–4 warehouse docs in DB, each with valid node ID | Pending |
| TC-1.2-02 | Parcels seeded | Warehouses seeded | Run stop generation | 100–120 parcel docs in DB, each with valid node ID, weight, SLA window | Pending |
| TC-1.2-03 | All stops reachable | Parcels seeded | Run `validate_stops.py` | Every parcel node reachable from at least one warehouse node via `networkx.has_path` | Pending |
| TC-1.2-04 (negative) | Unreachable stop rejected | Manually inject an isolated node as a parcel location | Run validator | Validator flags/rejects it, does not silently pass | Pending |
| TC-1.2-05 (edge case) | Boundary SLA windows | Parcels seeded | Inspect earliest/latest SLA windows | All windows fall within the simulated day's valid minute range (0–1439), no negative or >1439 values | Pending |
| TC-1.2-06 | Deterministic regeneration | Same seed used | Run generation script twice with same seed on a fresh DB | Identical stop set both times | Pending |

**7. Verification Checklist**
- [ ] 3–4 warehouses confirmed placed at real, spread-out Pune intersections.
- [ ] 100–120 parcels confirmed in DB, all fields populated, all in canonical units.
- [ ] Reachability validated for 100% of stops (or documented exceptions with justification).
- [ ] `docs/warehouse_locations.md` written and accurate.

**8. Milestone Completion Criteria**
Real problem instance (warehouses + parcels) fully seeded, validated reachable, deterministic, all test cases pass.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 1.2: warehouse placement, 100-120 delivery stop generation, reachability validation"
git push origin main
```
Do NOT commit: any personally-sensitive real address data if scraped from a real source; large raw POI datasets (keep generation scripts, not giant static files).

**10. Rollback / Recovery**
Since this is deterministic (seeded) generation, recovery is: drop `warehouses`/`parcels` collections and rerun the seeding scripts. Code-level: `git revert <commit-hash>`.

---

## Phase 1 Completion Checkpoint
- **Completed milestones:** 1.1, 1.2
- **Tests passed:** All TC-1.1-*, TC-1.2-* (12 total)
- **Known issues:** _(e.g. graph connectivity gaps in outer Pune, document any manually excluded regions)_
- **Git commit/hash:** _(record)_
- **Overall phase verification:** Graph cached and loads reliably; real warehouse/parcel data seeded and 100% reachability-validated.
- **Go/No-Go for Phase 2:** GO if reachability is fully validated — Phase 2/3 (QGA) cannot produce valid routes over unreachable stops.

---

# Phase 2 – Cost Function & Leiden Pre-Clustering

### Milestone 2.1 — Modular Cost Function (Physics + Normalization + Weighted Scoring)
**Depends on:** 1.1

**2. Objective**
Implement the three-layer cost function architecture from spec §3b exactly as specified — swappable congestion mode, normalization, and unit-safe weighted scoring — as a standalone, independently testable module used by both QGA and QPSO later.

**3. Tasks to Complete**
- [ ] Implement `backend/app/costing/physics.py`: `edge_travel_time(base_time_min, congestion_value, mode)` supporting `"multiplicative"` and `"additive"`, exactly per spec §3b.
- [ ] Implement `backend/app/costing/normalize.py`: `normalize(value, reference)`, plus a helper to compute a Dijkstra-baseline reference distance/time per route for use as the normalization reference.
- [ ] Implement `backend/app/costing/fitness.py`: the weighted scoring function `F = w1*norm_distance + w2*norm_time + w3*norm_congestion_exposure + w4*sla_soft_signal`.
- [ ] Implement the 4 business-priority presets from spec §9 ("Minimize Distance," "Minimize Cost/Fuel," "Prioritize SLA Compliance," "Balanced") as fixed `(w1,w2,w3,w4)` tuples summing to 1, stored in `backend/app/costing/presets.py`.
- [ ] Write unit tests proving unit-safety: feed deliberately mismatched-scale raw inputs and confirm normalization prevents one term from dominating purely due to units.
- [ ] Add a small benchmark script (per spec §3b's "recommended benchmark") comparing multiplicative vs additive congestion on a fixed test route — output a short markdown report to `docs/congestion_mode_benchmark.md`.

**4. Files / Modules Affected**
`backend/app/costing/physics.py`, `.../normalize.py`, `.../fitness.py`, `.../presets.py`, `backend/tests/test_costing.py`, `docs/congestion_mode_benchmark.md`

**5. Implementation Guidance**
- Keep this module pure/stateless (no DB or graph mutation) — it should take plain numbers/dicts in and return plain numbers out, so QGA (Phase 3) and QPSO (Phase 4) can both call it without coupling.
- The `sla_soft_signal` is a *secondary* soft signal only (per spec §3b's explicit clarification) — do not implement it as the hard SLA check; that belongs to QPSO in Phase 4.
- Preset weights should sum to 1 — validate this in code (assert or raise) so a future typo in a preset can't silently break the "genuinely comparable importance weights" property the spec relies on.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-2.1-01 | Multiplicative congestion | Module implemented | `edge_travel_time(10, 1.4, "multiplicative")` | Returns 14.0 | Pending |
| TC-2.1-02 | Additive congestion | Module implemented | `edge_travel_time(10, 8, "additive")` | Returns 18 | Pending |
| TC-2.1-03 (negative) | Invalid mode rejected | Module implemented | Call with `mode="unknown"` | Raises a clear `ValueError`, not silent fallback | Pending |
| TC-2.1-04 | Normalization scales correctly | Module implemented | `normalize(20, reference=10)` | Returns 2.0 | Pending |
| TC-2.1-05 (edge case) | Zero reference handled | Module implemented | `normalize(5, reference=0)` | Raises/handles gracefully (no `ZeroDivisionError` leaking as unhandled crash) | Pending |
| TC-2.1-06 | Preset weights sum to 1 | All 4 presets defined | Sum each preset's 4 weights | Each sums to 1.0 (±floating tolerance) | Pending |
| TC-2.1-07 | Fitness function unit-safety | Module implemented | Feed raw unnormalized vs normalized inputs, compare term dominance | Normalized version doesn't let raw-km term dwarf raw-penalty term purely from scale | Pending |
| TC-2.1-08 (integration) | End-to-end fitness on real edge | Graph loaded (Phase 1) | Pick real edge, compute full `F` with "Balanced" preset | Returns a finite float, no NaN/Inf | Pending |

**7. Verification Checklist**
- [ ] All three layers (physics/normalize/fitness) are independently unit-tested.
- [ ] Both congestion modes verified numerically correct.
- [ ] Presets validated to sum to 1.
- [ ] Benchmark report written comparing congestion modes.

**8. Milestone Completion Criteria**
All 8 test cases pass; benchmark report exists and is legible; module has zero DB/graph side effects (verified by code review).

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 2.1: modular cost function (physics/normalize/fitness), business-priority presets, congestion benchmark"
git push origin main
```
Do NOT commit: nothing sensitive here — standard exclusions apply.

**10. Rollback / Recovery**
Pure-function module — safe to `git revert <commit-hash>` with zero data-layer impact.

---

### Milestone 2.2 — Leiden Clustering Pre-Processing
**Depends on:** 1.2, 2.1

**2. Objective**
Implement the Leiden community-detection pre-clustering step from spec §3d, partitioning all active stops into geographically/network-coherent clusters before QGA runs on them — the core scalability mechanism for Deliverable #9.

**3. Tasks to Complete**
- [ ] Add `python-igraph` and `leidenalg` (or `networkx`-compatible equivalent) to `requirements.txt`.
- [ ] Implement `backend/app/clustering/leiden.py`: converts the relevant subgraph (warehouses + active parcel nodes + connecting paths) into an igraph structure and runs Leiden community detection.
- [ ] Decide and document the edge-weighting used for clustering (e.g. inverse distance) in `docs/leiden_design.md`.
- [ ] Return cluster assignments as `{parcel_id: cluster_id}`, plus per-cluster stop lists ready to hand to QGA.
- [ ] Handle degenerate cases: too few active stops for meaningful clustering (e.g. fewer than warehouse count) — fall back to a single cluster.
- [ ] Write a size-sweep benchmark script (per spec §3d "validated with a size-sweep in Project 1") measuring clustering time at increasing stop counts (e.g. 20, 50, 100, 120) — output to `docs/leiden_size_sweep.md`.

**4. Files / Modules Affected**
`backend/app/clustering/leiden.py`, `backend/tests/test_clustering.py`, `docs/leiden_design.md`, `docs/leiden_size_sweep.md`

**5. Implementation Guidance**
- Cluster on the *relevant* subgraph (stops + warehouses + shortest paths between them), not the entire city graph — clustering the full OSM graph is unnecessary overhead and dilutes the community structure that matters (delivery-relevant proximity).
- Keep cluster count non-deterministic-but-seedable: Leiden's resolution parameter affects cluster granularity — pick and document a resolution value that yields a reasonable number of clusters relative to 20–25 vehicles (e.g. roughly one cluster per few vehicles, not 1 giant cluster or 100 tiny ones).
- This step must be idempotent given the same input stop set and seed — Phase 9's escalation path (full QGA re-run) may re-invoke it.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-2.2-01 | Clusters produced for full stop set | 100-120 stops seeded (1.2) | Run Leiden clustering | Returns 2+ clusters, all stops assigned | Pending |
| TC-2.2-02 | Every stop assigned exactly once | Clustering run | Check cluster assignment map | No stop missing, no stop in 2 clusters | Pending |
| TC-2.2-03 (edge case) | Very few active stops | Simulate only 3 active parcels | Run clustering | Falls back to single cluster, doesn't crash | Pending |
| TC-2.2-04 (negative) | Empty stop set handled | Zero active parcels | Run clustering | Raises a clear, handled error/empty result, not an unhandled exception | Pending |
| TC-2.2-05 | Determinism | Fixed seed | Run twice on same stop set | Identical cluster assignments both times | Pending |
| TC-2.2-06 (integration) | Size-sweep completes | 1.1, 1.2 done | Run size-sweep script at 20/50/100/120 stops | Report generated, clustering time scales sub-quadratically (document actual curve) | Pending |

**7. Verification Checklist**
- [ ] All active stops covered by exactly one cluster in every test run.
- [ ] Degenerate small-input case verified handled gracefully.
- [ ] Size-sweep report produced and reviewed.
- [ ] `docs/leiden_design.md` documents the resolution parameter choice and rationale.

**8. Milestone Completion Criteria**
Clustering is correct (full coverage, no duplication), deterministic, handles edge cases, and size-sweep evidence exists supporting the scalability claim.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 2.2: Leiden pre-clustering, size-sweep benchmark, degenerate-case handling"
git push origin main
```
Do NOT commit: raw size-sweep timing logs if very large; keep only the summarized report.

**10. Rollback / Recovery**
`git revert <commit-hash>`. No persistent state — clustering is computed fresh from current DB contents each run.

---

## Phase 2 Completion Checkpoint
- **Completed milestones:** 2.1, 2.2
- **Tests passed:** All TC-2.1-*, TC-2.2-* (14 total)
- **Known issues:** _(fill in — e.g. resolution parameter needs re-tuning at very small stop counts)_
- **Git commit/hash:** _(record)_
- **Overall phase verification:** Cost function verified unit-safe and numerically correct; clustering verified complete, deterministic, and scalable.
- **Go/No-Go for Phase 3:** GO — QGA (Phase 3) directly consumes both the cost function and per-cluster stop lists.

---

# Phase 3 – QGA (Discrete/Combinatorial Layer)

### Milestone 3.1 — Chromosome Encoding & Decoding
**Depends on:** 2.2, 1.2

**2. Objective**
Implement the grouped-permutation chromosome representation (single permutation of stops split by break markers into per-vehicle, per-trip sub-routes) and its decoder, per spec §3d — the foundation every QGA operator in later milestones will act on.

**3. Tasks to Complete**
- [ ] Implement `backend/app/qga/chromosome.py`: chromosome = ordered list of stop IDs interleaved with break markers denoting vehicle/trip boundaries, plus a warehouse-selection encoding per stop (spec §3d "warehouse-selection dimension").
- [ ] Implement a random valid chromosome generator, operating **within a single Leiden cluster** (per spec §3d, QGA solves per-cluster sub-problems).
- [ ] Implement the decoder: converts a chromosome into a structured route object — `{vehicle_id: [{trip_number, warehouse_id, ordered_stops: [...]}]}`.
- [ ] Support multi-trip encoding (a vehicle can have 2+ trips within the same chromosome, per spec §3d "trip-chaining").
- [ ] Write validation logic confirming a decoded chromosome references only real, reachable stops within its cluster.

**4. Files / Modules Affected**
`backend/app/qga/chromosome.py`, `backend/app/qga/decoder.py`, `backend/tests/test_chromosome.py`

**5. Implementation Guidance**
- Keep the chromosome a flat, simple data structure (e.g. list of tuples) — over-engineering the representation early makes crossover/mutation (Milestone 3.2) harder to implement correctly.
- Warehouse assignment should be dynamic per spec §9 ("Parcel–warehouse assignment: Dynamic") — encode it as part of the chromosome (e.g. a warehouse tag on each break marker), not fixed beforehand.
- Decoder must be a pure function (chromosome + stop metadata in → structured routes out) so it's independently testable without running the full GA loop.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-3.1-01 | Random chromosome generates validly | Cluster of stops available | Generate random chromosome | All stops in cluster present exactly once | Pending |
| TC-3.1-02 | Decoder produces structured routes | Valid chromosome | Decode | Returns dict keyed by vehicle_id with ordered stop lists | Pending |
| TC-3.1-03 | Multi-trip encoding decodes correctly | Chromosome with 2 trips for one vehicle | Decode | Vehicle object has 2 trip entries, each independently ordered | Pending |
| TC-3.1-04 (negative) | Malformed chromosome rejected | Chromosome missing a stop ID | Decode | Validation raises a clear error, doesn't silently drop the stop | Pending |
| TC-3.1-05 (negative) | Duplicate stop in chromosome rejected | Chromosome with duplicate stop ID | Decode | Validation raises a clear error | Pending |
| TC-3.1-06 (edge case) | Single-stop cluster | Cluster with only 1 stop | Generate + decode | Produces a valid single-stop route, no crash | Pending |
| TC-3.1-07 | Warehouse tag round-trips | Chromosome with explicit warehouse assignment | Decode | Decoded route's warehouse matches encoded warehouse exactly | Pending |

**7. Verification Checklist**
- [ ] Every generated chromosome is a valid permutation of its cluster's stops (no missing/duplicate).
- [ ] Decoder output structure matches the documented schema exactly.
- [ ] Multi-trip and single-trip cases both verified.
- [ ] Malformed input handling verified (no silent corruption).

**8. Milestone Completion Criteria**
All 7 test cases pass; decoder is proven pure/side-effect-free by code review.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 3.1: grouped-permutation chromosome encoding, multi-trip decoder, warehouse-assignment encoding"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>` — no persistent state involved.

---

### Milestone 3.2 — Fitness Evaluation ($f_{QGA}$) with Soft Capacity Penalty
**Depends on:** 3.1, 2.1

**2. Objective**
Implement the QGA fitness function exactly per spec §3d: `f_QGA = w1·Σ(distance_i) + penalty(capacity violations) + penalty(load imbalance)`, using the Milestone 2.1 cost module for distance terms and a soft (not rejecting) capacity penalty per spec §2a.

**3. Tasks to Complete**
- [ ] Implement `backend/app/qga/fitness.py`: takes a decoded route structure, computes total distance per vehicle using Milestone 2.1's cost functions.
- [ ] Implement `capacity_penalty(vehicle_load, capacity_kg)`: a smoothly increasing penalty for overload (not a hard reject) per spec §2a/§2's "trade off a mild overload against a much better route" intent.
- [ ] Implement `load_imbalance_penalty(vehicle_loads)`: penalizes high variance in per-vehicle load across the fleet.
- [ ] Wire `w1` to come from the **fixed preset** selected for the session (per spec §9's circularity fix — `w1` is never free-tuned by QGA itself).
- [ ] Write tests proving overloaded-but-efficient routes are correctly penalized but not rejected outright.

**4. Files / Modules Affected**
`backend/app/qga/fitness.py`, `backend/tests/test_qga_fitness.py`

**5. Implementation Guidance**
- Penalty functions should be smooth/continuous (e.g. quadratic beyond capacity) rather than a step function — a step function creates a flat fitness landscape right at the capacity boundary, which hurts GA convergence.
- Do not let capacity penalty scale dominate the distance term unpredictably — use the same normalization approach as Milestone 2.1 so this fitness is also unit-safe.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-3.2-01 | Under-capacity route, zero penalty | Route with load < capacity | Compute fitness | `capacity_penalty` term is 0 | Pending |
| TC-3.2-02 | Over-capacity route penalized not rejected | Route with load > capacity | Compute fitness | Returns a finite, higher fitness value — not a rejection/exception | Pending |
| TC-3.2-03 | Penalty scales with overload severity | Two routes, overload by 5kg vs 50kg | Compute both fitnesses | 50kg-overload fitness is meaningfully worse than 5kg-overload | Pending |
| TC-3.2-04 | Load imbalance penalized | One route: all load on 1 vehicle; another: evenly split | Compute both fitnesses | Imbalanced route has worse fitness at equal total distance | Pending |
| TC-3.2-05 (negative) | Empty route handled | Vehicle with zero stops | Compute fitness | Returns 0 contribution, no division-by-zero crash | Pending |
| TC-3.2-06 | Preset weight correctly applied | Two different presets | Compute fitness for same route under both | `w1` term differs proportionally to preset value | Pending |

**7. Verification Checklist**
- [ ] Capacity penalty confirmed smooth (no fitness cliff at exact capacity boundary).
- [ ] Overload never causes rejection/exception — only penalty, per spec §2a.
- [ ] Load imbalance term verified to distinguish balanced vs unbalanced routes at equal distance.
- [ ] Preset weight wiring confirmed correct (no hardcoded `w1`).

**8. Milestone Completion Criteria**
All 6 test cases pass; fitness function proven consistent with spec §2a's "soft, not rejected" requirement.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 3.2: QGA fitness function with soft capacity + load-imbalance penalties"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

### Milestone 3.3 — Qubit Rotation-Gate Genetic Operators & GA Loop
**Depends on:** 3.2

**2. Objective**
Implement the quantum-inspired operators (qubit rotation-gate update mechanism for population evolution) plus standard GA loop machinery (selection, crossover, mutation, elitism, termination), producing a working QGA that converges toward minimizing $f_{QGA}$ on a real cluster.

**3. Tasks to Complete**
- [ ] Implement `backend/app/qga/qubit_encoding.py`: qubit-inspired probability amplitudes per stop-ordering decision, and the rotation-gate update rule that shifts amplitudes toward better-observed solutions.
- [ ] Implement observation/collapse: sampling a classical chromosome from qubit-state probabilities.
- [ ] Implement order-preserving crossover suitable for permutation chromosomes (e.g. order crossover / OX) adapted for the grouped-permutation structure.
- [ ] Implement mutation (e.g. swap/insertion mutation) respecting cluster and multi-trip boundaries.
- [ ] Implement elitism (carry best N chromosomes unchanged each generation) and a termination condition (max generations OR fitness-plateau detection).
- [ ] Implement `backend/app/qga/run_qga.py`: orchestrates the full loop per cluster, returns best chromosome + fitness history.
- [ ] Add convergence logging (best/avg fitness per generation) for later debugging/demo storytelling.

**4. Files / Modules Affected**
`backend/app/qga/qubit_encoding.py`, `backend/app/qga/operators.py`, `backend/app/qga/run_qga.py`, `backend/tests/test_qga_run.py`

**5. Implementation Guidance**
- Start with a small population size and generation count during development (e.g. 20 population, 50 generations) to keep iteration fast; tune upward once correctness is confirmed, and re-verify convergence at production scale before Phase 3's checkpoint.
- Keep the rotation-gate update rule's step size configurable — this is the parameter most likely to need tuning based on observed convergence behavior.
- Test on a small synthetic cluster (5–10 stops) first where the near-optimal answer is guessable/checkable by hand, before trusting behavior on full 100+ stop clusters.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-3.3-01 | GA improves fitness over generations | Small synthetic cluster | Run QGA, log fitness per generation | Best fitness is non-increasing across generations (monotonic improvement w/ elitism) | Pending |
| TC-3.3-02 | GA converges on trivial case | 2-stop, 1-vehicle synthetic case with obvious optimum | Run QGA | Final route matches the known-optimal ordering | Pending |
| TC-3.3-03 | Crossover preserves validity | Two parent chromosomes | Apply crossover | Offspring is a valid permutation (no duplicate/missing stops) | Pending |
| TC-3.3-04 | Mutation preserves validity | Valid chromosome | Apply mutation | Result remains a valid permutation | Pending |
| TC-3.3-05 (negative) | Degenerate population handled | Population size = 1 | Run QGA | Doesn't crash; degrades gracefully (documented minimum population size enforced) | Pending |
| TC-3.3-06 | Termination condition triggers | Fitness plateaus | Run QGA with plateau detection enabled | Loop terminates before max generations, logs reason | Pending |
| TC-3.3-07 (integration) | Full-scale cluster run completes | Real ~100-stop clustered data (Phase 2) | Run QGA on largest cluster | Completes within an acceptable time budget (document actual runtime), returns valid decoded routes | Pending |

**7. Verification Checklist**
- [ ] Fitness improvement curve confirmed non-increasing (best-so-far) across a real run.
- [ ] All operators verified to preserve chromosome validity 100% of the time across repeated random trials.
- [ ] Full-scale run timing measured and documented (this feeds the scalability claim).
- [ ] Trivial-case correctness confirmed.

**8. Milestone Completion Criteria**
All 7 test cases pass; a full-scale run on real clustered data produces valid, improving routes within a documented, acceptable runtime.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 3.3: qubit rotation-gate operators, crossover/mutation, full QGA loop with convergence logging"
git push origin main
```
Do NOT commit: large fitness-history logs from full-scale runs — summarize instead.

**10. Rollback / Recovery**
If convergence behavior regresses after a tuning change, `git revert <commit-hash>` to the last known-good operator parameters; keep a `docs/qga_tuning_log.md` noting parameter changes and their observed effect so regressions are diagnosable.

---

## Phase 3 Completion Checkpoint
- **Completed milestones:** 3.1, 3.2, 3.3
- **Tests passed:** All TC-3.1-*, TC-3.2-*, TC-3.3-* (20 total)
- **Known issues:** _(e.g. convergence time at max cluster size, rotation-gate step-size sensitivity)_
- **Git commit/hash:** _(record)_
- **Overall phase verification:** QGA produces valid, improving, decodable multi-trip routes with correctly soft-penalized capacity handling on real clustered data at full scale.
- **Go/No-Go for Phase 4:** GO — QPSO (Phase 4) requires QGA's fixed route structure as its starting input.

---

# Phase 4 – QPSO (Continuous Layer: Timing & Hard SLA Enforcement)

### Milestone 4.1 — Particle Encoding & Arrival-Time Simulation
**Depends on:** 3.3, 1.1

**2. Objective**
Implement QPSO particles representing per-vehicle departure-time offsets, and the simulation that turns a departure time + QGA's fixed route + graph congestion into actual predicted arrival times at each stop.

**3. Tasks to Complete**
- [ ] Implement `backend/app/qpso/particle.py`: particle position = vector of departure-time offsets, one per vehicle-trip (continuous, in minutes, per spec §3a).
- [ ] Implement `backend/app/qpso/arrival_simulator.py`: given a departure time + ordered route (from QGA decoder) + graph edge congestion, computes cumulative arrival time at each stop using Milestone 2.1's `edge_travel_time`.
- [ ] Implement velocity/position update using QPSO's quantum-behaved update rule (mean-best position attractor, per standard QPSO formulation) rather than classical PSO's velocity equation.
- [ ] Bound particle positions to a sane departure-time-of-day range (e.g. within warehouse operating hours).
- [ ] Write tests confirming arrival-time simulation is monotonic (later departure → later or equal arrival, holding congestion fixed).

**4. Files / Modules Affected**
`backend/app/qpso/particle.py`, `backend/app/qpso/arrival_simulator.py`, `backend/tests/test_qpso_particle.py`

**5. Implementation Guidance**
- Arrival simulation must reuse Milestone 2.1's cost module, not reimplement congestion math — keeps a single source of truth for the physics layer across QGA and QPSO.
- Bound departure times explicitly (don't let QPSO wander to physically nonsensical departure times like 3am unless warehouses genuinely operate then) — document the bound in code comments.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-4.1-01 | Arrival time computed correctly on simple route | Fixed 2-stop route, known congestion | Simulate | Arrival time matches hand-calculated expected value | Pending |
| TC-4.1-02 | Monotonicity holds | Fixed route/congestion | Simulate at departure T and T+30 | Arrival at T+30 >= arrival at T (shifted appropriately) | Pending |
| TC-4.1-03 (negative) | Out-of-bounds departure rejected/clamped | Particle position outside allowed range | Evaluate | Clamped to valid bound, not silently accepted as-is | Pending |
| TC-4.1-04 | Multi-stop cumulative arrival correct | 5-stop route | Simulate | Each stop's arrival = previous arrival + travel time of connecting edge | Pending |
| TC-4.1-05 (edge case) | Zero-length route | Vehicle with 1 stop only | Simulate | Arrival = departure (no travel segment), no crash | Pending |

**7. Verification Checklist**
- [ ] Arrival simulation matches hand-calculated values on a known test route.
- [ ] Monotonicity property verified.
- [ ] Departure-time bounds enforced and tested.

**8. Milestone Completion Criteria**
All 5 test cases pass; arrival simulator confirmed to reuse (not duplicate) the Phase 2 cost module.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 4.1: QPSO particle encoding, arrival-time simulation over congestion-tagged graph"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

### Milestone 4.2 — QPSO Fitness, Hard SLA Check, and Feasibility Flagging
**Depends on:** 4.1, 2.1

**2. Objective**
Implement the QPSO fitness function per spec §3d ($f_{QPSO} = \sum_i[\text{actual\_time}_i + w_4 \cdot \text{SLA\_penalty}_i]$), with SLA enforced as a genuine hard constraint — infeasible routes must be explicitly flagged back rather than silently penalized-and-accepted, matching spec §2a exactly.

**3. Tasks to Complete**
- [ ] Implement `backend/app/qpso/fitness.py`: computes total actual arrival time + `w4`-weighted SLA penalty across all vehicle-trips, using the fixed preset's `w4` (never free-tuned, per spec §9).
- [ ] Implement hard SLA feasibility check: for each stop, is `arrival_time` within `[sla_start, sla_end]`? If not for *any* stop after full particle-swarm optimization, mark that vehicle-trip as **infeasible** (distinct from merely "high penalty").
- [ ] Implement the feasibility-flagging return contract: QPSO returns `{feasible: bool, infeasible_routes: [...], per_vehicle_metrics: {...}}`, not just a fitness score.
- [ ] Implement the QPSO swarm loop: multiple particles, iterative update, convergence/termination condition.
- [ ] Write tests explicitly distinguishing "high SLA penalty but technically feasible" from "genuinely infeasible, no departure time works" — these must be different code paths.

**4. Files / Modules Affected**
`backend/app/qpso/fitness.py`, `backend/app/qpso/run_qpso.py`, `backend/tests/test_qpso_fitness.py`

**5. Implementation Guidance**
- This is the milestone where spec §2/§2a's hard-vs-soft distinction must be implemented precisely: capacity is soft (Phase 3), SLA is hard (this milestone) — do not accidentally reuse the same soft-penalty pattern here. A route with zero feasible departure time must return `feasible=False`, full stop.
- To determine "no feasible departure time exists," don't just check the single best particle — verify that even after full swarm convergence, no explored departure time satisfies the window (document your feasibility-declaration criterion, e.g. exhausting iterations without a satisfying particle, or an early analytical check that the route's minimum possible travel time already exceeds the SLA window).

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-4.2-01 | Feasible route found | Route with a workable SLA window | Run QPSO | Returns `feasible=True`, valid departure time, all stops within SLA | Pending |
| TC-4.2-02 | Infeasible route correctly flagged | Route where even minimum travel time exceeds SLA window | Run QPSO | Returns `feasible=False`, route listed in `infeasible_routes` | Pending |
| TC-4.2-03 (negative) | High-penalty-but-feasible not misflagged | Route just barely satisfiable | Run QPSO | Returns `feasible=True` (not incorrectly marked infeasible) | Pending |
| TC-4.2-04 | Fitness reflects `w4` from preset | Two different presets | Run QPSO on same route under both | SLA penalty term scales with preset's `w4` | Pending |
| TC-4.2-05 (edge case) | Multiple SLA windows on one vehicle-trip | Multi-stop route, each stop different window | Run QPSO | All stops checked independently; single violation still flags the trip | Pending |
| TC-4.2-06 (integration) | Full pipeline QGA→QPSO on real cluster | Phase 3 output available | Run QPSO on QGA's real output | Completes, returns feasible/infeasible breakdown consistent with manual spot-check of a few routes | Pending |

**7. Verification Checklist**
- [ ] Feasible vs infeasible distinction verified correct on constructed test cases in both directions.
- [ ] `w4` wiring confirmed to come from the fixed session preset.
- [ ] Full pipeline integration test passes on real data.
- [ ] No route is ever silently marked feasible when it structurally cannot meet its SLA.

**8. Milestone Completion Criteria**
All 6 test cases pass; feasibility flagging manually spot-checked against at least 3 real routes for correctness.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 4.2: QPSO fitness with hard SLA feasibility check and infeasibility flagging"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>` — if feasibility logic regresses, this is a correctness-critical milestone, so treat any post-push bug here as high priority to fix forward or revert immediately.

---

### Milestone 4.3 — QGA↔QPSO Feedback Loop (Infeasibility Bounce-Back)
**Depends on:** 4.2, 3.3

**2. Objective**
Wire the two stages together per spec §3d/§9: when QPSO finds a route infeasible, it bounces back to QGA for structural re-optimization (e.g. splitting an overloaded route) — and implement the best-effort fallback per spec §3d/§9 when even repeated re-optimization can't resolve it.

**3. Tasks to Complete**
- [ ] Implement `backend/app/pipeline/orchestrator.py`: runs QGA → QPSO, and on `infeasible_routes` non-empty, triggers a targeted QGA re-optimization pass restricted to the affected cluster/vehicle (not a full from-scratch rerun).
- [ ] Implement a bounce-back iteration cap (document the max retries) to prevent infinite QGA↔QPSO ping-pong.
- [ ] Implement the best-effort fallback per spec §3d/§9/§2a: after cap is reached, assign the parcel to the least-bad available route and flag the violation explicitly (a boolean/field on the route/parcel record — never silently drop or infinitely retry).
- [ ] Persist the full pipeline result (routes, metrics, feasibility flags, any fallback flags) to the `routing_sessions` collection per spec §7.
- [ ] Write an end-to-end test running the full loop on real seeded data (Phase 1) with at least one deliberately over-constrained parcel to force the fallback path.

**4. Files / Modules Affected**
`backend/app/pipeline/orchestrator.py`, `backend/tests/test_pipeline_e2e.py`, MongoDB `routing_sessions` collection

**5. Implementation Guidance**
- The bounce-back must be targeted, not a full-problem restart — re-run QGA only on the affected cluster (or affected vehicle's portion) to keep this fast, matching the spec's cost-tiering intent (this local retry is still cheaper than the full "Escalation" path used later in Phase 9's live-operation triggers).
- Document your chosen retry cap explicitly (e.g. 3 bounce-back cycles) — this is a design decision the spec leaves to you, so record and justify it in `docs/bounceback_policy.md`.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-4.3-01 | Feasible-from-start route needs no bounce-back | Normal problem instance | Run orchestrator | Completes in one QGA→QPSO pass, no bounce-back triggered | Pending |
| TC-4.3-02 | Infeasible route triggers bounce-back | Deliberately tight SLA on one parcel | Run orchestrator | QGA re-invoked on affected cluster, logged | Pending |
| TC-4.3-03 | Bounce-back resolves infeasibility | Moderately tight but solvable case | Run orchestrator | Final result shows `feasible=True` after 1+ bounce-back cycles | Pending |
| TC-4.3-04 (negative/edge) | Genuinely over-constrained parcel | Deliberately impossible SLA (e.g. window shorter than minimum travel time from any warehouse) | Run orchestrator | Retry cap reached, best-effort fallback applied, violation explicitly flagged in result | Pending |
| TC-4.3-05 | Retry cap enforced | Impossible case | Run orchestrator, count QGA invocations | Number of re-optimization attempts does not exceed documented cap | Pending |
| TC-4.3-06 (integration) | Full session persisted correctly | Orchestrator run completes | Query `routing_sessions` | Document contains routes, fitness, per-vehicle metrics, and any feasibility/fallback flags, all in canonical units | Pending |

**7. Verification Checklist**
- [ ] Bounce-back verified to trigger only on genuine infeasibility, not on merely high-penalty-but-feasible routes.
- [ ] Retry cap enforced and tested.
- [ ] Best-effort fallback confirmed to never silently drop a parcel.
- [ ] `routing_sessions` document schema matches spec §7 draft exactly.

**8. Milestone Completion Criteria**
All 6 test cases pass; a full pipeline run on real seeded data completes end-to-end and persists correctly, including at least one demonstrated fallback case.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 4.3: QGA-QPSO feedback loop, bounce-back retry cap, best-effort SLA fallback, session persistence"
git push origin main
```
Do NOT commit: full routing session dumps from test runs (keep DB-only, not as repo files).

**10. Rollback / Recovery**
Since this milestone writes to `routing_sessions`, if a bug causes bad data to be persisted, provide a small `backend/scripts/purge_test_sessions.py` to clean up test-run pollution before rollback. Code: `git revert <commit-hash>`.

---

## Phase 4 Completion Checkpoint
- **Completed milestones:** 4.1, 4.2, 4.3
- **Tests passed:** All TC-4.1-*, TC-4.2-*, TC-4.3-* (17 total)
- **Known issues:** _(e.g. bounce-back cap tuning, QPSO convergence speed at full particle count)_
- **Git commit/hash:** _(record)_
- **Overall phase verification:** Full QGA↔QPSO pipeline runs end-to-end on real data, correctly distinguishes feasible/infeasible/fallback cases, and persists results per spec §7 schema.
- **Go/No-Go for Phase 5:** GO — this is the core optimization engine; everything from here (live traffic, API, frontend) builds on top of a working pipeline. Do not proceed if any feasibility-flagging test is flaky.

---

# Phase 5 – Live Traffic Integration (TomTom)

### Milestone 5.1 — TomTom Client, Representative Segment Sampling & Propagation
**Depends on:** 1.1, 2.1

**2. Objective**
Implement the TomTom Flow Segment Data integration exactly per spec §3c: query ~60–80 representative arterial segments, propagate congestion to all other edges by nearest-neighbor + road-type similarity — never querying every edge live.

**3. Tasks to Complete**
- [ ] Obtain a TomTom API key (developer action — required before this milestone starts) and add `TOMTOM_API_KEY` to `.env` (never committed) and `.env.example` (placeholder only).
- [ ] Implement `backend/app/traffic/tomtom_client.py`: calls TomTom Flow Segment Data API for a given segment, proxied entirely through backend (per spec §8 — key never reaches frontend).
- [ ] Select and document 60–80 representative segments prioritizing roads actually used in warehouse-to-delivery routes (per spec §3c) — store as a fixed list in `backend/data/representative_segments.json`.
- [ ] Implement propagation: `backend/app/traffic/propagate.py` assigns every non-representative edge a `congestion_ratio` from its nearest representative segment (nearest-neighbor + road-class matching, no ML per spec §3c).
- [ ] Compute `congestion_ratio = freeFlowSpeed / currentSpeed` from TomTom response (multiplicative, per spec §3c point 6) and set `congestion_type="multiplicative"` on live-data edges.
- [ ] Write a budget-tracking test confirming request counts stay within TomTom's free-tier limits under the documented refresh cycle.

**4. Files / Modules Affected**
`backend/app/traffic/tomtom_client.py`, `.../propagate.py`, `backend/data/representative_segments.json`, `.env.example`, `backend/tests/test_traffic.py`

**5. Implementation Guidance**
- All TomTom calls must go through the backend proxy — verify no API key string ever appears in any frontend bundle or network request visible in browser devtools.
- Nearest-neighbor propagation: use graph-distance (not straight-line) to the nearest representative segment where feasible, falling back to straight-line distance if graph-distance computation is too slow for the demo's refresh cycle — document which you use and why.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-5.1-01 | TomTom client fetches live data | Valid API key, network access | Query one representative segment | Returns valid `currentSpeed`/`freeFlowSpeed`, `congestion_ratio` computed correctly | Pending |
| TC-5.1-02 (negative) | Invalid/missing API key handled | `.env` has bad key | Query segment | Clear error returned, not an unhandled exception | Pending |
| TC-5.1-03 | Propagation assigns all edges | 60-80 segments queried | Run propagation | Every graph edge has a `congestion_ratio` assigned | Pending |
| TC-5.1-04 (edge case) | Edge equidistant from two segments | Constructed test graph | Propagate | Deterministic tie-breaking rule applied consistently (document the rule) | Pending |
| TC-5.1-05 | Budget stays within free tier | Full refresh cycle simulated | Count requests over a simulated 30-min demo (per spec: 80×15=1200) | Total requests ≤ 2500/day cap, ≤10 QPS at any instant | Pending |
| TC-5.1-06 (security) | API key never exposed to frontend | Full stack running | Inspect frontend network tab/bundle for the key string | Key does not appear anywhere in frontend-visible code/requests | Pending |

**7. Verification Checklist**
- [ ] Representative segment list documented and covers major warehouse-to-delivery arterials.
- [ ] Propagation confirmed to cover 100% of graph edges.
- [ ] Budget math verified against actual staggered request timing (not just theoretical count).
- [ ] Key-exposure security check passed manually via browser devtools.

**8. Milestone Completion Criteria**
All 6 test cases pass; a manual security check confirms zero key exposure; budget math verified against real request logs from a test run.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 5.1: TomTom live traffic client, representative segment sampling, congestion propagation"
git push origin main
```
Do NOT commit: real `TOMTOM_API_KEY` value, any raw TomTom response dumps containing account-identifying info.

**10. Rollback / Recovery**
`git revert <commit-hash>`. If TomTom rate limits are hit accidentally during testing, wait for daily reset or use the fallback path (Milestone 5.2) — never work around limits by removing the staggering logic.

---

### Milestone 5.2 — Caching, Refresh Cycle, and Graceful Degradation Fallback
**Depends on:** 5.1

**2. Objective**
Implement the 120-second refresh cycle, per-segment caching with timestamps, and the simulated time-of-day fallback curve, so the demo degrades gracefully instead of visibly breaking if TomTom is unreachable or rate-limited — per spec §3c point 5.

**3. Tasks to Complete**
- [ ] Implement `backend/app/traffic/cache.py`: stores last successful `congestion_ratio` per segment with a timestamp (in-memory dict is sufficient for a single-demo-session scope, or a Mongo collection if persistence across restarts matters).
- [ ] Implement a background refresh loop (every 120 seconds) that re-queries all representative segments, staggered at ~8/sec per spec §3c point 4.
- [ ] On a failed/rate-limited request, serve the last cached value for that segment (with its age) instead of failing the whole cycle.
- [ ] Implement the simulated time-of-day congestion fallback curve, triggered when failures persist across multiple consecutive cycles (document your exact trigger threshold, e.g. 3 consecutive cycle failures).
- [ ] Add a status field (e.g. `traffic_source: "live" | "cached" | "simulated_fallback"`) surfaced somewhere queryable, so the admin UI (Phase 7) can later show data freshness/source.

**4. Files / Modules Affected**
`backend/app/traffic/cache.py`, `backend/app/traffic/refresh_loop.py`, `backend/app/traffic/fallback_curve.py`, `backend/tests/test_traffic_fallback.py`

**5. Implementation Guidance**
- The fallback curve should be a simple, pre-authored function of time-of-day (e.g. peaked congestion at typical rush hours) — not another live API call; it exists specifically to have zero external dependency when things go wrong.
- Make the "persistent failure" threshold and the refresh interval both configurable (env or constants file), so they can be tuned differently for dev testing (fast iteration) vs demo day (matching the spec's 120s/2500-request budget).

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-5.2-01 | Cache serves last good value on failure | Cache populated, then simulate API failure | Trigger refresh with mocked failure | Segment's `congestion_ratio` unchanged, `traffic_source="cached"` | Pending |
| TC-5.2-02 | Refresh cycle runs on schedule | Background loop started | Wait 2 cycles (or mock time) | Segments re-queried at ~120s intervals | Pending |
| TC-5.2-03 | Staggering respects QPS limit | Refresh cycle triggered | Monitor request timing | No more than ~10 requests/sec at any point | Pending |
| TC-5.2-04 (negative) | Persistent failure triggers fallback curve | Mock 3+ consecutive cycle failures | Trigger refresh cycles | System switches to `traffic_source="simulated_fallback"`, uses curve values | Pending |
| TC-5.2-05 | Recovery from fallback | Fallback active, then mock API recovery | Trigger refresh | System returns to `traffic_source="live"` on next successful cycle | Pending |
| TC-5.2-06 (edge case) | Cold start with no cache yet | Fresh backend start, first cycle not yet run | Query congestion before first refresh completes | Falls back to simulated curve (not `None`/crash) as an initial default | Pending |

**7. Verification Checklist**
- [ ] Cache-on-failure behavior verified with a mocked API failure.
- [ ] Fallback curve trigger threshold tested and documented.
- [ ] Recovery-from-fallback path tested.
- [ ] Cold-start (no cache yet) case handled without error.

**8. Milestone Completion Criteria**
All 6 test cases pass, including a simulated full TomTom outage scenario proving the system degrades gracefully end-to-end.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 5.2: traffic caching, 120s staggered refresh loop, simulated fallback curve for graceful degradation"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`. If the fallback curve itself produces unrealistic values during a real demo, this should be treated as a same-day fix-forward priority (it's the safety net — its own failure is high-impact).

---

## Phase 5 Completion Checkpoint
- **Completed milestones:** 5.1, 5.2
- **Tests passed:** All TC-5.1-*, TC-5.2-* (12 total)
- **Known issues:** _(e.g. propagation accuracy for segments far from any representative arterial)_
- **Git commit/hash:** _(record)_
- **Overall phase verification:** Live traffic data flows into the graph correctly, stays within API budget, and degrades gracefully under simulated failure — verified by explicit outage test.
- **Go/No-Go for Phase 6:** GO — API layer (Phase 6) will expose this live data to the frontend; verify the fallback path once more under real (not mocked) network conditions before proceeding if possible.

---

# Phase 6 – API Layer (FastAPI)

### Milestone 6.1 — API Contract Draft & Core CRUD Endpoints
**Depends on:** 4.3, 5.2, 0.3

**2. Objective**
Draft the full endpoint list/schema (spec §10 item) and implement core CRUD endpoints for warehouses, parcels, vehicles — the foundation the routing and live-update endpoints (later milestones) will sit alongside.

**3. Tasks to Complete**
- [ ] Write `docs/api_contract.md`: full endpoint list with request/response shapes for every planned route (CRUD + routing run + live position + delivery events) — draft now, refine once Phase 7 wireframes exist (per spec §10's recommendation), but don't block backend work waiting for pixel-perfect wireframes.
- [ ] Implement `GET/POST /warehouses`, `GET/POST /parcels`, `GET/POST/PATCH /vehicles` using Milestone 0.3's Pydantic models.
- [ ] Implement request validation (Pydantic) and consistent error response shape (`{"error": "...", "detail": "..."}`) across all endpoints.
- [ ] Implement pagination on list endpoints (parcels especially, given 100-120 records).
- [ ] Add CORS configuration allowing the two frontend origins.
- [ ] Add basic API-level tests using FastAPI's `TestClient`.

**4. Files / Modules Affected**
`backend/app/routers/warehouses.py`, `.../parcels.py`, `.../vehicles.py`, `backend/app/main.py` (router registration + CORS), `docs/api_contract.md`, `backend/tests/test_api_crud.py`

**5. Implementation Guidance**
- Keep response shapes in **display-ready but still-typed** form (e.g. minutes-since-midnight as an int field, with conversion to "2:00 PM" done client-side or via a separate formatting utility) — the spec is explicit that conversion happens "only at the API response layer / frontend," so decide clearly which side does the conversion and be consistent (recommend: backend returns canonical units, frontend formats for display, since Leaflet/React are naturally suited to formatting).
- CORS should be locked to known frontend origins (`localhost:5173`/`5174` in dev, actual deployed origins later) — not wildcard, even for a demo.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-6.1-01 | Create warehouse | Backend running | `POST /warehouses` with valid body | `201`, warehouse persisted, matches input | Pending |
| TC-6.1-02 | List parcels paginated | 100+ parcels seeded | `GET /parcels?page=1&limit=20` | Returns exactly 20 records, pagination metadata present | Pending |
| TC-6.1-03 (negative) | Invalid parcel payload rejected | Backend running | `POST /parcels` missing `sla_deadline_min` | `422` with clear validation error | Pending |
| TC-6.1-04 (negative) | Nonexistent resource | Backend running | `GET /vehicles/{fake_id}` | `404` with clear error body | Pending |
| TC-6.1-05 | Vehicle status update | Vehicle exists | `PATCH /vehicles/{id}` with new status | `200`, status updated, reflected on re-fetch | Pending |
| TC-6.1-06 (security/CORS) | Unknown origin blocked | Backend running | Request with disallowed `Origin` header | CORS blocks response as expected | Pending |
| TC-6.1-07 (integration) | Units remain canonical end-to-end | Parcel with known SLA window created | `GET /parcels/{id}` | `sla_deadline_min` returned as int minutes-since-midnight, not a formatted string | Pending |

**7. Verification Checklist**
- [ ] `docs/api_contract.md` covers every endpoint planned through Phase 9 (draft-level detail acceptable for not-yet-built ones).
- [ ] All CRUD endpoints tested via `TestClient`.
- [ ] CORS locked down and verified.
- [ ] Canonical-unit response verified end-to-end.

**8. Milestone Completion Criteria**
All 7 test cases pass; `docs/api_contract.md` exists and is complete enough to unblock Phase 7 frontend work.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 6.1: API contract draft, core CRUD endpoints for warehouses/parcels/vehicles, CORS"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

### Milestone 6.2 — Routing Run Endpoint (Pipeline Trigger + Preset Selection)
**Depends on:** 6.1, 4.3

**2. Objective**
Expose the full QGA↔QPSO pipeline (Phase 3/4) as a callable API endpoint, letting the admin trigger a routing run with a selected business-priority preset and receive back suggested routes/metrics — this is the "Route assignment screen" backend per spec §5.

**3. Tasks to Complete**
- [ ] Implement `POST /routing-sessions/run`: accepts `{preset: "balanced" | "min_distance" | ...}`, triggers `orchestrator.py` (Milestone 4.3) synchronously or as a background task (decide based on expected runtime from Phase 3/4 benchmarks).
- [ ] If runtime is long enough to need async handling, implement a job-status pattern: `POST` returns a `session_id` immediately, `GET /routing-sessions/{id}/status` polled for completion (this also sets useful precedent for Phase 9's polling-based live updates).
- [ ] Implement `GET /routing-sessions/{id}`: returns full route/metrics result once complete.
- [ ] Implement `POST /routing-sessions/{id}/assign`: admin confirms suggested routes, updates vehicle assignment status.
- [ ] Add tests covering both a fast-completing and (simulated) slow-completing run.

**4. Files / Modules Affected**
`backend/app/routers/routing_sessions.py`, `backend/tests/test_routing_endpoint.py`

**5. Implementation Guidance**
- Use FastAPI `BackgroundTasks` or a simple in-process task tracker if the pipeline takes more than ~2-3 seconds — polling UX (per spec §6, already the chosen live-update mechanism) fits naturally here too, keeping the whole system consistent on one update pattern rather than mixing sync-wait and polling arbitrarily.
- The preset name in the request must map exactly to Milestone 2.1's `presets.py` — validate against the known preset list, reject unknown preset names with a clear `422`.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-6.2-01 | Trigger routing run | Real seeded data present | `POST /routing-sessions/run {"preset":"balanced"}` | Returns session_id, eventually reaches completed status | Pending |
| TC-6.2-02 | Poll status until complete | Run triggered | Poll `GET /routing-sessions/{id}/status` | Status transitions pending → running → completed | Pending |
| TC-6.2-03 | Fetch completed result | Run completed | `GET /routing-sessions/{id}` | Returns routes, fitness, per-vehicle metrics matching orchestrator output | Pending |
| TC-6.2-04 (negative) | Invalid preset rejected | Backend running | `POST /routing-sessions/run {"preset":"invalid"}` | `422` with clear error | Pending |
| TC-6.2-05 (negative) | Fetch nonexistent session | Backend running | `GET /routing-sessions/{fake_id}` | `404` | Pending |
| TC-6.2-06 | Assign confirms routes | Run completed | `POST /routing-sessions/{id}/assign` | Vehicles updated to assigned/en-route status | Pending |
| TC-6.2-07 (integration) | Different presets produce different routes | Same data, two presets | Run both, compare | Route/fitness differ meaningfully between "min_distance" and "prioritize_sla" presets | Pending |

**7. Verification Checklist**
- [ ] Async/polling pattern verified functional under real pipeline runtime (not just mocked).
- [ ] Preset validation confirmed against actual `presets.py` list, not a hardcoded duplicate list.
- [ ] Session persistence (Milestone 4.3) confirmed queryable via this endpoint.

**8. Milestone Completion Criteria**
All 7 test cases pass; a real end-to-end run via this endpoint (not a mock) completes and is fetchable.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 6.2: routing run endpoint, session status polling, preset-driven pipeline trigger"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`. If a bad run pollutes `routing_sessions`, reuse the purge script from Milestone 4.3.

---

### Milestone 6.3 — Live Position, Delivery Events, and Auth Endpoints
**Depends on:** 6.2

**2. Objective**
Implement the remaining endpoints needed for Phase 7/8/9: simulated vehicle position polling, delivery status updates (delivered/failed), and the demo-grade role-based login per spec §5/§8.

**3. Tasks to Complete**
- [ ] Implement `GET /vehicles/{id}/position`: returns current simulated position (built on top of Phase 9's simulation, but stub with a placeholder/static response for now if Phase 9 isn't built yet — replace once it is).
- [ ] Implement `GET /vehicles/positions` (bulk, for admin fleet overview) — supports the "poll every few seconds" pattern from spec §6.
- [ ] Implement `POST /delivery-events`: records a delivered/failed status for a stop, links to `routing_sessions` per spec §7 schema.
- [ ] Implement simple demo-grade auth: `POST /auth/login` with hardcoded/seeded admin + driver accounts (per spec §5 "no real security — demo-only auth gate"), returning a simple token/session marker.
- [ ] Implement basic role-checking middleware: driver endpoints reject admin-only actions and vice versa (even though it's demo-grade, this should still be genuinely enforced, not cosmetic).
- [ ] **Decide and document** the driver account count/naming (spec §10 item — default: 3 accounts `driver1`/`driver2`/`driver3` if no other preference).

**4. Files / Modules Affected**
`backend/app/routers/vehicles.py` (extended), `backend/app/routers/delivery_events.py`, `backend/app/routers/auth.py`, `backend/app/auth/middleware.py`, `docs/demo_accounts.md`

**5. Implementation Guidance**
- "Demo-only auth" per spec §5 does not mean untested — it means simplified (e.g. no password hashing complexity required, a plain seeded credential table is fine), but role-enforcement itself should be real and tested, since a driver seeing another driver's data or admin controls would break the demo narrative.
- `POST /delivery-events` is the trigger point for Phase 9's re-optimization logic — design its response/side-effects now so Phase 9 has a clean hook (e.g. this endpoint can itself call into Phase 9's re-tune logic once built, or simply log the event for now and Phase 9 wires the reaction).

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-6.3-01 | Admin login succeeds | Seeded admin account | `POST /auth/login` with valid admin creds | `200`, token/session returned | Pending |
| TC-6.3-02 (negative) | Wrong password rejected | Seeded account | `POST /auth/login` with bad password | `401` | Pending |
| TC-6.3-03 (security) | Driver cannot access admin-only route | Driver logged in | Driver token calls an admin-only endpoint | `403` | Pending |
| TC-6.3-04 | Bulk vehicle positions returned | Vehicles exist | `GET /vehicles/positions` | Returns array with position for every active vehicle | Pending |
| TC-6.3-05 | Delivery event recorded | Vehicle + parcel exist | `POST /delivery-events {"status":"delivered",...}` | `201`, event linked to correct routing_session | Pending |
| TC-6.3-06 (negative) | Delivery event for nonexistent parcel | Backend running | `POST /delivery-events` with fake parcel_id | `404`/`422`, not silently accepted | Pending |
| TC-6.3-07 (edge case) | Driver views only own vehicle | Two drivers, two vehicles | Driver A polls position | Returns only Driver A's assigned vehicle, not fleet-wide | Pending |

**7. Verification Checklist**
- [ ] Role-based access control verified with both positive and negative tests.
- [ ] Driver data isolation confirmed (driver never sees another driver's assignment).
- [ ] Delivery event correctly linked to its routing session per spec §7.
- [ ] Demo account list documented.

**8. Milestone Completion Criteria**
All 7 test cases pass, including explicit security/isolation tests.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 6.3: live position endpoints, delivery event recording, demo-grade role-based auth"
git push origin main
```
Do NOT commit: real/seeded demo account passwords in plaintext in any committed doc beyond a clearly-marked demo-only credentials file (acceptable here since it's explicitly non-production, but still keep it out of `.env`-style secret files and clearly labeled).

**10. Rollback / Recovery**
`git revert <commit-hash>`. If auth middleware bug allows unauthorized access post-push, treat as urgent — revert immediately rather than fixing forward under time pressure.

---

## Phase 6 Completion Checkpoint
- **Completed milestones:** 6.1, 6.2, 6.3
- **Tests passed:** All TC-6.1-*, TC-6.2-*, TC-6.3-* (21 total)
- **Known issues:** _(e.g. routing run latency at full 120-stop scale, exact polling interval to tune in Phase 7/8)_
- **Git commit/hash:** _(record)_
- **Overall phase verification:** Full API surface for CRUD, routing execution, live position, delivery events, and auth is implemented, tested, and matches `docs/api_contract.md`.
- **Go/No-Go for Phase 7:** GO — frontend work can now proceed against a real, stable API contract.

---

# Phase 7 – Admin Web App (Frontend)

### Milestone 7.1 — Auth Gate, Layout Shell, and Fleet Overview Map
**Depends on:** 6.3, 1.2

**2. Objective**
Build the admin app's entry point: login screen, main layout/navigation, and the live fleet overview map (Leaflet) showing all vehicles across all warehouses, per spec §5A.

**3. Tasks to Complete**
- [ ] Implement login screen calling `POST /auth/login`; store session/token (e.g. in-memory context + sessionStorage, acceptable for demo-grade auth).
- [ ] Implement route guarding: unauthenticated users redirected to login.
- [ ] Implement main layout: nav sidebar/header with links to Fleet Overview, Route Assignment, Vehicles/Drivers, Analytics.
- [ ] Implement Fleet Overview screen: Leaflet map centered on Pune, markers for all warehouses and all vehicles, polling `GET /vehicles/positions` every few seconds per spec §6.
- [ ] Add basic marker styling distinguishing idle/en-route/delivering vehicle status.
- [ ] Add loading/error states for the polling call (network failure shouldn't blank the whole map).

**4. Files / Modules Affected**
`frontend-admin/src/pages/Login.jsx`, `.../Layout.jsx`, `.../FleetOverview.jsx`, `.../api/client.js`, `.../context/AuthContext.jsx`

**5. Implementation Guidance**
- Leaflet + React: use `react-leaflet` for idiomatic integration rather than raw Leaflet DOM manipulation inside React components.
- Poll interval should be a named constant (e.g. `POSITION_POLL_MS = 3000`) so it's easy to tune later against real backend load observed in Phase 6 testing.
- Keep the auth context simple — a token + role in React context is sufficient for demo-grade auth; don't over-build with refresh-token flows etc.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-7.1-01 | Login success redirects to dashboard | Backend running, admin seeded | Enter valid credentials, submit | Redirected to Fleet Overview | Pending |
| TC-7.1-02 (negative) | Login failure shows error | Backend running | Enter invalid credentials | Error message shown, no redirect | Pending |
| TC-7.1-03 (security) | Unauthenticated access blocked | Not logged in | Navigate directly to `/fleet-overview` URL | Redirected to login | Pending |
| TC-7.1-04 | Fleet map renders all vehicles | Vehicles seeded | Load Fleet Overview | All active vehicles shown as markers at correct coordinates | Pending |
| TC-7.1-05 | Polling updates positions | Vehicle position changes on backend (simulate) | Wait one poll interval | Marker position updates without full page reload | Pending |
| TC-7.1-06 (failure-handling) | Backend unreachable during polling | Backend stopped mid-session | Observe UI | Graceful error/stale-data indicator shown, not a blank/crashed page | Pending |

**7. Verification Checklist**
- [ ] Route guarding verified for all protected routes, not just Fleet Overview.
- [ ] Map renders correctly with real seeded warehouse/vehicle data.
- [ ] Polling confirmed to update UI without full reload.
- [ ] Network failure during polling handled gracefully.

**8. Milestone Completion Criteria**
All 6 test cases pass; manual walkthrough of login → fleet overview confirmed smooth.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 7.1: admin login, layout shell, fleet overview map with live polling"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

### Milestone 7.2 — Route Assignment Screen (Preset Selection, Run Trigger, Review, Assign)
**Depends on:** 7.1, 6.2

**2. Objective**
Build the core "run QPSO+QIGA, review suggested routes/metrics, assign to vehicles" screen per spec §5A — the primary demo-facing feature of the admin app.

**3. Tasks to Complete**
- [ ] Implement preset selector UI (4 business-priority presets as clearly-labeled buttons/cards, not raw sliders, per spec §9).
- [ ] Implement "Run Optimization" trigger calling `POST /routing-sessions/run`, with a progress/loading state polling `GET /routing-sessions/{id}/status`.
- [ ] Implement results review: per-vehicle route list, ordered stops, and metrics (distance/time/fuel/SLA outcome) rendered as a table/list plus route lines drawn on the Leaflet map.
- [ ] Visually distinguish feasible vs SLA-flagged/best-effort-fallback routes (per Milestone 4.3's flags) — this is important for demo credibility ("never silently dropped").
- [ ] Implement "Assign" action calling `POST /routing-sessions/{id}/assign`.
- [ ] Add empty/error states (no active parcels to route, pipeline failure, etc).

**4. Files / Modules Affected**
`frontend-admin/src/pages/RouteAssignment.jsx`, `.../components/PresetSelector.jsx`, `.../components/RouteResultsTable.jsx`, `.../components/RouteMap.jsx`

**5. Implementation Guidance**
- Route line rendering on Leaflet: draw each vehicle's route as a distinct-colored polyline using the actual graph edge geometry (not straight lines between stops) for visual accuracy, reusing node coordinates from the graph data already available via the API.
- The feasibility/fallback flag must be visually unmissable (e.g. a red badge on flagged routes) — this is a core spec requirement (§3d/§9: "violation clearly flagged in admin UI"), not a nice-to-have.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-7.2-01 | Run optimization end-to-end | Logged in, real data seeded | Select preset, click Run, wait | Results screen shows routes/metrics matching backend session data | Pending |
| TC-7.2-02 | Route lines render on map | Run completed | View results | Each vehicle's route drawn as a distinct polyline following real roads | Pending |
| TC-7.2-03 | Feasible routes shown normally | Run with all-feasible data | View results | No flags shown, all routes marked assignable | Pending |
| TC-7.2-04 (negative/edge) | Fallback route clearly flagged | Run with a deliberately over-constrained parcel (from Phase 4 test setup) | View results | Flagged route visually distinct, SLA violation explanation shown | Pending |
| TC-7.2-05 | Assign action updates vehicle status | Run completed | Click Assign | Vehicles show "en route"/assigned status; verified also via Fleet Overview screen (7.1) | Pending |
| TC-7.2-06 (failure-handling) | Pipeline run fails | Simulate backend error during run | Click Run | Clear error message shown, UI remains usable, retry possible | Pending |
| TC-7.2-07 | Different presets show different results | Same data | Run twice with different presets | Displayed routes/metrics visibly differ, consistent with backend TC-6.2-07 | Pending |

**7. Verification Checklist**
- [ ] End-to-end run→review→assign flow manually verified against real backend.
- [ ] Fallback/flagged-route visibility explicitly confirmed (screenshot for demo prep is a good idea here).
- [ ] Regression: Fleet Overview (7.1) correctly reflects assignments made here.

**8. Milestone Completion Criteria**
All 7 test cases pass; a full manual run-through from login to assignment works without errors on real seeded data.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 7.2: route assignment screen, preset selection, results review with flagged-route visibility, assign action"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

### Milestone 7.3 — Vehicle/Driver Management Screen
**Depends on:** 7.1, 6.1

**2. Objective**
Build the vehicle/driver list and management screen per spec §5A, letting the admin see and manage fleet composition and status.

**3. Tasks to Complete**
- [ ] Implement vehicle list table: ID, capacity, current status (idle/en route/delivering), assigned driver.
- [ ] Implement basic vehicle CRUD (add/edit vehicle) against `GET/POST/PATCH /vehicles`.
- [ ] Implement driver-to-vehicle assignment UI (simple dropdown/select, backed by seeded driver accounts from Milestone 6.3).
- [ ] Add filtering/sorting by status.
- [ ] Add regression check that this screen's status changes are reflected correctly on the Fleet Overview map (7.1).

**4. Files / Modules Affected**
`frontend-admin/src/pages/VehicleManagement.jsx`, `.../components/VehicleTable.jsx`

**5. Implementation Guidance**
Keep this screen simple relative to Route Assignment — spec scopes it as a management list, not a second optimization surface. Resist scope creep here to protect hackathon timeline.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-7.3-01 | Vehicle list loads | Vehicles seeded | Open screen | All vehicles listed with correct fields | Pending |
| TC-7.3-02 | Add new vehicle | Logged in as admin | Fill form, submit | New vehicle appears in list and in DB | Pending |
| TC-7.3-03 (negative) | Invalid vehicle form rejected | Form open | Submit with missing capacity | Client-side validation blocks submit with clear message | Pending |
| TC-7.3-04 | Driver assignment updates | Vehicle + driver exist | Assign driver via dropdown | Vehicle record updated, reflected on reload | Pending |
| TC-7.3-05 (regression) | Status change reflects on Fleet Overview | Vehicle status changed here | Navigate to Fleet Overview (7.1) | Marker status/styling matches updated status | Pending |

**7. Verification Checklist**
- [ ] CRUD verified against real backend, not mocked data.
- [ ] Cross-screen regression (7.1) explicitly checked.

**8. Milestone Completion Criteria**
All 5 test cases pass.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 7.3: vehicle/driver management screen with CRUD and cross-screen status consistency"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

## Phase 7 Completion Checkpoint
- **Completed milestones:** 7.1, 7.2, 7.3
- **Tests passed:** All TC-7.1-*, TC-7.2-*, TC-7.3-* (18 total) — analytics dashboard test cases come in Phase 10, deliberately deferred since it depends on seeded historical sessions.
- **Known issues:** _(e.g. polyline rendering performance at full 100+ stop scale)_
- **Git commit/hash:** _(record)_
- **Overall phase verification:** Admin app fully functional for login, fleet monitoring, route assignment, and vehicle management against the real backend.
- **Go/No-Go for Phase 8:** GO — Driver app (Phase 8) reuses the same auth/API patterns established here.

---

# Phase 8 – Driver Web App (Frontend)

### Milestone 8.1 — Driver Login, Assigned Route List, and Live Map
**Depends on:** 7.1 (shared patterns), 6.3

**2. Objective**
Build the driver-facing mobile-style view: login, assigned ordered stop list with SLA deadlines, and a live simulated-position map — per spec §5B.

**3. Tasks to Complete**
- [ ] Implement driver login (reuse the auth pattern from Milestone 7.1, adapted for driver role).
- [ ] Implement assigned route screen: ordered stop list for the logged-in driver's vehicle, each stop showing address/coords and SLA deadline (formatted human-readable at this layer, per spec §3a).
- [ ] Implement live map showing the driver's own simulated position along their route only (not fleet-wide) — enforced by the backend isolation from Milestone 6.3, verified here too.
- [ ] Mobile-first responsive layout (spec explicitly calls this a "mobile-style view").
- [ ] Add polling for position/route updates consistent with the admin app's interval.

**4. Files / Modules Affected**
`frontend-driver/src/pages/Login.jsx`, `.../AssignedRoute.jsx`, `.../LiveMap.jsx`

**5. Implementation Guidance**
Reuse as much of the admin app's API client/auth-context pattern as reasonable (via a shared package or simple copy-adapt, given hackathon time constraints a shared package may be overkill — copy-adapt is fine, just keep both in sync manually and note this in `docs/known_duplication.md`).

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-8.1-01 | Driver login succeeds | Seeded driver account | Login with valid creds | Redirected to Assigned Route screen | Pending |
| TC-8.1-02 | Assigned route displays correctly | Driver has an assigned vehicle with a route | Load screen | Ordered stops shown with SLA deadlines in human-readable form | Pending |
| TC-8.1-03 (security/isolation) | Driver sees only own route | Two drivers with different vehicles | Login as Driver A | Only Driver A's route/vehicle shown, never Driver B's | Pending |
| TC-8.1-04 | Live map shows own position | Assigned route active | Load Live Map | Marker shown at simulated position along assigned route | Pending |
| TC-8.1-05 (edge case) | No route assigned yet | Driver with no active assignment | Load screen | Clear "no route assigned" state, not blank/broken UI | Pending |
| TC-8.1-06 (responsive) | Mobile layout usable | Any state | View at narrow (mobile) viewport width | Layout remains usable, no horizontal scroll/overlap | Pending |

**7. Verification Checklist**
- [ ] Isolation (driver A never sees driver B's data) explicitly re-verified at the frontend layer, not just trusted from backend tests.
- [ ] Mobile responsiveness manually checked at common breakpoints.
- [ ] Empty-state (no assignment) verified.

**8. Milestone Completion Criteria**
All 6 test cases pass.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 8.1: driver login, assigned route list with SLA deadlines, live position map"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

### Milestone 8.2 — Delivery Status Updates (Delivered / Failed)
**Depends on:** 8.1, 6.3

**2. Objective**
Implement the driver's ability to mark a stop delivered or failed, feeding into `POST /delivery-events` — this is the trigger point for Phase 9's live re-optimization logic.

**3. Tasks to Complete**
- [ ] Implement per-stop action buttons ("Mark Delivered" / "Mark Failed") on the Assigned Route screen.
- [ ] Wire both actions to `POST /delivery-events`.
- [ ] Implement optimistic or confirmed UI update (stop marked visually complete/failed after the action).
- [ ] Implement confirmation dialog before marking "Failed" (irreversible in-session action, worth a confirm step).
- [ ] Add error handling if the event fails to record (network issue) — don't let the UI silently believe an unrecorded status.

**4. Files / Modules Affected**
`frontend-driver/src/components/StopActionButtons.jsx`, `.../AssignedRoute.jsx` (extended)

**5. Implementation Guidance**
This screen doesn't yet need to *react* to what happens on the backend after the event (that's Phase 9's re-optimization) — it just needs to reliably record the event and reflect it. Keep this milestone scoped to the recording/UI-feedback loop only.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-8.2-01 | Mark delivered succeeds | Active route with a pending stop | Click "Mark Delivered" | Stop shown as delivered, event recorded in backend | Pending |
| TC-8.2-02 | Mark failed succeeds (with confirmation) | Active route with a pending stop | Click "Mark Failed", confirm | Stop shown as failed, event recorded | Pending |
| TC-8.2-03 (negative) | Failed confirmation can be cancelled | Confirmation dialog open | Click Cancel | No event recorded, stop unchanged | Pending |
| TC-8.2-04 (failure-handling) | Network failure during event submission | Backend unreachable | Click "Mark Delivered" | Clear error shown, stop NOT shown as delivered until confirmed by backend | Pending |
| TC-8.2-05 (edge case) | Double-submission prevented | Stop already marked delivered | Click "Mark Delivered" again (e.g. double-tap) | Second submission blocked/no-op, no duplicate event | Pending |
| TC-8.2-06 (integration) | Event visible in admin analytics data source | Event recorded | Query `delivery_events` collection directly | Event present with correct stop/vehicle/session linkage | Pending |

**7. Verification Checklist**
- [ ] Optimistic UI never diverges from actual backend-confirmed state on failure.
- [ ] Double-submission explicitly tested and blocked.
- [ ] Event correctly linked in DB for later analytics consumption (Phase 10).

**8. Milestone Completion Criteria**
All 6 test cases pass.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 8.2: delivery status updates (delivered/failed) with confirmation and failure-safe UI state"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

## Phase 8 Completion Checkpoint
- **Completed milestones:** 8.1, 8.2
- **Tests passed:** All TC-8.1-*, TC-8.2-* (12 total)
- **Known issues:** _(e.g. shared-code duplication with admin app noted in `docs/known_duplication.md`)_
- **Git commit/hash:** _(record)_
- **Overall phase verification:** Driver app fully functional for login, route viewing, live position, and delivery status recording, with verified data isolation.
- **Go/No-Go for Phase 9:** GO — Phase 9 wires the reactive re-optimization logic behind the delivery events this phase now reliably produces.

---

# Phase 9 – Live Movement Simulation & Re-Optimization Triggers

### Milestone 9.1 — Accelerated-Clock Position Simulation Engine
**Depends on:** 4.3, 6.3

**2. Objective**
Implement the programmatic vehicle-position simulator per spec §6: interpolating position along a route's real graph geometry over an accelerated clock (e.g. 1 real minute ≈ 1 simulated hour), replacing the placeholder from Milestone 6.3.

**3. Tasks to Complete**
- [ ] Implement `backend/app/simulation/clock.py`: maintains simulated time, accelerated relative to wall-clock at a configurable ratio.
- [ ] Implement `backend/app/simulation/position_interpolator.py`: given a vehicle's assigned route (ordered graph nodes/edges) + departure time (from QPSO, Phase 4) + current simulated time, computes current lat/lon by interpolating along edge geometry at assumed average speed.
- [ ] Wire this into `GET /vehicles/{id}/position` and `GET /vehicles/positions` (replacing Milestone 6.3's placeholder).
- [ ] Handle vehicle state transitions: idle → en route → delivering (brief pause at each stop) → next leg, and completion of the full route/all trips.
- [ ] Handle multi-trip vehicles: after completing trip 1, vehicle "returns" to warehouse and begins trip 2 per its QGA-decided schedule (spec §3d/§9).

**4. Files / Modules Affected**
`backend/app/simulation/clock.py`, `.../position_interpolator.py`, `backend/app/routers/vehicles.py` (updated)

**5. Implementation Guidance**
- Keep the accelerated-clock ratio configurable (env var) — useful to slow it down during development/debugging and speed it up for the actual demo slot.
- Interpolation should follow actual edge geometry (OSMnx edges carry geometry/shape data) for visual realism on the Leaflet map, not straight lines between nodes.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-9.1-01 | Position interpolates correctly mid-edge | Vehicle assigned a route, simulated time mid-leg | Query position | Lat/lon falls correctly between the two edge endpoints, proportionally to elapsed time | Pending |
| TC-9.1-02 | Vehicle transitions idle→en route at departure time | Simulated time crosses departure time | Query status | Status changes from idle to en route | Pending |
| TC-9.1-03 | Multi-trip vehicle starts trip 2 after trip 1 | Vehicle with 2 trips, trip 1 complete in sim time | Query position/status | Vehicle shown departing on trip 2 per QGA schedule | Pending |
| TC-9.1-04 (edge case) | Route completion handled | Simulated time past final stop | Query status | Status = idle/complete, no crash on "no more edges" | Pending |
| TC-9.1-05 (edge case) | Clock acceleration ratio configurable | Different `.env` ratio values | Restart with different ratio | Simulated time advances proportionally differently as configured | Pending |
| TC-9.1-06 (integration) | Position visible on both admin and driver maps | Simulation running | Poll both `/vehicles/positions` and `/vehicles/{id}/position` | Same vehicle's position matches consistently across both endpoints | Pending |

**7. Verification Checklist**
- [ ] Interpolation verified against a hand-calculated expected position at a known simulated time.
- [ ] State transitions verified for single-trip and multi-trip vehicles.
- [ ] Consistency between bulk and single-vehicle position endpoints confirmed.

**8. Milestone Completion Criteria**
All 6 test cases pass; a manual visual check on the admin Fleet Overview map (Phase 7) confirms smooth, realistic-looking movement.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 9.1: accelerated-clock position simulation, multi-trip state transitions, real endpoint wiring"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

### Milestone 9.2 — "Delivered" Re-Tune and "Failed" Local Repair + Escalation
**Depends on:** 9.1, 4.3, 8.2

**2. Objective**
Implement the three live re-optimization tiers from spec §3d/§9 exactly: cheap QPSO re-tune on "delivered," local repair heuristic + QPSO re-tune on "failed," and full QGA re-run only as an escalation when no vehicle can absorb the failed parcel.

**3. Tasks to Complete**
- [ ] Implement `backend/app/pipeline/retune.py`: on a "delivered" event, re-run **only QPSO** (Phase 4) on that vehicle's remaining stops' timing — no structural (QGA) change, per spec.
- [ ] Implement `backend/app/pipeline/local_repair.py`: on a "failed" event, search existing routes for the nearest feasible insertion point for the unserved parcel (nearest-neighbor style heuristic, not a full re-optimization).
- [ ] After local repair, re-run QPSO re-tune (per spec) to re-validate timing/SLA feasibility of the modified route.
- [ ] Implement escalation logic: if local repair finds **no** feasible existing route to absorb the parcel, trigger a full QGA re-run (reusing Milestone 4.3's orchestrator) — this is the only path that reaches full re-solve.
- [ ] Wire `POST /delivery-events` (Milestone 6.3) to call the appropriate one of these three paths based on `status`.
- [ ] Add timing/cost logging distinguishing the three tiers, to support the "keeps frequent updates cheap" scalability claim with real evidence.

**4. Files / Modules Affected**
`backend/app/pipeline/retune.py`, `.../local_repair.py`, `backend/app/routers/delivery_events.py` (updated), `backend/tests/test_retrigger_pipeline.py`

**5. Implementation Guidance**
- This is the milestone that most directly proves the spec's central scalability claim — instrument it well (log elapsed time for each tier) so you can produce a comparison table/chart for demo/report purposes (e.g. "delivered re-tune: ~X ms, failed local repair: ~Y ms, full escalation: ~Z s").
- Local repair's "nearest feasible" search should reuse the QPSO hard-SLA-feasibility check (Milestone 4.2) to validate candidate insertion points — don't reimplement a separate feasibility check here.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-9.2-01 | Delivered triggers cheap re-tune only | Active route, one stop delivered | Mark stop delivered via API | Only QPSO re-run (verify via logs), no QGA invocation, remaining stops' timing updated | Pending |
| TC-9.2-02 | Failed triggers local repair | Active route, one stop fails, another vehicle has capacity/room | Mark stop failed | Parcel inserted into a different existing route; that route's QPSO re-tuned; original vehicle's route no longer includes it | Pending |
| TC-9.2-03 | Repaired route still meets SLA | Failed+repaired scenario | Check post-repair route | Inserted parcel's SLA window still satisfied per QPSO re-validation | Pending |
| TC-9.2-04 (negative/edge) | No feasible existing route triggers escalation | Failed event where all other vehicles are at capacity or SLA-incompatible | Mark stop failed | Full QGA re-run triggered (verify via logs), new structural solution produced | Pending |
| TC-9.2-05 | Escalation still resolves parcel or flags fallback | Escalation scenario | Observe final state | Parcel either successfully placed, or explicitly best-effort-flagged (never silently dropped, consistent with Milestone 4.3) | Pending |
| TC-9.2-06 (integration) | Tier cost ordering holds | All three tiers exercised | Compare logged timings | Delivered-retune < failed-repair < full-escalation, consistently | Pending |
| TC-9.2-07 (regression) | Delivered/failed still reflected correctly in driver/admin UI | Phase 7/8 apps running | Trigger each tier, observe both frontends | Route/status changes visible correctly in both apps without manual refresh (within one poll interval) | Pending |

**7. Verification Checklist**
- [ ] All three tiers independently verified to trigger the correct (and only the correct) underlying mechanism.
- [ ] Cost/timing ordering empirically confirmed, not just assumed.
- [ ] Fallback-flagging consistency with Milestone 4.3 reconfirmed at the escalation tier.
- [ ] Cross-frontend regression check passed.

**8. Milestone Completion Criteria**
All 7 test cases pass; a timing comparison table exists in `docs/reoptimization_cost_tiers.md` as evidence for the scalability claim.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 9.2: tiered re-optimization (delivered re-tune / failed local repair / escalation), cost-tier logging"
git push origin main
```
Do NOT commit: raw timing logs from many test runs — summarize into the docs report.

**10. Rollback / Recovery**
`git revert <commit-hash>`. This is a correctness-critical milestone (drives live demo behavior) — if a regression is found close to demo day, prefer reverting to the last known-good commit over debugging live.

---

## Phase 9 Completion Checkpoint
- **Completed milestones:** 9.1, 9.2
- **Tests passed:** All TC-9.1-*, TC-9.2-* (13 total)
- **Known issues:** _(e.g. local-repair heuristic quality at edge cases with very few vehicles having spare capacity)_
- **Git commit/hash:** _(record)_
- **Overall phase verification:** Full live-operation loop — simulated movement, delivered/failed handling, tiered re-optimization, escalation — verified end-to-end with real timing evidence.
- **Go/No-Go for Phase 10:** GO — this is the last core-functionality phase; analytics (Phase 10) is a read-layer on top of data this phase now reliably produces.

---

# Phase 10 – Analytics Dashboard & Historical Data

### Milestone 10.1 — Pre-Generated Historical Sessions (Seed Data for Demo)
**Depends on:** 4.3, 9.2

**2. Objective**
Seed 3–5 historical routing sessions before demo day per spec §9, so the analytics dashboard has real trend data to show rather than an empty/single-session view.

**3. Tasks to Complete**
- [ ] Write `backend/scripts/seed_historical_sessions.py`: runs the full pipeline (Phase 3/4/9 orchestrator) 3–5 times with varied inputs/constraints/timestamps (spread across simulated past days).
- [ ] **Decide and document**: should sessions show a deliberate improvement trend (spec §10 optional item)? Default: yes — vary one constraint-tuning parameter deliberately across the 3–5 sessions to create a visible improving trend for demo storytelling; document exactly what you varied and why in `docs/historical_seed_story.md`.
- [ ] Ensure each seeded session also produces plausible `delivery_events` (mix of on-time/late/failed outcomes) so SLA-compliance analytics has real variance to show.
- [ ] Verify seeded sessions are clearly distinguishable from live demo-day sessions (e.g. a `seeded: true` flag or distinct timestamp range) so demo-day data doesn't get confused with backstory data.

**4. Files / Modules Affected**
`backend/scripts/seed_historical_sessions.py`, `docs/historical_seed_story.md`, MongoDB `routing_sessions`/`delivery_events` collections

**5. Implementation Guidance**
This script should be safely re-runnable on a fresh DB (idempotent via a clear/reseed pattern) since you'll likely re-run it multiple times while tuning the "story" the trend tells.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-10.1-01 | 3-5 sessions created | Fresh/reset DB | Run seed script | Exactly the intended count of `routing_sessions` documents present | Pending |
| TC-10.1-02 | Sessions have varied metrics | Sessions seeded | Inspect fitness/SLA-compliance across sessions | Values differ meaningfully across sessions (not identical copies) | Pending |
| TC-10.1-03 | Delivery events present per session | Sessions seeded | Query `delivery_events` linked to each session | Each session has associated events with mixed outcomes | Pending |
| TC-10.1-04 | Seeded sessions flagged distinctly | Sessions seeded | Query sessions | All carry `seeded: true` or equivalent marker | Pending |
| TC-10.1-05 (edge case) | Re-running script on existing seeded data | Sessions already seeded | Run script again | Either safely no-ops or cleanly replaces (documented behavior, no duplicate pollution) | Pending |

**7. Verification Checklist**
- [ ] Trend story documented and matches what's actually visible in the data.
- [ ] No confusion possible between seeded and live sessions (verified by the flag/timestamp check).
- [ ] Script confirmed idempotent.

**8. Milestone Completion Criteria**
All 5 test cases pass; `docs/historical_seed_story.md` clearly explains the demo narrative these sessions support.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 10.1: pre-generated historical routing sessions with documented demo trend story"
git push origin main
```
Do NOT commit: the actual seeded session data dump as a repo file — keep it DB-only, generated by the script.

**10. Rollback / Recovery**
Drop and re-seed `routing_sessions`/`delivery_events` (safe, since this is script-generated data). Code: `git revert <commit-hash>`.

---

### Milestone 10.2 — Analytics API Endpoints (Aggregations)
**Depends on:** 10.1, 6.1

**2. Objective**
Implement backend aggregation endpoints for the four analytics categories from spec §7: fuel efficiency trends, SLA compliance %, constraint-violation history, per-vehicle/per-route performance stats.

**3. Tasks to Complete**
- [ ] Implement `GET /analytics/fuel-efficiency`: time-series of fuel/cost metric across sessions.
- [ ] Implement `GET /analytics/sla-compliance`: overall % and per-vehicle/per-route breakdown, using `delivery_events` linked to `routing_sessions`.
- [ ] Implement `GET /analytics/violations`: capacity-overrun and SLA-miss history over time.
- [ ] Implement `GET /analytics/vehicle-performance`: historical stats per vehicle/route.
- [ ] Use MongoDB aggregation pipelines (not application-level looping over all documents) for performance, given growing session counts.
- [ ] Add tests validating aggregation correctness against the known seeded data from Milestone 10.1 (hand-computed expected values).

**4. Files / Modules Affected**
`backend/app/routers/analytics.py`, `backend/tests/test_analytics.py`

**5. Implementation Guidance**
Since exact expected values are computable from Milestone 10.1's seed script (you control the seed), write tests that assert against precisely known values, not just "returns something non-null" — this is one of the few milestones where exact-value testing is both possible and worthwhile.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-10.2-01 | Fuel efficiency trend returned | Sessions seeded | `GET /analytics/fuel-efficiency` | Returns time-series matching hand-computed values from seed data | Pending |
| TC-10.2-02 | SLA compliance % correct | Sessions + events seeded | `GET /analytics/sla-compliance` | Overall % matches (on-time events / total events) from seed data | Pending |
| TC-10.2-03 | Per-vehicle breakdown correct | Sessions seeded | `GET /analytics/sla-compliance?groupBy=vehicle` | Per-vehicle values sum/match correctly against raw event counts | Pending |
| TC-10.2-04 | Violation history correct | Sessions with known capacity overruns (from Phase 3 test data) | `GET /analytics/violations` | Reported violations match seeded/known overrun instances | Pending |
| TC-10.2-05 (edge case) | No sessions yet | Fresh empty DB | `GET /analytics/fuel-efficiency` | Returns empty series gracefully, not an error | Pending |
| TC-10.2-06 (performance) | Aggregation performs adequately | Full seeded + demo-day session volume | Time the endpoint response | Returns within an acceptable latency for live dashboard use (document actual ms) | Pending |

**7. Verification Checklist**
- [ ] All four aggregation endpoints verified against hand-computed expected values.
- [ ] Empty-state handled gracefully.
- [ ] Aggregation performance measured and documented.

**8. Milestone Completion Criteria**
All 6 test cases pass with exact-value verification against known seed data.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 10.2: analytics aggregation endpoints for fuel/SLA/violations/vehicle-performance"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

### Milestone 10.3 — Analytics Dashboard UI
**Depends on:** 10.2, 7.1

**2. Objective**
Build the admin analytics dashboard screen per spec §5A/§7, visualizing all four metric categories to support the "betterment of future routing" demo narrative.

**3. Tasks to Complete**
- [ ] Add "Analytics" nav item to the admin layout (Milestone 7.1).
- [ ] Implement fuel-efficiency trend chart (line chart over sessions/time).
- [ ] Implement SLA compliance % display (overall + per-vehicle/route breakdown, e.g. bar chart or table).
- [ ] Implement constraint-violation history view (timeline or table).
- [ ] Implement per-vehicle/per-route historical stats table.
- [ ] Add date-range or session-range filtering if time allows (nice-to-have, not blocking).
- [ ] Add loading/empty states consistent with the rest of the app.

**4. Files / Modules Affected**
`frontend-admin/src/pages/Analytics.jsx`, `.../components/FuelTrendChart.jsx`, `.../components/SlaComplianceView.jsx`, `.../components/ViolationHistory.jsx`, `.../components/VehiclePerformanceTable.jsx`

**5. Implementation Guidance**
Use a lightweight charting library (e.g. Recharts) already common in the React ecosystem — no need to hand-roll SVG charts under hackathon time pressure. Keep visual styling consistent with the rest of the admin app (reuse Milestone 7.1's layout shell/design tokens).

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-10.3-01 | Dashboard loads all four sections | Seeded historical data (10.1) present | Navigate to Analytics | All four visualizations render with real data, matching backend values | Pending |
| TC-10.3-02 | Fuel trend chart reflects seeded story | Deliberate trend seeded (10.1) | View chart | Trend direction visually matches the documented story in `docs/historical_seed_story.md` | Pending |
| TC-10.3-03 (edge case) | Empty state before any sessions | Fresh DB, no seed run yet | View Analytics | Clear empty/"no data yet" state, no broken charts | Pending |
| TC-10.3-04 | Per-vehicle table accurate | Seeded data | Compare table values to `GET /analytics/vehicle-performance` response | Values match exactly | Pending |
| TC-10.3-05 (regression) | Nav/layout still consistent | 7.1 layout in place | Navigate across all admin screens | Analytics fits the shell without breaking other screens' nav state | Pending |

**7. Verification Checklist**
- [ ] Every chart/table cross-checked against raw API response for at least one data point.
- [ ] Empty state verified.
- [ ] Demo narrative (trend story) visually confirmed legible to someone unfamiliar with the underlying data.

**8. Milestone Completion Criteria**
All 5 test cases pass; a non-technical walkthrough of the dashboard clearly tells the "improving routing over time" story.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 10.3: analytics dashboard UI (fuel trends, SLA compliance, violations, vehicle performance)"
git push origin main
```

**10. Rollback / Recovery**
`git revert <commit-hash>`.

---

## Phase 10 Completion Checkpoint
- **Completed milestones:** 10.1, 10.2, 10.3
- **Tests passed:** All TC-10.1-*, TC-10.2-*, TC-10.3-* (16 total)
- **Known issues:** _(e.g. chart performance with large session counts, if relevant)_
- **Git commit/hash:** _(record)_
- **Overall phase verification:** Full analytics stack — seed data, aggregation API, dashboard UI — verified accurate against hand-computed values and tells a coherent demo story.
- **Go/No-Go for Phase 11:** GO — all functional requirements from the spec are now implemented; Phase 11 is integration hardening and deployment prep.

---

# Phase 11 – Integration, Hardening & Deployment Readiness

### Milestone 11.1 — Full End-to-End Regression Pass
**Depends on:** All of Phases 0–10

**2. Objective**
Run a comprehensive manual + automated regression across the entire system to catch integration gaps that per-milestone testing may have missed, before declaring the system demo-ready.

**3. Tasks to Complete**
- [ ] Run the full automated test suite (`pytest` + any frontend tests) end-to-end; fix any accumulated flakiness.
- [ ] Manual walkthrough: fresh DB → seed graph/warehouses/parcels → seed historical sessions → admin login → run optimization → assign routes → simulate live movement → mark deliveries/failures across all three re-optimization tiers → check analytics reflects new data.
- [ ] Cross-check every "Known issues" entry logged across all prior Phase Completion Checkpoints — resolve or explicitly accept/document each one.
- [ ] Load-test the routing run endpoint at full scale (100-120 stops, 20-25 vehicles) and record actual timings for the scalability claim (Deliverable #9).
- [ ] Verify TomTom budget compliance under a full realistic demo-length run (not just unit-tested staggering logic).

**4. Files / Modules Affected**
Potentially any file, depending on what regression finds; primarily produces `docs/regression_report.md` and `docs/scalability_evidence.md`.

**5. Implementation Guidance**
Treat this milestone as a bug-hunting pass, not a feature pass — resist adding new functionality here; if regression uncovers a genuine gap, decide explicitly whether it's a must-fix-before-demo or a documented known-limitation, and record which.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-11.1-01 | Full automated suite green | All phases complete | Run entire test suite | 100% pass (or documented, justified exceptions) | Pending |
| TC-11.1-02 | Full manual demo walkthrough | Fresh environment | Execute the full walkthrough listed above | Every step succeeds without unexpected errors | Pending |
| TC-11.1-03 (performance) | Full-scale routing run completes in acceptable time | 100-120 stops, 20-25 vehicles seeded | Trigger routing run | Completes within a time budget acceptable for live demo (document actual seconds) | Pending |
| TC-11.1-04 | TomTom budget holds over realistic demo length | Full demo-length run simulated | Monitor request counts | Stays within 2500/day, 10 QPS at all times | Pending |
| TC-11.1-05 (regression) | All three re-optimization tiers still behave correctly at full scale | Full-scale data | Trigger delivered/failed/escalation scenarios | All three tiers behave per Milestone 9.2 spec at full scale, not just small test data | Pending |

**7. Verification Checklist**
- [ ] Every prior phase's "Known issues" list reviewed and resolved/accepted.
- [ ] Full-scale performance numbers documented.
- [ ] Manual walkthrough completed by someone other than the original implementer if possible (fresh eyes catch more).

**8. Milestone Completion Criteria**
All test cases pass; `docs/regression_report.md` and `docs/scalability_evidence.md` completed and reviewed.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 11.1: full regression pass, scalability evidence, resolved known-issues backlog"
git push origin main
```

**10. Rollback / Recovery**
Given the breadth of this milestone, prefer targeted `git revert` of the specific fix commit that caused a regression, rather than reverting this entire milestone (which spans many small fixes) — keep fixes as separate, atomic commits within this milestone's branch to make this possible.

---

### Milestone 11.2 — Deployment Packaging & Environment Config
**Depends on:** 11.1

**2. Objective**
Package the application for deployment (or reliable local demo-day setup), with clean environment configuration and a documented, repeatable startup procedure.

**3. Tasks to Complete**
- [ ] Finalize `.env.example` files for backend (and frontend, if any env-driven config exists there) with every required variable documented.
- [ ] Write `docs/deployment.md`: exact steps to stand up the system from scratch (or from a deployed host) — DB setup, graph cache generation, seed scripts, service start order.
- [ ] If deploying (vs local-only demo): containerize backend (Dockerfile) and/or document hosting choice (document your choice and why — this is genuinely open given no deployment target was specified in the spec).
- [ ] Add a startup health-check sequence/script confirming DB, graph cache, and TomTom connectivity all pass before declaring "ready."
- [ ] Final secrets audit: grep the full git history for accidentally committed secrets (API keys, credentials) and rotate/purge if any are found.

**4. Files / Modules Affected**
`docs/deployment.md`, `Dockerfile` (if containerizing), `backend/scripts/startup_healthcheck.py`, `.env.example` files

**5. Implementation Guidance**
Given the spec doesn't specify a deployment target, and this is described as a hackathon project, a fully-documented **local run procedure** may be entirely sufficient — don't over-invest in cloud deployment infrastructure unless you know judging requires a hosted demo. Flag this decision explicitly rather than assuming.

**6. Test Cases**

| Test Case ID | Test Scenario | Preconditions | Steps | Expected Result | Status |
|---|---|---|---|---|---|
| TC-11.2-01 | Fresh-clone startup works | Fresh clone, no local state | Follow `docs/deployment.md` exactly | System reaches ready state with no undocumented manual steps | Pending |
| TC-11.2-02 | Health-check script catches missing config | `.env` intentionally incomplete | Run startup health check | Clearly reports which required piece is missing | Pending |
| TC-11.2-03 (security) | No secrets in git history | Full repo history | Search history for key patterns (API keys, credential strings) | None found; if found, rotated and purged | Pending |
| TC-11.2-04 (if containerized) | Docker build succeeds | Dockerfile present | `docker build .` | Builds successfully, container starts and passes health check | Pending |

**7. Verification Checklist**
- [ ] Fresh-clone startup verified by literally following the doc, not from memory.
- [ ] Secrets audit completed and documented.
- [ ] Deployment/local-only decision explicitly recorded with rationale.

**8. Milestone Completion Criteria**
All applicable test cases pass; a teammate unfamiliar with the setup can start the system using only `docs/deployment.md`.

**9. Git Checkpoint**
```
git status
git add .
git commit -m "Milestone 11.2: deployment packaging, environment config finalization, secrets audit"
git push origin main
```
Do NOT commit: any real secret values, Docker images with baked-in credentials.

**10. Rollback / Recovery**
`git revert <commit-hash>`. If a secret is found in history during the audit, rotation (invalidate the old key at the provider, e.g. TomTom) takes priority over any git-history rewriting.

---

## Phase 11 Completion Checkpoint
- **Completed milestones:** 11.1, 11.2
- **Tests passed:** All TC-11.1-*, TC-11.2-* (9 total)
- **Known issues:** _(final list — should be empty or explicitly accepted)_
- **Git commit/hash:** _(record — this is effectively the release candidate commit)_
- **Overall phase verification:** Full system regression-tested at scale, deployment/startup procedure verified from a clean state, secrets audited.
- **Go/No-Go for release:** GO if Final Release Checklist (below) is fully satisfied.

---

# Final Release Checklist

**Functionality**
- [ ] All Phase 0–10 milestones marked DONE per their individual completion criteria.
- [ ] Full pipeline (QGA → QPSO → feasibility/fallback) verified correct at full scale (100-120 stops, 20-25 vehicles, 3-4 warehouses).
- [ ] All three live re-optimization tiers (delivered/failed/escalation) verified at full scale.
- [ ] Admin and driver apps both fully functional against the real backend, not mocks.
- [ ] Analytics dashboard shows a coherent, accurate trend story from seeded historical sessions.

**Testing**
- [ ] 100% of documented test cases across all milestones pass (or exceptions explicitly justified and recorded).
- [ ] Full regression pass (Milestone 11.1) complete.
- [ ] Security/isolation tests (auth, role-based access, driver data isolation) all pass.
- [ ] Failure-handling tests (network failures, invalid input, infeasible routing scenarios) all pass.

**Security**
- [ ] No secrets in git history (audited, Milestone 11.2).
- [ ] TomTom API key never exposed to frontend (verified via devtools inspection).
- [ ] `.env` files never committed; `.env.example` complete and accurate.
- [ ] Role-based access control genuinely enforced, not cosmetic.

**Performance**
- [ ] Full-scale routing run timing documented and acceptable for live demo (Milestone 11.1).
- [ ] TomTom API usage confirmed within free-tier budget across a full demo-length run.
- [ ] Leiden clustering size-sweep evidence supports the scalability claim (Milestone 2.2).
- [ ] Re-optimization cost-tier evidence (delivered < failed-repair < escalation) documented (Milestone 9.2).

**Deployment**
- [ ] Fresh-clone startup verified working via `docs/deployment.md` (Milestone 11.2).
- [ ] Deployment/local-only decision explicitly recorded and matches actual demo-day plan.
- [ ] OSM graph cache pre-generated and committed to the deployment artifact/environment (never live-fetched during demo).
- [ ] Health-check script confirms all dependencies (DB, graph cache, TomTom) ready before demo start.

**Documentation**
- [ ] `README.md` accurate and complete for both backend and frontend setup.
- [ ] `docs/api_contract.md` matches actual implemented endpoints.
- [ ] All design-decision docs present: `warehouse_locations.md`, `leiden_design.md`, `congestion_mode_benchmark.md`, `bounceback_policy.md`, `historical_seed_story.md`, `reoptimization_cost_tiers.md`, `scalability_evidence.md`, `regression_report.md`, `deployment.md`.
- [ ] Demo account credentials documented (`docs/demo_accounts.md`).

**Git Repository Cleanliness**
- [ ] No `.env`, credentials, or large generated files (`.graphml`, `node_modules/`, `venv/`) in any commit.
- [ ] Commit history readable — each commit corresponds to a milestone with a clear, descriptive message.
- [ ] `main` branch is the verified release candidate from Milestone 11.1/11.2's final checkpoint.
- [ ] All feature branches merged and cleaned up (or explicitly documented if intentionally kept).

---

*End of playbook. Next step (per your note): prompt-book generation, to be produced in a follow-up once this playbook is reviewed/approved.*
