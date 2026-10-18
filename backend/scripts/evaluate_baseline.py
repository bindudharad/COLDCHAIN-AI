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

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
for p in [str(BACKEND_DIR), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

def _resolve_path(rel_path):
    p = Path(rel_path)
    if p.exists():
        return p
    cand = REPO_ROOT / rel_path
    if cand.exists() or cand.parent.exists():
        return cand
    return p

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
    
    csv_path = _resolve_path('data/raw/simulated_cold_chain.csv')

    if not csv_path.exists():
        print(f"Error: {csv_path} not found.")
        sys.exit(1)
        
    df_raw = pd.read_csv(csv_path)
    df_cc01 = df_raw[df_raw['sensor_id'] == 'CC-01'].copy()
    df_prep = prepare(df_cc01)
    
    # Chronological sequence generation
    X_all, y_all = sequences(df_prep, window=60, horizon=15)
    
    # Unified chronological split: 70% train (2747), 15% val (588), 15% held-out test (590)
    total_sequences = len(X_all)
    train_size = int(total_sequences * 0.70)
    val_size = int(total_sequences * 0.15)
    test_size = total_sequences - train_size - val_size
    test_start = train_size + val_size
    
    X_test = X_all[test_start:]
    y_test = y_all[test_start:]
    
    # Retrieve test timestamps
    test_timestamps = df_prep['timestamp'].iloc[test_start + 60 : test_start + 60 + test_size].tolist()
    start_ts = str(df_prep['timestamp'].iloc[test_start + 60])
    end_ts = str(df_prep['timestamp'].iloc[-1])
    
    print(f"Total sequences: {total_sequences}")
    print(f"Train sequences: {train_size} (First 70.0%, Chronological)")
    print(f"Val sequences:   {val_size} (Next 15.0%, Chronological)")
    print(f"Test sequences:  {len(X_test)} (Final 15.0%, Chronological Held-Out)")
    print(f"Test timeline:   {start_ts} to {end_ts}")
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
    # Model A: Original Pre-trained Checkpoint (Raw Features)
    # ---------------------------------------------------------
    orig_ckpt_path = _resolve_path('models/mad_tcn_best.pt')
    if not orig_ckpt_path.exists():
        print(f"Error: {orig_ckpt_path} not found.")
        sys.exit(1)
        
    model_orig = MADTCN(features=len(FEATURES), hidden=32, horizon=15)
    model_orig.load_state_dict(torch.load(orig_ckpt_path, map_location='cpu', weights_only=True))
    model_orig.eval()
    
    with torch.no_grad():
        pred_mad_tcn_orig = model_orig(torch.tensor(X_test, dtype=torch.float32)).numpy()
    metrics_mad_tcn_orig = evaluate_metrics(y_test, pred_mad_tcn_orig)
    
    # ---------------------------------------------------------
    # Model B: Retrained Checkpoint (with StandardScaler)
    # ---------------------------------------------------------
    retrained_ckpt_path = _resolve_path('models/mad_tcn_retrained.pt')
    scaler_path = _resolve_path('models/scaler_retrained.pkl')
    
    if retrained_ckpt_path.exists() and scaler_path.exists():
        import pickle
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        X_test_scaled = scaler.transform(X_test.reshape(-1, len(FEATURES))).reshape(X_test.shape)
        
        model_retrained = MADTCN(features=len(FEATURES), hidden=32, horizon=15)
        model_retrained.load_state_dict(torch.load(retrained_ckpt_path, map_location='cpu', weights_only=True))
        model_retrained.eval()
        
        with torch.no_grad():
            pred_mad_tcn_retrained = model_retrained(torch.tensor(X_test_scaled, dtype=torch.float32)).numpy()
        metrics_mad_tcn_retrained = evaluate_metrics(y_test, pred_mad_tcn_retrained)
    else:
        metrics_mad_tcn_retrained = None

    # Print formatted comparison table
    print(f"{'Method / Model':<35} {'MAE (°C)':<12} {'RMSE (°C)':<12} {'R² Score':<10}")
    print("-" * 72)
    print(f"{'1. Naive Persistence (Last Value)':<35} {metrics_persistence['mae']:<12.4f} {metrics_persistence['rmse']:<12.4f} {metrics_persistence['r2']:<10.4f}")
    print(f"{'2. 5-Step Moving Average':<35} {metrics_ma5['mae']:<12.4f} {metrics_ma5['rmse']:<12.4f} {metrics_ma5['r2']:<10.4f}")
    print(f"{'3. Linear Trend Extrapolation':<35} {metrics_linear['mae']:<12.4f} {metrics_linear['rmse']:<12.4f} {metrics_linear['r2']:<10.4f}")
    print(f"{'4. MAD-TCN Original (Raw Inputs)':<35} {metrics_mad_tcn_orig['mae']:<12.4f} {metrics_mad_tcn_orig['rmse']:<12.4f} {metrics_mad_tcn_orig['r2']:<10.4f}")
    if metrics_mad_tcn_retrained:
        print(f"{'5. MAD-TCN Retrained (StandardScaler)':<35} {metrics_mad_tcn_retrained['mae']:<12.4f} {metrics_mad_tcn_retrained['rmse']:<12.4f} {metrics_mad_tcn_retrained['r2']:<10.4f}")
    print("-" * 72)
    
    # Save unified results to reports directory
    rep_dir = _resolve_path('reports')
    rep_dir.mkdir(exist_ok=True)

    summary = {
        'dataset': 'simulated_cold_chain.csv (CC-01)',
        'target_column': 'temperature (°C)',
        'horizon_steps': 15,
        'chronological_split': '70% Train, 15% Val, 15% Held-Out Test',
        'train_samples': train_size,
        'val_samples': val_size,
        'test_samples': len(X_test),
        'test_timeline': {
            'start': start_ts,
            'end': end_ts
        },
        'metrics': {
            'persistence': metrics_persistence,
            'moving_average_5': metrics_ma5,
            'linear_extrapolation': metrics_linear,
            'mad_tcn_original': metrics_mad_tcn_orig,
            'mad_tcn_retrained': metrics_mad_tcn_retrained
        }
    }
    (rep_dir / 'model_baseline_comparison.json').write_text(json.dumps(summary, indent=2))
    print(f"\nSaved benchmark results to {rep_dir / 'model_baseline_comparison.json'}")

if __name__ == '__main__':
    main()
