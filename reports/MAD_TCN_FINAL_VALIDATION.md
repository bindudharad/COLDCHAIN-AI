# MAD-TCN Multi-Scale Dilated Forecaster: Final Scientific Validation Report

**Date:** 2026-10-15  
**Model Architecture:** Multi-scale Adaptive Dilated Temporal Convolutional Network (`MADTCN`)  
**Input Channels:** 12 engineered features (`temperature`, `humidity`, `ambient_temperature`, `power_kw`, `compressor_state`, `door_open`, `temperature_delta`, `rolling_mean`, `rolling_std`, `temperature_slope`, `ambient_difference`, `power_delta`)  
**Lookahead Horizon:** 15 timesteps (15 minutes into future)  
**Historical Sequence Window:** 60 timesteps (60 minutes history)  
**Evaluation Scripts:**  
- Unified Baseline Benchmark: [`scripts/evaluate_baseline.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/evaluate_baseline.py)  
- Retraining Pipeline: [`scripts/train_iot_temperature.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/train_iot_temperature.py)  
**Machine-Readable Artifacts:**  
- [`reports/model_baseline_comparison.json`](file:///C:/Projects/Cold-Chain-Ai/reports/model_baseline_comparison.json)  
- [`reports/training_report.json`](file:///C:/Projects/Cold-Chain-Ai/reports/training_report.json)  
- Checkpoints: [`models/mad_tcn_best.pt`](file:///C:/Projects/Cold-Chain-Ai/models/mad_tcn_best.pt) & [`models/mad_tcn_retrained.pt`](file:///C:/Projects/Cold-Chain-Ai/models/mad_tcn_retrained.pt)  

---

## 1. Unified Evaluation Protocol (Identical Held-Out Test Set)

To prevent discrepancies caused by differing test periods (e.g. 80/20 vs 70/15/15), all models and classical baselines were evaluated on the **exact same held-out test split**:
- **Dataset:** `data/raw/simulated_cold_chain.csv` (Sensor `CC-01`, 4,000 raw timesteps)
- **Total Valid Sequences:** 3,925
- **Train Set (70.0%):** 2,747 sequences (fitted with `StandardScaler` strictly on training slice)
- **Validation Set (15.0%):** 588 sequences
- **Held-Out Test Set (15.0%):** **590 sequences**
- **Test Set Timeline:** `2026-01-03 08:35:00+00:00` to `2026-01-03 18:39:00+00:00`
- **Units:** Physical degrees Celsius (°C)

### Reproducible Execution Command
```powershell
.\.venv\Scripts\python.exe scripts/evaluate_baseline.py
```

---

## 2. Comparative Benchmark on Identical Held-Out Records

| Method / Model | Preprocessing / Input | Test MAE (°C) | Test RMSE (°C) | Test $R^2$ Score | Characteristics / Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Naive Persistence ($T_{t+h} = T_t$)** | Last observed reading | **0.1219 °C** | **0.1624 °C** | **0.9928** | Flatline step baseline |
| **2. 5-Step Moving Average** | 5-minute mean | 0.1353 °C | 0.1785 °C | 0.9912 | Short-term smoothed baseline |
| **3. Linear Trend Extrapolation** | 10-minute slope | 0.1535 °C | 0.2107 °C | 0.9878 | First-order velocity extrapolation |
| **4. MAD-TCN Original Checkpoint** | Raw 12 channels | 1.0142 °C | 1.2236 °C | 0.5887 | Baseline model (`mad_tcn_best.pt`) |
| **5. MAD-TCN Retrained Checkpoint** | `StandardScaler` (Train fit) | **0.1672 °C** | **0.2131 °C** | **0.9875** | Retrained model (`mad_tcn_retrained.pt`) |

---

## 3. Scientific Reconciliation: Why Persistence Achieves Lower Step MAE

1. **High Thermal Inertia & 1-Minute Sampling:**  
   In refrigerated warehouses, internal temperature drifts slowly ($\Delta T \approx 0.02\text{--}0.04\text{ }^\circ\text{C}$ per minute). A naive flatline assumption ($T_{t+h} = T_t$) naturally achieves a low numerical step MAE ($0.1219\text{ }^\circ\text{C}$).
2. **The Inability of Persistence to Anticipate Thermal Risk:**  
   Naive persistence **cannot predict turning points, compressor cycle shifts, or future boundary breaches**; it can only report what has already occurred.
3. **MAD-TCN Breach Anticipation Performance:**  
   When evaluated on future breach transitions ($T_{current} \le 5.0\text{ }^\circ\text{C}$ but $T_{future} > 5.0\text{ }^\circ\text{C}$ within the 15-minute horizon), MAD-TCN delivers:
   - **Breach Recall:** **1.000** (100% of impending excursions detected early)
   - **Breach Precision:** **0.633**
   - **Breach F1-Score:** **0.775**
   This proactive lookahead capability is what enables the prediction-guided NSGA-II optimizer to engage pre-cooling and eliminate $104$ minutes of violations.

---

## 4. Leakage Verification & Data Compatibility
- **Chronological Split:** Zero lookahead or sequence shuffling.
- **Scaler Isolation:** Feature normalization is fitted strictly on the first 70% of chronological records; test sequences never influence mean or variance scaling.
- **Inference Verification:** Checkpoints [`models/mad_tcn_best.pt`](file:///C:/Projects/Cold-Chain-Ai/models/mad_tcn_best.pt) and [`models/mad_tcn_retrained.pt`](file:///C:/Projects/Cold-Chain-Ai/models/mad_tcn_retrained.pt) load without warnings or missing keys.
