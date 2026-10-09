# Comprehensive Source Provenance & Scientific Attribution

**Project:** COLDCHAIN-AI  
**Framework:** AI-Driven Framework Integrating Big Data Analytics and Energy-Aware IoT for Cold Chain Logistics  
**Date:** 2026-10-09  
**Status:** COMPLETE & AUTHORITATIVE  

---

## 1. Architectural Provenance & Independent Implementation

This codebase is an original, clean-room implementation of a prediction-guided cold-chain decision support platform. Architectural and algorithmic concepts were informed by foundational academic research:

1. **MAD-TCN Architectural Concepts:**
   - Conceptual reference: `qianmo2001/MAD-TCN` (Multi-scale adaptive dilated temporal convolution).
   - Implementation: Original PyTorch module (`ml/mad_tcn.py`) featuring 4-branch parallel dilated causal convolutions ($d \in \{1, 2, 4, 8\}$), adaptive attention gate pooling, GELU non-linearities, and causal residual connections.

2. **Multi-Objective Evolutionary Optimization:**
   - Conceptual reference: `wmaolin43/hydrobalance` for multi-objective optimization problem structuring; K. Deb et al. (2002) for Deb's constrained dominance principles.
   - Implementation: Original `pymoo` problem (`optimization/nsga2_optimizer.py`) with hard inequality constraints ($g_1, g_2 \le 0$) enforcing thermodynamic chamber safety limits.

3. **Telemetry Ingestion & Quality Guards:**
   - Conceptual reference: `Anusha0501/ThermaGuard-AI` for IoT ingestion patterns.
   - Implementation: Original Django REST endpoint (`apps/monitoring/views.py` `iot_telemetry_api`) with strict range enforcement, unit conversion, duplicate suppression, and provenance tagging.

---

## 2. Dataset Provenance Registry

| Dataset Identifier | Canonical File Path | Provenance Classification | Records | Source / Attribution | Research Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `simulated_cold_chain.csv` | `data/raw/simulated_cold_chain.csv` | `SIMULATION` | 12,000 | Domain Physical Model (`scripts/generate_sample_data.py`) | Baseline ground truth for cold-room thermal inertia, door events, and compressor cycling. |
| `iot_temperature_readings.csv` | `Datasets/02_iot_temperature_readings/` | `PUBLIC_DATASET` | 97,606 | Manikanta Kumar (Kaggle, ODbL) | Ambient room ESP8266 hardware telemetry validation. |
| `energy_consumption_prediction.csv` | `Datasets/03_energy_consumption/` | `PUBLIC_DATASET` | 1,000 | Kaggle Open Datasets | Thermal-environmental building HVAC energy modeling. |
| `eviot_predictive_maintenance.csv` | `Datasets/04_eviot_predictive_maintenance/` | `PUBLIC_DATASET` | 175,393 | Kaggle Research Benchmark | High-frequency telemetry Big Data scalability stress testing. |
| `journey_to_zero_electricity.csv` | `Datasets/05_electricity_forecasting/` | `PUBLIC_DATASET` | 8,592 | Journey to Zero (Kaggle) | Municipal power grid demand vs. outdoor temperature. |

---

## 3. Data Integrity & Scientific Governance Disclosures

1. **No Conflation of Domains:** Ambient room ESP8266 datasets and building HVAC energy datasets are never represented as cold-chain walk-in freezer data.
2. **Provenance Field Segregation:** The database model `SensorReading` enforces a `data_source` field distinguishing `SIMULATION`, `PUBLIC_DATASET`, and `REAL_SENSOR`.
3. **No Physical Actuator Connection:** All outputs represent supervisory decision-support setpoints; no real high-voltage compressor hardware is actuated.
