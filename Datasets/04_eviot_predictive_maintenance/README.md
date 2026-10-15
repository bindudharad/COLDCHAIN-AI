# 04 - EVIoT Predictive Maintenance (Kaggle)

## Source
- **Platform**: Kaggle
- **Classification**: `PUBLIC_DATASET`
- **Format**: CSV

## Schema
| Column | Type | Unit | Description |
|--------|------|------|-------------|
| timestamp | datetime | — | Measurement time |
| voltage | float | V | Electrical voltage |
| current | float | A | Electrical current |
| temperature | float | °C | Component temperature |
| vibration | float | mm/s | Vibration amplitude |
| pressure | float | psi | System pressure |
| humidity | float | % | Environmental humidity |
| operational_hours | float | h | Cumulative runtime |
| power_output | float | kW | Power generation |
| fuel_consumption | float | L/h | Fuel usage rate |

## Research Role
**Big Data Scalability Benchmark**: High-frequency (15-minute) electrical and
thermal telemetry used for streaming ingestion and memory stress testing.
Pipeline processes 175K+ rows in under 15 seconds.

## Rows
~175,393 readings

## Domain Classification
- **Domain**: Electric vehicle / industrial equipment predictive maintenance
- **NOT cold-chain**: EV battery pack and industrial equipment telemetry
- **Applicability**: Validates scalability of data preprocessing pipeline at high volumes

## Download Instructions
1. Visit the Kaggle dataset page for EVIoT Predictive Maintenance
2. Download `eviot_predictive_maintenance.csv`
3. Place in this directory
4. Run `python scripts/audit_datasets.py` to verify

## License
Refer to the original Kaggle dataset page for license terms.
