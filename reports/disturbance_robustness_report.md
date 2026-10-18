# Out-of-Sample Disturbance Robustness & Forecast Guidance Contribution Report

**Evaluation Scope:** 50 Out-of-Sample Disturbed Operational Regimes  
**Seed:** 101 (Documented deterministic protocol)  
**Evaluated Product Limit:** Food Profile (0.0 to 5.0 °C)  
**Disturbance Modes:** Delivery door openings (1–3 min), ambient heat spikes (+1.5 to +3.5 °C), condenser fouling (up to -20% efficiency).

---

## 1. Executive Research Summary

In deterministic scenarios without external disturbances, both Method C (Forecast-Guided NSGA-II) and Method D (Risk-Disabled Ablation) maintain the chamber within nominal safety limits ($0.0	ext<built-in function min>$ continuous breach). However, Method D operates at the exact edge of the safety boundary ($T_{\text{max}} \approx 4.79^\circ\text{C}$) to minimize compressor energy.

This out-of-sample disturbance study tests whether the proactive thermal headroom provided by MAD-TCN forecast guidance provides measurable protection when **unforeseen operational disturbances** occur after the control decision is enacted.

### Key Empirical Findings:

| Evaluation Metric | Method D (Ablation, Risk-Disabled) | Method C (Forecast-Guided NSGA-II) | Scientific Benefit / Cost |
| :--- | :---: | :---: | :---: |
| **Breach Incident Count (>5.0 °C)** | **49 / 50** | **22 / 50** | **-27 breach episodes** |
| **Simulated Breach Incident Rate** | **98.0%** | **44.0%** | **-54.0 percentage points** |
| **Total Continuous Excursion Duration**| **133.42 min** | **61.49 min** | **-71.93 min (-53.9%)** |
| **Mean Peak Chamber Temperature** | **5.662 °C** | **4.952 °C** | **0.710 °C deeper headroom** |
| **Total Modeled Energy Demand** | **7.5108 kWh** | **9.6268 kWh** | **+2.1160 kWh (+28.2%)** |

---

## 2. Research Conclusion & The Safety-Energy Trade-Off

1. **Vulnerability of Boundary-Riding Optimization (Method D):** Without predictive foresight, the optimizer treats all candidates meeting the static threshold equally and strictly minimizes energy. When unforeseen operational heat spikes (such as a 2-minute delivery door opening) occur, **98.0% of scenarios experience thermal violations**.
2. **Resilience of Forecast Guidance (Method C):** By penalizing predicted future thermal drift, MAD-TCN guidance commands proactive precooling. When identical unforeseen heat shocks occur, only **44.0% of scenarios breach**, reducing total excursion duration by **53.9%**.
3. **The Honest Cost:** This superior robustness requires an additional **2.1160 kWh (+28.2%)** of modeled electrical energy across the 50 operational intervals. In cold-chain logistics, this represents a justifiable insurance premium against high-value cargo spoilage.
