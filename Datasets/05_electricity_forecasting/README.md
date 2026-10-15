# 05 - Journey to Zero: Electricity Forecasting (Kaggle)

## Source
- **Platform**: Kaggle
- **Classification**: `PUBLIC_DATASET`
- **Format**: CSV

## Schema
| Column | Type | Unit | Description |
|--------|------|------|-------------|
| timestamp | datetime | — | Hourly timestamp |
| temperature | float | °F | Outdoor temperature |
| dew_point | float | °F | Dew point temperature |
| humidity | float | % | Relative humidity |
| wind_speed | float | mph | Wind speed |
| cloud_cover | string | — | Cloud coverage description |
| electricity | float | kWh | Hourly electricity consumption |

## Research Role
**Weather-Dependent Grid Demand**: Macro hourly electricity consumption correlated
with outdoor temperature and dew point. Demonstrates weather-energy coupling at
a municipal/grid scale.

## Rows
~8,592 readings

## Domain Classification
- **Domain**: Municipal/grid electricity demand forecasting
- **NOT cold-chain energy**: Represents aggregate grid demand, not individual cold-chain equipment
- **Applicability**: Validates weather-energy correlation for broad context

## Download Instructions
1. Visit the Kaggle dataset page for Journey to Zero Electricity
2. Download `journey_to_zero_electricity_train.csv`
3. Place in this directory
4. Run `python scripts/audit_datasets.py` to verify

## License
Refer to the original Kaggle dataset page for license terms.
