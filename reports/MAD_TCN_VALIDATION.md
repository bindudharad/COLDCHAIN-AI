# MAD-TCN Multi-Scale Dilated Forecaster: Final Scientific Validation Report

**Project:** COLDCHAIN-AI: Intelligent Multi-Objective Cold-Chain Optimization  
**Date:** 2026-10-15  
**Code Revision:** Branch `completion-dev`  
**Model Architecture:** Multi-scale Adaptive Dilated Temporal Convolutional Network (`MADTCN`)  
**Input Channels:** 12 engineered features (`temperature`, `humidity`, `ambient_temperature`, `power_kw`, `compressor_state`, `door_open`, `temperature_delta`, `rolling_mean`, `rolling_std`, `temperature_slope`, `ambient_difference`, `power_delta`)  
**Historical Sequence Window:** 60 timesteps (60 minutes history at 1-minute sampling)  
**Lookahead Horizon:** 15 timesteps (15 minutes into future at 1-minute sampling)  
**Evaluation Script:** [`scripts/evaluate_baseline.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/evaluate_baseline.py)  
**Machine-Readable Report:** [`reports/model_baseline_comparison.json`](file:///C:/Projects/Cold-Chain-Ai/reports/model_baseline_comparison.json)  
**Production Baseline Checkpoint:** [`models/mad_tcn_best.pt`](file:///C:/Projects/Cold-Chain-Ai/models/mad_tcn_best.pt)  
**Retrained Checkpoint:** [`models/mad_tcn_retrained.pt`](file:///C:/Projects/Cold-Chain-Ai/models/mad_tcn_retrained.pt)  
**Document Status:** COMPLETE & VERIFIED  
**Data Provenance:** All MAD-TCN training, validation and test results in this report use `SIMULATION` data from `data/raw/simulated_cold_chain.csv`. The daily real cold-storage benchmarks (`Datasets/cold_storage_case_study/`) are evaluated separately using daily statistical baselines — they are **never** cross-validated with, or substituted for, the 1-minute neural model evaluation.

---

## 1. Unified Common Test Split Protocol

All classical baselines and neural network checkpoints were evaluated on the **exact same held-out test split**:
- **Dataset:** `data/raw/simulated_cold_chain.csv` (Sensor `CC-01`, 4,000 raw timesteps)
- **Total Valid Sequences:** 3,925
- **Train Set (70.0%):** 2,747 sequences (fitted with `StandardScaler` strictly on training slice)
- **Validation Set (15.0%):** 588 sequences
- **Held-Out Test Set (15.0%):** **590 sequences**
- **Test Timeline:** `2026-01-03 08:35:00+00:00` to `2026-01-03 18:39:00+00:00`
- **Units:** Physical degrees Celsius (°C)

### Reproducible Execution Command
```powershell
.\.venv\Scripts\python.exe scripts/evaluate_baseline.py
```

---

## 2. Quantitative Comparative Benchmark on Identical Test Records

| Method / Model | Input Features / Normalization | Test MAE (°C) | Test RMSE (°C) | Test $R^2$ Score | Characteristics / Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Naive Persistence ($T_{t+h} = T_t$)** | Last observed reading | **0.1219 °C** | **0.1624 °C** | **0.9928** | Flatline step baseline |
| **2. 5-Step Moving Average** | 5-minute mean | 0.1353 °C | 0.1785 °C | 0.9912 | Short-term smoothed baseline |
| **3. Linear Trend Extrapolation** | 10-minute slope | 0.1535 °C | 0.2107 °C | 0.9878 | First-order velocity extrapolation |
| **4. Original Checkpoint (`mad_tcn_best.pt`)** | Raw 12 channels | 1.0142 °C | 1.2236 °C | 0.5887 | Baseline model trained on unscaled features |
| **5. Retrained Checkpoint (`mad_tcn_retrained.pt`)** | `StandardScaler` (Train fit) | **0.1672 °C** | **0.2131 °C** | **0.9875** | Retrained model (`mad_tcn_retrained.pt`) |

---

## 3. Scientific Investigation: Why Persistence Yields Lower Numerical Error

### 3.1 Horizon-by-Horizon Error Breakdown
A step-by-step audit of forecast error across the 15-minute horizon explains why persistence reports lower aggregate MAE:

| Horizon Step | Lead Time Ahead | Naive Persistence MAE (°C) | MAD-TCN Retrained MAE (°C) | Superior Method for Numerical Fit |
| :--- | :--- | :--- | :--- | :--- |
| $h = 1$ | $t + 1\text{ min}$ | **0.0366 °C** | 0.1381 °C | Persistence (due to thermal lag) |
| $h = 5$ | $t + 5\text{ min}$ | **0.0990 °C** | 0.1565 °C | Persistence |
| $h = 10$ | $t + 10\text{ min}$ | **0.1454 °C** | 0.1653 °C | Persistence |
| $h = 12$ | $t + 12\text{ min}$ | **0.1604 °C** | 0.1716 °C | Persistence |
| $h = 15$ | $t + 15\text{ min}$ | 0.1813 °C | **0.1597 °C** | **MAD-TCN Outperforms Persistence** |

In high-inertia refrigerated rooms sampled at 1-minute intervals, temperature changes slowly ($\approx 0.02\text{--}0.04\text{ }^\circ\text{C/min}$). Naive persistence achieves low error for short horizons ($t+1$ to $t+5$), lowering its 15-step average MAE ($0.1219\text{ }^\circ\text{C}$). However, as lead time approaches 15 minutes, persistence degrades ($0.1813\text{ }^\circ\text{C}$), while MAD-TCN remains stable ($0.1597\text{ }^\circ\text{C}$).

---

## 4. Ground-Truth Future-Breach Anticipation vs Flatline Inability

While naive persistence achieves lower aggregate step MAE, **persistence cannot predict upcoming boundary breaches or turning points**; it predicts zero future change.

### 4.1 Ground-Truth Breach Definition
A future breach event is strictly defined as:
$$\text{Event} = \begin{cases} 1 & \text{if } T_t \le 5.0\text{ }^\circ\text{C} \text{ and } \max_{k \in [1, 15]} T_{t+k} > 5.0\text{ }^\circ\text{C} \\ 0 & \text{otherwise} \end{cases}$$

### 4.2 Classification Performance Across 50 Operational Cold-Chain Scenarios:
Evaluated strictly via [`scripts/compare_nsga2_methods.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/compare_nsga2_methods.py) across 50 chronologically distributed operational scenarios on Sensor `CC-01`:
- **Ground-Truth Excursion Scenarios ($T \le 5.0 \to T_{fut} > 5.0\text{ }^\circ\text{C}$):** 31 scenarios
- **True Positives (TP):** 31 (All excursions successfully anticipated ahead of occurrence)
- **False Positives (FP):** 18 (Conservative alerts where trajectory stayed marginally within bounds)
- **False Negatives (FN):** 0
- **True Negatives (TN):** 1
- **MAD-TCN Breach Recall:** **1.0000 (100% of impending excursions detected early)**
- **MAD-TCN Breach Precision:** **0.6327 (63.3%)**
- **MAD-TCN Breach F1-Score:** **0.7750**
- **Naive Persistence Breach Recall:** **0.0000 (0%)** (Cannot alert before breach occurs)
- **Naive Persistence Breach F1-Score:** **0.0000**

> *Note on 590-Sequence Test Split:* In the continuous 590-sequence held-out test split of `evaluate_baseline.py`, exactly 5 boundary crossing transitions occur in ground truth (due to the sensor operating predominantly within steady-state regime), resulting in sparse boundary statistics. The 50-scenario comparison samples across multi-day diurnal cycles to evaluate excursion dynamics under thermal stress.

---

## 5. Public Real-World Cold-Storage Baseline Evaluations

To establish external empirical validity across genuine physical deployments, baseline forecasting was evaluated on acquired public cold-storage records:

### 5.1 Macro Daily Cold Storage Benchmark (`Cold_Storage_Temp_Data.csv`)
- **Dataset:** 365 daily observations from a commercial cold storage facility ($T_{min} = 1.7^\circ\text{C}$, $T_{max} = 5.0^\circ\text{C}$, $T_{mean} = 2.96^\circ\text{C}$).
- **Evaluation Cadence:** 1-day ahead macro forecasting.
- **Naive Persistence MAE:** **0.4431 °C** (RMSE = 0.5900 °C, $N = 364$).
- **5-Day Moving Average MAE:** **0.4088 °C** (RMSE = 0.5208 °C, $N = 360$).
- **Breach Support:** Exactly **0 readings exceed 5.0 °C** (2 readings equal 5.0 °C). Because no positive excursion events exist in this dataset, it cannot be used to validate breach anticipation algorithms.

### 5.2 High-Frequency Physical Cold-Room Telemetry (University of Hohenheim, Zenodo 15130001)
- **Dataset:** SENSOR03 from the 9-sensor refrigerated room monitoring campaign (DOI: `10.5281/zenodo.15130001`).
- **Cadence & Resolution:** Downsampled to 1-minute sampling interval ($N = 7,037$ continuous readings over 9 days; temperature range $4.8^\circ\text{C}$ to $12.3^\circ\text{C}$, mean $6.54^\circ\text{C}$, std $1.44^\circ\text{C}$).
- **Held-Out Test Set:** Chronological final 15% ($N = 1,041$ sequences of 15-minute horizons).
- **15-Step Average Persistence MAE:** **0.3089 °C** (higher error than 0.1219 °C in simulation, reflecting real-world air draft turbulence and loading dynamics).
- **15th-Step Endpoint Persistence MAE ($t+15$):** **0.4049 °C**.
- **5-Step Moving Average MAE:** **0.3226 °C**.

**Summary Conclusion:**  
1. All MAD-TCN neural weights and breach metrics are evaluated on **`SIMULATION`** data (`data/raw/simulated_cold_chain.csv`).
2. External public datasets (**`PUBLIC_DATASET`**) confirm that physical cold storage environments exhibit higher thermal variability (0.31–0.44 °C baseline MAE) than calibrated simulations.
3. Daily datasets are suited for macro tracking, while 1-minute downsampled physical sensor streams validate high-frequency thermal lag dynamics.
