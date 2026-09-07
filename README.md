# Last-Mile Delivery Routing Platform

Hybrid optimization engine (QGA + QPSO) with Leiden pre-clustering, FastAPI backend, and React frontends (Admin and Driver) for dynamic last-mile logistics in Pune.

---

## Repository Structure

```
├── backend/                  # FastAPI backend service
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI application entrypoint & health routes
│   ├── .env.example         # Environment variables template
│   └── requirements.txt     # Python dependencies
├── frontend-admin/           # React + Vite admin dashboard (Port 5173)
│   ├── src/
│   │   ├── App.jsx          # Admin portal root component
│   │   └── ...
│   └── package.json
├── frontend-driver/          # React + Vite driver mobile-view app (Port 5174)
│   ├── src/
│   │   ├── App.jsx          # Driver portal root component
│   │   └── ...
│   └── package.json
├── docs/                     # Design documents, benchmarks, and API contracts
├── Development_Playbook.md   # Step-by-step phased development plan
└── README.md                 # Project setup and execution guide
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm**
- **Git**

---

## Quickstart Guide

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run FastAPI development server (runs on http://localhost:8000)
uvicorn app.main:app --reload --port 8000
```

Verify backend health:
```bash
curl http://localhost:8000/health
# Expected response: {"status":"ok"}
```

---

### 2. Admin Frontend Setup

```bash
# Navigate to frontend-admin directory
cd frontend-admin

# Install dependencies
npm install

# Start Vite dev server (runs on http://localhost:5173)
npm run dev
```

---

### 3. Driver Frontend Setup

```bash
# Navigate to frontend-driver directory
cd frontend-driver

# Install dependencies
npm install

# Start Vite dev server (runs on http://localhost:5174)
npm run dev
```

---

## Makefile Shortcuts

Run from the repository root:

| Command | Description |
|---|---|
| `make run-backend` | Start FastAPI backend on port 8000 |
| `make run-frontend-admin` | Start admin Vite dev server on port 5173 |
| `make run-frontend-driver` | Start driver Vite dev server on port 5174 |
| `make test-backend` | Run the backend pytest suite |
| `make lint-backend` | Run ruff lint on backend Python code |
| `make lint-frontend-admin` | Run oxlint on frontend-admin |
| `make lint-frontend-driver` | Run oxlint on frontend-driver |
| `make lint` | Run all lint checks (backend + both frontends) |
| `make install` | Install backend Python dependencies |

---

## Pre-Push Checklist

Before every `git push`, run:

```bash
make test-backend    # must be 0 failures
make lint            # must be 0 errors
```
