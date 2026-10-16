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
- **Cadence & Resolution:** Natively recorded at **5-second sampling** ($84{,}450$ clean physical readings after a 4.19-day sensor offline gap). Downsampled to 1-minute intervals ($N = 7{,}037$ continuous readings over 4.88 days; temperature range $4.8^\circ\text{C}$ to $12.3^\circ\text{C}$, mean $6.54^\circ\text{C}$, std $1.44^\circ\text{C}$).
- **Held-Out Test Set with Purged Boundaries:** Chronological final 15.01% ($N = 1{,}045$ sequences of 15-minute horizons, sequence indices `5917` to `6961`, origin timestamps `2024-09-10 17:44:00` to `2024-09-11 11:08:00`, horizon ends `11:23:00`, evaluated in `scripts/evaluate_real_forecasting.py`). Exactly 28 boundary sequences (14 train-val, 14 val-test) are purged to guarantee zero target-timestamp overlap between splits. Purged train set comprises 4,859 sequences (69.79%, idx 0..4858); purged validation set comprises 1,030 sequences (14.80%, idx 4873..5902). Zero target overlap (overlap = 0) is mathematically enforced and tested.
- **Seeded Neural & Baseline Metrics:** Genuine MAD-TCN (Seed 42, Dilated Conv) achieves $\text{MAE} = \mathbf{0.2637^\circ\text{C}}$ ($R^2 = 0.3876$), Dense MLP (Seed 42) achieves $\text{MAE} = \mathbf{0.2710^\circ\text{C}}$ ($R^2 = 0.3627$), Ridge AR(60) achieves $\text{MAE} = \mathbf{0.2528^\circ\text{C}}$ ($R^2 = 0.4178$), and Naive Persistence yields $\text{MAE} = 0.3048^\circ\text{C}$ ($R^2 = 0.2557$).
- **Early-Warning Dynamic Transition Detection (>6.0 °C):** On safe origins ($T_0 \le 6.0^\circ\text{C}$, $N=706$), Ridge AR(60) achieves $F_1 = 0.4982$ (Recall 37.1%, Precision 75.9%), Dense MLP achieves $F_1 = 0.3566$ (Recall 22.7%, Precision 82.9%), and Genuine MAD-TCN achieves $F_1 = 0.2947$ (Recall 18.3%, Precision 76.1%) vs Persistence $F_1 = 0.0000$ (Missed Event Rate 100.0%).
- **Physical Event-Level Early-Warning Efficacy Across Thresholds:** Evaluated over unique contiguous physical breach episodes in the continuous test series ($N = 1{,}045$ sequences, 17.42 hours):
  - **5.0 °C (Food-Safety Limit — STATISTICALLY INSUFFICIENT / INCONCLUSIVE):** The chamber was pre-breached for 99.2% of the test period (mean temp 5.90 °C), leaving only 8 safe origins and 5 physical events. Persistence: 0/5 (0.0% [0.0–43.4%]); Ridge AR(60): 3/5 (60.0% [23.1–88.2%]); Dense MLP: 3/5 (60.0% [23.1–88.2%]); Genuine MAD-TCN: 3/5 (60.0% [23.1–88.2%]). Due to the wide 95% Wilson confidence interval spanning 23.1% to 88.2%, early warning at 5.0 °C on this dataset is **statistically inconclusive**. Results at higher thresholds do not prove compliance at 5.0 °C.
  - **5.5 °C (Precautionary Bound — SUFFICIENT SAMPLE SUPPORT):** 39 unique events (167 safe origins). Persistence: 0/39 (0.0% [0.0–9.0%]); Ridge AR(60): 38/39 (**97.4%** [86.8–99.5%], lead 7.6 min, 1 FA seq, 1.4 FA/day); Dense MLP: 37/39 (**94.9%** [83.1–98.6%], lead 6.9 min, 1 FA seq, 1.4 FA/day); Genuine MAD-TCN: 38/39 (**97.4%** [86.8–99.5%], lead 7.6 min, 2 FA seqs, 2.8 FA/day).
  - **6.0 °C (Chamber Median — SUFFICIENT SAMPLE SUPPORT):** 44 unique events (706 safe origins). Persistence: 0/44 (0.0% [0.0–8.0%]); Ridge AR(60): 42/44 (**95.5%** [84.9–98.7%], lead 9.9 min, 45 FA seqs, 14 clustered FA episodes, 19.3 FA/day); Dense MLP: 39/44 (**88.6%** [76.0–95.0%], lead 9.1 min, 18 FA seqs, 12 clustered FA episodes, 16.5 FA/day); Genuine MAD-TCN: 27/44 (**61.4%** [46.6–74.3%], lead 9.8 min, 22 FA seqs, 9 clustered FA episodes, 12.4 FA/day).
  - **6.5 °C (Deep Incursions — SUFFICIENT SAMPLE SUPPORT, HIGH UNCERTAINTY):** 14 unique events (943 safe origins). Persistence: 0/14 (0.0% [0.0–21.5%]); Ridge AR(60): 13/14 (**92.9%** [68.5–98.7%], lead 6.5 min, 12 FA seqs); Dense MLP: 8/14 (**57.1%** [32.6–78.6%], lead 6.1 min, 6 FA seqs, 4.1 FA/day); Genuine MAD-TCN: 7/14 (**50.0%** [26.8–73.2%], lead 6.6 min, 5 FA seqs, 2.8 FA/day).
  - *Statistical Assumption Note:* Standard binomial Wilson intervals assume independent Bernoulli trials. Events in this single ~17.42h continuous series possess temporal autocorrelation and environmental coupling (compressor/ambient). Intervals are descriptive binomial confidence intervals conditional on this test trace, not cross-facility inferences.
  - *Operational Finding:* In high-inertia cold storage, persistence fails completely (0.0% detection rate across all thresholds). Both Ridge AR(60), Dense MLP, and Genuine MAD-TCN successfully anticipate physical breach events with 7 to 10 minutes of advance notice. Both neural models generate significantly fewer false alarm sequences than Ridge at 6.0 °C, suppressing unnecessary operator alerts. Genuine MAD-TCN provides the lowest false alarm rate at severe thresholds (2.8 clustered episodes/day at 6.5 °C).
- **Product Limits Context:** The Hohenheim dataset logs operational events ("Products in", "Products out", "Door opened") without documenting specific stored commodity temperature requirements. The 5.0 °C limit is the project's chosen evaluation threshold; recorded conditions ($T_{mean} = 6.54^\circ\text{C}$) do not constitute a proven food-safety failure of that public research facility.

**Summary Conclusion:**  
1. All MAD-TCN neural weights and breach metrics in Section 2–4 are evaluated on **`SIMULATION`** data (`data/raw/simulated_cold_chain.csv`).
2. External public datasets (**`PUBLIC_DATASET`**) confirm that physical cold storage environments exhibit higher thermal variability (0.27–0.44 °C baseline MAE) than calibrated simulations.
3. Daily datasets are suited for macro tracking, while 1-minute downsampled physical sensor streams validate high-frequency thermal lag and early-warning transition dynamics.
