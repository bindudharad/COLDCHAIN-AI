"""Validation of Energy Modeling Equations and Metric Units.
Evaluates relationship between cooling intensity, duty cycle,
ambient thermal lift, and electrical energy consumption.
Explicitly labels all metrics as SIMULATED, ESTIMATED, or MEASURED.
"""
from __future__ import annotations
import sys, os, json
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import energy

def main():
    print("=" * 70)
    print("COLDCHAIN-AI: ENERGY MODEL VALIDATION & THERMODYNAMIC ANALYSIS")
    print("=" * 70)
    
    csv_path = Path('data/raw/simulated_cold_chain.csv')
    df = pd.read_csv(csv_path)
    cc01 = df[df['sensor_id'] == 'CC-01'].copy()
    
    # 1. Analyze simulated power readings in baseline dataset
    # power_kw was generated as: 0.25 + (compressor_state) * 0.75 + door * 0.12 kW
    power_active = cc01[cc01['compressor_state'] == 1]['power_kw']
    power_idle = cc01[cc01['compressor_state'] == 0]['power_kw']
    
    print(f"Simulated Baseline Electrical Power (CC-01):")
    print(f"  Active Compressor Power: Mean = {power_active.mean():.3f} kW (Range: {power_active.min():.2f} - {power_active.max():.2f} kW)")
    print(f"  Idle Compressor Power:   Mean = {power_idle.mean():.3f} kW (Range: {power_idle.min():.2f} - {power_idle.max():.2f} kW)")
    
    # 2. Evaluate thermodynamic energy formula across operating conditions
    test_cases = [
        {'name': 'Mild Ambient (15 °C), Low Cooling', 't_cur': 3.5, 't_amb': 15.0, 'intensity': 0.3, 'duty': 0.4},
        {'name': 'Nominal Ambient (22 °C), Balanced Setpoint', 't_cur': 3.8, 't_amb': 22.0, 'intensity': 0.6, 'duty': 0.6},
        {'name': 'Extreme Summer Heat (32 °C), Max Cooling', 't_cur': 4.5, 't_amb': 32.0, 'intensity': 1.0, 'duty': 1.0},
        {'name': 'Low Ambient Cold Snap (5 °C), Minimal Duty', 't_cur': 3.0, 't_amb': 5.0, 'intensity': 0.2, 'duty': 0.2},
    ]
    
    print("\nThermodynamic Formula Evaluations across Scenarios (15-min cycle):")
    eval_results = []
    for tc in test_cases:
        e_val = energy(tc['t_cur'], tc['t_amb'], tc['intensity'], tc['duty'])
        # Power in kW = energy / 0.25 hours
        p_avg = e_val / 0.25
        eval_results.append({**tc, 'estimated_energy_kwh': e_val, 'estimated_power_kw': round(p_avg, 3)})
        print(f"  [{tc['name']}] -> Energy = {e_val:.3f} kWh | Avg Power = {p_avg:.3f} kW")
        
    # 3. Model Fit against Simulated Power Profile
    # Sample 100 intervals of 15 minutes from CC-01
    intervals = []
    for start_idx in range(0, len(cc01) - 15, 30):
        chunk = cc01.iloc[start_idx:start_idx+15]
        duty_actual = chunk['compressor_state'].mean()
        t_cur = chunk['temperature'].iloc[0]
        t_amb = chunk['ambient_temperature'].mean()
        actual_energy_kwh = chunk['power_kw'].sum() / 60.0  # kW * min / 60 = kWh
        est_energy_kwh = energy(t_cur, t_amb, 0.75, duty_actual)
        intervals.append({'actual_kwh': actual_energy_kwh, 'est_kwh': est_energy_kwh})
        
    df_eval = pd.DataFrame(intervals)
    errors = df_eval['est_kwh'] - df_eval['actual_kwh']
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    ss_res = np.sum(errors ** 2)
    ss_tot = np.sum((df_eval['actual_kwh'] - df_eval['actual_kwh'].mean()) ** 2)
    r2 = float(1.0 - (ss_res / (ss_tot + 1e-9)))
    
    print(f"\nEnergy Estimator vs Simulated Cycle Telemetry (N={len(df_eval)} cycles):")
    print(f"  MAE:  {mae:.4f} kWh / cycle")
    print(f"  RMSE: {rmse:.4f} kWh / cycle")
    print(f"  R²:   {r2:.4f}")
    
    # 4. Save validation metrics
    rep_dir = Path('reports')
    rep_dir.mkdir(exist_ok=True)
    summary = {
        'status': 'ESTIMATED / SIMULATED',
        'classification': 'Empirical thermodynamic thermal-lift model',
        'hardware_wattmeter_connected': False,
        'formula': 'E = max(0.05, 0.25 + 0.035 * max(T_amb - T_cur, 0)) * (0.35 + 0.65 * intensity) * duty',
        'units': {
            'power': 'kW',
            'energy': 'kWh per 15-minute control interval',
            'temperature': 'Degrees Celsius (°C)'
        },
        'validation_against_simulated_ground_truth': {
            'cycles_evaluated': len(df_eval),
            'mae_kwh': round(mae, 4),
            'rmse_kwh': round(rmse, 4),
            'r2_score': round(r2, 4)
        },
        'scenario_evaluations': eval_results,
        'limitations': [
            'Energy values are derived from thermodynamic equations, not physical wattmeter hardware.',
            'External Kaggle HVAC dataset represents residential buildings, not cold-chain walk-in coolers.',
            'No physical compressor PWM controller was modulated.'
        ]
    }
    (rep_dir / 'energy_validation_report.json').write_text(json.dumps(summary, indent=2))
    print(f"\nSaved energy validation summary to {rep_dir / 'energy_validation_report.json'}")

if __name__ == '__main__':
    main()
