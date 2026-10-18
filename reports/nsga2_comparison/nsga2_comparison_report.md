# NSGA-II Scientific Comparative Audit & Feasibility Reconciliation Report

**Date:** 2026-10-18  
**Evaluation Scope:** 50 Identical Matched Operational Scenarios from Cold Chain Telemetry  
**Product Profile:** Food ($0.0$ to $5.0$ °C safe limits)  
**Simulation Baseline:** Calibrated thermodynamic room model ($k_{inf}=0.018$, $k_{cool}=0.32$, ambient $18.8$–$27.3$ °C)  
**Total Simulated Operating Horizon:** 50 scenarios $\times$ 16 minutes = 800 minutes  

---

## 1. Executive Reconciliation: The Feasibility and Violation Contradiction

### A. Clarification of the 479-Minute Violation Metric:
In previous drafts, a phrasing ambiguity ("reduced violations by 479 minutes (-17.8%)") led to an erroneous backward calculation assuming a 2,693-minute baseline and 2,214-minute outcome. 

**The definitive, reproduced empirical numbers across the 50 matched scenarios are:**
- **Reactive Thermostatic Baseline (Method A):** **583 minutes** of temperature excursion ($> 5.0$ °C).
- **Legacy Unconstrained Optimization (Method B):** **565 minutes** of temperature excursion.
- **Constrained NSGA-II with Predictive Risk Disabled (Method D Ablation):** **544 minutes** of temperature excursion.
- **Forecast-Guided Constrained NSGA-II with Emergency Fallback (Method C):** **479 minutes** of temperature excursion.
- **Empirical Violation Reduction:** Exactly **104 minutes** ($583 - 479 = 104$ min), representing a **-17.84% reduction** against reactive control, and a **65 minute (-11.95%) reduction** against unguided optimization.
- The value **479 minutes** is the **resulting total excursion time** of Method C, not the subtracted difference.

### B. Reconciliation of the "100% Feasibility" Claim:
Claims that "100% of Pareto solutions satisfy physical temperature constraints" were scientifically invalid and conflated decision-variable bounds with trajectory thermal feasibility:
1. **Decision Variable Bounds ($100\%$ Feasible):** All solutions strictly satisfy $u \in [0.1, 1.0]$ and $d \in [0.2, 1.0]$.
2. **Algebraic End-State Constraints ($g_1 \le 0, g_2 \le 0$):** Exactly **23 out of 50 scenarios (46.0%)** admit ordinary feasible Pareto solutions.
3. **Emergency Fallback Overrides:** Exactly **27 out of 50 scenarios (54.0%)** begin in an initial state ($T_0 > 5.0$ °C, reaching up to $9.31$ °C) or encounter ambient heat gain ($0.18 \cdot (T_{amb} - T_0) > 3.20$ °C) where no mathematical solution can bring expected temperature below $4.8$ °C within 15 minutes. In these cases, NSGA-II is algebraically infeasible and triggers an Emergency Fallback Override ($u=1.0, d=1.0$), which is **NOT an ordinary feasible solution**.
4. **Full 15-Minute Trajectory Thermal Feasibility:** Across the complete minute-by-minute simulation, exactly **18 out of 50 scenarios (36.0%)** remain within $[0.0, 5.0]$ °C across all 16 time steps. 32 scenarios experience temperature excursion because cooling takes finite physical time to arrest and reverse pre-existing thermal spikes.

---

## 2. Multi-Method Quantitative Benchmark Table

| Metric | Method A: Reactive Baseline | Method B: Legacy Unconstrained | Method D: Risk-Disabled Ablation | Method C: Forecast-Guided NSGA-II |
| :--- | :---: | :---: | :---: | :---: |
| **Lookahead Foresight** | None ($T_0$ only) | MAD-TCN Risk (Unconstrained) | None ($fr = 0.0$, Constrained) | **Genuine MAD-TCN Risk (Constrained)** |
| **Total Energy (kWh / 50 cycles)** | **7.0321 kWh** | 8.2164 kWh (+16.8%) | 8.7924 kWh (+25.0%) | 10.4838 kWh (+49.1%) |
| **Mean Power Demand (kW)** | 0.563 kW | 0.657 kW | 0.703 kW | 0.839 kW |
| **Mean Compressor Duty Cycle** | 77.6% | 77.3% | 84.2% | 99.1% |
| **Total Temperature Violations** | **583 min** | 565 min | 544 min | **479 min (-17.84%)** |
| **Violation Reduction vs Method A** | Reference (0 min) | -18 min (-3.09%) | -39 min (-6.69%) | **-104 min (-17.84%)** |
| **Violation Reduction vs Method D** | N/A | N/A | Reference (0 min) | **-65 min (-11.95%)** |
| **Scenarios with Any Breach ($> 5.0$ °C)** | 50 / 50 | 50 / 50 | 50 / 50 | 32 / 50 |
| **Complete Trajectory Feasible ($0–5$ °C)** | 0 / 50 (0%) | 0 / 50 (0%) | 0 / 50 (0%) | **18 / 50 (36%)** |
| **Ordinary Algebraic Feasible Scenarios** | N/A | N/A | 23 / 50 (46.0%) | **23 / 50 (46.0%)** |
| **Emergency Fallback Overrides** | 0 | 0 | 27 / 50 (54.0%) | **27 / 50 (54.0%)** |
| **Maximum Trajectory Temperature** | 10.72 °C | 9.36 °C | 9.36 °C | 9.36 °C |
| **Maximum Threshold Exceedance** | 5.72 °C | 4.36 °C | 4.36 °C | 4.36 °C |
| **Average Solve Time** | ~0.1 ms | 247.9 ms | 264.4 ms | 260.6 ms |

---

## 3. Proof of Forecast-to-Optimizer Coupling

1. **Direct Decision Sensitivity:** In **22 out of 50 scenarios (44.0%)**, injecting the MAD-TCN future risk directly shifted the Pareto selection compared to Method D (risk-disabled), compelling earlier and stronger compressor activation.
2. **Excursion Reduction via Lookahead:** Forecast foresight reduced total excursion duration by **65 minutes (-11.95%)** relative to the identical constrained optimizer operating blind to future trends.
3. **Data Flow Verification:** 
   $$\text{Input Window (60x12)} \xrightarrow{\text{ml.inference:forecast}} \hat{y}_{t+1..15} \xrightarrow{\text{core:risk}} \text{Risk Score} \xrightarrow{\text{ColdProblem}} F_0 \xrightarrow{\text{NSGA-II}} \text{Pareto Set} \xrightarrow{\text{Recommendation}} (u, d)$$
4. **Counterfactual Note:** The forecast predicts status-quo trajectory under baseline conditions. In NSGA-II, the forward thermodynamic simulator $dT/dt = k_{inf}(T_{amb} - T) - k_{cool} u \cdot d$ evaluates alternative candidate schedules.

---

## 4. Energy Model & Units Verification

- **Power demand (kW):** $P = \max(0.05, 0.25 + 0.035 \max(T_{amb} - T_{cur}, 0)) \cdot (0.35 + 0.65 u) \cdot d$
- **Energy consumption (kWh):** For 15-minute intervals, $E = P \times (15 / 60) = P \times 0.25$.
- Total electrical energy consumed across 50 15-minute cycles (12.5 operating hours) is **10.4838 kWh** for Method C, corresponding to an average electrical demand of **0.839 kW**.
- **Data Notice:** Energy figures are analytically simulated from thermodynamic models, not metered on physical 3-phase hardware analyzers.
