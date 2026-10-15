# MAD-TCN Multi-Scale Dilated Forecaster: Final Scientific Validation Report

**Date:** 2026-10-15  
**Code Revision:** Branch `completion-dev`  
**Model Architecture:** Multi-scale Adaptive Dilated Temporal Convolutional Network (`MADTCN`)  
**Input Channels:** 12 engineered features (`temperature`, `humidity`, `ambient_temperature`, `power_kw`, `compressor_state`, `door_open`, `temperature_delta`, `rolling_mean`, `rolling_std`, `temperature_slope`, `ambient_difference`, `power_delta`)  
**Lookahead Horizon:** 15 timesteps (15 minutes into future)  
**Historical Sequence Window:** 60 timesteps (60 minutes history)  
**Evaluation Script:** [`scripts/evaluate_baseline.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/evaluate_baseline.py)  
**Machine-Readable Report:** [`reports/model_baseline_comparison.json`](file:///C:/Projects/Cold-Chain-Ai/reports/model_baseline_comparison.json)  
**Production Baseline Checkpoint:** [`models/mad_tcn_best.pt`](file:///C:/Projects/Cold-Chain-Ai/models/mad_tcn_best.pt)  
**Retrained Checkpoint:** [`models/mad_tcn_retrained.pt`](file:///C:/Projects/Cold-Chain-Ai/models/mad_tcn_retrained.pt)  

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

| Horizon Step | Lead Time | Naive Persistence MAE (°C) | MAD-TCN Retrained MAE (°C) | Superior Method for Numerical Fit |
| :--- | :--- | :--- | :--- | :--- |
| $h = 1$ | $t + 1\text{ min}$ | **0.0366 °C** | 0.1381 °C | Persistence (due to thermal lag) |
| $h = 5$ | $t + 5\text{ min}$ | **0.0990 °C** | 0.1565 °C | Persistence |
| $h = 10$ | $t + 10\text{ min}$ | **0.1454 °C** | 0.1653 °C | Persistence |
| $h = 12$ | $t + 12\text{ min}$ | **0.1604 °C** | 0.1716 °C | Persistence |
| $h = 15$ | $t + 15\text{ min}$ | 0.1813 °C | **0.1597 °C** | **MAD-TCN Outperforms Persistence** |

In high-inertia refrigerated rooms sampled at 1-minute intervals, temperature changes slowly ($\approx 0.02\text{--}0.04\text{ }^\circ\text{C/min}$). Naive persistence achieves low error for short horizons ($t+1$ to $t+5$), lowering its 15-step average MAE ($0.1219\text{ }^\circ\text{C}$). However, as lead time approaches 15 minutes, persistence degrades ($0.1813\text{ }^\circ\text{C}$), while MAD-TCN remains stable ($0.1597\text{ }^\circ\text{C}$).

### 3.2 Ground-Truth Breach Anticipation vs Flatline Inability
While naive persistence achieves lower aggregate step MAE, **persistence cannot predict upcoming boundary breaches or turning points**; it predicts zero future change.

When evaluated specifically on upcoming breach transitions ($T_{current} \le 5.0\text{ }^\circ\text{C}$ but $T_{future} > 5.0\text{ }^\circ\text{C}$ within the 15-minute horizon):
- **MAD-TCN Breach Recall:** **1.000** (100% of impending excursions detected early)
- **MAD-TCN Breach Precision:** **0.633**
- **MAD-TCN Breach F1-Score:** **0.775**

**Conclusion:** Naive persistence is the superior numerical forecasting baseline for short-term thermal tracking. MAD-TCN is the superior model for proactive thermal risk anticipation and early excursion warnings.
