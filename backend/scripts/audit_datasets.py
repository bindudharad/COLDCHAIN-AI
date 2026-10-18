"""Dataset Auditing and Inventory Utility for ColdChain-AI.

Scans data directories (data/raw/ and Datasets/) recursively for CSV datasets,
extracts comprehensive structural, statistical, and temporal metrics, validates
data integrity, classifies domain boundaries, and exports a canonical JSON inventory.

Referenced in README line 90: `python scripts/audit_datasets.py`
"""
from __future__ import annotations

import argparse
from datetime import datetime, date
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Add project root to sys.path according to project architectural pattern
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

# Canonical domain classifications defined for ColdChain-AI research framework
CANONICAL_DOMAINS = [
    "COLD_CHAIN",
    "IOT_TEMPERATURE",
    "ENERGY",
    "PREDICTIVE_MAINTENANCE",
    "ELECTRICITY",
    "SIMULATION",
]

# Registered reference catalog for tracking expected project benchmarks
CANONICAL_CATALOG = [
    {
        "identifier": "simulated_cold_chain.csv",
        "relative_path": "data/raw/simulated_cold_chain.csv",
        "primary_domain": "COLD_CHAIN",
        "provenance": "SIMULATION",
        "expected_records": 12000,
        "expected_columns": 10,
        "description": "Multi-sensor cold rooms (CC-01..03), food [0, 5] deg C, compressor cycles, door events",
    },
    {
        "identifier": "iot_temperature_readings.csv",
        "relative_path": "Datasets/02_iot_temperature_readings/iot_temperature_readings.csv",
        "primary_domain": "IOT_TEMPERATURE",
        "provenance": "PUBLIC_DATASET",
        "expected_records": 97606,
        "expected_columns": 5,
        "description": "ESP8266 living space telemetry (21-51 deg C ambient), Manikanta Kumar (Kaggle)",
    },
    {
        "identifier": "energy_consumption_prediction.csv",
        "relative_path": "Datasets/03_energy_consumption/energy_consumption_prediction.csv",
        "primary_domain": "ENERGY",
        "provenance": "PUBLIC_DATASET",
        "expected_records": 1000,
        "expected_columns": 5,
        "description": "Building HVAC energy consumption vs ambient temperature & occupancy (Kaggle)",
    },
    {
        "identifier": "eviot_predictive_maintenance.csv",
        "relative_path": "Datasets/04_eviot_predictive_maintenance/eviot_predictive_maintenance.csv",
        "primary_domain": "PREDICTIVE_MAINTENANCE",
        "provenance": "PUBLIC_DATASET",
        "expected_records": 175393,
        "expected_columns": 5,
        "description": "High-frequency EV battery pack thermal/electrical telemetry for Big Data stress testing",
    },
    {
        "identifier": "journey_to_zero_electricity.csv",
        "relative_path": "Datasets/05_electricity_forecasting/journey_to_zero_electricity_train.csv",
        "primary_domain": "ELECTRICITY",
        "provenance": "PUBLIC_DATASET",
        "expected_records": 8592,
        "expected_columns": 4,
        "description": "Macro municipal power grid electricity demand vs outdoor climate (Journey to Zero)",
    },
    {
        "identifier": "synthetic_cold_chain_stream.csv",
        "relative_path": "data/raw/synthetic_scalability_100k.csv",
        "primary_domain": "SIMULATION",
        "provenance": "SIMULATION",
        "expected_records": 100000,
        "expected_columns": 8,
        "description": "High-throughput synthetic thermodynamic stream for scalability stress testing",
    },
]


def format_bytes(num_bytes: int) -> str:
    """Format file size into human-readable representation."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.2f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def to_json_serializable(val: Any) -> Any:
    """Recursively convert NumPy/pandas scalars and temporal objects to native Python types."""
    if isinstance(val, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(val)
    if isinstance(val, (np.floating, np.float64, np.float32, np.float16)):
        if math.isnan(val) or math.isinf(val):
            return None
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
        return {str(k): to_json_serializable(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [to_json_serializable(x) for x in val]
    return val


def render_ascii_table(
    headers: List[str],
    rows: List[List[str]],
    alignments: Optional[List[str]] = None,
) -> str:
    """Render a well-spaced ASCII table with alignment support ('<', '>', '^')."""
    if not headers:
        return ""
    col_count = len(headers)
    if alignments is None:
        alignments = ["<"] * col_count

    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            if idx < col_count:
                col_widths[idx] = max(col_widths[idx], len(str(cell)))

    def format_row(cells: List[str]) -> str:
        parts = []
        for cell, width, align in zip(cells, col_widths, alignments):
            c_str = str(cell)
            if align == ">":
                parts.append(c_str.rjust(width))
            elif align == "^":
                parts.append(c_str.center(width))
            else:
                parts.append(c_str.ljust(width))
        return " | ".join(parts)

    header_line = format_row(headers)
    separator = "-+-".join(["-" * w for w in col_widths])
    body_lines = [format_row(r) for r in rows]

    return f"{header_line}\n{separator}\n" + "\n".join(body_lines)


def classify_dataset_domain(
    file_path: Path, df: Optional[pd.DataFrame] = None
) -> Dict[str, str]:
    """Classify dataset into canonical research domain.

    Returns dict with primary domain (one of CANONICAL_DOMAINS), provenance, and rationale.
    """
    path_lower = str(file_path).lower().replace("\\", "/")
    name_lower = file_path.name.lower()
    cols_lower = [str(c).lower() for c in (df.columns if df is not None else [])]
    col_set = set(cols_lower)

    # Detect physical file type
    file_type = "RAW_TIMESERIES"
    if "overview" in name_lower:
        file_type = "SUMMARY_STATISTICS"
    elif "experiment_actions" in name_lower or "action" in name_lower:
        file_type = "EVENT_LOGS"
    elif "cold_storage" in path_lower or "season" in col_set:
        file_type = "DAILY_MACRO_OBSERVATIONS"
    elif "browser_upload" in name_lower:
        file_type = "SINGLE_TEST_UPLOAD"
    elif name_lower.endswith((".ino", ".py", ".sh")):
        file_type = "SOURCE_CODE"
    elif "preprocessed" in name_lower or "preprocessed" in path_lower:
        file_type = "PREPROCESSED_TIMESERIES"

    # 1. Predictive Maintenance (EV Battery / Industrial)
    if (
        "eviot" in path_lower
        or "predictive_maintenance" in path_lower
        or any(k in col_set for k in ["battery_temp", "state_of_charge"])
    ):
        return {
            "domain": "PREDICTIVE_MAINTENANCE",
            "provenance": "PUBLIC_DATASET",
            "file_type": file_type,
            "rationale": "High-frequency EV battery pack thermal and electrical telemetry",
        }

    # 2. Electricity Load / Demand
    if (
        "electricity" in path_lower
        or "journey_to_zero" in path_lower
        or any(k in col_set for k in ["consumption_kwh", "dew_point"])
    ):
        return {
            "domain": "ELECTRICITY",
            "provenance": "PUBLIC_DATASET",
            "file_type": file_type,
            "rationale": "Municipal grid electricity demand load vs outdoor ambient conditions",
        }

    # 3. Energy Consumption (HVAC)
    if (
        "energy" in path_lower
        or any(
            k in col_set
            for k in ["squarefootage", "occupancy", "energyconsumption"]
        )
    ):
        return {
            "domain": "ENERGY",
            "provenance": "PUBLIC_DATASET",
            "file_type": file_type,
            "rationale": "Building HVAC electrical demand vs ambient temperature & occupancy",
        }

    # 4. IoT Temperature (ESP8266 Ambient)
    if (
        "02_iot" in path_lower
        or "01_temperature" in path_lower
        or "iot_temp" in path_lower
        or any(k in col_set for k in ["noted_date", "room_id/id", "out/in"])
    ):
        return {
            "domain": "IOT_TEMPERATURE",
            "provenance": "PUBLIC_DATASET",
            "file_type": file_type,
            "rationale": "Living space room ambient IoT temperature telemetry (ESP8266 node)",
        }

    # 5. Cold Chain Logistics (Chamber Storage 0.0 to 5.0 deg C)
    if (
        "cold_chain" in path_lower
        or "coldchain" in path_lower
        or "zenodo" in path_lower
        or "cold_storage" in path_lower
        or {"compressor_state", "door_open"}.issubset(col_set)
        or (
            {"temperature", "humidity"}.issubset(col_set)
            and not {"squarefootage", "occupancy"}.intersection(col_set)
            and not {"voltage", "battery_temp"}.intersection(col_set)
        )
    ):
        # Strict Provenance Determination
        if "datasets/" in path_lower or "zenodo" in path_lower or "case_study" in path_lower or "hohenheim" in path_lower:
            provenance = "PUBLIC_DATASET"
        elif "simulat" in path_lower or "synthetic" in path_lower or "browser_upload" in path_lower:
            provenance = "SIMULATION"
        else:
            provenance = "SIMULATION"

        # Refined Rationale
        if file_type == "SUMMARY_STATISTICS":
            rationale = "Summary statistics matrix across 9 physical cold room sensors (not raw time-series)"
        elif file_type == "EVENT_LOGS":
            rationale = "Event log of physical door openings and sensor repositioning actions"
        elif file_type == "DAILY_MACRO_OBSERVATIONS":
            rationale = "Daily aggregated cold storage temperature records (1.7 to 5.0 deg C)"
        elif "zenodo" in path_lower:
            rationale = "Physical 5-second multi-sensor cold storage room telemetry (Hohenheim, DOI: 10.5281/zenodo.15130001)"
        elif "browser_upload" in name_lower:
            rationale = "Single-row interactive browser test upload"
        else:
            rationale = "Refrigerated cold-chain food safety storage logistics (0.0 to 5.0 deg C)"

        return {
            "domain": "COLD_CHAIN",
            "provenance": provenance,
            "file_type": file_type,
            "rationale": rationale,
        }

    # 6. Generic Simulation
    if "simulat" in path_lower or "synthetic" in path_lower:
        return {
            "domain": "SIMULATION",
            "provenance": "SIMULATION",
            "file_type": file_type,
            "rationale": "Synthetically generated benchmark stream for stress testing",
        }

    return {
        "domain": "COLD_CHAIN",
        "provenance": "PUBLIC_DATASET" if "datasets/" in path_lower else "SIMULATION",
        "file_type": file_type,
        "rationale": "Cold-chain telemetry stream",
    }


def find_csv_files(
    directories: List[Path], project_root: Path
) -> Tuple[List[Path], Dict[str, Dict[str, Any]]]:
    """Scan candidate directories recursively for CSV files, handling missing paths gracefully."""
    discovered: List[Path] = []
    dir_reports: Dict[str, Dict[str, Any]] = {}

    for d in directories:
        rel_key = str(d.relative_to(project_root) if d.is_relative_to(project_root) else d)
        if not d.exists():
            dir_reports[rel_key] = {
                "status": "NOT FOUND",
                "path": str(d),
                "csv_count": 0,
            }
            print(f"  [-] Directory {rel_key}: [NOT FOUND] (checked {d})")
            continue

        if not d.is_dir():
            dir_reports[rel_key] = {
                "status": "NOT A DIRECTORY",
                "path": str(d),
                "csv_count": 0,
            }
            print(f"  [-] Path {rel_key}: [NOT A DIRECTORY]")
            continue

        # Scan recursively for CSV files
        csvs_in_dir = []
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix.lower() == ".csv":
                csvs_in_dir.append(p)
                if p not in discovered:
                    discovered.append(p)

        dir_reports[rel_key] = {
            "status": "FOUND",
            "path": str(d),
            "csv_count": len(csvs_in_dir),
        }
        print(f"  [+] Directory {rel_key}: [FOUND] ({len(csvs_in_dir)} CSV files located)")

    return discovered, dir_reports


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


def compute_file_sha256(file_path: Path) -> str:
    """Compute cryptographic SHA-256 hash of a file for integrity provenance."""
    import hashlib
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "UNKNOWN"


def audit_single_csv(file_path: Path, project_root: Path) -> Dict[str, Any]:
    """Perform in-depth structural, missing-value, numeric, and temporal audit of a CSV file."""
    stat = file_path.stat()
    file_size_bytes = stat.st_size
    file_size_formatted = format_bytes(file_size_bytes)
    rel_path = file_path.relative_to(project_root) if file_path.is_relative_to(project_root) else file_path
    sha256 = compute_file_sha256(file_path)

    # Count raw lines in the file to detect malformed / skipped rows
    raw_lines = 0
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_lines = sum(1 for _ in f)
    except Exception:
        pass

    # Detect delimiter
    delim = detect_delimiter(file_path)

    # Read CSV with detected delimiter
    try:
        df = pd.read_csv(file_path, sep=delim, low_memory=False)
        # If read as single column and delimiter appears in header, fallback to python engine
        if len(df.columns) == 1 and (";" in df.columns[0] or "," in df.columns[0]):
            alt_delim = ";" if ";" in df.columns[0] else ","
            df = pd.read_csv(file_path, sep=alt_delim, low_memory=False)
            delim = alt_delim
    except Exception as exc:
        try:
            df = pd.read_csv(file_path, sep=None, engine="python", on_bad_lines="skip")
            delim = "auto"
        except Exception as exc2:
            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "relative_path": str(rel_path),
                "sha256": sha256,
                "file_size_bytes": file_size_bytes,
                "file_size_formatted": file_size_formatted,
                "delimiter": delim,
                "read_error": str(exc2),
                "row_count": 0,
                "column_count": 0,
                "raw_lines": raw_lines,
                "malformed_rows": raw_lines,
                "exact_duplicates": 0,
                "columns": [],
                "missing_values": {"total_missing": 0, "columns": {}},
                "numeric_statistics": {},
                "timestamp_info": None,
                "sensor_id_info": None,
                "domain_classification": {
                    "domain": "UNKNOWN",
                    "provenance": "UNKNOWN",
                    "rationale": f"Read failed: {exc2}",
                },
            }

    row_count = int(len(df))
    col_count = int(len(df.columns))
    columns = [str(c) for c in df.columns]

    # Calculate malformed rows count
    expected_rows = max(0, raw_lines - 1)
    malformed_rows = max(0, expected_rows - row_count)

    # Ensure numeric columns (e.g., temperature, humidity, power) are properly cast to float
    for col in df.columns:
        col_l = str(col).lower()
        if any(k in col_l for k in ["temp", "hum", "power", "volt", "curr", "energy", "duty", "state"]):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Data types
    dtypes_map = {str(c): str(t) for c, t in df.dtypes.items()}
    dtype_counts: Dict[str, int] = {}
    for t_str in dtypes_map.values():
        dtype_counts[t_str] = dtype_counts.get(t_str, 0) + 1

    # Missing values per column
    missing_by_col = {}
    total_missing = 0
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = round((null_count / row_count * 100) if row_count > 0 else 0.0, 4)
        missing_by_col[str(col)] = {
            "count": null_count,
            "percentage": null_pct,
        }
        total_missing += null_count

    # Numeric statistics
    numeric_stats: Dict[str, Dict[str, Optional[float]]] = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for ncol in numeric_cols:
        series = df[ncol].dropna()
        if len(series) > 0:
            c_min = float(series.min())
            c_max = float(series.max())
            c_mean = float(series.mean())
            c_std = float(series.std(ddof=1)) if len(series) > 1 else 0.0
            numeric_stats[str(ncol)] = {
                "min": round(c_min, 4),
                "max": round(c_max, 4),
                "mean": round(c_mean, 4),
                "std": round(c_std, 4),
                "count": int(len(series)),
            }
        else:
            numeric_stats[str(ncol)] = {
                "min": None,
                "max": None,
                "mean": None,
                "std": None,
                "count": 0,
            }

    # Timestamp column check
    timestamp_info = None
    detected_ts_col = None
    parsed_ts = None

    # Check for combined Date + Time columns (e.g. Hohenheim)
    if "Date" in df.columns and "Time" in df.columns:
        detected_ts_col = "Date + Time"
        try:
            parsed_ts = pd.to_datetime(
                df["Date"].astype(str) + " " + df["Time"].astype(str),
                dayfirst=True,
                errors="coerce",
            )
        except Exception:
            parsed_ts = None

    if parsed_ts is None:
        ts_candidates = ["timestamp", "noted_date", "datetime", "date", "time", "ts"]
        for cand in ts_candidates:
            match = [c for c in df.columns if c.lower() == cand]
            if match:
                detected_ts_col = match[0]
                try:
                    parsed_ts = pd.to_datetime(df[detected_ts_col], errors="coerce")
                    break
                except Exception:
                    continue

    if parsed_ts is not None and detected_ts_col is not None:
        valid_ts = parsed_ts.dropna()
        if len(valid_ts) > 0:
            min_dt = valid_ts.min()
            max_dt = valid_ts.max()
            time_span = str(max_dt - min_dt)
            sampling_interval_sec = None
            gaps_gt_30s = 0
            if len(valid_ts) > 1:
                diffs = valid_ts.diff().dropna()
                mode_diff = diffs.mode()
                if len(mode_diff) > 0:
                    sampling_interval_sec = round(float(mode_diff.iloc[0].total_seconds()), 2)
                gaps_gt_30s = int((diffs > pd.Timedelta(seconds=30)).sum())

            timestamp_info = {
                "column_name": str(detected_ts_col),
                "min_timestamp": min_dt.isoformat(),
                "max_timestamp": max_dt.isoformat(),
                "time_span": time_span,
                "valid_rows": int(len(valid_ts)),
                "invalid_rows": int(len(parsed_ts) - len(valid_ts)),
                "sampling_interval_sec": sampling_interval_sec,
                "gaps_gt_30s": gaps_gt_30s,
            }

    # Sensor ID check
    sensor_id_info = None
    sensor_col_candidates = ["sensor_id", "sensor", "room_id/id", "id"]
    detected_sensor_col = None
    for sc in sensor_col_candidates:
        match = [c for c in df.columns if c.lower() == sc]
        if match:
            detected_sensor_col = match[0]
            break

    if detected_sensor_col is not None:
        unique_vals = [str(x) for x in sorted(df[detected_sensor_col].dropna().unique())]
        counts_dict = {
            str(k): int(v)
            for k, v in df[detected_sensor_col].value_counts().items()
        }
        sensor_id_info = {
            "column_name": str(detected_sensor_col),
            "unique_count": len(unique_vals),
            "unique_values": unique_vals,
            "counts_per_sensor": counts_dict,
        }

    # Duplicate rows check
    exact_duplicates = int(df.duplicated().sum())

    # Domain classification
    classification = classify_dataset_domain(file_path, df)

    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "relative_path": str(rel_path),
        "sha256": sha256,
        "file_size_bytes": file_size_bytes,
        "file_size_formatted": file_size_formatted,
        "delimiter": delim,
        "row_count": row_count,
        "column_count": col_count,
        "raw_lines": raw_lines,
        "malformed_rows": malformed_rows,
        "exact_duplicates": exact_duplicates,
        "columns": columns,
        "data_types": dtypes_map,
        "data_type_counts": dtype_counts,
        "missing_values": {
            "total_missing": total_missing,
            "columns": missing_by_col,
        },
        "numeric_statistics": numeric_stats,
        "timestamp_info": timestamp_info,
        "sensor_id_info": sensor_id_info,
        "domain_classification": classification,
    }


def print_dataset_audit(audit: Dict[str, Any]) -> None:
    """Print readable console details for an audited dataset."""
    print("=" * 80)
    print(f"DATASET AUDIT REPORT: {audit['file_name']}")
    print("=" * 80)
    print(f"  Relative Path:   {audit['relative_path']}")
    print(f"  File Size:       {audit['file_size_formatted']} ({audit['file_size_bytes']:,} bytes)")
    print(f"  Dimensions:      {audit['row_count']:,} rows x {audit['column_count']} columns")

    cls_info = audit["domain_classification"]
    print(f"  Classified:      {cls_info['domain']} [{cls_info['provenance']}]")
    print(f"  Role/Rationale:  {cls_info['rationale']}")

    if audit.get("read_error"):
        print(f"\n  [!] READ ERROR: {audit['read_error']}")
        return

    # Data Types Summary
    dt_counts = audit.get("data_type_counts", {})
    dt_str = ", ".join([f"{k}: {v}" for k, v in dt_counts.items()])
    print(f"  Dtype Breakdown: {dt_str}")

    # Temporal info
    ts_info = audit.get("timestamp_info")
    if ts_info:
        print(f"  Temporal Span:   {ts_info['min_timestamp']}  -->  {ts_info['max_timestamp']} (Span: {ts_info['time_span']})")
    else:
        print("  Temporal Span:   None / No timestamp column detected")

    # Sensor IDs
    sid_info = audit.get("sensor_id_info")
    if sid_info:
        val_str = ", ".join(sid_info["unique_values"][:6])
        if len(sid_info["unique_values"]) > 6:
            val_str += f" ... (+{len(sid_info['unique_values']) - 6} more)"
        print(f"  Sensors ({sid_info['column_name']}): {sid_info['unique_count']} unique: [{val_str}]")
    else:
        print("  Sensors:         None / No sensor identifier column detected")

    # Missing values breakdown
    miss_info = audit["missing_values"]
    total_miss = miss_info["total_missing"]
    print(f"\n[1] Missing Value Analysis: Total Missing = {total_miss:,}")
    miss_rows = []
    for col, mdata in miss_info["columns"].items():
        miss_rows.append([
            col,
            str(audit["data_types"].get(col, "-")),
            f"{mdata['count']:,}",
            f"{mdata['percentage']:.2f}%",
            "CLEAN" if mdata["count"] == 0 else ("WARN" if mdata["percentage"] < 5 else "HIGH"),
        ])
    print(render_ascii_table(
        ["Column Name", "Data Type", "Null Count", "Null %", "Status"],
        miss_rows,
        alignments=["<", "<", ">", ">", "^"],
    ))

    # Numeric statistics breakdown
    num_stats = audit.get("numeric_statistics", {})
    if num_stats:
        print(f"\n[2] Numeric Column Statistics ({len(num_stats)} numeric channels):")
        stat_rows = []
        for col, sdata in num_stats.items():
            if sdata["min"] is not None:
                stat_rows.append([
                    col,
                    f"{sdata['count']:,}",
                    f"{sdata['min']:.4f}",
                    f"{sdata['max']:.4f}",
                    f"{sdata['mean']:.4f}",
                    f"{sdata['std']:.4f}",
                ])
            else:
                stat_rows.append([col, "0", "-", "-", "-", "-"])
        print(render_ascii_table(
            ["Numeric Channel", "Observed", "Min", "Max", "Mean", "Std Dev"],
            stat_rows,
            alignments=["<", ">", ">", ">", ">", ">"],
        ))
    print()


def print_summary_table(audits: List[Dict[str, Any]]) -> None:
    """Print high-level formatted comparison table across all audited CSV files."""
    print("=" * 80)
    print("DATASET AUDIT SUMMARY TABLE")
    print("=" * 80)
    if not audits:
        print("No CSV datasets were discovered to summarize.")
        print("=" * 80 + "\n")
        return

    headers = [
        "Dataset Name",
        "Size",
        "Rows",
        "Cols",
        "Missing",
        "Date Range",
        "Sensors",
        "Domain Tag",
    ]
    rows = []
    for a in audits:
        fname = a["file_name"]
        sz = a["file_size_formatted"]
        rows_str = f"{a['row_count']:,}"
        cols_str = str(a["column_count"])
        miss_str = f"{a['missing_values']['total_missing']:,}"

        ts_info = a.get("timestamp_info")
        if ts_info:
            d_start = ts_info["min_timestamp"].split("T")[0]
            d_end = ts_info["max_timestamp"].split("T")[0]
            dt_str = f"{d_start}..{d_end}"
        else:
            dt_str = "None"

        sid_info = a.get("sensor_id_info")
        if sid_info:
            if sid_info["unique_count"] <= 3:
                s_str = ",".join(sid_info["unique_values"])
            else:
                s_str = f"{sid_info['unique_count']} ids"
        else:
            s_str = "None"

        domain = a["domain_classification"]["domain"]
        rows.append([fname, sz, rows_str, cols_str, miss_str, dt_str, s_str, domain])

    print(render_ascii_table(
        headers,
        rows,
        alignments=["<", ">", ">", ">", ">", "^", "^", "^"],
    ))
    print("=" * 80 + "\n")


def print_classification_table(audits: List[Dict[str, Any]], project_root: Path) -> None:
    """Print the final domain classification table showcasing all 6 canonical research domains."""
    print("=" * 80)
    print("RESEARCH DOMAIN CLASSIFICATION TABLE (CANONICAL BENCHMARKS)")
    print("=" * 80)
    print("ColdChain-AI classifies data across 6 discrete telemetry and modeling domains:")
    print("  1. COLD_CHAIN             - Calibrated refrigerated storage baseline")
    print("  2. IOT_TEMPERATURE        - External physical ambient IoT telemetry (ESP8266)")
    print("  3. ENERGY                 - Building HVAC thermal-lift energy demand")
    print("  4. PREDICTIVE_MAINTENANCE - High-frequency EV battery pack thermal stress")
    print("  5. ELECTRICITY            - Municipal power grid electricity demand")
    print("  6. SIMULATION             - Chronological synthetic scalability stress stream")
    print("-" * 80)

    # 1. Audited Datasets Present on Disk
    headers = [
        "Dataset Identifier",
        "Domain Classification",
        "File Type",
        "Provenance Tag",
        "Records",
        "Research Function / Role",
    ]
    rows = []

    for a in audits:
        cls_info = a["domain_classification"]
        rows.append([
            a["file_name"],
            cls_info["domain"],
            cls_info.get("file_type", "RAW_TIMESERIES"),
            cls_info["provenance"],
            f"{a['row_count']:,}",
            cls_info["rationale"],
        ])

    print("\n[ACTIVE DATASETS AUDITED ON LOCAL DISK]")
    if rows:
        print(render_ascii_table(
            headers,
            rows,
            alignments=["<", "^", "^", "^", ">", "<"],
        ))
    else:
        print("  No active CSV files located on local disk.")

    # 2. Canonical Registry Cross-Reference Matrix
    print("\n[CANONICAL BENCHMARK REGISTRY & STATUS ON DISK]")
    reg_headers = [
        "Canonical Benchmark",
        "Domain",
        "Provenance",
        "Expected Path",
        "Disk Status",
    ]
    reg_rows = []
    for item in CANONICAL_CATALOG:
        target_path = project_root / item["relative_path"]
        exists = target_path.exists()
        status_str = "[PRESENT]" if exists else "[AWAITING_DOWNLOAD]"
        reg_rows.append([
            item["identifier"],
            item["primary_domain"],
            item["provenance"],
            item["relative_path"],
            status_str,
        ])

    print(render_ascii_table(
        reg_headers,
        reg_rows,
        alignments=["<", "^", "^", "<", "^"],
    ))
    print("=" * 80 + "\n")


def build_audit_inventory(
    audits: List[Dict[str, Any]],
    dir_reports: Dict[str, Dict[str, Any]],
    project_root: Path,
) -> Dict[str, Any]:
    """Assemble structured JSON dictionary for export."""
    total_records = sum(a.get("row_count", 0) for a in audits)
    total_bytes = sum(a.get("file_size_bytes", 0) for a in audits)

    # Domain summary counts
    domain_counts: Dict[str, int] = {d: 0 for d in CANONICAL_DOMAINS}
    for a in audits:
        dom = a.get("domain_classification", {}).get("domain", "UNKNOWN")
        domain_counts[dom] = domain_counts.get(dom, 0) + 1

    return {
        "audit_meta": {
            "generated_at": datetime.now().isoformat(),
            "execution_user": os.getenv("USERNAME", "System"),
            "project_root": str(project_root),
            "script": "scripts/audit_datasets.py",
            "framework": "ColdChain-AI Big Data & IoT Audit Suite",
        },
        "scan_summary": {
            "scanned_directories": dir_reports,
            "total_csv_datasets_found": len(audits),
            "total_records_audited": total_records,
            "total_size_bytes": total_bytes,
            "total_size_formatted": format_bytes(total_bytes),
            "domain_distribution": domain_counts,
        },
        "canonical_domains": CANONICAL_DOMAINS,
        "canonical_benchmark_catalog": CANONICAL_CATALOG,
        "datasets": audits,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Dataset Auditing & Inventory Tool for ColdChain-AI"
    )
    parser.add_argument(
        "--data-raw",
        "-r",
        type=str,
        default="data/raw",
        help="Path to primary raw data directory (default: data/raw)",
    )
    parser.add_argument(
        "--datasets-dir",
        "-d",
        type=str,
        default="Datasets",
        help="Path to external Datasets directory (default: Datasets)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="reports/dataset_audit_inventory.json",
        help="Path for exported JSON inventory (default: reports/dataset_audit_inventory.json)",
    )
    args = parser.parse_args()

    # Determine project root (handling backend/ subdirectory)
    project_root = Path(__file__).resolve().parents[1]
    if not (project_root / "data").exists() and (project_root.parent / "data").exists():
        project_root = project_root.parent


    # Resolve scan directories
    raw_dir = Path(args.data_raw)
    if not raw_dir.is_absolute():
        raw_dir = project_root / raw_dir

    datasets_dir = Path(args.datasets_dir)
    if not datasets_dir.is_absolute():
        datasets_dir = project_root / datasets_dir

    # Resolve output path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    # Banner
    print("=" * 80)
    print("COLDCHAIN-AI DATASET AUDITING & PROVENANCE INVENTORY SUITE")
    print(f"Timestamp:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project Root: {project_root}")
    print(f"Inventory:    {output_path}")
    print("=" * 80)
    print("\nScanning target directories recursively:")

    # 1. Discover CSV files (handling missing directories gracefully)
    candidate_dirs = [raw_dir, datasets_dir]
    csv_files, dir_reports = find_csv_files(candidate_dirs, project_root)

    print(f"\nTotal CSV dataset files discovered: {len(csv_files)}")
    for idx, cf in enumerate(csv_files, 1):
        rel = cf.relative_to(project_root) if cf.is_relative_to(project_root) else cf
        print(f"  [{idx}] {rel}")
    print()

    # 2. Audit each dataset
    audits: List[Dict[str, Any]] = []
    for cf in csv_files:
        audit_res = audit_single_csv(cf, project_root)
        audits.append(audit_res)
        print_dataset_audit(audit_res)

    # 3. Print high-level summary table
    print_summary_table(audits)

    # 4. Print domain classification table
    print_classification_table(audits, project_root)

    # 5. Export JSON inventory
    inventory = build_audit_inventory(audits, dir_reports, project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(to_json_serializable(inventory), f, indent=2)

    print("=" * 80)
    print("AUDIT EXECUTION COMPLETE")
    print(f"Datasets Audited:        {len(audits)}")
    print(f"Total Rows Scanned:      {inventory['scan_summary']['total_records_audited']:,}")
    print(f"Structured Inventory:    {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
