# Cold-Chain AI — Frontend & Backend Architecture Guide

## Overview

Cold-Chain AI combines big data predictive analytics (MAD-TCN) and energy-aware actuator optimization (NSGA-II) for temperature-sensitive supply chains. 

The application architecture has been organized into a decoupled, clean **Frontend/Backend Separation**:
- **Backend:** Django 5 REST Framework serving high-frequency sensor ingest, authentication, real-time MAD-TCN inference, and NSGA-II optimization.
- **Frontend:** Modern Single Page Application (SPA) built with React 19, TypeScript, Vite, Tailwind CSS, and Recharts, styled with the **Blue-Pink** industrial UI theme.

---

## 1. Directory Structure

```text
Cold-Chain-Ai/
├── apps/
│   └── monitoring/          # Django monitoring app (models, views, routes, serializers)
├── config/                  # Django project settings (CORS, URLs, WSGI/ASGI)
├── data/                    # Cold-chain simulation and ground truth datasets
├── Datasets/                # Public research datasets (Hohenheim, Kaggle)
├── docs/
│   └── screenshots/
│       ├── baseline/        # Archived screenshots of original server-rendered UI (12 routes)
│       └── redesign/        # Captured screenshots of React Blue-Pink UI (12 routes + responsive)
├── frontend/                # Standalone React + TypeScript + Vite SPA
│   ├── src/
│   │   ├── components/      # UI components (MetricCard, StatusBadge, Sidebar, Topbar, Layout)
│   │   ├── pages/           # 12 mapped application pages
│   │   ├── services/        # Centralized typed Axios API client
│   │   └── types/           # TypeScript interface definitions
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── ml/                      # PyTorch MAD-TCN model architecture and inference engine
├── models/                  # Trained neural weights (mad_tcn_best.pt) and scaler
├── optimization/            # Pymoo NSGA-II full-trajectory safety optimizer
├── reports/                 # Machine-readable evaluation reports & comparison JSONs
├── scripts/
│   ├── verify_browser_pages.py     # Automated Playwright test for Django templates
│   └── verify_react_frontend.py    # Automated Playwright test for React frontend
└── templates/               # Server-rendered templates (fully preserved for rollback)
```

---

## 2. Blue-Pink Design Tokens

The new frontend uses an accessible, high-contrast, modern Blue-Pink color palette:

| Token | Hex Value | Application |
| :--- | :--- | :--- |
| **Primary Blue** | `#2563EB` | Primary actions, branding, active navigation, lower bound curves |
| **Dark Slate** | `#0F172A` | Sidebar background, headings, high-contrast text |
| **Accent Pink** | `#EC4899` | Actuator alerts, upper temperature bounds, badges, highlights |
| **Card Background** | `#FFFFFF` | Clean elevation panels, borders `#E2E8F0` |
| **Page Background** | `#F8FAFC` | Neutral soft slate canvas |
| **Success Emerald**| `#10B981` | Provenance verified (`REAL_SENSOR`), low risk, normal status |
| **Warning Amber**  | `#F59E0B` | External ambient thermal lift warnings |

---

## 3. Route Inventory & Verification Matrix

Both the React SPA and Django server-rendered routes are tested with Playwright on Microsoft Edge:

| Route Path | React Page | Functional Scope | Playwright Status |
| :--- | :--- | :--- | :--- |
| `/` | `HomePage` | Hero overview, real-time KPI cards, 15-min forecast curve | **PASS (200)** |
| `/dashboard` | `DashboardPage` | Operational command, simulation stream controls, actuator setpoints | **PASS (200)** |
| `/live-monitoring` | `LiveMonitoringPage` | High-frequency telemetry stream, status indicators, CSV export | **PASS (200)** |
| `/predictions` | `PredictionsPage` | MAD-TCN 60-min lookback vs 15-min forward trajectory | **PASS (200)** |
| `/optimization` | `OptimizationPage` | Bi-objective NSGA-II Pareto frontier & actuator inspector | **PASS (200)** |
| `/alerts` | `AlertsPage` | Real-time anomaly center, breach countdown, alarm acknowledge | **PASS (200)** |
| `/sensors` | `SensorsPage` | Registered edge sensor network, hardware provenance cards | **PASS (200)** |
| `/model` | `ModelPage` | MAD-TCN layer specs, causal dilation rates, training guarantees | **PASS (200)** |
| `/datasets` | `DatasetsPage` | Scientific data catalog (294k rows), provenance classification | **PASS (200)** |
| `/reports` | `ReportsPage` | Report generation suite, file viewer, raw data export | **PASS (200)** |
| `/upload` | `UploadPage` | CSV dropzone, schema validation, safe ingestion pipeline | **PASS (200)** |
| `/methodology` | `MethodologyPage` | Research equations, thermodynamic proofs, 50-scenario benchmark | **PASS (200)** |

---

## 4. Running the Applications

### Starting Backend (Django):
```bash
# From repository root
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### Starting Frontend (React + Vite):
```bash
cd frontend
npm run dev
# Browser opens at http://127.0.0.1:5173
```

### Building Frontend for Production:
```bash
cd frontend
npm run build
# Outputs optimized static bundle to frontend/dist/
```

### Running Automated Test Suites:
```bash
# 1. Backend 92 Django Unit & Integration Tests
.\.venv\Scripts\python.exe manage.py test --no-input

# 2. React Full-Stack Browser Verification (12 routes + multi-viewport)
.\.venv\Scripts\python.exe scripts/verify_react_frontend.py

# 3. Preserved Django Templates Browser Verification
.\.venv\Scripts\python.exe scripts/verify_browser_pages.py
```
