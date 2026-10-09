# ColdChain-AI: Comprehensive Dataset Guide & Provenance Registry

**Project:** COLDCHAIN-AI  
**Date:** 2026-10-09  
**Status:** COMPLETE & AUTHORITATIVE  

---

## 1. Dataset Classification Matrix

| Directory / Path | Canonical Name | Provenance Classification | Records | Columns | Source / Attribution | Research Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `data/raw/` | `simulated_cold_chain.csv` | `SIMULATION` | 12,000 | 10 | Calibrated Physical Simulator | **Primary Ground Truth**: Multi-sensor cold rooms (CC-01..03), food profile [0, 5] °C, compressor cycles, door events. |
| `Datasets/01_temperature_forecasting/` | `iot_temperature_forecasting.ipynb` | `PUBLIC_DATASET` | 97,606 | 5 | Kaggle Study | **Methodology Benchmark**: ESP8266 temporal sequence structure. |
| `Datasets/02_iot_temperature_readings/` | `iot_temperature_readings.csv` | `PUBLIC_DATASET` | 97,606 | 5 | Manikanta Kumar (Kaggle) | **External Hardware Validation**: Real physical ESP8266 room telemetry (21–51 °C ambient). |
| `Datasets/03_energy_consumption/` | `energy_consumption_prediction.csv` | `PUBLIC_DATASET` | 1,000 | 5 | Kaggle | **Thermal-Environmental Energy Modeling**: Building HVAC energy demand vs ambient temperature & occupancy. |
| `Datasets/04_eviot_predictive_maintenance/` | `eviot_predictive_maintenance.csv` | `PUBLIC_DATASET` | 175,393 | 5 | Kaggle | **Big Data Scalability Benchmark**: High-frequency thermal/electrical telemetry for memory and throughput stress testing. |
| `Datasets/05_electricity_forecasting/` | `journey_to_zero_electricity_train.csv` | `PUBLIC_DATASET` | 8,592 | 4 | Kaggle (Journey to Zero) | **Macro Grid Electricity Load**: Weather-dependent regional power demand. |

---

## 2. Detailed Dataset Profiles

### 2.1 Simulated Cold Chain (`data/raw/simulated_cold_chain.csv`)
- **Domain:** Cold-Chain Food Storage Logistics (0.0 to 5.0 °C).
- **Sampling Frequency:** 1 minute over 4,000 minutes per sensor (3 sensors: CC-01, CC-02, CC-03 = 12,000 total rows).
- **Features:** `timestamp`, `sensor_id`, `temperature` (°C), `humidity` (%), `ambient_temperature` (°C), `power_kw` (kW), `compressor_state` (0/1), `door_open` (0/1), `product_type`, `location`.
- **Physical Dynamics:** Modeled via differential equations:
  $$T_t = T_{t-1} + 0.018 \cdot (T_{amb} - T_{t-1}) - 0.32 \cdot \text{comp} + 0.16 \cdot \text{door} + \mathcal{N}(0, 0.035^2)$$
- **Missing Values:** 0 nulls across all columns.
- **Suitability:** High. Calibrated specifically for food preservation optimization.

### 2.2 IoT Temperature Readings (`Datasets/02_iot_temperature_readings/`)
- **Domain:** Ambient residential living space telemetry.
- **Hardware:** ESP8266 Wi-Fi node reporting room temperature.
- **Temperature Range:** 21.0 to 51.0 °C.
- **Missing Values:** Zero nulls in core temperature stream.
- **Suitability Assessment:** Suitable for testing temporal neural convolutional feature extraction on physical hardware noise, but **unsuitable for cold-chain safety validation** due to lack of refrigeration dynamics.

### 2.3 Energy Consumption Prediction (`Datasets/03_energy_consumption/`)
- **Domain:** Building HVAC electrical demand.
- **Features:** `Temperature`, `Humidity`, `SquareFootage`, `Occupancy`, `EnergyConsumption` (kWh).
- **Missing Values:** 0 nulls.
- **Suitability Assessment:** Validates thermal-lift energy equations ($R^2 = 0.5866$), but **must not be relabeled as cold-chain compressor energy**.

### 2.4 EVIoT Predictive Maintenance (`Datasets/04_eviot_predictive_maintenance/`)
- **Domain:** Electric vehicle battery pack thermal management.
- **Records:** 175,393 high-frequency rows.
- **Suitability Assessment:** Used strictly for Big Data throughput and ingestion stress tests.

---

## 3. Provenance and Portability Principles

1. **Portable Paths:** All code accesses files using `Path(settings.BASE_DIR) / ...` or relative project paths. Absolute paths referencing developer drives are prohibited.
2. **Original Immutability:** Original raw downloads are strictly preserved in their original format. Preprocessed sequences and model tensors are generated in separate working directories.
3. **No False Equivalence:** A public HVAC dataset is never presented as proof of cold-chain refrigeration performance. Historical static files are never described as live IoT streams.
