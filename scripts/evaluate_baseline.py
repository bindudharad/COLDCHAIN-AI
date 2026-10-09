"""Evaluate MAD-TCN against Persistence, Moving Average, and Extrapolation baselines.
Enforces strict chronological train/test split without lookahead leakage.
Reports MAE, RMSE, and R² in original physical units (°C).
"""
from __future__ import annotations
import sys, os, json
from pathlib import Path
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core_preprocessing import prepare, sequences, FEATURES
from ml.mad_tcn import MADTCN

def evaluate_metrics(y_true, y_pred):
    """Compute MAE, RMSE, and R² in physical degrees Celsius."""
    errors = y_pred - y_true
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    ss_res = np.sum(errors ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = float(1.0 - (ss_res / (ss_tot + 1e-9)))
    return {'mae': round(mae, 4), 'rmse': round(rmse, 4), 'r2': round(r2, 4)}

def main():
    print("=" * 70)
    print("MAD-TCN FORECASTING BENCHMARK: COMPARISON AGAINST CLASSICAL BASELINES")
    print("=" * 70)
    
    csv_path = Path('data/raw/simulated_cold_chain.csv')
    if not csv_path.exists():
        print(f"Error: {csv_path} not found.")
        sys.exit(1)
        
    df_raw = pd.read_csv(csv_path)
    df_cc01 = df_raw[df_raw['sensor_id'] == 'CC-01'].copy()
    df_prep = prepare(df_cc01)
    
    # Chronological sequence generation
    X_all, y_all = sequences(df_prep, window=60, horizon=15)
    
    # Strict chronological split: 80% train, 20% held-out test
    split_idx = int(len(X_all) * 0.8)
    X_test = X_all[split_idx:]
    y_test = y_all[split_idx:]
    
    print(f"Total sequences: {len(X_all)}")
    print(f"Train sequences: {split_idx} (First 80%, Chronological)")
    print(f"Test sequences:  {len(X_test)} (Final 20%, Chronological Held-Out)")
    print(f"Horizon:         15 timesteps (15 minutes lookahead)")
    print(f"Features:        {len(FEATURES)} channels\n")
    
    # ---------------------------------------------------------
    # Baseline 1: Naive Persistence (Last Observed Reading)
    # T_{t+h} = T_t for all h in [1..15]
    # ---------------------------------------------------------
    last_temp = X_test[:, -1, 0]  # feature 0 is temperature
    pred_persistence = np.tile(last_temp[:, np.newaxis], (1, 15))
    metrics_persistence = evaluate_metrics(y_test, pred_persistence)
    
    # ---------------------------------------------------------
    # Baseline 2: 5-step Moving Average
    # T_{t+h} = mean(T_{t-4..t})
    # ---------------------------------------------------------
    ma5 = np.mean(X_test[:, -5:, 0], axis=1)
    pred_ma5 = np.tile(ma5[:, np.newaxis], (1, 15))
    metrics_ma5 = evaluate_metrics(y_test, pred_ma5)
    
    # ---------------------------------------------------------
    # Baseline 3: Linear Trend Extrapolation
    # T_{t+h} = T_t + h * slope(T_{t-9..t})
    # ---------------------------------------------------------
    recent_diffs = np.mean(np.diff(X_test[:, -10:, 0], axis=1), axis=1)
    steps = np.arange(1, 16)
    pred_linear = last_temp[:, np.newaxis] + np.outer(recent_diffs, steps)
    metrics_linear = evaluate_metrics(y_test, pred_linear)
    
    # ---------------------------------------------------------
    # Model: MAD-TCN (Pre-trained Checkpoint)
    # ---------------------------------------------------------
    ckpt_path = Path('models/mad_tcn_best.pt')
    if not ckpt_path.exists():
        print(f"Error: {ckpt_path} not found.")
        sys.exit(1)
        
    model = MADTCN(features=len(FEATURES), hidden=32, horizon=15)
    model.load_state_dict(torch.load(ckpt_path, map_location='cpu', weights_only=True))
    model.eval()
    
    with torch.no_grad():
        x_tensor = torch.tensor(X_test, dtype=torch.float32)
        pred_mad_tcn = model(x_tensor).numpy()
    metrics_mad_tcn = evaluate_metrics(y_test, pred_mad_tcn)
    
    # Print formatted comparison table
    print(f"{'Method / Model':<32} {'MAE (°C)':<12} {'RMSE (°C)':<12} {'R² Score':<10}")
    print("-" * 68)
    print(f"{'1. Naive Persistence (Last Value)':<32} {metrics_persistence['mae']:<12.4f} {metrics_persistence['rmse']:<12.4f} {metrics_persistence['r2']:<10.4f}")
    print(f"{'2. 5-Step Moving Average':<32} {metrics_ma5['mae']:<12.4f} {metrics_ma5['rmse']:<12.4f} {metrics_ma5['r2']:<10.4f}")
    print(f"{'3. Linear Trend Extrapolation':<32} {metrics_linear['mae']:<12.4f} {metrics_linear['rmse']:<12.4f} {metrics_linear['r2']:<10.4f}")
    print(f"{'4. MAD-TCN (Multi-Scale Dilated)':<32} {metrics_mad_tcn['mae']:<12.4f} {metrics_mad_tcn['rmse']:<12.4f} {metrics_mad_tcn['r2']:<10.4f}")
    print("-" * 68)
    
    mae_improvement = ((metrics_persistence['mae'] - metrics_mad_tcn['mae']) / metrics_persistence['mae']) * 100
    rmse_improvement = ((metrics_persistence['rmse'] - metrics_mad_tcn['rmse']) / metrics_persistence['rmse']) * 100
    print(f"\nMAD-TCN Error Reduction vs Naive Persistence:")
    print(f"  MAE Reduction:  {mae_improvement:+.2f}%")
    print(f"  RMSE Reduction: {rmse_improvement:+.2f}%")
    
    # Save results to reports directory
    rep_dir = Path('reports')
    rep_dir.mkdir(exist_ok=True)
    summary = {
        'dataset': 'simulated_cold_chain.csv (CC-01)',
        'test_sequences': len(X_test),
        'horizon_steps': 15,
        'chronological_split': '80% Train, 20% Test',
        'metrics': {
            'persistence': metrics_persistence,
            'moving_average_5': metrics_ma5,
            'linear_extrapolation': metrics_linear,
            'mad_tcn': metrics_mad_tcn
        },
        'improvement_vs_persistence': {
            'mae_pct': round(mae_improvement, 2),
            'rmse_pct': round(rmse_improvement, 2)
        }
    }
    (rep_dir / 'model_baseline_comparison.json').write_text(json.dumps(summary, indent=2))
    print(f"\nSaved benchmark results to {rep_dir / 'model_baseline_comparison.json'}")

if __name__ == '__main__':
    main()
