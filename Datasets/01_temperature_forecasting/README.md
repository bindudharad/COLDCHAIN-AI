# 01 - IoT Temperature Forecasting (Kaggle Study)

## Source
- **Platform**: Kaggle
- **Classification**: `PUBLIC_DATASET`
- **Format**: Jupyter Notebook + CSV

## Schema
| Column | Type | Unit | Description |
|--------|------|------|-------------|
| timestamp | datetime | UTC | Reading timestamp |
| temperature | float | °C | ESP8266 room temperature sensor |
| humidity | float | % | DHT sensor humidity |

## Research Role
**Baseline Methodology Benchmark**: Ingests ESP8266 room telemetry to validate temporal
trends and sequence modeling methodology. Used to confirm that the MAD-TCN architecture
generalizes beyond simulation data to real physical sensor noise patterns.

## Rows
~97,606 readings

## Domain Classification
- **Domain**: General IoT ambient room temperature monitoring
- **NOT cold-chain**: Measured in residential/office environment (21–51 °C range)
- **Applicability**: Validates temporal forecasting methodology, not cold-chain temperature ranges

## Download Instructions
1. Visit the Kaggle dataset page for IoT Temperature Forecasting
2. Download the dataset files
3. Place CSV files in this directory
4. Run `python scripts/audit_datasets.py` to verify

## License
Refer to the original Kaggle dataset page for license terms.
