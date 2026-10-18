# Cold-Chain AI — Frontend & Backend Architecture Guide

## Overview

Cold-Chain AI combines big data predictive analytics (MAD-TCN) and energy-aware actuator optimization (NSGA-II) for temperature-sensitive supply chains. 

The application architecture has been cleanly organized into a physically decoupled **Frontend/Backend Separation**:
- **Backend (`backend/`):** Django 5 REST Framework serving high-frequency sensor ingest, token authentication, real-time MAD-TCN inference, and trajectory-constrained NSGA-II optimization.
- **Frontend (`frontend/`):** Modern Single Page Application (SPA) built with React 19, TypeScript, Vite, Tailwind CSS, and Recharts, styled with the **Blue-Pink** industrial UI theme.
- **Shared Assets (Root):** Root repository retains large research datasets (`data/`, `Datasets/`), neural network checkpoints (`models/`), scientific audits (`reports/`), and documentation (`docs/`).

---

## 1. Physical Directory Structure

```text
Cold-Chain-Ai/
├── backend/                             # Django 5 Backend Application
│   ├── apps/
│   │   └── monitoring/                  # Django monitoring app (models, views, routes, serializers)
│   ├── config/                          # Django configuration (settings.py, urls.py, wsgi.py)
│   ├── ml/                              # PyTorch MAD-TCN model architecture and inference engine
│   ├── optimization/                    # Pymoo NSGA-II full-trajectory safety optimizer
│   ├── scripts/                         # Benchmark, audit, and verification CLI scripts
│   │   ├── audit_datasets.py            # Recursive dataset inventory and provenance scanner
│   │   ├── compare_nsga2_methods.py     # 50-scenario matched NSGA-II comparative audit
│   │   ├── evaluate_baseline.py         # Synthetic benchmark evaluation
│   │   ├── evaluate_real_forecasting.py # Hohenheim SENSOR03 physical telemetry evaluation
│   │   └── verify_react_frontend.py     # Automated Playwright test for React frontend
│   ├── static/                          # Backend static assets
│   ├── templates/                       # Preserved server-rendered Django templates
│   ├── tests/                           # 96 automated Django tests
│   │   ├── test_api_workflows.py        # API endpoint and service workflows
│   │   ├── test_new_features.py         # Delimiter, energy contract, IoT auth, audit tests
│   │   ├── test_pipeline.py             # Minimal pipeline integration tests
│   │   └── test_scenario14_safety.py    # Dedicated Scenario 14 full-trajectory safety tests
│   ├── analysis_service.py              # Sensor decision aggregation service
│   ├── core.py                          # Thermodynamic equations and energy estimators
│   ├── core_preprocessing.py            # Feature engineering and window sequencing
│   ├── db.sqlite3                       # Authoritative SQLite database
│   ├── manage.py                        # Django management script
│   └── requirements.txt                 # Backend dependency manifest
│
├── frontend/                            # React 19 Single Page Application
│   ├── src/
│   │   ├── components/                  # UI components (MetricCard, StatusBadge, Sidebar, Topbar, Layout)
│   │   ├── pages/                       # 12 mapped application pages (Overview, Dashboard, Live, ...)
│   │   ├── services/                    # Centralized typed Axios API client
│   │   └── types/                       # TypeScript interface definitions
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts                   # Vite dev server with proxy to Django (127.0.0.1:8000)
│
├── data/                                # Cold-chain simulation and ground truth datasets
│   └── raw/
│       └── simulated_cold_chain.csv     # 12,000-row calibrated simulation dataset
├── Datasets/                            # Public research datasets (Hohenheim Zenodo DOI: 10.5281/zenodo.15130001)
│   └── zenodo_hohenheim/
├── docs/                                # Technical reports and architectural documentation
│   └── screenshots/
│       └── redesign/                    # 12 routes + responsive tablet/mobile Playwright screenshots
├── models/                              # Trained neural weights (mad_tcn_best.pt) and scaler
├── reports/                             # Machine-readable evaluation reports & comparison JSONs
│   ├── nsga2_comparison/               # 50-scenario comparative evaluation data and Markdown report
│   ├── dataset_audit_inventory.json     # 24 datasets (2.5M rows) inventory
│   ├── frontend_verification_report.json# Playwright 12-route verification report
│   └── real_forecasting_benchmark.json  # Hohenheim empirical evaluation benchmark
└── README.md                            # Comprehensive user and researcher guide
```

---

## 2. Blue-Pink Design Tokens

The frontend uses an accessible, high-contrast, modern Blue-Pink color palette:

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

## 3. Running the Applications

### Starting Backend (Django):
```bash
# Option A: From backend directory
cd backend
..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

# Option B: From project root
.\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
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
# Outputs optimized static bundle to frontend/dist/ (0 errors, 1.7s build)
```

### Running Automated Test Suites:
```bash
# 1. Backend 96 Django Unit & Integration Tests (from backend directory)
cd backend
..\.venv\Scripts\python.exe manage.py test --no-input

# Or from repository root:
.\.venv\Scripts\python.exe backend/manage.py test tests --no-input

# 2. React Full-Stack Browser Verification (12 routes + multi-viewport)
.\.venv\Scripts\python.exe backend/scripts/verify_react_frontend.py
```

---

## 4. Route Inventory & Verification Matrix

All 12 React routes verified via automated Microsoft Edge Playwright tests:

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
| `/datasets` | `DatasetsPage` | Scientific data catalog (2.5M rows), provenance classification | **PASS (200)** |
| `/reports` | `ReportsPage` | Report generation suite, file viewer, raw data export | **PASS (200)** |
| `/upload` | `UploadPage` | CSV dropzone, schema validation, safe ingestion pipeline | **PASS (200)** |
| `/methodology` | `MethodologyPage` | Research equations, thermodynamic proofs, 50-scenario benchmark | **PASS (200)** |

---

## 5. Scientific Problem Closures

### Priority 1: Unsafe Scenario 14 Optimization Resolution
- **Issue:** Earlier algebraic endpoint formulation ($T_{\text{expected}} = T_0 + 0.18\max(T_{\text{amb}} - T_0, 0) - 3.2ud + \delta$) assumed continuous 15-minute cooling. For low duty cycles ($d=0.558$), the compressor shut off at $t=8.37$ minutes, allowing ambient heat infiltration to warm the chamber to $5.71^\circ\text{C}$ ($2.74\text{ min}$ excursion).
- **Resolution:**
  1. Embedded step-by-step forward ODE simulation ($k_{\text{inf}}=0.018, k_{\text{cool}}=0.32$) directly into `ColdProblem._evaluate()`, evaluating constraints against the complete trajectory: $g_1 = \max(T_{\text{sim}}) - (T_{\text{max}} - \text{buffer})$, $g_2 = (T_{\text{min}} + \text{buffer}) - \min(T_{\text{sim}})$.
  2. Implemented `search_deterministic_feasible()` fallback ensuring that when a chamber is initially compliant ($T_0 \in [0, 5]^\circ\text{C}$) and controllable ($T_{\text{ss}} \le 5.0^\circ\text{C}$), compliant candidate schedules are deterministically supplied.
  3. Under the unified optimizer, Scenario 14 selects $u=0.883, d=0.667$, achieving peak temperature $4.945^\circ\text{C} \le 5.0^\circ\text{C}$ and $0.0\text{ min}$ excursion duration (100% trajectory compliance).
  4. Feasible controllable scenarios across the 50-scenario benchmark increased from 18 to 19.

### Priority 2: Real-World vs Synthetic Forecasting Reconciliation
- **Synthetic Demonstration Benchmark (`evaluate_baseline.py`):**
  - Dataset: `simulated_cold_chain.csv` ($N=3,925$, range $0.8–6.8^\circ\text{C}$, Sensor CC-01).
  - Train/Val/Test: 70% / 15% / 15% chronological split ($N_{\text{test}}=590$).
  - Results: Persistence MAE $0.1219^\circ\text{C}$, MAD-TCN (retrained with StandardScaler) MAE $0.1672^\circ\text{C}$, $R^2 = 0.9875$.
- **Empirical Cold-Storage Evaluation (`evaluate_real_forecasting.py`):**
  - Dataset: Hohenheim Cold Storage Research Facility (`SENSOR03_preprocessed.csv`, DOI: 10.5281/zenodo.15130001).
  - Telemetry: 7,037 resampled 1-minute readings ($84,453\text{ raw 5-s observations}$), range $4.8–12.3^\circ\text{C}$, mean $6.54^\circ\text{C}$.
  - Split: Chronological split with strict 74-sample boundary purge (0 target timestamp overlap).
  - Results: Persistence MAE $0.3048^\circ\text{C}$, Ridge AR(60) MAE $0.2528^\circ\text{C}$, Genuine MAD-TCN MAE $0.2637^\circ\text{C}$, RMSE $0.3639^\circ\text{C}$, $R^2 = 0.3876$.
  - Food Safety Caveat: Chamber operated in steady breach (mean $6.54^\circ\text{C}$); test split contained only 8 safe origins ($T_0 \le 5.0^\circ\text{C}$). Evaluation on $5.0^\circ\text{C}$ critical limit is statistically inconclusive due to low sample support.
