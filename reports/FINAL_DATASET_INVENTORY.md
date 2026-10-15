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

## 4. Newly Integrated Real-World Cold Storage Benchmarks (Present On Disk)

The following real cold-storage benchmarks and supporting experimental artifacts are downloaded, extracted, and present on disk under `Datasets/`:

| Dataset / File | File Path | Provenance | File Type | Record Count | Cadence & Details | Experimental Role & Findings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Zenodo Preprocessed Archive** | `Datasets/zenodo_hohenheim/Preprocessed.zip` | `PUBLIC_DATASET` | Archive (ZIP) | 9 CSVs | 5,819,018 bytes | Complete preprocessed multi-sensor dataset from University of Hohenheim (DOI: `10.5281/zenodo.15130001`, CC BY 4.0). |
| **Zenodo Raw Archive** | `Datasets/zenodo_hohenheim/Raw.zip` | `PUBLIC_DATASET` | Archive (ZIP) | 9 CSVs | 5,056,109 bytes | Complete raw sensor logs from nine Arduino-based DHT22 data loggers. |
| **SENSOR01-09 Preprocessed** | `Datasets/zenodo_hohenheim/preprocessed_extracted/` | `PUBLIC_DATASET` | `PREPROCESSED_TIMESERIES` | 156,835 / sensor (1,411,515 total grid cells) | 5-second aligned calendar grid (9.08 days) | Unified 5-second calendar grid containing **1,082,622 valid temperature observations** and **328,893 `NaN` downtime values**. Zero missing timestamps on the 5-second grid. SENSOR03 downsampled to 1-min intervals ($N_{test}=1{,}045$) yields Real-TCN $\text{MAE} = 0.2707^\circ\text{C}$, Ridge AR(60) $\text{MAE} = 0.2524^\circ\text{C}$. |
| **SENSOR01-09 Raw Logs** | `Datasets/zenodo_hohenheim/raw_extracted/` | `PUBLIC_DATASET` | `RAW_TIMESERIES` | 1,083,195 clean observations across 9 files | 5-second native sensor sampling | Unfiltered physical sensor readings directly from SD cards (1,083,199 lines minus 4 mid-file repeated headers). SENSOR03 has 84,450 clean rows with a 4.19-day recording gap. |
| **Cold Storage Temp Data** | `Datasets/cold_storage_case_study/Cold_Storage_Temp_Data.csv` | `PUBLIC_DATASET` | `DAILY_MACRO_OBSERVATIONS` | 365 rows | Daily ($T_{mean} = 2.96^\circ\text{C}$, range 1.7–5.0°C) | Validates daily macro persistence ($\text{MAE}=0.4431^\circ\text{C}$) and moving average ($\text{MAE}=0.4088^\circ\text{C}$). Contains **0 readings $> 5.0^\circ\text{C}$**; cannot validate future breach prediction. |
| **Cold Storage Mar 2018** | `Datasets/cold_storage_case_study/Cold_Storage_Mar2018.csv` | `PUBLIC_DATASET` | `DAILY_MACRO_OBSERVATIONS` | 35 rows | Daily ($T_{mean} = 3.97^\circ\text{C}$, range 3.8–4.6°C) | Validates summer operational cold storage temperature variation (0 readings $> 5.0^\circ\text{C}$). |
| **Zenodo Experiment Actions** | `Datasets/zenodo_hohenheim/experiment_actions.csv` | `PUBLIC_DATASET` | `EVENT_LOGS` | 127 events | Event Table (Timestamps + Actions) | Logs physical door opening and product loading duration without specifying stored product limits. Used to calibrate realistic thermal disturbance schedules in simulation. |
| **Zenodo Sensor Overview** | `Datasets/zenodo_hohenheim/overview.csv` | `PUBLIC_DATASET` | `SUMMARY_STATISTICS` | 42 metrics $\times$ 9 sensors | Summary Matrix | Records physical distribution parameters (min, max, mean, quartiles) across 9 DHT22 sensors in a physical cold chamber. Demonstrates spatial stratification. |
| **Zenodo Arduino Logger** | `Datasets/zenodo_hohenheim/temphum_logger.ino` | `PUBLIC_DATASET` | `SOURCE_CODE` | 132 lines | C++ Firmware | Arduino firmware source code for DHT22 loggers operating at 5-second sampling frequency. |

### Critical Scientific Provenance & Cadence Distinction:
1. **Raw Sensor Telemetry vs. Summaries vs. Event Logs:**  
   `overview.csv` is an aggregate summary matrix and `experiment_actions.csv` is an operational event log. Neither file contains continuous raw time-series measurements. In contrast, the files under `preprocessed_extracted/` and `raw_extracted/` contain continuous, 5-second physical measurements across 9 sensors.
2. **5-Second Native Sampling vs 1-Minute Resampling:**  
   Both raw and preprocessed Hohenheim sensor series are natively sampled at **5-second resolution** (`mode_step = 5 seconds`), NOT a 1-minute grid. The 1,411,515 preprocessed rows represent 9 synchronized 5-second grids of 156,835 timestamps each. Downsampling to 1-minute intervals is performed strictly within `scripts/evaluate_real_forecasting.py` to enable 60-minute window / 15-minute horizon neural modeling.
3. **Product Temperature Limits Disclosure:**  
   The Hohenheim Zenodo repository logs operational actions ("Products in", "Products out", "Door opened") during physical cold-room stress testing, but does **not document the specific product type or its preservation thresholds**. The 5.0 °C threshold used in ColdChain-AI evaluations is the **project's chosen cold-chain food-safety benchmark**, and high temperatures recorded in the public facility ($T_{mean} = 6.54^\circ\text{C}$) do not constitute a proven food-safety failure of that research facility.
4. **Daily Cadence vs. High-Frequency IoT:**  
   The 365-row dataset records daily aggregated observations. It is evaluated separately using daily statistical baselines and is never conflated with high-frequency 1-minute IoT telemetry.
5. **Zenodo Archive Status (DOI: `10.5281/zenodo.15130001`):**  
   The full raw and preprocessed 5-second time series (`Preprocessed.zip` and `Raw.zip`) have been successfully acquired and audited on local disk, with total rows across all 24 CSV datasets on disk reaching **2,507,284**.

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

