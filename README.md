# COLDCHAIN-AI: Prediction-Guided Multi-Objective Cold-Chain Optimization

> **Research Objective**: An AI-driven framework integrating Big Data analytics and energy-aware IoT for cold chain logistics.

```
Sensor / IoT Telemetry
        ↓
Data Validation & Vectorized Preprocessing
        ↓
Temporal Feature Engineering (12 Channels)
        ↓
MAD-TCN (Multi-scale Adaptive Dilated Temporal Convolutional Network)
        ↓
15-Step Future Temperature Prediction
        ↓
Future Risk Estimation Engine
        ↓
Prediction-Guided NSGA-II (pymoo)
        ↓
Safety Risk + Energy Consumption Multi-Objective Optimization
        ↓
Non-Dominated Pareto Frontier & Optimal Operating Setpoint
        ↓
Industrial Real-Time Control Center (Django Web Application)
```

---

## 1. Datasets and Experiments

The project integrates a calibrated simulation baseline ground truth alongside 5 public real-world datasets:

| Dataset Directory | Canonical Name | Source | Classification | Rows | Role in Research |
|---|---|---|---|---|---|
| `data/raw/` | `simulated_cold_chain.csv` | Domain Simulator | `SIMULATION` | 12,000 | **Baseline Demonstration Ground Truth**: Multi-sensor cold rooms (CC-01..CC-03) with compressor cycles, door events, and Food profile (0–5 °C). |
| `Datasets/01_temperature_forecasting/` | `iot_temperature_forecasting.ipynb` | Kaggle Study | `PUBLIC_DATASET` | 97,606 | **Baseline Methodology Benchmark**: Ingests ESP8266 room telemetry to validate temporal trends and sequence modeling. |
| `Datasets/02_iot_temperature_readings/` | `iot_temperature_readings.csv` | Kaggle (Manikanta Kumar) | `PUBLIC_DATASET` | 97,606 | **External Hardware Telemetry**: Real ESP8266 sensor node in ambient room conditions (21–51 °C). Trained MAD-TCN achieves **0.7576 °C MAE** and **0.8778 F1 risk detection**. |
| `Datasets/03_energy_consumption/` | `energy_consumption_prediction.csv` | Kaggle | `PUBLIC_DATASET` | 1,000 | **Thermal-Environmental Energy Modeling**: Building HVAC energy demand driven by temperature and occupancy (**R² = 0.5866**, **MAE = 4.0994 kWh**). |
| `Datasets/04_eviot_predictive_maintenance/` | `eviot_predictive_maintenance.csv` | Kaggle | `PUBLIC_DATASET` | 175,393 | **Big Data Scalability Benchmark**: High-frequency (15-min) electrical/thermal telemetry used for streaming ingestion and memory stress testing (< 15s pipeline). |
| `Datasets/05_electricity_forecasting/` | `journey_to_zero_electricity_train.csv` | Kaggle | `PUBLIC_DATASET` | 8,592 | **Weather-Dependent Grid Demand**: Macro hourly electricity consumption correlated with outdoor temperature and dew point. |

All original downloaded archives are preserved strictly unmodified in `Datasets/_original_downloads/`.

---

## 2. Model Performance Summary

- **Architecture**: MAD-TCN (Causal Conv1d with dilations $d \in \{1, 2, 4, 8\}$, GELU, BatchNorm, Feature Attention Gate).
- **Execution Device**: Edge/Server CPU (PyTorch CPU).

| Model / Experiment | Dataset Source | MAE | RMSE | R² Score | Status |
|---|---|---|---|---|---|
| `exp_baseline_simulation` | Simulated Cold Chain (CC-01) | **1.0131 °C** | **1.2224 °C** | **0.5893** | `ACTIVE_BASELINE` |
| `iot_temperature_readings` | Real Physical ESP8266 Telemetry | **0.7576 °C** | **1.2040 °C** | **0.4850** | `EXTERNAL_VALIDATION` |
| `eviot_temperature` | Electric Vehicle Battery Telemetry | 6.1046 °C | 8.6461 °C | -0.0102 | `TRANSIENT_STRESS_TEST` |
| `energy_model` | Building HVAC Electricity Demand | 4.0994 kWh | 4.9602 kWh | 0.5866 | `ENERGY_VALIDATED` |

---

## 3. Prediction-Guided NSGA-II vs Current-State Optimization

Across 50 operational cold-chain cycles evaluated in `reports/nsga2_comparison/nsga2_comparison_report.md`:
- **Method A (Current-State Reactive)**: Consumed **0.5561 kWh / cycle** with 68.5% compressor duty cycle.
- **Method B (Prediction-Guided NSGA-II)**: Consumed **0.4471 kWh / cycle** with 54.8% compressor duty cycle (**19.6% Energy Reduction**).
- **Pareto Frontier**: Generates an average of 43.3 non-dominated Pareto solutions per run with an average solve time of ~303 ms.

---

## 4. Scientific Honesty & Limitations

1. **No Physical Cold-Chain Hardware**: Public datasets measure ambient rooms (ESP8266), residential HVAC, EV battery packs, or municipal power grids. Calibrated cold-storage demonstration is performed using `data/raw/simulated_cold_chain.csv`.
2. **Estimated Energy**: Energy consumption during optimization is **ESTIMATED / SIMULATED** via thermodynamic compressor functions calibrated to ambient differentials ($T_{amb} - T$), not physically measured wattmeter data.
3. **No Physical Compressor Actuation**: Optimization recommendations are algorithmic setpoint targets; no physical PLC or high-voltage compressor hardware is connected.
4. **Historical Public Data**: Public datasets are historical static downloads classified as `PUBLIC_DATASET`, not live streaming telemetry.
5. **Big Data Scalability**: Scalability stress tests at 500K and 1M rows were generated using documented synthetic chronological replication with stochastic noise.

---

## 5. Quickstart & Verification Commands

### Environment Setup
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Dataset Audit & Inventory
```powershell
python backend/scripts/audit_datasets.py
python backend/scripts/generate_quality_and_duplicate_reports.py
```

### Model Training & Benchmarking
```powershell
# Evaluate synthetic demonstration baseline
python backend/scripts/evaluate_baseline.py

# Evaluate real Hohenheim research facility telemetry (DOI: 10.5281/zenodo.15130001)
python backend/scripts/evaluate_real_forecasting.py

# Train MAD-TCN on public IoT temperature dataset
python backend/scripts/train_iot_temperature.py

# Train energy model
python backend/scripts/train_energy_model.py

# Run NSGA-II comparison (Method A vs Method B vs Method C vs Method D)
python backend/scripts/compare_nsga2_methods.py

# Run Big Data scalability stress test (10K to 1M rows)
python backend/scripts/run_scalability_benchmark.py
```

### Running Backend & Frontend
```powershell
# 1. Start Django Backend (API & Ingestion Service)
cd backend
..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

# 2. Start React Frontend (Modern Blue-Pink Single Page App)
cd frontend
npm run dev
# React interface launches at: http://127.0.0.1:5173/
```

### Testing & Verification
```powershell
# Run complete 96 automated tests
cd backend
..\.venv\Scripts\python.exe manage.py test --no-input

# Run automated full-stack Playwright browser verification (12 routes)
.\.venv\Scripts\python.exe backend/scripts/verify_react_frontend.py
```

For complete architectural details, see [FRONTEND_BACKEND_ARCHITECTURE.md](docs/FRONTEND_BACKEND_ARCHITECTURE.md).

