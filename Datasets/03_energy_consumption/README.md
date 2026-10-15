# 03 - Energy Consumption Prediction (Kaggle)

## Source
- **Platform**: Kaggle
- **Classification**: `PUBLIC_DATASET`
- **Format**: CSV

## Schema
| Column | Type | Unit | Description |
|--------|------|------|-------------|
| Temperature | float | °C | Outdoor temperature |
| Humidity | float | % | Relative humidity |
| SquareFootage | int | sq ft | Building area |
| Occupancy | int | count | Number of occupants |
| HVACUsage | string | — | HVAC mode (On/Off) |
| LightingUsage | string | — | Lighting mode |
| RenewableEnergy | float | kWh | Solar/wind generation |
| DayOfWeek | string | — | Day name |
| Holiday | string | — | Holiday indicator |
| EnergyConsumption | float | kWh | Target: total energy consumed |

## Research Role
**Thermal-Environmental Energy Modeling**: Building HVAC energy demand driven
by temperature and occupancy. Validates the relationship between thermal lift
and energy consumption. Achieves **R² = 0.5866** and **MAE = 4.0994 kWh**.

## Rows
~1,000 readings

## Domain Classification
- **Domain**: Residential/commercial building HVAC energy
- **NOT cold-chain energy**: Represents general building HVAC, not walk-in cooler compressors
- **Applicability**: Validates energy-temperature correlation methodology

## Download Instructions
1. Visit the Kaggle dataset page for Energy Consumption Prediction
2. Download `energy_consumption_prediction.csv`
3. Place in this directory
4. Run `python scripts/audit_datasets.py` to verify

## License
Refer to the original Kaggle dataset page for license terms.
