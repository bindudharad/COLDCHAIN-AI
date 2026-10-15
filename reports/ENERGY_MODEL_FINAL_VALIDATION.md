# Cold-Chain Energy Estimation: Final Scientific Validation & Limitations Report

**Date:** 2026-10-15  
**Model Target:** Refrigeration compressor electrical demand (`power_kw` in kW)  
**Evaluation Scripts:**  
- Energy ML training & evaluation: [`scripts/train_energy_model.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/train_energy_model.py)  
- First-principles thermodynamic analysis: [`scripts/validate_energy.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/validate_energy.py)  
**Machine-Readable Reports:**  
- [`reports/energy_training_report.json`](file:///C:/Projects/Cold-Chain-Ai/reports/energy_training_report.json)  
- [`reports/energy_validation_report.json`](file:///C:/Projects/Cold-Chain-Ai/reports/energy_validation_report.json)  
- Serialized Model: [`models/energy_model.pkl`](file:///C:/Projects/Cold-Chain-Ai/models/energy_model.pkl)  

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

## 3. Scientific Investigation of the Low $R^2$ (0.1362)

1. **Discrete Square-Wave Ground Truth:**  
   In `simulated_cold_chain.csv`, power is modeled as a discrete binary step:
   $$P_{sim} = 0.25 + 0.75 \cdot \text{compressor\_state} + 0.12 \cdot \text{door\_open}$$
   The target fluctuates instantaneously between $0.25\text{ kW}$ (idle) and $1.00\text{ kW}$ (compressor active).
2. **Continuous Predictor Input:**  
   The ML models and optimization formulations use **continuous 15-minute rolling duty cycle averages** ($d \in [0.2, 1.0]$) to provide continuous gradients for NSGA-II optimization. Predicting an instantaneous binary switch from a rolling average inherently limits the fraction of instantaneous variance explained ($R^2 = 0.1362$), although the absolute prediction error is tiny ($\text{MAE} = 0.0142\text{ kW}$).
3. **Analytical Formula Role:**  
   The analytical equation:
   $$E = \left(0.25 + 0.035 \cdot \max(T_{amb} - T_{cur}, 0.0)\right) \cdot (0.35 + 0.65 \cdot u) \cdot d$$
   is designed to provide smooth convex gradients for NSGA-II setpoint optimization, not to fit instantaneous square-wave telemetry.

---

## 4. Hardware Boundary & Data Requirements for Physical Deployment

1. **No Hardware Claim:** Every energy value in reports and UI is explicitly labeled as **`ESTIMATED / SIMULATED`**.
2. **Domain Segregation:** The external Kaggle dataset (`Datasets/03_energy_consumption/`) records residential building HVAC consumption (MAE = 4.0994 kWh, $R^2 = 0.5866$). It is kept strictly distinct and **is never claimed as cold-chain warehouse validation**.
3. **Data Required for Hardware Validation:**  
   True hardware validation requires on-site 3-phase true RMS power transducer readings (kW, kVA, Power Factor), compressor suction/discharge pressures, and refrigerant mass flow rates.
