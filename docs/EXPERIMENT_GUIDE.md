# ColdChain-AI: Complete Experiment Reproduction Guide

**Project:** COLDCHAIN-AI  
**Date:** 2026-10-09  
**Runtime Environment:** Windows PowerShell, Python 3.10.11 Virtual Environment (`.venv`)  

---

## 1. Environment Verification

Ensure the virtual environment is activated and dependencies are verified:
```powershell
# 1. Verify Django configuration integrity (0 issues)
.\.venv\Scripts\python.exe manage.py check

# 2. Run automated test suite (Unit & Integration tests)
.\.venv\Scripts\python.exe manage.py test
```

---

## 2. Full Experiment Reproduction Commands

### 2.1 End-to-End Pipeline Verification
Runs the integrated data ingestion → preprocessing → MAD-TCN → risk assessment → constrained NSGA-II workflow:
```powershell
.\.venv\Scripts\python.exe -m scripts.end_to_end
```
*Expected Output:*
```text
COLDCHAIN AI END-TO-END TEST
{'sensor': 'CC-01', 'current_temperature': 3.93, 'forecast': [...], 'risk': {'risk_score': 26.04, 'risk_level': 'MEDIUM'}, 'pareto_solutions': 48, 'recommended': {'cooling_intensity': 0.999, 'compressor_duty_cycle': 1.0, 'feasible': True}}
PASS
```

### 2.2 NSGA-II Scientific Comparison Experiment
Evaluates 50 identical operational scenarios comparing Method A (Reactive), Method B (Legacy Unconstrained), and Method C (Audited Constrained):
```powershell
.\.venv\Scripts\python.exe scripts/compare_nsga2_methods.py
```
*Outputs Created:*
- `reports/nsga2_comparison/nsga2_comparison_report.md`
- `reports/nsga2_comparison/nsga2_comparison_data.json`

### 2.3 MAD-TCN Model Baseline Evaluation
Evaluates MAD-TCN against Naive Persistence, 5-Step Moving Average, and Linear Extrapolation on held-out test data:
```powershell
.\.venv\Scripts\python.exe scripts/evaluate_baseline.py
```
*Outputs Created:*
- `reports/model_baseline_comparison.json`

### 2.4 Energy Model Thermodynamic Validation
Evaluates empirical refrigeration equations against baseline power traces and environmental scenarios:
```powershell
.\.venv\Scripts\python.exe scripts/validate_energy.py
```
*Outputs Created:*
- `reports/energy_validation_report.json`

### 2.5 Big Data Scalability Stress Benchmark
Executes end-to-end pipeline stress test across 10K, 100K, 500K, and 1,000,000 synthetic records:
```powershell
.\.venv\Scripts\python.exe scripts/run_scalability_benchmark.py
```
*Outputs Created:*
- `reports/scalability_benchmark_report.json`

### 2.6 Real-IoT Telemetry Ingestion Tests
Validates the industrial `POST /api/iot/telemetry/` endpoint:
```powershell
.\.venv\Scripts\python.exe scripts/mock_iot_device.py --direct-test
```

---

## 3. Web Application & Control Center Server

To launch the industrial dashboard:
```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```
Open your browser to:
- Overview Dashboard: `http://127.0.0.1:8000/dashboard/`
- Datasets Catalog: `http://127.0.0.1:8000/datasets/`
- Live Telemetry: `http://127.0.0.1:8000/live-monitoring/`
- Deep Forecasting: `http://127.0.0.1:8000/predictions/`
- Optimization & Pareto: `http://127.0.0.1:8000/optimization/`
- Audit Reports: `http://127.0.0.1:8000/reports/`
