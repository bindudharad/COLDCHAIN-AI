# ColdChain-AI: Live Demonstration Walkthrough Guide

**Project:** COLDCHAIN-AI  
**Date:** 2026-10-09  
**Audience:** Researchers, Industrial Operators, and Evaluation Committee  

---

## 1. Demonstration Protocol Overview

This demonstration illustrates the complete predictive cold-chain lifecycle:
$$\text{Sensor Telemetry Ingestion} \longrightarrow \text{MAD-TCN Forecasting} \longrightarrow \text{Risk Assessment} \longrightarrow \text{Constrained NSGA-II Optimization} \longrightarrow \text{Operator Decision Support}$$

> [!NOTE]
> All controls shown operate in **Decision-Support Simulation Mode**. Optimization outputs represent recommended actuator setpoints; physical compressors are not modulated.

---

## 2. Step-by-Step Demonstration Script

### Step 1: Open the Control Center Dashboard
1. Start the server: `.\.venv\Scripts\python.exe manage.py runserver`
2. Navigate to: `http://127.0.0.1:8000/dashboard/`
3. **What to Observe:**
   - Dark graphite industrial user interface.
   - Live KPI cards: Active Temperature ($3.93\text{ }^\circ\text{C}$), 15-Step Lookahead, Safety Margin ($+1.07\text{ }^\circ\text{C}$), and Residual Risk ($26.04\text{ MEDIUM}$).
   - Notice banner clearly stating: *Demonstration / Simulation Telemetry · Energy Values are Estimated*.

### Step 2: Multi-Sensor Fleet Selection
1. Use the left sidebar selector: switch between **CC-01**, **CC-02**, and **CC-03**.
2. **What to Observe:**
   - The entire dashboard context reactively updates to reflect the chosen cold room.
   - Real-time temperature trends and historical readings fetched dynamically from the database.

### Step 3: Inspect Historical Readings & Fleet Monitoring
1. Click **Sensors Fleet** (`/sensors/`) or **Live Monitoring** (`/live-monitoring/`).
2. Click on sensor nodes to inspect historical 30-minute temperature traces, ambient fluctuations, compressor cycles, and door status.
3. Click **START** simulation cursor to observe dynamic temporal sequence stepping.

### Step 4: Inspect the MAD-TCN 15-Step Forecast
1. Click **Predictions** (`/predictions/`).
2. **What to Observe:**
   - Canvas visualization plotting observed historical readings (solid line) alongside the 15-step MAD-TCN forecast (dashed line).
   - Safe temperature corridor ($0.0\text{ to }5.0\text{ }^\circ\text{C}$) clearly visible with warning buffer bands.
   - Step-by-step breakdown table detailing forecasted temperature at each future minute $t+1 \dots t+15$.

### Step 5: Examine Future Risk & Early Breach Detection
1. Click **Alert Center** (`/alerts/`).
2. **What to Observe:**
   - Active Alert generated: `MEDIUM Risk Detected at t+2`.
   - Explanation: Demonstrates that while current temperature ($3.93\text{ }^\circ\text{C}$) is technically within range, the forecast anticipates a thermal breach at minute $t+2$ ($5.02\text{ }^\circ\text{C}$).
   - Click **Resolve Incident** to test persistent alert acknowledgment.

### Step 6: Review Prediction-Guided NSGA-II Optimization
1. Click **Optimization** (`/optimization/`).
2. **What to Observe:**
   - Pareto Frontier scatter plot displaying non-dominated trade-off points between Safety Risk and Estimated Energy (kWh).
   - Recommended Setpoint: Pre-emptive cooling intensity ($0.999$), compressor duty ($1.00$), and setpoint offset ($-0.42\text{ }^\circ\text{C}$).
   - Expected stabilized temperature: $3.06\text{ }^\circ\text{C}$ — safely mitigating the forecasted breach!
   - Table of feasible Pareto solutions when within/near envelope, or explicit red emergency override banner when severe starting breach requires maximum cooling ($u=1.0, d=1.0$).

### Step 7: Inspect Multi-Format Audit Reports
1. Click **Reports** (`/reports/`).
2. **What to Observe:**
   - Generated reports catalog listing `coldchain_report.json`, `coldchain_report.md`, and `coldchain_report.csv`.
   - Click **Generate New Report** to capture live snapshot of the system state.
   - Click **Inspect** to read formatted JSON in-browser; click **Download** for CSV export.

### Step 8: Review Datasets & Provenance Disclosures
1. Click **Datasets Catalog** (`/datasets/`).
2. **What to Observe:**
   - Transparent registry of all 6 datasets with exact row counts, schemas, and domain classifications.
   - Clear distinction between `SIMULATION`, `PUBLIC_DATASET`, and `REAL_SENSOR`.
   - Honest research disclosures: no physical actuation, estimated energy models.
