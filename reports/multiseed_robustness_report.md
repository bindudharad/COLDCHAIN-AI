# Multi-Seed Out-of-Sample Disturbance Robustness & Reproducibility Report

**Evaluation Scope:** 10 Independent Random Seeds, 50 Matched Scenarios Each (500 Matched Operational Intervals)  
**Seeds Evaluated:** `[201, 202, 203, 204, 205, 206, 207, 208, 209, 210]` (Predeclared, non-overlapping with seed 101)  
**Product Specification:** Food Profile ($0.0^\circ\text{C}$ to $5.0^\circ\text{C}$ with $0.2^\circ\text{C}$ hard buffer)  
**Disturbance Regimes:** Delivery door openings (1–3 min), ambient heat surges (+1.5 to +3.5 °C), condenser fouling (up to -20% efficiency).  
**Statistical Method:** 95% Student's t Confidence Intervals across independent seed batches ($df=9, t=2.262$), McNemar's paired test for discordant breach transitions.

---

## 1. Executive Summary: Scientific Reproducibility Gate

This study directly tests the scientific reproducibility of the forecast-guidance advantage. Across 10 independent evaluation seeds that were not used during model development or tuning:

1. **Replicated Breach Reduction:** Forecast-guided NSGA-II (Method C) consistently and significantly outperforms the risk-disabled ablation (Method D) across all 10 independent seeds.
   - Method D Breach Rate: **98.00% ± 1.78%** [95% CI: 96.22%, 99.78%]
   - Method C Breach Rate: **34.00% ± 6.50%** [95% CI: 27.50%, 40.50%]
   - Mean Breach Reduction: **64.00 percentage points ± 6.33 pp** [95% CI: 57.67 pp, 70.33 pp]
2. **Excursion Duration Protection:**
   - Excursion Saved: **81.32 min ± 5.49 min** per 50 scenarios (**65.6% ± 3.7% reduction**).
3. **Thermal Safety Headroom:**
   - Method C maintains an average peak chamber temperature of **4.865°C**, providing **0.739°C ± 0.027°C deeper thermal headroom** compared to Method D (5.605°C).
4. **Modeled Energy Premium:**
   - The proactive precooling requires an average additional modeled energy of **+2.1514 kWh (+28.3%)** per 50 scenarios.
5. **Statistical Significance:**
   - In 500 matched scenarios, Method C prevented a breach that Method D suffered in **320 cases (64.0%)**, while Method D prevented a breach in only **0 cases (0.0%)**.
   - McNemar's paired chi-squared statistic: **$\chi^2 = 318.00$ ($p = 3.943e-71$)**, confirming extreme statistical significance.

---

## 2. Seed-by-Seed Empirical Results Table

| Seed | Scenarios | Method D Breaches (%) | Method C Breaches (%) | Breach Diff (pp) | Excursion Saved (min) | Excursion Red. (%) | Peak Headroom (°C) | Energy Delta (kWh, %) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **201** | 50 | 49 (98.0%) | 16 (32.0%) | +66.0 pp | 83.53 min | -75.2% | +0.751 °C | +2.1334 kWh (+28.6%) |
| **202** | 50 | 50 (100.0%) | 18 (36.0%) | +64.0 pp | 95.54 min | -65.6% | +0.763 °C | +2.1672 kWh (+28.7%) |
| **203** | 50 | 49 (98.0%) | 23 (46.0%) | +52.0 pp | 80.15 min | -63.7% | +0.713 °C | +2.1590 kWh (+28.3%) |
| **204** | 50 | 50 (100.0%) | 11 (22.0%) | +78.0 pp | 76.58 min | -63.8% | +0.788 °C | +2.1751 kWh (+28.7%) |
| **205** | 50 | 46 (92.0%) | 12 (24.0%) | +68.0 pp | 67.66 min | -62.9% | +0.744 °C | +2.2621 kWh (+29.6%) |
| **206** | 50 | 50 (100.0%) | 14 (28.0%) | +72.0 pp | 73.72 min | -63.7% | +0.795 °C | +2.2452 kWh (+29.8%) |
| **207** | 50 | 48 (96.0%) | 20 (40.0%) | +56.0 pp | 84.83 min | -64.5% | +0.744 °C | +2.1775 kWh (+28.3%) |
| **208** | 50 | 50 (100.0%) | 25 (50.0%) | +50.0 pp | 79.99 min | -57.2% | +0.696 °C | +2.1314 kWh (+27.8%) |
| **209** | 50 | 49 (98.0%) | 15 (30.0%) | +68.0 pp | 86.92 min | -72.9% | +0.721 °C | +2.1096 kWh (+27.3%) |
| **210** | 50 | 49 (98.0%) | 16 (32.0%) | +66.0 pp | 84.29 min | -66.5% | +0.679 °C | +1.9538 kWh (+25.7%) |

---

## 3. Matched Pairs Contingency Table (500 Scenarios)

| Condition | Method D Maintained Safety (<5.0 °C) | Method D Suffered Breach (>5.0 °C) | Marginal Total |
| :--- | :---: | :---: | :---: |
| **Method C Maintained Safety (<5.0 °C)** | **10** (Concordant Safe) | **320** (Breach Prevented by Forecast) | **330** |
| **Method C Suffered Breach (>5.0 °C)** | **0** (Forecast Ineffective) | **170** (Concordant Breach) | **170** |
| **Marginal Total** | **10** | **490** | **500** |

- **Discordant Ratio:** Method C is successful in avoiding thermal excursion when Method D fails at a ratio of **320 to 0 (320000000000.0:1)**.
- **McNemar's Test:** $\chi^2 = \frac{(|b - c| - 1)^2}{b + c} = 318.00$, two-tailed $p$-value $= 3.943e-71$.

---

## 4. Scientific Limitations & Disclosure Boundaries

1. **Synthetic Disturbance Modelling:** All heat infiltration spikes (door events, ambient steps, condenser fouling) are simulated using physical differential heat equations ($k_{\text{inf}}=0.018$, $k_{\text{cool}}=0.32$). While thermodynamically grounded, these do not substitute for physical wind-tunnel or live cold-room testing.
2. **Modeled Electrical Energy:** Energy values represent mathematical estimates computed as $P_{\text{elec}} \times 0.25\text{ h}$ using thermodynamic lift formulas. Validated savings on physical utility bills require calibrated power meters.
3. **Forecast Transferability:** The underlying MAD-TCN model was trained on historical data from Hohenheim SENSOR03. Transferability to different facility geometries and refrigeration capacities requires domain-specific calibration.
