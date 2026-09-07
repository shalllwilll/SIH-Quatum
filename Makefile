# Logistics Platform — Developer Shortcuts
# Usage: make <target>
# Paths are relative to repo root; cd backend is used where needed.

.PHONY: run-backend run-frontend-admin run-frontend-driver test-backend lint-backend lint-frontend-admin lint-frontend-driver lint install build-graph seed-data healthcheck scale-benchmark help

PYTHON_VENV = backend/.venv/bin

help:
	@echo "Available targets:"
	@echo "  run-backend            Start the FastAPI backend on http://localhost:8000"
	@echo "  run-frontend-admin     Start the Admin React app on http://localhost:5173"
	@echo "  run-frontend-driver    Start the Driver React app on http://localhost:5174"
	@echo "  test-backend           Run the backend pytest suite"
	@echo "  lint-backend           Run ruff lint on backend Python code"
	@echo "  lint-frontend-admin    Run linter on frontend-admin"
	@echo "  lint-frontend-driver   Run linter on frontend-driver"
	@echo "  lint                   Run all lint checks (backend + both frontends)"
	@echo "  install                Install backend Python deps into backend/.venv"
	@echo "  build-graph            Fetch Pune OSM road network and save to backend/data/pune_graph.graphml"
	@echo "  seed-data              Seed core Pune parcels, hubs, vehicles, and historical sessions"
	@echo "  healthcheck            Run platform pre-flight dependency & data health check"
	@echo "  scale-benchmark        Run full-scale 120-stop load test and benchmark sweep"

build-graph:
	$(PYTHON_VENV)/python -m backend.scripts.build_graph

seed-data:
	$(PYTHON_VENV)/python backend/scripts/seed_dev_data.py
	$(PYTHON_VENV)/python backend/scripts/seed_historical_sessions.py

healthcheck:
	$(PYTHON_VENV)/python backend/scripts/startup_healthcheck.py

scale-benchmark:
	$(PYTHON_VENV)/python backend/scripts/run_scale_benchmark.py

run-backend:
	$(PYTHON_VENV)/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend

run-frontend-admin:
	npm --prefix frontend-admin run dev

run-frontend-driver:
	npm --prefix frontend-driver run dev -- --port 5174

test-backend:
	$(PYTHON_VENV)/pytest backend/tests/ -v --rootdir=backend

lint-backend:
	$(PYTHON_VENV)/ruff check backend/app/ backend/scripts/ backend/tests/

lint-frontend-admin:
	npm --prefix frontend-admin run lint

lint-frontend-driver:
	npm --prefix frontend-driver run lint

lint: lint-backend lint-frontend-admin lint-frontend-driver

install:
	$(PYTHON_VENV)/pip install -e backend/
