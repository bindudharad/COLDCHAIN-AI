# COLDCHAIN-AI Final Dataset Inventory & Quality Provenance Audit

**Project:** COLDCHAIN-AI: Intelligent Multi-Objective Cold-Chain Optimization  
**Date:** 2026-10-15  
**Code Revision:** Branch `completion-dev`  
**Audit Scripts:**  
- [`scripts/audit_datasets.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/audit_datasets.py)  
- [`scripts/generate_quality_and_duplicate_reports.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/generate_quality_and_duplicate_reports.py)  
**Machine-Readable Reports:**  
- [`reports/dataset_audit_inventory.json`](file:///C:/Projects/Cold-Chain-Ai/reports/dataset_audit_inventory.json)  
- [`reports/data_quality_report.json`](file:///C:/Projects/Cold-Chain-Ai/reports/data_quality_report.json)  
**Document Status:** COMPLETE & VERIFIED  

---

## 1. Active In-Repository Data Store (Present On Disk)

The primary dataset driving all simulation, training, optimization, and API endpoints is:

| Dataset Attribute | Value / Specification |
| :--- | :--- |
| **File Path** | `data/raw/simulated_cold_chain.csv` |
| **File Size** | 1,578,733 bytes (1.51 MB) |
| **Total Rows / Records** | **12,000 records** (Header + 12,000 observations) |
| **Total Columns** | 10 columns |
| **Monitored Sensors** | 3 sensors: `CC-01` (4,000 rows), `CC-02` (4,000 rows), `CC-03` (4,000 rows) |
| **Timestamp Range** | `2026-01-01 00:00:00` to `2026-01-03 18:39:00 UTC` (1-minute continuous resolution) |
| **Domain Classification** | `COLD_CHAIN` (Physical simulation of refrigerated cold rooms) |
| **Verification Status** | **VERIFIED & ACTIVE** |

### Column Schema & Physical Units:
1. `timestamp` (datetime, ISO 8601, UTC, monotonic per sensor)
2. `sensor_id` (string: `CC-01`, `CC-02`, `CC-03`)
3. `temperature` (float, °C, chamber air temperature)
4. `humidity` (float, %, relative humidity [60.0% to 85.0%])
5. `ambient_temperature` (float, °C, outdoor environmental boundary [20.0°C to 32.0°C])
6. `power_kw` (float, kW, compressor electrical power draw [0.25 kW to 1.12 kW])
7. `compressor_state` (int, binary {0, 1}, refrigeration active/idle)
8. `door_open` (int, binary {0, 1}, chamber access intrusion events)
9. `cooling_intensity` (float, continuous [0.0..1.0])
10. `compressor_duty_cycle` (float, continuous [0.0..1.0])

---

## 2. Data Quality & Integrity Audit Summary

Audited via `scripts/generate_quality_and_duplicate_reports.py`:

| Quality Dimension | Test Criterion | Observed Metric | Quality Assessment |
| :--- | :--- | :--- | :--- |
| **Missing Values** | Null or NaN check across all columns | **0 missing values (0.00%)** | **PASS** (100% complete) |
| **Exact Duplicates** | Identical consecutive rows | **0 duplicate records (0.00%)** | **PASS** |
| **Timestamp Collisions** | `(sensor_id, timestamp)` unique constraint | **0 collisions (100% unique)** | **PASS** |
| **Physical Temperature Range** | Valid cold storage bounds (-60 to +70 °C) | Min: -0.12 °C, Max: +11.36 °C | **PASS** (Physical range valid) |
| **Physical Humidity Range** | Relative humidity [0 to 100%] | Min: 59.8%, Max: 84.6% | **PASS** |
| **Physical Ambient Range** | Ambient weather [-40 to +60 °C] | Min: 21.0 °C, Max: 31.8 °C | **PASS** |
| **Instantaneous Power Range** | Operational compressor bounds [0 to 20 kW] | Min: 0.25 kW, Max: 1.12 kW | **PASS** |
| **Timestamp Monotonicity** | Strictly increasing time sequence | 100.0% strictly monotonic per sensor | **PASS** |
| **Statistical Outliers** | Readings $> 3\sigma$ from sensor mean | 14 readings (0.12%) during severe door events | **PASS / EXPECTED** |

---

## 3. External Benchmark Dataset Catalog (`Datasets/` Directory)

To establish standard benchmark references across adjacent domains without distributing multi-gigabyte proprietary files, the repository maintains structured catalog documentation under `Datasets/`:

```
Datasets/
├── 01_temperature_forecasting/
│   └── README.md
├── 02_iot_temperature_readings/
│   └── README.md
├── 03_energy_consumption/
│   └── README.md
├── 04_eviot_predictive_maintenance/
│   └── README.md
├── 05_electricity_forecasting/
│   └── README.md
└── _original_downloads/
    └── README.md
```

### Benchmark Catalog Specification:

| Directory | Domain Name | Benchmark Source & Citation | Expected Records | Schema / Format | Disk Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `01_temperature_forecasting` | Multi-Sensor Cold Storage | Internal physical simulator | 12,000 | 10 cols (`timestamp`, `sensor_id`, `temperature`...) | **LOCAL DISK** (`data/raw/simulated_cold_chain.csv`) |
| `02_iot_temperature_readings` | IoT Temperature Ingestion | Manikanta Kumar (Kaggle ESP8266 IoT readings) | 97,606 | 5 cols (`id`, `room_id`, `noted_date`, `temp`, `out/in`) | `[AWAITING_DOWNLOAD]` (External Open Access) |
| `03_energy_consumption` | Building HVAC Energy Demand | Kaggle Building HVAC Energy Consumption | 1,000 | 5 cols (`SquareFootage`, `Occupancy`, `EnergyConsumption`...) | `[AWAITING_DOWNLOAD]` (External Open Access) |
| `04_eviot_predictive_maintenance` | High-Frequency Battery IoT | Kaggle EV IoT Battery Telemetry | 175,393 | 5 cols (`Timestamp`, `Vehicle_ID`, `Battery_Temp`...) | `[AWAITING_DOWNLOAD]` (External Open Access) |
| `05_electricity_forecasting` | Municipal Grid Electricity | Journey to Zero Municipal Electricity Forecasting | 8,592 | 4 cols (`timestamp`, `demand_mw`, `temp`, `humidity`) | `[AWAITING_DOWNLOAD]` (External Open Access) |

### Strict Scientific Disclosures:
1. **Domain Isolation:** External datasets from residential HVAC (`03_energy_consumption`) and residential living spaces (`02_iot_temperature_readings`) are **never claimed as commercial cold-chain warehouse data**.
2. **Download on Demand:** External benchmarks are cataloged for reproducibility and stress-testing. Users wishing to evaluate adjacent transfer learning can populate the respective folder by following the instructions in `Datasets/*/README.md`.
3. **No Fabricated Data:** The repository does not fabricate or synthesize fake external benchmark files. All internal experiments execute strictly against `data/raw/simulated_cold_chain.csv`.

---

## 4. Newly Cataloged Real-World Cold Storage Benchmark

Through open-access research indexing, the following verified real cold-storage dataset has been cataloged for future offline empirical validation:

- **Dataset Title:** *Temperature and Humidity Time Series of Cold Storage Room Monitoring*
- **Authors & Affiliation:** Elia Henrichs, Florian Stoll, Christian Krupitzer (University of Hohenheim)
- **Repository:** Zenodo (DOI: 10.1109/ACSOS-C66519.2025.00033 / IEEE ACSOS-C 2025)
- **Physical Setup:** 9 DHT22 environmental sensors deployed as distributed Arduino loggers across a physical cold storage chamber (sampling interval: 5 seconds).
- **Recorded Channels:** Date, Time, Chamber Air Temperature (°C), Relative Humidity (%), Door Opening Event Log (`experiment_actions.csv`).
- **Access Status:** Open Access on Zenodo. Programmatic automated fetch from python is restricted by Zenodo Cloudflare bot filtering (HTTP 403 Forbidden). Manual download of `Raw.zip` and `Preprocessed.zip` is supported.

---

## 5. Practical Real Cold-Chain Data Acquisition Guide

For organizations transitioning from simulation to physical cold-storage logging:

### 5.1 What Data Is Required
1. **Chamber Temperature:** Continuous internal air temperature measured at multiple heights (bottom, center, top evaporator discharge) to account for thermal stratification.
2. **Ambient Boundary Temperature:** Outdoor or loading dock temperature to model convective infiltration lift ($T_{ambient} - T_{chamber}$).
3. **Refrigeration Duty Cycle:** Compressor runtime state (binary ON/OFF or variable inverter percentage [0.0..1.0]).
4. **Thermal Intrusion Events:** Door opening sensor contact switches (reed switch / limit switch) logging chamber access events and duration.
5. **Electrical Power Telemetry:** 3-phase true RMS power transducer readings (kW, kVA, Power Factor, and cumulative kWh).

### 5.2 Required Schema & Units
The project's ingestion engine (`core_preprocessing.prepare` and `POST /api/iot/telemetry/`) requires:
```csv
timestamp,sensor_id,temperature,humidity,ambient_temperature,power_kw,compressor_state,door_open
2026-01-01 00:00:00+00:00,CC-01,3.82,71.4,24.5,0.25,0,0
```
- `timestamp`: ISO 8601 UTC format (`YYYY-MM-DD HH:MM:SS+00:00`).
- `sensor_id`: Alphanumeric facility identifier (e.g., `WH-BLR-CHAMBER-01`).
- `temperature`: Degrees Celsius (°C), calibrated to $\pm 0.1\text{ }^\circ\text{C}$ (PT100 RTD or SHT35).
- `power_kw`: Real power in kilowatts (kW), computed as $P = \sqrt{3} \cdot V_{LL} \cdot I \cdot PF / 1000$.

### 5.3 Sample Size Requirements for Model Transfer
- **Initial Baseline Tuning (Linear & Moving Average):** Minimum 1,000 continuous timesteps (approx. 16 hours at 1-minute sampling).
- **MAD-TCN Neural Fine-Tuning:** Minimum 10,000 continuous timesteps (approx. 7 days at 1-minute sampling) capturing at least 3 distinct day/night ambient temperature cycles and $\ge 20$ defrost/door disturbance cycles.
- **NSGA-II Plant Calibration:** Least-squares regression on $\ge 5$ natural warming curves (compressor off) to fit $k_{inf}$ and $\ge 5$ cooldown curves (compressor on) to fit $k_{cool}$.

### 5.4 Data Provenance Spectrum Definitions
All internal reports and web interfaces enforce strict three-tier classification:
- `SIMULATION`: Synthesized via calibrated physical differential equations (current active store: `data/raw/simulated_cold_chain.csv`).
- `PUBLIC_DATASET`: External secondary benchmark data (e.g. Zenodo cold room, Kaggle HVAC, Kaggle EV battery).
- `REAL_SENSOR`: Direct hardware telemetry ingested from physically wired factory sensors.

