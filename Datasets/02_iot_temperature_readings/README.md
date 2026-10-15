# 02 - IoT Temperature Readings (Manikanta Kumar, Kaggle)

## Source
- **Platform**: Kaggle (Manikanta Kumar)
- **Classification**: `PUBLIC_DATASET`
- **Format**: CSV

## Schema
| Column | Type | Unit | Description |
|--------|------|------|-------------|
| id | int | — | Row identifier |
| room_id/area | string | — | Sensor location |
| noted_date | datetime | — | Date of reading |
| temp | float | °F | Raw temperature (Fahrenheit) |
| out/in | string | — | Indoor vs outdoor classification |

## Research Role
**External Hardware Telemetry Validation**: Real ESP8266 sensor node capturing
ambient room conditions (21–51 °C converted). MAD-TCN trained on this dataset
achieves **0.7576 °C MAE** and **0.8778 F1 risk detection score**.

## Rows
~97,606 readings

## Domain Classification
- **Domain**: Real physical IoT hardware sensor readings
- **NOT cold-chain**: Ambient room temperatures, not refrigerated storage
- **Applicability**: Validates MAD-TCN on real hardware noise; temperature ranges differ from cold-chain

## Download Instructions
1. Visit: https://www.kaggle.com/datasets/manikantakumar/iot-temperature-readings
2. Download `iot_temperature_readings.csv`
3. Place in this directory
4. Run `python scripts/audit_datasets.py` to verify

## License
Refer to the original Kaggle dataset page for license terms.
