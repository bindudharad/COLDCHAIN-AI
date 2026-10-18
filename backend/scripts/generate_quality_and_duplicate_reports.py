"""Data Quality and Duplicate Detection Audit for COLDCHAIN-AI Telemetry.

Performs comprehensive data health diagnostics across simulated cold chain
and public validation datasets:
1. Physical Range Validation (temperature, humidity, ambient_temperature, power_kw)
2. Timestamp Monotonicity Per Sensor (chronological order, time reversals, gaps)
3. Missing Value Analysis Per Column
4. Statistical Outlier Detection (values beyond 3 standard deviations per sensor)
5. Duplicate & Sensor Flatline Detection:
   - Exact row duplicates
   - Same sensor_id + timestamp duplicates
   - Near-duplicate / stuck temperature readings (>10 consecutive identical readings)
6. Scans data/raw/simulated_cold_chain.csv and all CSVs in Datasets/ (if present).
7. Outputs formatted ASCII report with PASS/WARN/FAIL indicators and saves
   reports/data_quality_report.json.

Uses only pandas, numpy, and Python standard library.
"""
from __future__ import annotations

import argparse
from datetime import datetime, date
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Physical Range Specifications according to domain requirements
PHYSICAL_RANGES = {
    'temperature': {
        'min': -60.0,
        'max': 70.0,
        'unit': '°C',
        'desc': 'Cold storage core temperature'
    },
    'humidity': {
        'min': 0.0,
        'max': 100.0,
        'unit': '%',
        'desc': 'Relative humidity'
    },
    'ambient_temperature': {
        'min': -40.0,
        'max': 60.0,
        'unit': '°C',
        'desc': 'Outdoor / ambient temperature'
    },
    'power_kw': {
        'min': 0.0,
        'max': 20.0,
        'unit': 'kW',
        'desc': 'Compressor electrical power'
    }
}

STUCK_SENSOR_THRESHOLD = 10  # Consecutive identical readings threshold


def to_serializable(val: Any) -> Any:
    """Recursively convert numpy/pandas types to native Python types for JSON."""
    if isinstance(val, (np.integer, np.int64, np.int32)):
        return int(val)
    if isinstance(val, (np.floating, np.float64, np.float32)):
        return float(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, (pd.Timestamp, datetime, date)):
        return val.isoformat()
    if isinstance(val, pd.Timedelta):
        return str(val)
    if isinstance(val, Path):
        return str(val)
    if isinstance(val, dict):
        return {k: to_serializable(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [to_serializable(x) for x in val]
    return val


def format_table(headers: List[str], rows: List[List[str]], alignments: Optional[List[str]] = None) -> str:
    """Render a clean ASCII table with custom column alignments ('<', '>', '^')."""
    if not rows:
        return ""
    col_count = len(headers)
    if alignments is None:
        alignments = ['<'] * col_count

    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            if idx < col_count:
                col_widths[idx] = max(col_widths[idx], len(str(cell)))

    def render_row(cells: List[str]) -> str:
        formatted = []
        for cell, w, align in zip(cells, col_widths, alignments):
            c_str = str(cell)
            if align == '>':
                formatted.append(c_str.rjust(w))
            elif align == '^':
                formatted.append(c_str.center(w))
            else:
                formatted.append(c_str.ljust(w))
        return " | ".join(formatted)

    header_line = render_row(headers)
    separator_line = "-+-".join(['-' * w for w in col_widths])
    data_lines = [render_row(r) for r in rows]

    return f"{header_line}\n{separator_line}\n" + "\n".join(data_lines)


def check_physical_ranges(df: pd.DataFrame) -> Tuple[Dict[str, Any], str]:
    """Validate numeric columns against domain-defined physical operating ranges."""
    results = {}
    overall_status = "PASS"

    for col, spec in PHYSICAL_RANGES.items():
        if col not in df.columns:
            continue

        series = pd.to_numeric(df[col], errors='coerce').dropna()
        if series.empty:
            results[col] = {
                'status': 'WARN',
                'min_allowed': spec['min'],
                'max_allowed': spec['max'],
                'min_observed': None,
                'max_observed': None,
                'violations_below': 0,
                'violations_above': 0,
                'total_violations': 0,
                'violation_rate_pct': 0.0,
                'unit': spec['unit']
            }
            if overall_status == "PASS":
                overall_status = "WARN"
            continue

        min_obs = float(series.min())
        max_obs = float(series.max())
        below = int((series < spec['min']).sum())
        above = int((series > spec['max']).sum())
        total_viol = below + above
        viol_pct = round((total_viol / len(series)) * 100, 4)

        if total_viol > 0:
            status = "FAIL"
            overall_status = "FAIL"
        else:
            status = "PASS"

        results[col] = {
            'status': status,
            'min_allowed': spec['min'],
            'max_allowed': spec['max'],
            'min_observed': round(min_obs, 4),
            'max_observed': round(max_obs, 4),
            'violations_below': below,
            'violations_above': above,
            'total_violations': total_viol,
            'violation_rate_pct': viol_pct,
            'unit': spec['unit']
        }

    return results, overall_status


def check_timestamp_monotonicity(df: pd.DataFrame) -> Tuple[Dict[str, Any], str]:
    """Verify chronological monotonicity and identify time reversals or duplicated timestamps."""
    ts_col = None
    for candidate in ['timestamp', 'noted_date', 'date', 'datetime', 'time']:
        if candidate in df.columns:
            ts_col = candidate
            break

    if ts_col is None:
        return {'status': 'PASS', 'note': 'No timestamp column present in dataset'}, 'PASS'

    # Parse timestamps
    df_ts = df.copy()
    df_ts['parsed_dt'] = pd.to_datetime(df_ts[ts_col], errors='coerce')
    invalid_dt = int(df_ts['parsed_dt'].isna().sum())

    results: Dict[str, Any] = {
        'timestamp_column': ts_col,
        'invalid_timestamps': invalid_dt,
        'per_sensor': {}
    }
    overall_status = "PASS"

    if 'sensor_id' in df_ts.columns:
        sensor_groups = df_ts.groupby('sensor_id', sort=False)
    else:
        sensor_groups = [('ALL', df_ts)]

    for sensor_id, group in sensor_groups:
        dts = group['parsed_dt'].dropna()
        total_readings = len(dts)

        if total_readings < 2:
            results['per_sensor'][str(sensor_id)] = {
                'total_readings': total_readings,
                'status': 'PASS',
                'note': 'Insufficient readings for monotonicity check'
            }
            continue

        diffs = dts.diff().dropna()
        neg_diffs = int((diffs < pd.Timedelta(0)).sum())
        zero_diffs = int((diffs == pd.Timedelta(0)).sum())
        is_strictly_monotonic = bool(neg_diffs == 0 and zero_diffs == 0)

        if neg_diffs > 0:
            status = "FAIL"
            overall_status = "FAIL"
        elif zero_diffs > 0:
            status = "WARN"
            if overall_status == "PASS":
                overall_status = "WARN"
        else:
            status = "PASS"

        results['per_sensor'][str(sensor_id)] = {
            'total_readings': total_readings,
            'start_timestamp': str(dts.iloc[0]),
            'end_timestamp': str(dts.iloc[-1]),
            'time_reversals_backwards': neg_diffs,
            'duplicate_timestamp_steps': zero_diffs,
            'is_strictly_monotonic': is_strictly_monotonic,
            'status': status
        }

    results['status'] = overall_status
    return results, overall_status


def check_missing_values(df: pd.DataFrame) -> Tuple[Dict[str, Any], str]:
    """Calculate missing and null value rates per column."""
    results = {}
    overall_status = "PASS"
    total_rows = len(df)

    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        missing_pct = round((missing_count / total_rows) * 100, 4) if total_rows > 0 else 0.0

        if missing_count == 0:
            status = "PASS"
        elif missing_pct <= 5.0:
            status = "WARN"
            if overall_status == "PASS":
                overall_status = "WARN"
        else:
            status = "FAIL"
            overall_status = "FAIL"

        results[col] = {
            'missing_count': missing_count,
            'missing_pct': missing_pct,
            'total_rows': total_rows,
            'status': status
        }

    return results, overall_status


def check_statistical_outliers(df: pd.DataFrame) -> Tuple[Dict[str, Any], str]:
    """Detect statistical anomalies exceeding 3 standard deviations (Z > 3) per sensor."""
    numeric_cols = [
        c for c in ['temperature', 'humidity', 'ambient_temperature', 'power_kw']
        if c in df.columns
    ]
    if not numeric_cols:
        # Fallback to any numeric float/int column
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if not c.endswith('_state') and not c.endswith('_open')]

    results: Dict[str, Any] = {'per_sensor': {}}
    overall_status = "PASS"

    if 'sensor_id' in df.columns:
        sensors = df['sensor_id'].dropna().unique()
    else:
        sensors = ['ALL']

    for sensor in sensors:
        sensor_key = str(sensor)
        results['per_sensor'][sensor_key] = {}
        sensor_df = df[df['sensor_id'] == sensor] if 'sensor_id' in df.columns else df

        for col in numeric_cols:
            series = pd.to_numeric(sensor_df[col], errors='coerce').dropna()
            n = len(series)
            if n < 5:
                continue

            mean_val = float(series.mean())
            std_val = float(series.std(ddof=1))

            if std_val < 1e-9:
                results['per_sensor'][sensor_key][col] = {
                    'mean': round(mean_val, 4),
                    'std': round(std_val, 4),
                    'lower_3sigma': round(mean_val, 4),
                    'upper_3sigma': round(mean_val, 4),
                    'outlier_count': 0,
                    'outlier_pct': 0.0,
                    'min_observed': round(float(series.min()), 4),
                    'max_observed': round(float(series.max()), 4),
                    'status': 'PASS'
                }
                continue

            lower_bound = mean_val - 3.0 * std_val
            upper_bound = mean_val + 3.0 * std_val
            outliers = series[(series < lower_bound) | (series > upper_bound)]
            outlier_count = int(len(outliers))
            outlier_pct = round((outlier_count / n) * 100, 4)

            # In standard normal distributions, ~0.27% naturally falls outside 3 sigma.
            # > 1.5% indicates an unusually heavy tail or transient shock.
            if outlier_count == 0:
                status = "PASS"
            elif outlier_pct <= 1.5:
                status = "PASS"  # Natural statistical variation
            elif outlier_pct <= 3.5:
                status = "WARN"
                if overall_status == "PASS":
                    overall_status = "WARN"
            else:
                status = "FAIL"
                overall_status = "FAIL"

            results['per_sensor'][sensor_key][col] = {
                'mean': round(mean_val, 4),
                'std': round(std_val, 4),
                'lower_3sigma': round(lower_bound, 4),
                'upper_3sigma': round(upper_bound, 4),
                'outlier_count': outlier_count,
                'outlier_pct': outlier_pct,
                'min_observed': round(float(series.min()), 4),
                'max_observed': round(float(series.max()), 4),
                'status': status
            }

    results['status'] = overall_status
    return results, overall_status


def check_duplicates_and_stuck_readings(df: pd.DataFrame) -> Tuple[Dict[str, Any], str]:
    """Detect exact duplicates, timestamp collisions, and stuck sensor flatlines."""
    overall_status = "PASS"
    total_rows = len(df)

    # 1. Exact row duplicates
    exact_dup_count = int(df.duplicated().sum())
    exact_status = "PASS" if exact_dup_count == 0 else "WARN"
    if exact_status == "WARN" and overall_status == "PASS":
        overall_status = "WARN"

    # 2. Same sensor_id + timestamp duplicates
    ts_col = 'timestamp' if 'timestamp' in df.columns else None
    sensor_col = 'sensor_id' if 'sensor_id' in df.columns else None

    if sensor_col and ts_col:
        sensor_ts_dup_count = int(df.duplicated(subset=[sensor_col, ts_col]).sum())
        sensor_ts_status = "PASS" if sensor_ts_dup_count == 0 else "FAIL"
        if sensor_ts_status == "FAIL":
            overall_status = "FAIL"
    else:
        sensor_ts_dup_count = 0
        sensor_ts_status = "PASS"

    # 3. Near-duplicate / stuck temperature readings (> 10 consecutive identical readings)
    temp_col = 'temperature' if 'temperature' in df.columns else ('temp' if 'temp' in df.columns else None)
    stuck_episodes: List[Dict[str, Any]] = []
    total_stuck_readings = 0
    max_streak = 0

    if temp_col:
        sensor_groups = df.groupby(sensor_col, sort=False) if sensor_col else [('ALL', df)]
        for sensor_id, grp in sensor_groups:
            # Sort chronologically if timestamp exists
            if ts_col:
                grp = grp.sort_values(ts_col)
            temps = grp[temp_col].reset_index(drop=True)
            ts_series = grp[ts_col].reset_index(drop=True) if ts_col else None

            if len(temps) <= STUCK_SENSOR_THRESHOLD:
                continue

            # Run Length Encoding: consecutive equality mask
            is_diff = (temps != temps.shift(1))
            run_ids = is_diff.cumsum()
            run_sizes = temps.groupby(run_ids).size()

            # Filter for streaks strictly > 10 readings
            stuck_runs = run_sizes[run_sizes > STUCK_SENSOR_THRESHOLD]

            for run_id, count in stuck_runs.items():
                indices = run_ids[run_ids == run_id].index
                start_i = indices[0]
                end_i = indices[-1]
                val = float(temps.iloc[start_i])
                st_time = str(ts_series.iloc[start_i]) if ts_series is not None else str(start_i)
                en_time = str(ts_series.iloc[end_i]) if ts_series is not None else str(end_i)

                streak_len = int(count)
                total_stuck_readings += streak_len
                max_streak = max(max_streak, streak_len)

                stuck_episodes.append({
                    'sensor_id': str(sensor_id),
                    'repeated_temperature': round(val, 4),
                    'streak_length': streak_len,
                    'start_time': st_time,
                    'end_time': en_time
                })

    stuck_status = "PASS" if len(stuck_episodes) == 0 else "WARN"
    if stuck_status == "WARN" and overall_status == "PASS":
        overall_status = "WARN"

    results = {
        'status': overall_status,
        'exact_row_duplicates': {
            'count': exact_dup_count,
            'rate_pct': round((exact_dup_count / total_rows) * 100, 4) if total_rows > 0 else 0.0,
            'status': exact_status
        },
        'sensor_timestamp_duplicates': {
            'count': sensor_ts_dup_count,
            'rate_pct': round((sensor_ts_dup_count / total_rows) * 100, 4) if total_rows > 0 else 0.0,
            'status': sensor_ts_status
        },
        'stuck_sensor_readings': {
            'threshold_consecutive': STUCK_SENSOR_THRESHOLD,
            'episodes_detected': len(stuck_episodes),
            'total_stuck_rows': total_stuck_readings,
            'max_streak_length': max_streak,
            'status': stuck_status,
            'episodes': stuck_episodes[:20]  # Store top 20 episodes
        }
    }

    return results, overall_status


def detect_delimiter(file_path: Path) -> str:
    """Detect CSV delimiter by inspecting first non-empty lines."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(5):
                line = f.readline()
                if not line:
                    break
                s = line.strip()
                if s:
                    semi = s.count(";")
                    comma = s.count(",")
                    tab = s.count("\t")
                    if semi > comma and semi > 0:
                        return ";"
                    if tab > comma and tab > 0:
                        return "\t"
                    if comma > 0:
                        return ","
    except Exception:
        pass
    return ","


def audit_dataset(file_path: Path) -> Dict[str, Any]:
    """Execute complete diagnostic suite on a single CSV telemetry file."""
    print(f"\n{'=' * 78}")
    print(f"AUDITING DATASET: {file_path.name}")
    print(f"Location: {file_path}")
    print(f"{'=' * 78}")

    delim = detect_delimiter(file_path)
    try:
        df = pd.read_csv(file_path, sep=delim, low_memory=False)
        if len(df.columns) == 1 and (";" in df.columns[0] or "," in df.columns[0]):
            alt_delim = ";" if ";" in df.columns[0] else ","
            df = pd.read_csv(file_path, sep=alt_delim, low_memory=False)
    except Exception as e:
        print(f"  [FAIL] Unable to read CSV file: {e}")
        return {
            'file_path': str(file_path),
            'error': str(e),
            'overall_status': 'FAIL'
        }

    # Normalize common datetime and sensor column variations for diagnostics
    if 'Date' in df.columns and 'Time' in df.columns and 'timestamp' not in df.columns:
        df['timestamp'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str), dayfirst=True, errors='coerce')
    if 'Temperature (C)' in df.columns and 'temperature' not in df.columns:
        df['temperature'] = pd.to_numeric(df['Temperature (C)'], errors='coerce')
    elif 'Temperature' in df.columns and 'temperature' not in df.columns:
        df['temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
    if 'Humidity (%)' in df.columns and 'humidity' not in df.columns:
        df['humidity'] = pd.to_numeric(df['Humidity (%)'], errors='coerce')
    elif 'Humidity' in df.columns and 'humidity' not in df.columns:
        df['humidity'] = pd.to_numeric(df['Humidity'], errors='coerce')
    if 'sensor_id' not in df.columns:
        # If filename implies sensor (e.g. SENSOR01), attach synthetic sensor_id for grouping
        stem = file_path.stem.split('_')[0]
        if stem.upper().startswith('SENSOR'):
            df['sensor_id'] = stem.upper()

    total_rows, total_cols = df.shape
    file_size_kb = round(file_path.stat().st_size / 1024, 2)
    sensors = sorted(df['sensor_id'].dropna().unique().tolist()) if 'sensor_id' in df.columns else ['None']

    print(f"  Dimensions:   {total_rows:,} rows x {total_cols} columns ({file_size_kb:,} KB)")
    print(f"  Sensors:      {', '.join(sensors)}")
    print(f"  Columns:      {', '.join(df.columns.tolist()[:8])}{' ...' if total_cols > 8 else ''}\n")

    # 1. Physical Ranges
    range_res, range_stat = check_physical_ranges(df)
    print(f"[1] PHYSICAL RANGE VALIDATION: [{range_stat}]")
    if range_res:
        r_headers = ["Channel", "Allowed Range", "Observed Range", "Violations", "Rate (%)", "Status"]
        r_rows = []
        for col, r in range_res.items():
            allowed = f"{r['min_allowed']} to {r['max_allowed']} {r['unit']}"
            observed = f"{r['min_observed']} to {r['max_observed']} {r['unit']}" if r['min_observed'] is not None else "N/A"
            r_rows.append([
                col,
                allowed,
                observed,
                str(r['total_violations']),
                f"{r['violation_rate_pct']:.2f}%",
                f"[{r['status']}]"
            ])
        print(format_table(r_headers, r_rows, alignments=['<', '<', '<', '>', '>', '^']))
    else:
        print("  No recognized physical telemetry channels present for range validation.")
    print()

    # 2. Timestamp Monotonicity
    mono_res, mono_stat = check_timestamp_monotonicity(df)
    print(f"[2] TIMESTAMP MONOTONICITY PER SENSOR: [{mono_stat}]")
    if 'per_sensor' in mono_res and mono_res['per_sensor']:
        m_headers = ["Sensor ID", "Readings", "Start Timestamp", "End Timestamp", "Reversals", "Zero Diffs", "Status"]
        m_rows = []
        for s_id, s_info in mono_res['per_sensor'].items():
            if 'time_reversals_backwards' in s_info:
                m_rows.append([
                    str(s_id),
                    f"{s_info['total_readings']:,}",
                    str(s_info.get('start_timestamp', ''))[:19],
                    str(s_info.get('end_timestamp', ''))[:19],
                    str(s_info['time_reversals_backwards']),
                    str(s_info['duplicate_timestamp_steps']),
                    f"[{s_info['status']}]"
                ])
            else:
                m_rows.append([str(s_id), str(s_info.get('total_readings', 0)), "N/A", "N/A", "0", "0", f"[{s_info.get('status', 'PASS')}]"])
        print(format_table(m_headers, m_rows, alignments=['<', '>', '<', '<', '>', '>', '^']))
    else:
        print(f"  Note: {mono_res.get('note', 'No timestamp data')}")
    print()

    # 3. Missing Value Analysis
    miss_res, miss_stat = check_missing_values(df)
    print(f"[3] MISSING VALUE ANALYSIS: [{miss_stat}]")
    miss_headers = ["Column", "Null Count", "Missing (%)", "Status"]
    miss_rows = []
    for col, m in miss_res.items():
        miss_rows.append([
            col,
            str(m['missing_count']),
            f"{m['missing_pct']:.2f}%",
            f"[{m['status']}]"
        ])
    print(format_table(miss_headers, miss_rows, alignments=['<', '>', '>', '^']))
    print()

    # 4. Statistical Outliers
    outl_res, outl_stat = check_statistical_outliers(df)
    print(f"[4] STATISTICAL OUTLIER DETECTION (Z > 3 Sigma): [{outl_stat}]")
    if 'per_sensor' in outl_res and outl_res['per_sensor']:
        o_headers = ["Sensor", "Channel", "Mean ± Std", "3-Sigma Bounds", "Outliers", "Rate (%)", "Status"]
        o_rows = []
        for s_id, channels in outl_res['per_sensor'].items():
            for ch, st in channels.items():
                mean_std = f"{st['mean']:.2f} ± {st['std']:.2f}"
                bounds = f"[{st['lower_3sigma']:.2f}, {st['upper_3sigma']:.2f}]"
                o_rows.append([
                    str(s_id),
                    ch,
                    mean_std,
                    bounds,
                    str(st['outlier_count']),
                    f"{st['outlier_pct']:.2f}%",
                    f"[{st['status']}]"
                ])
        print(format_table(o_headers, o_rows, alignments=['<', '<', '^', '^', '>', '>', '^']))
    print()

    # 5. Duplicate & Stuck Sensor Detection
    dup_res, dup_stat = check_duplicates_and_stuck_readings(df)
    print(f"[5] DUPLICATE & STUCK SENSOR DETECTION: [{dup_stat}]")
    d_exact = dup_res['exact_row_duplicates']
    d_sensor_ts = dup_res['sensor_timestamp_duplicates']
    d_stuck = dup_res['stuck_sensor_readings']

    print(f"  - Exact Row Duplicates:            {d_exact['count']:,} ({d_exact['rate_pct']:.2f}%) [{d_exact['status']}]")
    print(f"  - Sensor + Timestamp Collisions:   {d_sensor_ts['count']:,} ({d_sensor_ts['rate_pct']:.2f}%) [{d_sensor_ts['status']}]")
    print(f"  - Stuck Episodes (>10 Identical):  {d_stuck['episodes_detected']} episodes, {d_stuck['total_stuck_rows']} rows (Max: {d_stuck['max_streak_length']}) [{d_stuck['status']}]")
    if d_stuck['episodes_detected'] > 0:
        for ep in d_stuck['episodes'][:3]:
            print(f"    * Sensor {ep['sensor_id']}: {ep['streak_length']} readings stuck at {ep['repeated_temperature']} °C ({ep['start_time']} to {ep['end_time']})")
    print()

    # Determine overall status for this dataset
    statuses = [range_stat, mono_stat, miss_stat, outl_stat, dup_stat]
    if "FAIL" in statuses:
        overall_status = "FAIL"
    elif "WARN" in statuses:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    print(f"DATASET DIAGNOSTIC VERDICT: [{overall_status}]")

    return {
        'file_path': str(file_path),
        'file_name': file_path.name,
        'row_count': total_rows,
        'column_count': total_cols,
        'columns': df.columns.tolist(),
        'sensors': sensors,
        'quality_checks': {
            'physical_ranges': {
                'status': range_stat,
                'channels': range_res
            },
            'timestamp_monotonicity': mono_res,
            'missing_values': {
                'status': miss_stat,
                'columns': miss_res
            },
            'statistical_outliers_3sigma': outl_res
        },
        'duplicate_checks': dup_res,
        'overall_status': overall_status
    }


def find_target_csvs(project_root: Path, input_arg: Optional[str] = None, datasets_dir_arg: Optional[str] = None) -> List[Path]:
    """Discover simulated cold chain baseline CSV and any CSVs present in Datasets/ directory."""
    csv_paths: List[Path] = []

    if input_arg:
        custom_p = Path(input_arg)
        if not custom_p.is_absolute():
            custom_p = project_root / custom_p
        if custom_p.exists() and custom_p.is_file():
            return [custom_p]
        else:
            print(f"Warning: Specified input file {custom_p} does not exist.")

    # 1. Primary ground truth baseline
    baseline_csv = project_root / "data" / "raw" / "simulated_cold_chain.csv"
    if baseline_csv.exists():
        csv_paths.append(baseline_csv)
    else:
        print(f"Warning: Primary baseline dataset not found at {baseline_csv}")

    # 2. Datasets/ directory (if exists)
    datasets_dir = project_root / (datasets_dir_arg or "Datasets")
    if datasets_dir.exists() and datasets_dir.is_dir():
        # Find all CSV files recursively
        for p in sorted(datasets_dir.rglob("*.csv")):
            # Ignore archives / temp files if any
            if "_original_downloads" in p.parts:
                continue
            if p not in csv_paths:
                csv_paths.append(p)

    return csv_paths


def main():
    parser = argparse.ArgumentParser(description="ColdChain-AI Data Quality and Duplicate Diagnostics")
    parser.add_argument("--input", "-i", type=str, default=None, help="Custom single CSV file to audit")
    parser.add_argument("--output", "-o", type=str, default=None, help="Custom path for JSON quality report")
    parser.add_argument("--datasets-dir", "-d", type=str, default="Datasets", help="Directory name for external datasets")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    if not (project_root / "data").exists() and (project_root.parent / "data").exists():
        project_root = project_root.parent
    reports_dir = project_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if args.output else reports_dir / "data_quality_report.json"
    if not output_path.is_absolute():
        output_path = project_root / output_path

    print("=" * 78)
    print("COLDCHAIN-AI DATA QUALITY & DUPLICATE DETECTION SUITE")
    print(f"Execution Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project Root:        {project_root}")
    print("=" * 78)

    csv_files = find_target_csvs(project_root, args.input, args.datasets_dir)
    if not csv_files:
        print("\n[ERROR] No CSV datasets found to audit. Please ensure data/raw/simulated_cold_chain.csv exists.")
        sys.exit(1)

    print(f"Found {len(csv_files)} dataset(s) for audit:")
    for idx, f in enumerate(csv_files, 1):
        print(f"  {idx}. {f.relative_to(project_root) if f.is_relative_to(project_root) else f}")

    audits = []
    total_records = 0
    passed_count = 0
    warn_count = 0
    fail_count = 0

    for csv_file in csv_files:
        audit_res = audit_dataset(csv_file)
        audits.append(audit_res)
        total_records += audit_res.get('row_count', 0)
        st = audit_res.get('overall_status', 'FAIL')
        if st == 'PASS':
            passed_count += 1
        elif st == 'WARN':
            warn_count += 1
        else:
            fail_count += 1

    overall_system_status = "FAIL" if fail_count > 0 else ("WARN" if warn_count > 0 else "PASS")

    # JSON report structure
    report_dict = {
        'generated_at': datetime.now().isoformat(),
        'project_root': str(project_root),
        'summary': {
            'datasets_scanned': len(audits),
            'total_telemetry_rows': total_records,
            'overall_status': overall_system_status,
            'passed_datasets': passed_count,
            'warning_datasets': warn_count,
            'failed_datasets': fail_count
        },
        'datasets': audits
    }

    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(to_serializable(report_dict), f, indent=2)

    print(f"\n{'=' * 78}")
    print("DATA QUALITY AUDIT COMPLETED")
    print(f"Total Datasets Scanned:  {len(audits)}")
    print(f"Total Telemetry Rows:    {total_records:,}")
    print(f"System Quality Verdict:  [{overall_system_status}]")
    print(f"Saved Structured Report: {output_path}")
    print(f"{'=' * 78}\n")


if __name__ == '__main__':
    main()
