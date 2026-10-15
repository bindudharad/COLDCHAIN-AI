# Scientific Correction Changelog & Audit Reconciliation

**Date:** 2026-10-15  
**Project:** COLDCHAIN-AI  
**Branch:** `completion-dev`  

---

## 1. Corrected Claims & Discrepancies Resolved

| Area / Claim | Previous Inconsistency | Scientific Root Cause | Corrected Resolution & Verified Metric | Affected Files |
| :--- | :--- | :--- | :--- | :--- |
| **MAD-TCN Evaluation Set** | Claimed retrained model had $\text{MAE} = 0.1672\text{ }^\circ\text{C}$ on 590 sequences, while baseline had persistence $\text{MAE} = 0.1144\text{ }^\circ\text{C}$ on 785 sequences (different splits). | Split mismatch (80/20 vs 70/15/15). Persistence was evaluated on 785 sequences, retrained MAD-TCN on 590 sequences. | Unified all models onto identical 70/15/15 held-out test split (590 sequences, Jan 3 08:35 to 18:39 UTC). Persistence $\text{MAE} = 0.1219\text{ }^\circ\text{C}$; retrained MAD-TCN $\text{MAE} = 0.1672\text{ }^\circ\text{C}$. MAD-TCN's demonstrated superiority is in future breach anticipation ($\text{Recall} = 1.000$, $\text{F1} = 0.775$), not step flatlining. | `scripts/evaluate_baseline.py`, `reports/model_baseline_comparison.json`, `reports/MAD_TCN_FINAL_VALIDATION.md` |
| **NSGA-II Maximum Temperature** | Method C reported -17.8% violation duration, but max temperature was $11.36\text{ }^\circ\text{C}$ vs $10.72\text{ }^\circ\text{C}$ for reactive baseline. | When starting at $T_0 = 9.31\text{ }^\circ\text{C}$ under $27.31\text{ }^\circ\text{C}$ ambient, evolutionary search found zero feasible single-interval solutions. The previous fallback throttled cooling to $70\%$ duty, causing ambient infiltration to spike the chamber. | Implemented emergency cooling override ($u = 1.0, d = 1.0, \delta = -0.5$) when chamber is in excursion. Peak temperature under Method C dropped to **$9.36\text{ }^\circ\text{C}$** (contained), beating baseline ($10.72\text{ }^\circ\text{C}$) while maintaining -17.8% violations. | `optimization/nsga2_optimizer.py`, `scripts/compare_nsga2_methods.py`, `reports/nsga2_comparison/nsga2_comparison_data.json`, `reports/NSGA2_FINAL_VALIDATION.md` |
| **Energy Estimation Units** | Comparing analytical formula output (in kWh per 15-minute interval) against target `power_kw` (instantaneous kW) yielded negative $R^2$ (-4.1991). | Dimensional mismatch ($E$ in kWh vs $P$ in kW). | Documented formula role as a continuous convex optimization surrogate. Clarified evaluation of formula against simulated interval energy ($E = P_{avg} \times 0.25\text{ h}$). GradientBoosting on instantaneous kW achieves $\text{MAE} = 0.0142\text{ kW}, R^2 = 0.1362$. | `scripts/train_energy_model.py`, `reports/energy_training_report.json`, `reports/ENERGY_MODEL_FINAL_VALIDATION.md` |
| **Dataset Inventory Zero Count** | Script reported zero CSVs under `Datasets/`. | `Datasets/` subdirectories contained schemas and download instructions (`README.md`), while external Kaggle CSVs await manual user download. Primary data is `data/raw/simulated_cold_chain.csv`. | Auditing script confirms existence of all directory structures and marks expected benchmarks as `[AWAITING_DOWNLOAD]` while correctly analyzing active local datasets. | `scripts/audit_datasets.py`, `reports/dataset_audit_inventory.json` |
| **Commit ID Inconsistency** | Reports referenced older commit `01b75c6`. | Intervening commits (`10e0e89`) added experimental scripts and test cases. | Re-ran all benchmarks, test suites, and browser verifications on current revision. | All reports updated. |

---

## 2. Summary of Modified Code & Reports
- **Code:**
  - [`optimization/nsga2_optimizer.py`](file:///C:/Projects/Cold-Chain-Ai/optimization/nsga2_optimizer.py): Emergency cooling override ($u=1.0, d=1.0$) when current temperature exceeds safe profile limits.
  - [`scripts/compare_nsga2_methods.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/compare_nsga2_methods.py): Full per-scenario raw trajectory export to `reports/nsga2_comparison/nsga2_comparison_data.json`.
  - [`scripts/evaluate_baseline.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/evaluate_baseline.py): Unified 70/15/15 chronological evaluation protocol comparing Persistence, Moving Average, Linear, Original, and Retrained MAD-TCN models on identical 590 sequences.
  - [`scripts/train_energy_model.py`](file:///C:/Projects/Cold-Chain-Ai/scripts/train_energy_model.py): Dimensional unit separation between instantaneous kW and interval kWh.
  - [`tests/__init__.py`](file:///C:/Projects/Cold-Chain-Ai/tests/__init__.py), [`tests/test_api_workflows.py`](file:///C:/Projects/Cold-Chain-Ai/tests/test_api_workflows.py), [`tests/test_pipeline.py`](file:///C:/Projects/Cold-Chain-Ai/tests/test_pipeline.py): Configured standalone unittest execution and added tests 33–36 (39 total tests passing).
- **Reports:**
  - [`reports/NSGA2_FINAL_VALIDATION.md`](file:///C:/Projects/Cold-Chain-Ai/reports/NSGA2_FINAL_VALIDATION.md)
  - [`reports/MAD_TCN_FINAL_VALIDATION.md`](file:///C:/Projects/Cold-Chain-Ai/reports/MAD_TCN_FINAL_VALIDATION.md)
  - [`reports/ENERGY_MODEL_FINAL_VALIDATION.md`](file:///C:/Projects/Cold-Chain-Ai/reports/ENERGY_MODEL_FINAL_VALIDATION.md)
  - [`reports/FINAL_END_TO_END_VERIFICATION.md`](file:///C:/Projects/Cold-Chain-Ai/reports/FINAL_END_TO_END_VERIFICATION.md)
  - [`reports/FINAL_REMAINING_LIMITATIONS.md`](file:///C:/Projects/Cold-Chain-Ai/reports/FINAL_REMAINING_LIMITATIONS.md)
