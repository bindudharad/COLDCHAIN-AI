"""Big Data Scalability Benchmark for COLDCHAIN-AI Pipeline.
Measures ingestion throughput, preprocessing time, memory consumption,
neural inference latency, and optimization runtime across:
10K, 100K, 500K, and 1,000,000 synthetic records.
"""
from __future__ import annotations
import sys, os, time, gc, json, tracemalloc
from pathlib import Path
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core_preprocessing import prepare, sequences, FEATURES
from ml.mad_tcn import MADTCN
from optimization.nsga2_optimizer import run_nsga2

def generate_synthetic_stream(num_records: int) -> pd.DataFrame:
    """Generate reproducible chronological synthetic cold-chain telemetry."""
    rng = np.random.default_rng(42)
    ts = pd.date_range('2026-01-01', periods=num_records, freq='min')
    
    ambient = 22.0 + 4.0 * np.sin(np.arange(num_records) / 240.0) + rng.normal(0, 0.4, num_records)
    door = (rng.random(num_records) < 0.02).astype(int)
    temp = np.empty(num_records)
    temp[0] = 3.8
    for i in range(1, num_records):
        comp = temp[i-1] > 3.8
        temp[i] = temp[i-1] + 0.018 * (ambient[i] - temp[i-1]) - 0.32 * comp + 0.16 * door[i] + rng.normal(0, 0.03)
        
    return pd.DataFrame({
        'timestamp': ts,
        'sensor_id': 'CC-BENCH',
        'temperature': temp,
        'humidity': 70.0 + rng.normal(0, 3, num_records),
        'ambient_temperature': ambient,
        'power_kw': 0.25 + (temp > 3.8) * 0.75 + door * 0.12,
        'compressor_state': (temp > 3.8).astype(int),
        'door_open': door
    })

def benchmark_scale(num_records: int, model: torch.nn.Module):
    """Profile a single scale level."""
    print(f"\n--- Benchmarking Scale: {num_records:,} Records ---")
    tracemalloc.start()
    t_start = time.perf_counter()
    
    # 1. Ingestion / Generation
    t0 = time.perf_counter()
    df = generate_synthetic_stream(num_records)
    ingestion_time = time.perf_counter() - t0
    throughput_ingest = num_records / ingestion_time
    size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(f"  1. Ingestion:     {ingestion_time:.3f} s ({throughput_ingest:,.0f} rows/s, {size_mb:.1f} MB in-memory)")
    
    # 2. Vectorized Preprocessing
    t1 = time.perf_counter()
    df_prep = prepare(df)
    prep_time = time.perf_counter() - t1
    throughput_prep = num_records / prep_time
    print(f"  2. Preprocessing: {prep_time:.3f} s ({throughput_prep:,.0f} rows/s across 12 channels)")
    
    # 3. Peak Memory Measurement
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mb = peak_mem / (1024 * 1024)
    print(f"  3. Peak Memory:   {peak_mb:.1f} MB")
    
    # 4. Neural Inference (Inference on final batch of 32 windows)
    t2 = time.perf_counter()
    # Extract recent windows
    feature_arr = df_prep[FEATURES].tail(60 * 32).to_numpy(float)
    windows = []
    for w in range(min(32, len(feature_arr) // 60)):
        windows.append(feature_arr[w*60:(w+1)*60])
    if not windows:
        windows = [df_prep[FEATURES].tail(60).to_numpy(float)]
    x_tensor = torch.tensor(np.array(windows), dtype=torch.float32)
    with torch.no_grad():
        preds = model(x_tensor)
    inference_time = time.perf_counter() - t2
    print(f"  4. MAD-TCN Infer: {inference_time*1000:.1f} ms for {len(windows)} sequence windows")
    
    # 5. NSGA-II Optimization
    t3 = time.perf_counter()
    last_temp = float(df_prep['temperature'].iloc[-1])
    last_amb = float(df_prep['ambient_temperature'].iloc[-1])
    pareto, rec = run_nsga2(last_temp, last_amb, 25.0, population=40, generations=20)
    opt_time = (time.perf_counter() - t3) * 1000
    print(f"  5. NSGA-II Solve: {opt_time:.1f} ms (Found {len(pareto)} Pareto points)")
    
    total_time = time.perf_counter() - t_start
    print(f"  >> Total Pipeline Runtime: {total_time:.3f} s")
    
    # Clean memory
    del df, df_prep, feature_arr, windows, x_tensor
    gc.collect()
    
    return {
        'scale_records': num_records,
        'size_mb': round(size_mb, 2),
        'ingestion_time_s': round(ingestion_time, 3),
        'ingestion_throughput_rows_per_s': round(throughput_ingest, 1),
        'preprocessing_time_s': round(prep_time, 3),
        'preprocessing_throughput_rows_per_s': round(throughput_prep, 1),
        'peak_memory_mb': round(peak_mb, 2),
        'inference_time_ms': round(inference_time * 1000, 2),
        'optimization_time_ms': round(opt_time, 2),
        'total_runtime_s': round(total_time, 3)
    }

def main():
    print("=" * 70)
    print("COLDCHAIN-AI: BIG DATA SCALABILITY BENCHMARK (10K TO 1M ROWS)")
    print("=" * 70)
    
    # Load model once on CPU
    ckpt = Path('models/mad_tcn_best.pt')
    model = MADTCN(features=len(FEATURES), hidden=32, horizon=15)
    if ckpt.exists():
        model.load_state_dict(torch.load(ckpt, map_location='cpu', weights_only=True))
    model.eval()
    
    scale_levels = [10_000, 100_000, 500_000, 1_000_000]
    bench_results = []
    
    for count in scale_levels:
        res = benchmark_scale(count, model)
        bench_results.append(res)
        
    print("\n" + "=" * 70)
    print("SCALABILITY BENCHMARK SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Scale':<12} {'Size':<10} {'Ingest (s)':<12} {'Prep (s)':<12} {'Peak Mem':<12} {'Total (s)':<10}")
    print("-" * 70)
    for r in bench_results:
        print(f"{r['scale_records']:<12,d} {r['size_mb']:<7.1f} MB {r['ingestion_time_s']:<12.3f} {r['preprocessing_time_s']:<12.3f} {r['peak_memory_mb']:<7.1f} MB {r['total_runtime_s']:<10.3f}")
    print("-" * 70)
    
    rep_dir = Path(__file__).resolve().parents[2] / 'reports'
    rep_dir.mkdir(exist_ok=True)
    out_payload = {
        'benchmark': 'Single-Node Big Data Scalability Stress Test',
        'hardware_environment': {
            'os': 'Windows 11 AMD64',
            'python_version': '3.10.11',
            'pytorch': '2.14.1 (CPU)',
            'distributed_infrastructure': 'None (Disclosed limitation: Local Single-Node Execution, not Spark/Hadoop)'
        },
        'results': bench_results
    }
    (rep_dir / 'scalability_benchmark_report.json').write_text(json.dumps(out_payload, indent=2))
    print(f"\nSaved benchmark results to {rep_dir / 'scalability_benchmark_report.json'}")

if __name__ == '__main__':
    main()
