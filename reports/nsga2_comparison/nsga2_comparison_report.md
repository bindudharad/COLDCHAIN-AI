# NSGA-II Scientific Comparative Audit & Time-Grid Reconciliation Report

**Date:** 2026-10-18  
**Evaluation Scope:** 50 Identical Matched Operational Scenarios from Cold Chain Telemetry  
**Product Profile:** Food (0.0 to 5.0 °C safe limits)  
**Simulation Baseline:** Calibrated thermodynamic room model (k_inf=0.018, k_cool=0.32, ambient 18.8–27.3 °C)  
**Time Grid & Resolution:** 50 scenarios × 15 operational intervals (1.0 min timestep) = **750.0 elapsed minutes** (12.5 operating hours)  
**Trajectory Endpoint Sampling:** 16 discrete temperature samples per scenario (t = 0, 1, 2, ..., 15 min), totaling **800 discrete samples**  

---

## 1. Executive Reconciliation: The Time Axis and Duration Metric

### A. Audit of the Time Axis:
1. **Simulation Timestep:** Delta_t = 1.0 minute.
2. **Endpoint Samples vs Intervals:** Each 15-minute scenario records 16 endpoint-inclusive temperature samples (t = 0, 1, 2, ..., 15 minutes). These 16 points define exactly **15 elapsed operational intervals**: [0, 1], [1, 2], ..., [14, 15].
3. **Total Elapsed Operating Time:** Across 50 scenarios, total operational elapsed time is 50 × 15.0 min = **750.0 minutes**, corresponding exactly to the 12.5 hours of simulated compressor electrical energy consumption.
4. **Resolution of the 800-Minute Citation:** Previous citations of '800 minutes' erroneously treated the 16 point samples as 16 elapsed minutes (50 × 16 = 800), which double-counted the initial state t=0 as an extra elapsed minute. The actual elapsed time is **750.0 minutes**.

### B. Audit of the 479-Minute Metric (Samples vs Continuous Duration):
The figures **583, 565, 544, and 479** were **DISCRETE SAMPLE POINT COUNTS** (out of 800 discrete samples across the 50 scenarios), NOT physical elapsed duration:
- In each scenario, if all 16 discrete samples were > 5.0 °C, the sample counter added 16.
- The difference 583 - 479 = 104 represented a reduction of **104 violating sample points (-17.84%)**.
- **Continuous Physical Excursion Duration (Linear Interpolation across Boundaries):**
  When continuous boundary crossings are interpolated (t* = (5.0 - T_a) / (T_b - T_a)):
  - **Method A (Reactive Baseline):** **543.25 elapsed minutes** of excursion (72.4% of elapsed time).
  - **Method B (Legacy Unconstrained):** **525.52 elapsed minutes** of excursion (70.1% of elapsed time).
  - **Method D (Risk-Disabled Ablation):** **503.51 elapsed minutes** of excursion (67.1% of elapsed time).
  - **Method C (Forecast-Guided NSGA-II):** **449.14 elapsed minutes** of excursion (59.9% of elapsed time).
  - **Actual Duration Saved vs Reactive Control:** **94.12 minutes (-17.32%)**!
  - **Actual Duration Saved vs Unguided Optimization:** **54.37 minutes (-10.80%)**!

Both metrics are fully verified and reported side-by-side below.

---

## 2. Multi-Method Quantitative Benchmark Table

| Metric | Method A: Reactive Baseline | Method B: Legacy Unconstrained | Method D: Risk-Disabled Ablation | Method C: Forecast-Guided NSGA-II |
| :--- | :---: | :---: | :---: | :---: |
| **Control Philosophy** | Fixed hysteresis band (T_0) | Unchecked prediction (n_c=0) | Constrained, blind (fr=0.0) | **Constrained + Forecast Guidance + Fallback** |
| **Total Elapsed Operating Time** | **750.0 minutes** | **750.0 minutes** | **750.0 minutes** | **750.0 minutes** |
| **Continuous Excursion Duration** | **543.25 minutes** | 525.52 minutes | 503.51 minutes | **449.14 minutes (-17.32%)** |
| **Duration Above 5.0 °C** | 543.25 minutes | 525.52 minutes | 503.51 minutes | **449.14 minutes** |
| **Duration Below 0.0 °C (Freezing)** | 0.00 minutes | 0.00 minutes | 0.00 minutes | **0.00 minutes** |
| **Duration Reduction vs Method A** | Reference (0.0 min) | -17.73 min (-3.26%) | -39.75 min (-7.32%) | **-94.12 min (-17.32%)** |
| **Duration Reduction vs Method D** | N/A | N/A | Reference (0.0 min) | **-54.37 min (-10.80%)** |
| **Discrete Violating Samples (out of 800)**| **583 samples** | 565 samples | 544 samples | **479 samples (-104 samples, -17.84%)** |
| **Total Energy (kWh / 50 cycles)** | **7.0321 kWh** | 8.2164 kWh (+16.8%) | 8.7924 kWh (+25.0%) | **10.4838 kWh (+49.1%)** |
| **Mean Electrical Power Demand (kW)** | 0.563 kW | 0.657 kW | 0.703 kW | **0.839 kW** |
| **Mean Compressor Duty Cycle** | 77.6% | 77.3% | 84.2% | **99.1%** |
| **Complete Trajectory Feasible (0–5 °C)** | 0 / 50 (0.0%) | 0 / 50 (0.0%) | 0 / 50 (0.0%) | **18 / 50 (36%)** |
| **Ordinary Algebraic Feasible Scenarios** | N/A | N/A | 23 / 50 (46.0%) | **23 / 50 (46.0%)** |
| **Emergency Fallback Overrides** | 0 | 0 | 27 / 50 (54.0%) | **27 / 50 (54.0%)** |
| **Decision Bounds Compliance** | 100% | 100% | 100% | **100%** |
| **Maximum Trajectory Temperature** | 10.72 °C | 9.36 °C | 9.36 °C | **9.36 °C** |
| **Maximum Threshold Exceedance** | 5.72 °C | 4.36 °C | 4.36 °C | **4.36 °C** |

---

## 3. Proof of Forecast-to-Optimizer Coupling

1. **Direct Decision Sensitivity:** In **22 out of 50 scenarios (44.0%)**, injecting the MAD-TCN future risk directly shifted the Pareto selection compared to Method D (risk-disabled), compelling earlier and stronger compressor activation.
2. **Continuous Excursion Reduction via Lookahead:** Forecast foresight reduced physical violation duration by **54.37 minutes (-10.80%)** relative to the identical constrained optimizer operating blind to future trends.
3. **Data Flow Verification:** Input Window (60x12) -> ml.inference:forecast -> Risk Score -> ColdProblem F0 -> NSGA-II -> Recommendation (u, d).

---

## 4. Energy Model & Units Verification

- **Power demand (kW):** P = max(0.05, 0.25 + 0.035 * max(T_amb - T_cur, 0)) * (0.35 + 0.65 * u) * d
- **Energy consumption (kWh):** Over 15-minute operational intervals, E = P * (15 / 60) = P * 0.25.
- Total electrical energy consumed across 50 15-minute cycles (750.0 elapsed minutes = 12.5 operating hours) is **10.4838 kWh** for Method C, corresponding to an average electrical demand of **0.839 kW**.
- **Data Notice:** Energy figures are analytically simulated from thermodynamic models, not metered on physical 3-phase hardware analyzers.
