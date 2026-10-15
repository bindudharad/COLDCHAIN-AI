# Cold-Chain Energy Estimation: Final Scientific Validation & Limitations Report

**Project:** COLDCHAIN-AI: Intelligent Multi-Objective Cold-Chain Optimization  
**Date:** 2026-10-15  
**Code Revision:** Branch `completion-dev`  
**Model Target:** Refrigeration compressor electrical demand (`power_kw` in kW)  
**Evaluation Scripts:**  
- Energy ML training & evaluation: [`scripts/train_energy_model.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/train_energy_model.py)  
- First-principles thermodynamic analysis: [`scripts/validate_energy.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/validate_energy.py)  
**Machine-Readable Reports:**  
- [`reports/energy_training_report.json`](file:///C:/Projects/Cold-Chain-Ai/reports/energy_training_report.json)  
- [`reports/energy_validation_report.json`](file:///C:/Projects/Cold-Chain-Ai/reports/energy_validation_report.json)  
- Serialized Model: [`models/energy_model.pkl`](file:///C:/Projects/Cold-Chain-Ai/models/energy_model.pkl)  
**Document Status:** COMPLETE & VERIFIED  

---

## 1. Reproducible Evaluation Commands

```powershell
# 1. Train and benchmark energy models (GradientBoosting vs Linear vs Analytical Formula)
.\.venv\Scripts\python.exe scripts/train_energy_model.py

# 2. Evaluate thermodynamic energy formula across operating temperature regimes
.\.venv\Scripts\python.exe scripts/validate_energy.py
```

---

## 2. Experimental Results on Held-Out Test Set

- **Dataset:** `data/raw/simulated_cold_chain.csv` (12,000 samples across sensors `CC-01`, `CC-02`, `CC-03`)
- **Features:**
  1. `thermal_lift`: $T_{ambient} - T_{chamber}$ (°C)
  2. `compressor_duty`: 15-minute rolling average of `compressor_state` [0.0..1.0]
  3. `door_exposure`: 15-minute rolling sum of `door_open` occurrences
- **Split:** 70% Train (8,400 rows), 15% Val (1,800 rows), 15% Test (1,800 rows) strictly chronological.

| Model / Estimator | Target Tested | Test MAE | Test RMSE | Test $R^2$ Score | Characteristics / Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GradientBoostingRegressor** | `power_kw` (kW) | **0.0142 kW** | **0.0710 kW** | **0.1362** | **Best Data-Driven Estimator** (Saved in `models/energy_model.pkl`) |
| **LinearRegression Baseline** | `power_kw` (kW) | 0.0227 kW | 0.0719 kW | 0.1146 | Baseline linear model |
| **Analytical Formula (`core.py`)** | `power_kw` (Surrogate) | 0.1666 kW | 0.1743 kW | -4.1991 | Optimization objective proxy |
| **Analytical Formula (`core.py`)** | Interval Energy (kWh) | 0.5893 kWh | 0.5902 kWh | -14454.7 | Cumulative interval energy equation |

### Feature Importance (GradientBoosting)
- `compressor_duty`: **62.46%**
- `thermal_lift`: **34.45%**
- `door_exposure`: **3.09%**

---

## 3. Scientific Investigation of the Low $R^2$ (0.1362) & Dominant-State Distribution

1. **Target Distribution & Dominant Operating State:**  
   In `simulated_cold_chain.csv`, electrical power is modeled as a discrete step function:
   $$P_{sim} = 0.25 + 0.75 \cdot \text{compressor\_state} + 0.12 \cdot \text{door\_open}$$
   Auditing the held-out test split ($N = 600$ readings on `CC-01`) reveals a heavily skewed discrete distribution:
   - **Active Compressor ($1.00\text{ kW}$):** **584 readings (97.33%)**
   - **Door Open Defrost / Loading ($1.12\text{ kW}$):** **10 readings (1.67%)**
   - **Idle Compressor ($0.25\text{ kW}$):** **6 readings (1.00%)**
   
   Across the entire 12,000-record dataset, $1.00\text{ kW}$ accounts for **95.28%** of all observations ($11,434$ records). The target variance is therefore tiny ($\sigma^2 \approx 0.0188\text{ kW}^2$).

2. **Source of the Low MAE (0.0142 kW) vs Low $R^2$ (0.1362):**  
   Because 97.33% of test samples occupy the $1.00\text{ kW}$ state, predicting near $\sim 0.98\text{--}1.00\text{ kW}$ naturally yields an extraordinarily small mean absolute error ($\text{MAE} = 0.0142\text{ kW}$, $\approx 1.4\%$ of compressor rating). However, when the compressor turns idle ($0.25\text{ kW}$) or doors open ($1.12\text{ kW}$), the continuous 15-minute rolling duty cycle average ($d \in [0.2, 1.0]$) cannot instantaneously reproduce a binary step. In a target distribution with minimal total variance ($SS_{tot}$), the residual variance from these few discrete transitions represents a significant fraction of $SS_{tot}$, yielding $R^2 = 0.1362$.

3. **Analytical Formula Role in Multi-Objective Optimization:**  
   The analytical equation used in NSGA-II:
   $$E = \left(0.25 + 0.035 \cdot \max(T_{amb} - T_{cur}, 0.0)\right) \cdot (0.35 + 0.65 \cdot u) \cdot d$$
   is designed to provide smooth convex gradients for evolutionary setpoint search ($u, d \in [0.2, 1.0]$), rather than fitting instantaneous discrete power telemetry. It acts as an optimization surrogate, not a physical power measurement.

---

## 4. Hardware Boundary & Data Requirements for Physical Deployment

1. **No Hardware Claim:** Every energy value in reports and UI is explicitly labeled as **`ESTIMATED / SIMULATED`**.
2. **Domain Segregation:** The external Kaggle dataset (`Datasets/03_energy_consumption/`) records residential building HVAC consumption (MAE = 4.0994 kWh, $R^2 = 0.5866$). It is kept strictly distinct and **is never claimed as cold-chain warehouse validation**.
3. **Data Required for Hardware Validation:**  
   True hardware validation requires on-site 3-phase true RMS power transducer readings (kW, kVA, Power Factor), compressor suction/discharge pressures, and refrigerant mass flow rates.
