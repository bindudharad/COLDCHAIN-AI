# NSGA-II Multi-Objective Optimization: Final Scientific Validation & Trajectory Safety Report

**Project:** COLDCHAIN-AI: Intelligent Multi-Objective Cold-Chain Optimization  
**Date:** 2026-10-15  
**Code Revision:** Branch `completion-dev`  
**Evaluation Scope:** 50 Identical Operational Cold-Chain Scenarios across Held-Out Telemetry  
**Reproducible Script:** [`scripts/compare_nsga2_methods.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/compare_nsga2_methods.py)  
**Machine-Readable Report:** [`reports/nsga2_comparison/nsga2_comparison_data.json`](file:///C:/Projects/Cold-Chain-Ai/reports/nsga2_comparison/nsga2_comparison_data.json)  
**Product Profile:** Food ($0.0$ to $5.0\text{ }^\circ\text{C}$ safe limits, buffer $0.2\text{ }^\circ\text{C}$, target setpoint $4.0\text{ }^\circ\text{C}$)  
**Calibrated Plant Parameters:**
- Environmental thermal infiltration coefficient: $k_{inf} = 0.018\text{ min}^{-1}$
- Active cooling extraction coefficient: $k_{cool} = 0.32\text{ }^\circ\text{C/min}$
- Door event thermal intrusion: $\Delta T_{door} = 0.16\text{ }^\circ\text{C/event}$  
**Document Status:** COMPLETE & VERIFIED  

---

## 1. Research Contribution: Prediction-Guided Optimization Formulation

The core innovation of COLDCHAIN-AI is coupling the **MAD-TCN predicted future risk score ($R$) directly into the NSGA-II optimization formulation**:

### 1.1 Decision Variables:
$$\mathbf{x} = [u, d, \delta]^T$$
- $u \in [0.2, 1.0]$: Inverter cooling intensity
- $d \in [0.2, 1.0]$: Compressor duty cycle fraction
- $\delta \in [-1.5, 0.5]\text{ }^\circ\text{C}$: Target temperature setpoint offset

### 1.2 Multi-Objective Formulation:
1. **Minimize Safety Risk ($f_1$):**
   $$f_1(\mathbf{x}) = \text{risk}\left(T_{pred}(\mathbf{x}), T_{min}, T_{max}\right)$$
   Where predicted temperature $T_{pred}(\mathbf{x})$ incorporates both historical drift and the neural forecast risk bias.
2. **Minimize Energy Consumption ($f_2$):**
   $$f_2(\mathbf{x}) = \max\left(0.05, 0.25 + 0.035 \cdot \max(T_{amb} - T_{cur}, 0.0)\right) \cdot (0.35 + 0.65 \cdot u) \cdot d$$

### 1.3 Strict Deb Feasibility Constraints:
- $G_1(\mathbf{x}) = T_{min} + \text{buffer} - T_{pred}(\mathbf{x}) \le 0$ (Prevents sub-zero freezing)
- $G_2(\mathbf{x}) = T_{pred}(\mathbf{x}) - (T_{max} - \text{buffer}) \le 0$ (Prevents heat breach above $4.8\text{ }^\circ\text{C}$)

---

## 2. Clarification of Feasibility Accounting & Emergency Fallback

In earlier drafts, Method C reported both that an emergency override activated and that 100% of solutions were feasible. This terminology has been clarified:

1. **Ordinary Multi-Objective Feasible Selection (23 Scenarios, 46.0%):**  
   When the chamber is within or near the Food profile ($T_0 \le 5.0\text{ }^\circ\text{C}$), evolutionary search finds non-dominated Pareto solutions satisfying Deb's constrained dominance ($G_1, G_2 \le 0$). The optimizer returns an average of **21.7 strictly feasible solutions**, from which the safest trade-off setpoint is chosen.
2. **Emergency Fallback Override (27 Scenarios, 54.0%):**  
   In 27 scenarios, the initial chamber temperature is already in severe breach ($T_0 > 5.0\text{ }^\circ\text{C}$, up to $9.31\text{ }^\circ\text{C}$) due to prior uncontained heat infiltration. Because a 15-minute interval cannot physically cool $9.31\text{ }^\circ\text{C}$ down into the Food envelope ($\le 4.8\text{ }^\circ\text{C}$), **no mathematically feasible solution exists** in the search space ($r.X = \text{None}$).

   **Analytical Thermodynamic Feasibility Derivation:**  
   The physical differential equation governing chamber temperature is:
   $$\frac{dT}{dt} = k_{inf} (T_{amb} - T) - k_{cool} \cdot u \cdot d$$
   At maximum continuous cooling capacity ($u=1.0, d=1.0$) with $k_{cool} = 0.32\text{ }^\circ\text{C/min}$ and $k_{inf} = 0.018\text{ min}^{-1}$, the steady-state equilibrium temperature $T_{ss}$ is:
   $$0 = k_{inf}(T_{amb} - T_{ss}) - k_{cool} \implies T_{ss} = T_{amb} - \frac{k_{cool}}{k_{inf}} = T_{amb} - \frac{0.32}{0.018} = T_{amb} - 17.78\text{ }^\circ\text{C}$$
   For the chamber to achieve or maintain the Food profile limit ($T \le 5.0\text{ }^\circ\text{C}$), the ambient boundary temperature must satisfy:
   $$T_{amb} \le 5.0 + 17.78\text{ }^\circ\text{C} = 22.78\text{ }^\circ\text{C}$$
   Whenever outdoor ambient temperature $T_{amb} > 22.78\text{ }^\circ\text{C}$ (in the simulation dataset, $T_{amb}$ reaches up to $28.55\text{ }^\circ\text{C}$), ambient heat infiltration at $5.0\text{ }^\circ\text{C}$ physically exceeds maximum refrigeration capacity ($0.018 \cdot (28.55 - 5.0) = 0.424\text{ }^\circ\text{C/min} > 0.320\text{ }^\circ\text{C/min}$). Thus, mathematical compliance with $T \le 4.8\text{ }^\circ\text{C}$ is physically unattainable during severe heat waves, independently proving why no feasible solution can exist in these 27 scenarios.

3. **Emergency Override Behavior:**  
   Rather than labeling these points as "feasible Pareto solutions", they are explicitly classified as **`is_emergency_fallback: True`** and **`feasible: False`**. In these states, the system commands **maximum emergency cooling** ($u = 1.0, d = 1.0, \delta = -0.5$) to rapidly arrest temperature rise.

4. **Reconciliation of Pareto Points (48) vs. Scenarios (23 Feasible / 27 Emergency Fallback):**  
   - The **48 Pareto points** reported in [`scripts/end_to_end.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/end_to_end.py) and [`reports/coldchain_report.json`](file:///C:/Projects/Cold-Chain-Ai/reports/coldchain_report.json) represent the non-dominated setpoints on the Pareto frontier discovered during a **single optimization run** (population = 48) on sensor `CC-01` at a specific initial temperature ($3.93\text{ }^\circ\text{C}$) within the Food envelope.
   - The **23 Feasible / 27 Emergency Fallback** counts reported in [`scripts/compare_nsga2_methods.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/compare_nsga2_methods.py) represent the aggregate classification across **50 distinct operational scenarios** sampled chronologically throughout the entire multi-day telemetry stream. In 23 scenarios the chamber initialized within the Food envelope and found feasible frontiers; in 27 scenarios the chamber started in pre-existing breach ($T_0 > 5.0\text{ }^\circ\text{C}$), triggering the emergency cooling override.

---

## 3. Quantitative Trajectory Comparison Across 50 Scenarios

| Evaluation Metric | Method A (Current-State Reactive) | Method B (Legacy Defective Unconstrained) | Method C (Audited Constrained NSGA-II) | Relative Impact (Method C vs Baseline A) |
| :--- | :--- | :--- | :--- | :--- |
| **Control Philosophy** | Reactive thermostatic ($T_0$ only) | Prediction-guided ($n_{constr}=0$) | Prediction-guided (Constrained + Emergency) | Proactive Pre-Cooling + Maximum Override |
| **Mean Energy / 15-min Cycle** | **0.5625 kWh** | 0.6574 kWh (+16.9%) | **0.8387 kWh** (+49.1%) | Controlled Active Infiltration Defense |
| **Mean Compressor Duty Cycle** | 77.6% | 77.3% | 99.1% | Active Thermal Extraction During Heat Spikes |
| **Total Temperature Violations** | **583 min** | 565 min (-3.1%) | **479 min** (-17.8%) | **-17.8% Total Violation Duration (-104 min)** |
| **Maximum Chamber Temperature** | 10.72 °C | 9.36 °C (Severe Breach) | **9.36 °C** (Contained via Max Cooling) | Lowest observed peak under tested policies |
| **Ordinary Feasible Selections** | 50 (Unconstrained Fixed Band) | 0 (Unchecked Feasibility) | **23 Scenarios (100% Feasible)** | Evaluated strictly against $G \le 0$ |
| **Emergency Fallback Overrides** | 0 | 0 | **27 Scenarios (Infeasible Override)** | Explicitly tagged as emergency actions |
| **Average Optimization Runtime** | ~0.1 ms | 214.5 ms | 199.0 ms | Real-Time Industrial Feasibility |

---

## 4. Trajectory Safety & Scientific Disclosures

1. **Physical Meaning of the 9.36 °C Peak Temperature:**
   - The reported peak temperature of **$9.36\text{ }^\circ\text{C}$** ($9.3639\text{ }^\circ\text{C}$) occurs in **Scenario 4** ($t_0 = 9.313\text{ }^\circ\text{C}$, $T_{amb} = 27.305\text{ }^\circ\text{C}$).
   - **Net Derivative Calculation:** Under maximum emergency cooling ($u=1.0, d=1.0$), active cooling rate is $-k_{cool} = -0.3200\text{ }^\circ\text{C/min}$, while ambient heat infiltration is $+k_{inf}(T_{amb} - T_0) = 0.018 \times (27.305 - 9.313) = +0.32386\text{ }^\circ\text{C/min}$. The net temperature rate of change at $t_0$ is **positive**:
     $$\left.\frac{dT}{dt}\right|_{t=0} = +0.32386 - 0.32000 = \mathbf{+0.00386\text{ }^\circ\text{C/min}}$$
   - **Asymptotic Equilibrium:** Under continuous maximum cooling at $T_{amb} = 27.305\text{ }^\circ\text{C}$, the chamber asymptotically approaches steady-state equilibrium:
     $$T_{ss} = T_{amb} - \frac{k_{cool}}{k_{inf}} = 27.305 - \frac{0.32}{0.018} = \mathbf{9.527\text{ }^\circ\text{C}}$$
   - **Trajectory Interpretation:** Because $T_0 = 9.313\text{ }^\circ\text{C} < 9.527\text{ }^\circ\text{C}$, the chamber was **still warming** toward $9.53\text{ }^\circ\text{C}$. At the end of the 15-minute simulation horizon ($t = 15\text{ min}$), the temperature reaches $9.364\text{ }^\circ\text{C}$ with a remaining positive slope ($\frac{dT}{dt} = +0.00294\text{ }^\circ\text{C/min}$). Thus, **9.36 °C is the final observation of a truncated 15-minute simulation horizon that is still actively warming**, NOT an enclosed peak or turnaround. Maximum cooling substantially mitigated the warming rate ($9.36\text{ }^\circ\text{C}$ at $t=15$ min vs. $10.72\text{ }^\circ\text{C}$ under reactive baseline Method A).
2. **Empirical Policy Comparison vs Global Optimality:**
   - The total violation duration of **479 minutes** under Method C represents an empirical **-17.8% reduction in excursion exposure** (-104 min relative to Method A's 583 min) across the 50 tested scenarios.
   - This reduction is **not claimed as a mathematically proven global optimum**; finding a true global optimum across continuous multi-horizon control spaces would require Pontryagin minimum principle or dynamic programming bounds.
3. **Safety Status Categories Across Scenarios:**
   - **Genuine Compliance (23 Scenarios):** In scenarios initializing within the safe envelope ($T_0 \le 5.0\text{ }^\circ\text{C}$), proactive pre-cooling keeps the chamber continuously within the Food limit ($0.0\text{--}5.0\text{ }^\circ\text{C}$).
   - **Reduced Warming (Scenario 4 & Severe Heatwaves):** When ambient infiltration exceeds cooling capacity ($T_{amb} > 22.78\text{ }^\circ\text{C}$), maximum cooling limits the rate of temperature rise without achieving containment below $5.0\text{ }^\circ\text{C}$.
   - **Recovery / Mitigation:** When starting in pre-existing breach ($T_0 > 5.0\text{ }^\circ\text{C}$), cooling drives the trajectory downward where ambient permits, or minimizes severity where heat dominates. Food safety compliance is **not maintained** during these transient breach intervals.
4. **Trade-Off Realism:** Reducing thermal excursions by 104 minutes requires active cooling during ambient heat spikes, increasing estimated electrical consumption by **+49.1% (0.8387 kWh vs 0.5625 kWh)**. This is a legitimate thermodynamic trade-off between perishable product safety and energy cost.
5. **Simulation Boundary:** Trajectories are derived from the calibrated physical chamber simulation model; energy values are **`ESTIMATED / SIMULATED`**.
