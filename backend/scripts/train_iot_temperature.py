"""Train MAD-TCN (Multi-scale Adaptive Dilated Temporal Convolutional Network) on IoT temperature dataset.

Features:
- CLI flags for dataset path and sensor ID filter
- Preprocessing with core_preprocessing.prepare and sequences
- Strict chronological 70/15/15 train/val/test split
- Feature normalization fitted strictly on training data (StandardScaler)
- MSE loss with Adam and ReduceLROnPlateau
- Early stopping on validation MAE (patience=15)
- Evaluates test set performance (MAE, RMSE, R²) in original physical units (°C)
- Safeguarded saving to models/mad_tcn_retrained.pt (never overwriting models/mad_tcn_best.pt)
- Exports feature scaler to models/scaler_retrained.pkl
- Generates comprehensive reports/training_report.json
- Compares performance against baseline metrics in models/metrics.json
"""
from __future__ import annotations

import argparse
import copy
import datetime
import json
import os
import pickle
import sys
from pathlib import Path

# Ensure project modules are importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler

from core_preprocessing import prepare, sequences, FEATURES
from ml.mad_tcn import MADTCN


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Compute MAE, RMSE, and R² in original physical units (°C)."""
    errors = y_pred - y_true
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    ss_res = float(np.sum(errors ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1.0 - (ss_res / (ss_tot + 1e-9)))
    return {
        'mae': round(mae, 4),
        'rmse': round(rmse, 4),
        'r2': round(r2, 4)
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train MAD-TCN multi-scale forecasting model on cold-chain IoT temperature telemetry."
    )
    parser.add_argument(
        '--dataset', '--data', '-d',
        dest='dataset',
        type=str,
        default='data/raw/simulated_cold_chain.csv',
        help="Path to CSV dataset (default: data/raw/simulated_cold_chain.csv)"
    )
    parser.add_argument(
        '--sensor', '-s',
        dest='sensor',
        type=str,
        default='CC-01',
        help="Sensor ID to filter (default: CC-01)"
    )
    parser.add_argument(
        '--epochs', '-e',
        type=int,
        default=100,
        help="Maximum training epochs (default: 100)"
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=64,
        help="Mini-batch size (default: 64)"
    )
    parser.add_argument(
        '--lr',
        type=float,
        default=1e-3,
        help="Initial learning rate for Adam optimizer (default: 0.001)"
    )
    parser.add_argument(
        '--patience',
        type=int,
        default=15,
        help="Early stopping patience in epochs based on validation MAE (default: 15)"
    )
    parser.add_argument(
        '--output-model',
        type=str,
        default='models/mad_tcn_retrained.pt',
        help="Destination path for retrained model weights (default: models/mad_tcn_retrained.pt)"
    )
    parser.add_argument(
        '--output-scaler',
        type=str,
        default='models/scaler_retrained.pkl',
        help="Destination path for fitted StandardScaler (default: models/scaler_retrained.pkl)"
    )
    parser.add_argument(
        '--output-report',
        type=str,
        default='reports/training_report.json',
        help="Destination path for JSON training report (default: reports/training_report.json)"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    print("=" * 75)
    print("MAD-TCN IOT TEMPERATURE TRAINING PIPELINE")
    print("=" * 75)
    print(f"Dataset path:    {args.dataset}")
    print(f"Sensor filter:   {args.sensor}")
    print(f"Max epochs:      {args.epochs}")
    print(f"Batch size:      {args.batch_size}")
    print(f"Learning rate:   {args.lr}")
    print(f"Patience:        {args.patience}")
    print(f"Output model:    {args.output_model}")
    print(f"Output scaler:   {args.output_scaler}")
    print(f"Output report:   {args.output_report}")
    print("=" * 75)

    # Set random seed for reproducibility
    torch.manual_seed(42)
    np.random.seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Resolve dataset path
    dataset_path = Path(args.dataset)
    if not dataset_path.is_absolute():
        dataset_path = PROJECT_ROOT / dataset_path

    if not dataset_path.exists():
        print(f"Error: Dataset file not found at {dataset_path}")
        sys.exit(1)

    print(f"\n1. Loading dataset from {dataset_path} ...")
    df_raw = pd.read_csv(dataset_path)

    # Apply sensor filter
    if 'sensor_id' in df_raw.columns and args.sensor:
        sensor_df = df_raw[df_raw['sensor_id'] == args.sensor].copy()
        if len(sensor_df) == 0:
            available_sensors = df_raw['sensor_id'].unique().tolist()
            print(f"Warning: Sensor '{args.sensor}' not found in dataset. Available: {available_sensors}")
            fallback_sensor = available_sensors[0]
            print(f"Falling back to sensor: '{fallback_sensor}'")
            args.sensor = fallback_sensor
            sensor_df = df_raw[df_raw['sensor_id'] == fallback_sensor].copy()
    else:
        sensor_df = df_raw.copy()
        if 'sensor_id' not in sensor_df.columns:
            sensor_df['sensor_id'] = 'DEFAULT'

    print(f"   Sensor '{args.sensor}' row count: {len(sensor_df)}")

    # 2. Preprocessing via prepare()
    print("2. Preprocessing features via core_preprocessing.prepare() ...")
    df_prep = prepare(sensor_df)
    print(f"   Engineered features ({len(FEATURES)} channels): {', '.join(FEATURES)}")

    # 3. Chronological sequence generation
    print("3. Generating temporal sequences (window=60, horizon=15) ...")
    X_all, y_all = sequences(df_prep, window=60, horizon=15)
    total_sequences = len(X_all)
    if total_sequences < 30:
        print(f"Error: Insufficient sequences generated ({total_sequences}). Need at least 30.")
        sys.exit(1)

    # 4. Strict chronological 70 / 15 / 15 split
    train_size = int(total_sequences * 0.70)
    val_size = int(total_sequences * 0.15)
    test_size = total_sequences - train_size - val_size

    train_end = train_size
    val_end = train_size + val_size

    X_train, y_train = X_all[:train_end], y_all[:train_end]
    X_val, y_val = X_all[train_end:val_end], y_all[train_end:val_end]
    X_test, y_test = X_all[val_end:], y_all[val_end:]

    print(f"4. Chronological 70/15/15 Data Split:")
    print(f"   Total sequences:      {total_sequences}")
    print(f"   Training set:         {len(X_train)} ({len(X_train)/total_sequences*100:.1f}%)")
    print(f"   Validation set:       {len(X_val)} ({len(X_val)/total_sequences*100:.1f}%)")
    print(f"   Test set (held-out):  {len(X_test)} ({len(X_test)/total_sequences*100:.1f}%)")

    # 5. Feature normalization fitted ONLY on training data
    print("5. Fitting StandardScaler strictly on training set features ...")
    scaler = StandardScaler()
    num_features = X_train.shape[2]
    scaler.fit(X_train.reshape(-1, num_features))

    X_train_scaled = scaler.transform(X_train.reshape(-1, num_features)).reshape(X_train.shape)
    X_val_scaled = scaler.transform(X_val.reshape(-1, num_features)).reshape(X_val.shape)
    X_test_scaled = scaler.transform(X_test.reshape(-1, num_features)).reshape(X_test.shape)

    # Convert to PyTorch datasets and DataLoaders
    train_dataset = TensorDataset(
        torch.tensor(X_train_scaled, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32)
    )
    val_dataset = TensorDataset(
        torch.tensor(X_val_scaled, dtype=torch.float32),
        torch.tensor(y_val, dtype=torch.float32)
    )
    test_dataset = TensorDataset(
        torch.tensor(X_test_scaled, dtype=torch.float32),
        torch.tensor(y_test, dtype=torch.float32)
    )

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    # 6. Model initialization, Optimizer, Loss, and Scheduler
    print(f"6. Initializing MADTCN model on {device} ...")
    model = MADTCN(features=len(FEATURES), hidden=32, horizon=15).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5, min_lr=1e-6
    )
    criterion = nn.MSELoss()

    best_val_mae = float('inf')
    best_epoch = 0
    best_model_state = None
    patience_counter = 0
    history = []

    print("\nStarting training loop:")
    print(f"{'Epoch':<8} {'Train MSE':<12} {'Val MSE':<12} {'Val MAE (°C)':<15} {'Learning Rate':<15} {'Status'}")
    print("-" * 75)

    for epoch in range(1, args.epochs + 1):
        # Training step
        model.train()
        train_batch_losses = []
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            preds = model(bx)
            loss = criterion(preds, by)
            loss.backward()
            optimizer.step()
            train_batch_losses.append(loss.item())

        train_loss = float(np.mean(train_batch_losses))

        # Validation step
        model.eval()
        val_batch_losses = []
        val_batch_maes = []
        with torch.no_grad():
            for bx, by in val_loader:
                bx, by = bx.to(device), by.to(device)
                preds = model(bx)
                loss = criterion(preds, by)
                mae = torch.mean(torch.abs(preds - by))
                val_batch_losses.append(loss.item())
                val_batch_maes.append(mae.item())

        val_loss = float(np.mean(val_batch_losses))
        val_mae = float(np.mean(val_batch_maes))
        current_lr = optimizer.param_groups[0]['lr']

        # Learning rate schedule step based on validation MAE
        scheduler.step(val_mae)

        # Early stopping logic on validation MAE
        status_note = ""
        if val_mae < best_val_mae - 1e-4:
            best_val_mae = val_mae
            best_epoch = epoch
            best_model_state = copy.deepcopy(model.state_dict())
            patience_counter = 0
            status_note = " * (Best)"
        else:
            patience_counter += 1

        history.append({
            'epoch': epoch,
            'train_mse': round(train_loss, 5),
            'val_mse': round(val_loss, 5),
            'val_mae': round(val_mae, 5),
            'lr': current_lr
        })

        # Progress printing every 5 epochs, epoch 1, or final epoch
        if epoch == 1 or epoch % 5 == 0 or patience_counter >= args.patience or epoch == args.epochs:
            print(f"{epoch:<8d} {train_loss:<12.4f} {val_loss:<12.4f} {val_mae:<15.4f} {current_lr:<15.6f}{status_note}")

        if patience_counter >= args.patience:
            print(f"\nEarly stopping triggered at epoch {epoch}: No validation improvement for {args.patience} epochs.")
            break

    # Restore best checkpoint weights
    if best_model_state is not None:
        print(f"Restoring best checkpoint weights from epoch {best_epoch} (Val MAE: {best_val_mae:.4f} °C).")
        model.load_state_dict(best_model_state)

    # 7. Evaluate on held-out test set in original physical units (°C)
    print("\n7. Evaluating retrained model on held-out test set ...")
    model.eval()
    test_preds_list = []
    test_trues_list = []
    with torch.no_grad():
        for bx, by in test_loader:
            bx = bx.to(device)
            preds = model(bx).cpu().numpy()
            test_preds_list.append(preds)
            test_trues_list.append(by.numpy())

    y_test_pred = np.vstack(test_preds_list)
    y_test_true = np.vstack(test_trues_list)
    test_metrics = compute_metrics(y_test_true, y_test_pred)

    # 8. Save retrained model checkpoint (Safeguarded against overwriting best.pt)
    output_model_path = Path(args.output_model)
    if not output_model_path.is_absolute():
        output_model_path = PROJECT_ROOT / output_model_path

    best_checkpoint_path = (PROJECT_ROOT / 'models' / 'mad_tcn_best.pt').resolve()
    if output_model_path.resolve() == best_checkpoint_path:
        raise ValueError(
            "CRITICAL SAFEGUARD: Overwriting 'models/mad_tcn_best.pt' is strictly prohibited. "
            "Please use 'models/mad_tcn_retrained.pt' or an alternate path."
        )

    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_model_path)
    print(f"8. Checkpoint saved to: {output_model_path}")

    # 9. Save scaler to models/scaler_retrained.pkl
    output_scaler_path = Path(args.output_scaler)
    if not output_scaler_path.is_absolute():
        output_scaler_path = PROJECT_ROOT / output_scaler_path

    output_scaler_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"9. Scaler saved to:     {output_scaler_path}")

    # 10. Load baseline metrics and build training report
    baseline_metrics_path = PROJECT_ROOT / 'models' / 'metrics.json'
    baseline_metrics = {}
    if baseline_metrics_path.exists():
        try:
            baseline_metrics = json.loads(baseline_metrics_path.read_text())
        except Exception as e:
            print(f"Warning: Failed to parse baseline metrics ({baseline_metrics_path}): {e}")

    mae_delta = None
    rmse_delta = None
    mae_improvement_pct = None
    rmse_improvement_pct = None

    if 'mae' in baseline_metrics and baseline_metrics['mae']:
        base_mae = baseline_metrics['mae']
        mae_delta = round(test_metrics['mae'] - base_mae, 4)
        mae_improvement_pct = round(((base_mae - test_metrics['mae']) / base_mae) * 100, 2)

    if 'rmse' in baseline_metrics and baseline_metrics['rmse']:
        base_rmse = baseline_metrics['rmse']
        rmse_delta = round(test_metrics['rmse'] - base_rmse, 4)
        rmse_improvement_pct = round(((base_rmse - test_metrics['rmse']) / base_rmse) * 100, 2)

    output_report_path = Path(args.output_report)
    if not output_report_path.is_absolute():
        output_report_path = PROJECT_ROOT / output_report_path

    output_report_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        rel_model_path = str(output_model_path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel_model_path = str(output_model_path)

    try:
        rel_scaler_path = str(output_scaler_path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel_scaler_path = str(output_scaler_path)

    report_payload = {
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'dataset': str(args.dataset),
        'sensor_id': args.sensor,
        'features': FEATURES,
        'split_summary': {
            'total_sequences': total_sequences,
            'train_sequences': len(X_train),
            'val_sequences': len(X_val),
            'test_sequences': len(X_test),
            'split_ratios': '70% Train, 15% Val, 15% Test (Chronological)'
        },
        'training_config': {
            'max_epochs': args.epochs,
            'batch_size': args.batch_size,
            'initial_lr': args.lr,
            'patience': args.patience,
            'loss_function': 'MSELoss',
            'optimizer': 'Adam',
            'scheduler': 'ReduceLROnPlateau (factor=0.5, patience=5)'
        },
        'training_summary': {
            'epochs_trained': len(history),
            'best_epoch': best_epoch,
            'best_val_mae': round(best_val_mae, 4),
            'stopped_early': len(history) < args.epochs
        },
        'test_metrics': test_metrics,
        'baseline_comparison': {
            'baseline_metrics': baseline_metrics,
            'mae_delta': mae_delta,
            'rmse_delta': rmse_delta,
            'mae_improvement_pct': mae_improvement_pct,
            'rmse_improvement_pct': rmse_improvement_pct
        },
        'artifacts': {
            'model_checkpoint': rel_model_path,
            'scaler': rel_scaler_path
        }
    }

    output_report_path.write_text(json.dumps(report_payload, indent=2))
    print(f"10. Training report saved to: {output_report_path}")

    # 11. Print comparison with existing baseline metrics
    print("\n" + "=" * 75)
    print("TEST EVALUATION & BASELINE COMPARISON")
    print("=" * 75)
    print(f"{'Metric':<18} {'Baseline (metrics.json)':<26} {'Retrained Model':<20} {'Improvement'}")
    print("-" * 75)

    base_mae_str = f"{baseline_metrics.get('mae'):.4f} °C" if baseline_metrics.get('mae') is not None else "N/A"
    base_rmse_str = f"{baseline_metrics.get('rmse'):.4f} °C" if baseline_metrics.get('rmse') is not None else "N/A"

    mae_imp_str = f"{mae_improvement_pct:+.2f}%" if mae_improvement_pct is not None else "N/A"
    rmse_imp_str = f"{rmse_improvement_pct:+.2f}%" if rmse_improvement_pct is not None else "N/A"

    print(f"{'MAE (°C)':<18} {base_mae_str:<26} {test_metrics['mae']:<20.4f} {mae_imp_str}")
    print(f"{'RMSE (°C)':<18} {base_rmse_str:<26} {test_metrics['rmse']:<20.4f} {rmse_imp_str}")
    print(f"{'R² Score':<18} {'N/A':<26} {test_metrics['r2']:<20.4f} {'N/A'}")
    print("=" * 75)


if __name__ == '__main__':
    main()
