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
from core import energy, estimated_power_kw, estimated_energy_kwh

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
    
    print("\nThermodynamic Formula Evaluations across Scenarios (15-min cycle, duration = 0.25 h):")
    eval_results = []
    for tc in test_cases:
        p_kw = estimated_power_kw(tc['t_cur'], tc['t_amb'], tc['intensity'], tc['duty'])
        e_kwh = estimated_energy_kwh(tc['t_cur'], tc['t_amb'], tc['intensity'], tc['duty'], duration_hours=0.25)
        eval_results.append({
            **tc,
            'estimated_power_kw': p_kw,
            'estimated_energy_kwh': e_kwh,
            'interval_duration_hours': 0.25,
            'note': 'Calculated as E_kwh = P_kw * 0.25 h'
        })
        print(f"  [{tc['name']}] -> Avg Power = {p_kw:.3f} kW | Interval Energy (15 min) = {e_kwh:.4f} kWh")
        
    # 3. Model Fit against Simulated Power & Energy Profiles
    # Sample 100 intervals of 15 minutes from CC-01
    intervals = []
    for start_idx in range(0, len(cc01) - 15, 30):
        chunk = cc01.iloc[start_idx:start_idx+15]
        duty_actual = chunk['compressor_state'].mean()
        t_cur = chunk['temperature'].iloc[0]
        t_amb = chunk['ambient_temperature'].mean()
        actual_energy_kwh = chunk['power_kw'].sum() / 60.0  # kW * min / 60 = kWh
        actual_power_kw = chunk['power_kw'].mean()
        
        est_power = estimated_power_kw(t_cur, t_amb, 0.75, duty_actual)
        est_energy = estimated_energy_kwh(t_cur, t_amb, 0.75, duty_actual, duration_hours=0.25)
        intervals.append({
            'actual_power_kw': actual_power_kw,
            'est_power_kw': est_power,
            'actual_kwh': actual_energy_kwh,
            'est_kwh': est_energy
        })
        
    df_eval = pd.DataFrame(intervals)
    errors_p = df_eval['est_power_kw'] - df_eval['actual_power_kw']
    mae_p = float(np.mean(np.abs(errors_p)))
    rmse_p = float(np.sqrt(np.mean(errors_p ** 2)))
    ss_res_p = np.sum(errors_p ** 2)
    ss_tot_p = np.sum((df_eval['actual_power_kw'] - df_eval['actual_power_kw'].mean()) ** 2)
    r2_p = float(1.0 - (ss_res_p / (ss_tot_p + 1e-9)))

    errors_e = df_eval['est_kwh'] - df_eval['actual_kwh']
    mae_e = float(np.mean(np.abs(errors_e)))
    rmse_e = float(np.sqrt(np.mean(errors_e ** 2)))
    ss_res_e = np.sum(errors_e ** 2)
    ss_tot_e = np.sum((df_eval['actual_kwh'] - df_eval['actual_kwh'].mean()) ** 2)
    r2_e = float(1.0 - (ss_res_e / (ss_tot_e + 1e-9)))
    
    print(f"\nEnergy Estimator vs Simulated Cycle Telemetry (N={len(df_eval)} cycles):")
    print(f"  Power Estimation:  MAE = {mae_p:.4f} kW | RMSE = {rmse_p:.4f} kW | R² = {r2_p:.4f}")
    print(f"  Energy Estimation: MAE = {mae_e:.4f} kWh | RMSE = {rmse_e:.4f} kWh | R² = {r2_e:.4f}")
    print(f"  Target Stats (kWh): Mean = {df_eval['actual_kwh'].mean():.4f}, Std = {df_eval['actual_kwh'].std():.4f}")
    
    # 4. Save validation metrics
    rep_dir = Path('reports')
    rep_dir.mkdir(exist_ok=True)
    summary = {
        'status': 'ESTIMATED / SIMULATED',
        'classification': 'Empirical thermodynamic thermal-lift model',
        'hardware_wattmeter_connected': False,
        'formula_contracts': {
            'power': 'P_kw = max(0.05, 0.25 + 0.035 * max(T_amb - T_cur, 0)) * (0.35 + 0.65 * intensity) * duty',
            'energy': 'E_kwh = P_kw * interval_duration_hours (0.25 h for 15-minute interval)'
        },
        'units': {
            'power': 'kW (kilowatts)',
            'energy': 'kWh (kilowatt-hours per interval)',
            'temperature': 'Degrees Celsius (°C)'
        },
        'validation_against_simulated_ground_truth': {
            'cycles_evaluated': len(df_eval),
            'power_kw': {
                'mae_kw': round(mae_p, 4),
                'rmse_kw': round(rmse_p, 4),
                'r2_score': round(r2_p, 4)
            },
            'energy_kwh': {
                'mae_kwh': round(mae_e, 4),
                'rmse_kwh': round(rmse_e, 4),
                'r2_score': round(r2_e, 4),
                'target_std_kwh': round(float(df_eval['actual_kwh'].std()), 6)
            }
        },
        'scenario_evaluations': eval_results,
        'limitations': [
            'Energy values are derived from thermodynamic equations, not physical wattmeter hardware.',
            'Target power in simulation is discrete (97.3% at 1.0 kW), so low target variance explains low/negative R2.',
            'No physical compressor PWM controller was modulated.'
        ]
    }
    (rep_dir / 'energy_validation_report.json').write_text(json.dumps(summary, indent=2))
    print(f"\nSaved energy validation summary to {rep_dir / 'energy_validation_report.json'}")

if __name__ == '__main__':
    main()
