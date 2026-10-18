# COLDCHAIN-AI: Academic & Research Judge Demonstration Guide

**Project Title:** AI-Driven Framework Integrating Big Data Analytics and Energy-Aware IoT for Cold-Chain Logistics  
**Repository Working Directory:** `C:\Projects\Cold-Chain-Ai`  
**Branch:** `completion-dev`  
**Git HEAD Commit:** `7491bb5`  
**Release Gate Status:** `PASS WITH LIMITATIONS`  

---

## 1. System Architecture & Component Separation

The ColdChain-AI platform strictly separates concerns across full-stack layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        REACT 19 FRONTEND                               │
│  - Vite + TailwindCSS Blue-Pink Theme                                  │
│  - 12 Dynamic Routes, Recharts Interactive Visualizations              │
│  - Typed REST API Client (services/api.ts)                             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (JSON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       DJANGO 5.2 BACKEND API                           │
│  - Device-Token Authentication & Provenance Demotion                   │
│  - RESTful Endpoints: /api/dashboard/, /api/iot/telemetry/, etc.       │
└───────────────┬───────────────────────────────────────┬────────────────┘
                │                                       │
                ▼                                       ▼
┌───────────────────────────────┐     ┌──────────────────────────────────┐
│      PYTORCH MAD-TCN          │     │    NSGA-II MULTI-OBJECTIVE       │
│  - Multi-Scale Causal Conv1d  │     │  - ColdProblem (Safety vs Energy)│
│  - Dilations: d = 1, 2, 4, 8  │     │  - True 15-min ODE Trajectory    │
│  - Adaptive Softmax Gating    │     │  - Hard 0.2 °C Buffer Constraint │
│  - 15-min Lookahead Horizon   │     │  - Emergency Fallback (u=1, d=1) │
└───────────────┬───────────────┘     └─────────────────┬────────────────┘
                │                                       │
                ▼                                       ▼
┌───────────────────────────────┐     ┌──────────────────────────────────┐
│    CALIBRATED RISK ENGINE     │     │     THERMODYNAMIC PLANT ODE      │
│  - Impending Excursion Score  │────▶│  - Infiltration: k_inf = 0.018   │
│  - Trend & Severity Penalty   │     │  - Cooling Lift: k_cool = 0.320  │
└───────────────────────────────┘     └──────────────────────────────────┘
```

---

## 2. Fast-Start Execution Sequence

Follow this exact sequence to start both servers for live presentation:

### Step 1: Start Django Backend (Terminal 1)
```powershell
cd C:\Projects\Cold-Chain-Ai\backend
..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```
*Expected Output:*
`Starting development server at http://127.0.0.1:8000/`  
`Quit the server with CTRL-BREAK.`

### Step 2: Start React Frontend (Terminal 2)
```powershell
cd C:\Projects\Cold-Chain-Ai\frontend
npm run dev
```
*Expected Output:*
`VITE v8.3.4  ready in 320 ms`  
`➜  Local:   http://localhost:5173/`

### Step 3: Access Live Application
Open your browser (Edge or Chrome) to:
**`http://localhost:5173`**

---

## 3. Recommended 15-Step Judge Walkthrough

### Stage 1: System Overview & Physical Telemetry
1. **Overview Page (`/`):**
   - View top-level system health: 98 passing tests, clean Django check, active sensors, and model status.
   - Point out the architectural disclaimer: Electrical energy values are analytically modeled from thermal ODEs; physical 3-phase CT sub-metering is marked as externally blocked awaiting hardware commissioning.
2. **Dashboard (`/dashboard`):**
   - Click the **Sensor Dropdown** at the top right to switch between `CC-01` (nominal food compartment) and `CC-02` (deep chiller).
   - Observe real-time dynamic UI reactivity without page reload.
3. **Datasets & Provenance (`/datasets`):**
   - Showcase the Zenodo Hohenheim dataset inventory (DOI: 10.5281/zenodo.15130001).
   - Point out SENSOR03 clean record counts: 7,037 resampled 1-minute observations derived from 84,450 clean 5-second physical sensor readings.

### Stage 2: Genuine MAD-TCN Time-Series Forecasting
4. **Neural Model Architecture (`/model`):**
   - View the genuine MAD-TCN structure: Multi-scale causal dilated convolutions ($d \in \{1, 2, 4, 8\}$), adaptive gating weights, and residual skip connections.
5. **Predictions Inspector (`/predictions`):**
   - Inspect the 15-minute lookahead forecast curve plotted against actual chamber readings.
   - Note the empirical accuracy: On held-out chronological test sequences, retrained MAD-TCN achieves $\text{MAE} = 0.1672\text{ }^\circ\text{C}$ ($\text{RMSE} = 0.2131\text{ }^\circ\text{C}$, $R^2 = 0.9875$).

### Stage 3: Forecast-Risk Engine & NSGA-II Optimization
6. **Risk Assessment (`/alerts`):**
   - Explain how raw predicted temperatures enter `core.py:risk()`. When future temperatures approach or breach profile thresholds ($5.0^\circ\text{C}$ for Food), risk escalates from `LOW` to `MEDIUM`, `HIGH`, or `CRITICAL`.
7. **NSGA-II Multi-Objective Optimization (`/optimization`):**
   - Inspect the interactive **Pareto Surface Scatter Plot** (Energy Demand vs. Target Temperature).
   - Show how the optimizer balances the 70% safety-risk weight against the 30% energy-minimization weight.
   - View the selected actuator recommendation: Modulated cooling intensity $u$ and compressor duty cycle $d$.
8. **Trajectory Safety Constraints:**
   - Note the **"19 Nominally / 18 Buffered Feasible Regimes"** badge.
   - Explain that the optimizer simulates the complete 15-minute differential trajectory ($t = 0 \dots 15\text{ min}$) rather than a static terminal point, preventing mid-interval warming breaches.

### Stage 4: Scientific Contribution & Ablation Proof
9. **Methodology & Ablation Evidence (`/methodology`):**
   - Review Section 4: *Comparative Scenario Acceptance*.
   - **Method A (Reactive Control):** 543.25 excursion min (583 discrete violating samples).
   - **Method C (Forecast-Guided NSGA-II):** 446.40 excursion min (476 discrete violating samples).
   - **Improvement:** 17.83% continuous time reduction (saving 96.85 scenario-minutes) and 18.35% discrete violation reduction.
10. **The Forecast Guidance Contribution (Method C vs Method D):**
    - Explain the out-of-sample disturbance study (`reports/disturbance_robustness_report.md`):
    - Without forecast guidance (Method D ablation), the optimizer rides right at the edge ($4.79^\circ\text{C}$) to minimize energy, resulting in a **98.0% breach rate** under unforeseen delivery door openings and heat surges.
    - With MAD-TCN forecast guidance (Method C), proactive precooling maintains an average $\mathbf{0.71^\circ\text{C}}$ cooler peak, reducing disturbance breach incidents from **98.0% down to 44.0%** and cutting excursion duration by **53.9%**!

### Stage 5: Reports, Upload, and Quality Verification
11. **Reports View (`/reports`):**
    - Browse generated markdown and JSON research audit reports.
12. **Telemetry Upload (`/upload`):**
    - Demonstrate custom CSV upload with automatic delimiter detection (handling both commas and European semicolons).

---

## 4. Key CLI Commands for Live Judge Verification

Run these commands in PowerShell from `C:\Projects\Cold-Chain-Ai` to demonstrate live test passing and reproducibility:

```powershell
# 1. Verify Django System Integrity (0 issues)
.\.venv\Scripts\python.exe backend/manage.py check

# 2. Run Full Backend Unit & Regression Suite (98 tests passing)
.\.venv\Scripts\python.exe backend/manage.py test --no-input

# 3. Verify Scenario 14 Safety & Buffer Invariance (6 tests passing)
.\.venv\Scripts\python.exe backend/manage.py test tests.test_scenario14_safety

# 4. Run Hohenheim SENSOR03 Real-Data Forecasting Benchmark
.\.venv\Scripts\python.exe backend/scripts/evaluate_real_forecasting.py

# 5. Run Out-of-Sample Disturbance Robustness Study
.\.venv\Scripts\python.exe backend/scripts/evaluate_disturbance_robustness.py

# 6. Run 1-Million Record Big Data Scalability Profiling
.\.venv\Scripts\python.exe backend/scripts/run_scalability_benchmark.py

# 7. Run Full-Stack Playwright Headless Browser Audit (12/12 routes HTTP 200, 0 console errors)
.\.venv\Scripts\python.exe backend/scripts/verify_react_frontend.py
```

---

## 5. Summary of Defensible Research Claims & Limitations

| Dimension | Defensible Scientific Claim | Explicitly Declared Limitation |
| :--- | :--- | :--- |
| **Forecasting** | Genuine MAD-TCN with dilated causal convolutions achieves $\text{MAE} = 0.2637^\circ\text{C}$ on Hohenheim SENSOR03 physical telemetry. | Telemetry is from a single cold-room trace; multi-facility cross-validation is pending external datasets. |
| **Optimization** | Dynamic 16-point forward trajectory simulation enforces hard $0.2^\circ\text{C}$ safety buffer throughout all 15 operational minutes. | In 31 of 50 scenarios, extreme ambient infiltration ($T_{\text{amb}} > 22.78^\circ\text{C}$) or initial breach exceeds physical cooling capacity, triggering emergency fallback. |
| **Ablation & Value** | MAD-TCN guidance reduces unforeseen disturbance breach rates from 98.0% to 44.0% and cuts excursion duration by 53.9%. | In static undisturbed scenarios, forecast guidance alters actuator settings to build thermal headroom at the cost of $+10.9\%$ modeled energy. |
| **Energy** | Transparent first-principles thermodynamic lift formulation cleanly separates instantaneous power (kW) from interval energy (kWh). | Values are modeled simulation outputs; physical 3-phase hardware sub-metering is awaiting on-site commissioning. |
| **Full-Stack** | Clean physical separation of Django backend and React 19 frontend; 98 unit tests; 12/12 Playwright browser routes verified. | Production deployment requires production WSGI/Reverse proxy configuration (e.g. Nginx/Gunicorn). |
