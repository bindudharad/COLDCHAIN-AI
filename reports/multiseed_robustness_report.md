# Multi-Seed Out-of-Sample Disturbance Robustness & Statistical Reproducibility Report

**Evaluation Scope:** 10 Independent Random Seeds, 50 Matched Scenarios Each (500 Matched Operational Intervals)  
**Seeds Evaluated:** `[201, 202, 203, 204, 205, 206, 207, 208, 209, 210]` (Predeclared, non-overlapping with exploratory seed 101)  
**Evaluated Product Limits:** Food Profile ($0.0^\circ\text{C}$ to $5.0^\circ\text{C}$ with $0.2^\circ\text{C}$ hard buffer)  
**Disturbance Regimes:** Delivery door openings (1–3 min), ambient thermal surges (+1.5 to +3.5 °C), condenser fouling (up to -20% efficiency).  
**Statistical Methods:** 
- Seed-level paired Student's t 95% Confidence Intervals ($df=9, t=2.262$).
- Seed-aware Cluster Bootstrap 95% Confidence Intervals ($B=10,000$ cluster resamples).
- Non-parametric Wilcoxon signed-rank test on independent seed clusters ($N=10$).
- Pooled McNemar's paired test across all 500 matched pairs (with documented i.i.d. assumptions).

---

## 1. Executive Summary: Statistical Validity & Reproducibility Gate

This audit evaluates whether the observed resilience advantage of forecast-guided NSGA-II (Method C) over risk-disabled NSGA-II (Method D) is robust to seed selection and intra-seed correlation.

### Key Empirical Findings:

1. **Replicated Breach Reduction Across All 10 Seeds:**
   - **Method D Breach Rate:** **98.00% ± 1.78%** [t-95% CI: 96.22%, 99.78%]
   - **Method C Breach Rate:** **34.00% ± 6.50%** [t-95% CI: 27.50%, 40.50%]
   - **Absolute Breach Rate Reduction:** **64.00 percentage points (pp)** [t-95% CI: 57.67, 70.33 pp; Cluster Bootstrap: **[58.60, 69.00] pp**].
   - **Relative Breach Count Reduction:** **65.34%** [t-95% CI: 58.85%, 71.82%; Cluster Bootstrap: **[59.85%, 70.42%]**; Pooled: **65.31%**].
2. **Excursion Duration Protection:**
   - **Excursion Saved per 50 Scenarios:** **81.32 min ± 5.49 min** [Cluster Bootstrap: **[76.82, 85.78] min**].
   - **Relative Excursion Reduction:** **65.6% ± 3.7%** [Cluster Bootstrap: **[62.8%, 68.8%]**].
3. **Thermal Safety Headroom:**
   - Method C maintains an average peak chamber temperature of **4.865°C**, delivering **0.739°C ± 0.027°C deeper thermal headroom** compared to Method D (5.605°C) [Cluster Bootstrap: **[0.718, 0.761] °C**].
4. **Modeled Electrical Energy Trade-off:**
   - The proactive precooling commands an average additional modeled energy of **+2.1514 kWh (+28.3%)** per 50 scenarios [Cluster Bootstrap: **[+2.0978, +2.1965] kWh**].
5. **Statistical Significance without Artificially Inflated Assumptions:**
   - Under the non-parametric **Wilcoxon signed-rank test** evaluating the 10 independent seed batches:
     $$W = 55.0, \quad p = 0.00098$$
     All 10 seeds independently favored Method C with zero negative ranks ($2^{-10} = 0.000977$).

---

## 2. Seed-by-Seed Empirical Results Table (N=10 Independent Clusters)

| Seed | Scenarios | Method D Breaches (%) | Method C Breaches (%) | Absolute Diff (pp) | Relative Red. (%) | Excursion Saved (min) | Excursion Red. (%) | Peak Headroom (°C) | Energy Delta (kWh, %) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **201** | 50 | 49 (98.0%) | 16 (32.0%) | +66.0 pp | -67.3% | 83.53 min | -75.2% | +0.751 °C | +2.1334 kWh (+28.6%) |
| **202** | 50 | 50 (100.0%) | 18 (36.0%) | +64.0 pp | -64.0% | 95.54 min | -65.6% | +0.763 °C | +2.1672 kWh (+28.7%) |
| **203** | 50 | 49 (98.0%) | 23 (46.0%) | +52.0 pp | -53.1% | 80.15 min | -63.7% | +0.713 °C | +2.1590 kWh (+28.3%) |
| **204** | 50 | 50 (100.0%) | 11 (22.0%) | +78.0 pp | -78.0% | 76.58 min | -63.8% | +0.788 °C | +2.1751 kWh (+28.7%) |
| **205** | 50 | 46 (92.0%) | 12 (24.0%) | +68.0 pp | -73.9% | 67.66 min | -62.9% | +0.744 °C | +2.2621 kWh (+29.6%) |
| **206** | 50 | 50 (100.0%) | 14 (28.0%) | +72.0 pp | -72.0% | 73.72 min | -63.7% | +0.795 °C | +2.2452 kWh (+29.8%) |
| **207** | 50 | 48 (96.0%) | 20 (40.0%) | +56.0 pp | -58.3% | 84.83 min | -64.5% | +0.744 °C | +2.1775 kWh (+28.3%) |
| **208** | 50 | 50 (100.0%) | 25 (50.0%) | +50.0 pp | -50.0% | 79.99 min | -57.2% | +0.696 °C | +2.1314 kWh (+27.8%) |
| **209** | 50 | 49 (98.0%) | 15 (30.0%) | +68.0 pp | -69.4% | 86.92 min | -72.9% | +0.721 °C | +2.1096 kWh (+27.3%) |
| **210** | 50 | 49 (98.0%) | 16 (32.0%) | +66.0 pp | -67.3% | 84.29 min | -66.5% | +0.679 °C | +1.9538 kWh (+25.7%) |

---

## 3. Standardized Metric Granularity & Aggregation Breakdown

To ensure transparency across reporting levels, the table below provides the metrics across three explicit granularities:
1. **Aggregate Totals across all 500 Scenarios** (cumulative impact over 7,500 simulated operating minutes).
2. **Per-Seed Totals across 50 Scenarios** (mean and spread across the 10 evaluation batches).
3. **Per-Scenario Means per 15-Minute Operational Interval** (normalized impact per single dispatch decision).

| Metric Category | Evaluation Level / Granularity | Method D (Ablation, Risk=0) | Method C (Forecast-Guided) | Delta / Observed Advantage |
| :--- | :--- | :---: | :---: | :---: |
| **Breach Incident Count** | Aggregate Total (N=500) | **490 / 500 (98.0%)** | **170 / 500 (34.0%)** | **-320 breach episodes avoided** |
| | Per-Seed Total (N=50) | 49.0 ± 1.2 breaches | 17.0 ± 4.3 breaches | -32.0 ± 4.2 breaches / seed |
| **Breach Rate** | Absolute Metric (%) | 98.00% [96.22%, 99.78%] | 34.00% [27.50%, 40.50%] | **-64.00 pp** [-70.33, -57.67 pp] |
| | Relative Reduction (%) | Reference (0.0%) | — | **-65.31% pooled** (-65.34% ± 6.48% seed mean) |
| **Continuous Excursion** | Aggregate Total (N=500) | **1,243.26 min** | **430.04 min** | **-813.21 min saved (-65.41%)** |
| | Per-Seed Total (N=50) | 124.33 ± 9.47 min | 43.00 ± 8.60 min | **-81.32 ± 5.49 min saved (-65.6%)** |
| | Per-Scenario Mean (15-min) | **2.487 min / scenario** | **0.860 min / scenario** | **-1.626 min / scenario saved** |
| **Peak Chamber Temp** | Scenario Average (°C) | 5.605°C [5.570, 5.640°C] | 4.865°C [4.817, 4.914°C] | **-0.739°C cooler headroom** |
| **Modeled Electrical Energy**| Aggregate Total (N=500) | **76.1312 kWh** | **97.6455 kWh** | **+21.5143 kWh (+28.26%)** |
| | Per-Seed Total (N=50) | 7.6131 ± 0.082 kWh | 9.7645 ± 0.112 kWh | **+2.1514 ± 0.060 kWh (+28.26%)** |
| | Per-Scenario Mean (15-min) | **0.1523 kWh / scenario** | **0.1953 kWh / scenario** | **+0.0430 kWh / scenario premium** |

> **Denominators & Formulas Note**:
> - **Percentage Points (pp)**: Absolute difference between breach proportions: $\text{Rate}_D - \text{Rate}_C = 98.00\% - 34.00\% = \mathbf{64.00\text{ pp}}$.
> - **Relative Percentage Reduction (%)**: Proportional reduction in breach count relative to Method D baseline: $\frac{490 - 170}{490} \times 100\% = \mathbf{65.31\%}$.
> - **Excursion Duration**: In a 15-minute operational interval, the maximum possible continuous excursion duration is 15.0 minutes. A seed total of 124.33 min reflects the cumulative sum across 50 scenarios ($124.33 / 50 = 2.487\text{ min/scenario}$ on average).

---

## 4. Audit of Statistical Assumptions & Hypothesis Testing

### A. Formal Statistical Hypothesis & Test Specifications
- **Unit of Analysis**: Seed-level cluster outcomes ($N=10$ independent random seed experiments `[201..210]`).
- **Paired Variable**: $\Delta \text{Breach Rate}_s = \text{Breach Rate}_{D, s} - \text{Breach Rate}_{C, s}$ for $s \in \{1 \dots 10\}$.
- **Hypotheses for Non-Parametric Wilcoxon Signed-Rank Test**:
  - **Null Hypothesis ($H_0$)**: The median paired difference between Method D and Method C breach rates is $\le 0$ (Method C provides no resilience advantage or worsens breach rates).
  - **Alternative Hypothesis ($H_1$)**: The median paired difference is $> 0$ (one-sided: Method C reduces breach rates).
- **Test Statistic**: $W = 55.0$ (sum of ranks for positive differences; the maximum possible value for $N=10$).
- **Significance ($p$-value)**:
  - **One-Sided $p$-value**: $p = \left(\frac{1}{2}\right)^{10} = \frac{1}{1024} = \mathbf{0.0009766} \approx \mathbf{0.00098}$.
  - **Two-Sided $p$-value**: $p = 2 \times 0.0009766 = \mathbf{0.001953} \approx \mathbf{0.00195}$.
  - Both one-sided and two-sided specifications reject $H_0$ with high statistical confidence ($\alpha = 0.01$).

### B. Intra-Seed Correlation vs. Cluster-Robust Bootstrap
- **The Assumption**: Pooled 500-scenario tests (such as standard McNemar's test) treat each operational scenario pair as a mutually independent Bernoulli trial.
- **The Reality**: Scenarios generated under the same pseudo-random seed share generator state. If latent clustering exists within a seed batch, scenario-level standard errors can be artificially small, producing astronomically small $p$-values (e.g. McNemar's $\chi^2 = 318.00, p = 3.943 \times 10^{-71}$).
- **The Defensible Resolution**: We report **Seed-Aware Cluster Bootstrap** ($B=10,000$ resamples of the 10 independent seed units), confirming that:
  - Absolute breach rate reduction is robustly bounded between **58.60 pp and 69.00 pp** (95% Bootstrap CI).
  - Relative breach reduction is robustly bounded between **59.85% and 70.42%** (95% Bootstrap CI).
  - Excursion duration saved is robustly bounded between **76.82 min and 85.78 min** per 50 scenarios.

### C. Matched Pairs Contingency Table (500 Scenarios)

| Condition | Method D Maintained Safety ($T \le 5.0^\circ\text{C}$) | Method D Suffered Breach ($T > 5.0^\circ\text{C}$) | Marginal Total |
| :--- | :---: | :---: | :---: |
| **Method C Maintained Safety ($T \le 5.0^\circ\text{C}$)** | **10** (Concordant Safe: 2.0%) | **320** (Breach Prevented by C: 64.0%) | **330** (66.0%) |
| **Method C Suffered Breach ($T > 5.0^\circ\text{C}$)** | **0** (D Safe, C Breached: 0.0%) | **170** (Concordant Breach: 34.0%) | **170** (34.0%) |
| **Marginal Total** | **10** (2.0%) | **490** (98.0%) | **500** (100.0%) |

- **Discordant Pairs**: In **320 cases (64.0%)**, Method C prevented a breach that Method D suffered. In **0 cases (0.0%)** did Method D prevent a breach that Method C suffered.
- **Pooled McNemar's Test**: With continuity correction, $\chi^2 = \frac{(|320 - 0| - 1)^2}{320 + 0} = 318.00$ ($p = 3.943 \times 10^{-71}$). We note that this assumes mutual scenario-level independence; the seed-level Wilcoxon test ($p = 0.00098$) serves as the primary cluster-robust test.

---

## 5. Verification of Comparison Fairness & Mechanism

1. **Information Isolation:**
   - At decision time $t_0$, the optimizer receives only current telemetry $(T_0, T_{\text{amb}})$ and the predicted forecast risk.
   - The disturbance parameters (door opening duration, ambient step magnitude, condenser fouling factor) are generated strictly after decision variables $(u, d)$ are locked.
   - The optimizer has zero future disturbance knowledge.
2. **Coupling Mechanism:**
   - Method D minimizes energy subject to the $0.2^\circ\text{C}$ trajectory buffer, selecting minimal cooling ($u \approx 0.60, d \approx 0.50$) that rides the $4.79^\circ\text{C}$ boundary.
   - Method C penalizes predicted future drift via the MAD-TCN forecast risk, commanding deeper cooling ($u \approx 0.90, d \approx 0.70$).
   - This proactive thermal headroom ($\sim 0.74^\circ\text{C}$ cooler) absorbs subsequent heat shocks, directly explaining the 64 pp reduction in breaches.

---

## 6. Explicit Limitations & Physical Validity Boundaries

1. **Simulated Disturbances:** All heat shocks (door events, ambient surges, condenser fouling) are simulated via ordinary differential equations ($k_{\text{inf}}=0.018, k_{\text{cool}}=0.32$). Live environmental chamber validation remains an external dependency.
2. **Modeled Electrical Energy:** Energy demand is calculated via first-principles thermodynamic lift formulas ($P_{\text{elec}} \times 0.25\text{ h}$). It is not measured on a physical utility power meter.
3. **Hardware Actuation:** Real compressor inverter dynamics (minimum run-times, oil return cycles, variable frequency ramps) are approximated via equivalent continuous intensity $u$ and duty cycle $d$.
