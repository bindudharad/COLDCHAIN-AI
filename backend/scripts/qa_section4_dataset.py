"""QA Section 4 — Dataset validation (corrected for actual CSV schema)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

PASS = []
FAIL = []

def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append(name)
        print(f"  FAIL  {name}: {e}")

CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'data', 'raw', 'simulated_cold_chain.csv')

df = None

def test_file_exists():
    assert os.path.exists(CSV), f"Not found: {CSV}"

def test_readable():
    global df
    df = pd.read_csv(CSV)
    print(f"         Shape: {df.shape}")

# Actual columns from inspection:
# timestamp, sensor_id, temperature, humidity, ambient_temperature,
# power_kw, compressor_state, door_open, product_type, location
ACTUAL_COLS = ['timestamp', 'sensor_id', 'temperature', 'humidity',
               'ambient_temperature', 'power_kw', 'compressor_state',
               'door_open', 'product_type', 'location']

def test_columns():
    print(f"         Actual columns: {list(df.columns)}")
    missing = [c for c in ACTUAL_COLS if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"

def test_row_count():
    assert len(df) == 12000, f"Expected 12000, got {len(df)}"
    print(f"         Rows: {len(df)}")

def test_sensor_ids():
    ids = set(df['sensor_id'].unique())
    assert ids == {'CC-01', 'CC-02', 'CC-03'}, f"Sensor IDs: {ids}"
    counts = df['sensor_id'].value_counts().to_dict()
    print(f"         Per-sensor counts: {counts}")

def test_no_nulls():
    nulls = df.isnull().sum()
    total = nulls.sum()
    bad = nulls[nulls > 0]
    if len(bad):
        print(f"         Nulls found:\n{bad}")
    assert total == 0, f"Null values present"

def test_temperature_range():
    tmin = df['temperature'].min()
    tmax = df['temperature'].max()
    print(f"         Temperature range: {tmin:.2f} to {tmax:.2f} degC")
    assert -30 <= tmin, f"Temperature too low: {tmin}"
    assert tmax <= 30, f"Temperature too high: {tmax}"

def test_timestamp_parse():
    ts = pd.to_datetime(df['timestamp'])
    assert ts.notna().all(), "Some timestamps could not be parsed"
    print(f"         Timestamp range: {ts.min()} to {ts.max()}")

def test_temporal_sort():
    for sid in ['CC-01', 'CC-02', 'CC-03']:
        sub = df[df['sensor_id'] == sid].copy()
        sub['ts'] = pd.to_datetime(sub['timestamp'])
        diffs = sub['ts'].diff().dropna()
        assert (diffs >= pd.Timedelta(0)).all(), f"{sid} timestamps not sorted"
    print(f"         All sensors: timestamps monotonically increasing")

def test_product_types():
    pts = set(df['product_type'].unique())
    print(f"         Product types present: {pts}")
    assert len(pts) >= 1

def test_ambient_range():
    amin = df['ambient_temperature'].min()
    amax = df['ambient_temperature'].max()
    print(f"         Ambient temperature range: {amin:.2f} to {amax:.2f}")
    assert -10 <= amin and amax <= 50

def test_compressor_binary():
    vals = set(df['compressor_state'].unique())
    print(f"         Compressor state values: {vals}")
    # should be 0/1 or True/False
    assert vals.issubset({0, 1, True, False})

print("\n=== SECTION 4 — DATASET TEST ===")
check("file_exists", test_file_exists)
check("readable", test_readable)
check("columns", test_columns)
check("row_count", test_row_count)
check("sensor_ids", test_sensor_ids)
check("no_nulls", test_no_nulls)
check("temperature_range", test_temperature_range)
check("timestamp_parse", test_timestamp_parse)
check("temporal_sort", test_temporal_sort)
check("product_types", test_product_types)
check("ambient_range", test_ambient_range)
check("compressor_binary", test_compressor_binary)

print(f"\nSection 4 Result: {len(PASS)} PASS / {len(FAIL)} FAIL")
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)

print("\n[DISCLAIMER] Dataset is DEMONSTRATION / SIMULATION.")
print("             12,000 rows, 3 sensors (CC-01/CC-02/CC-03).")
print("             NOT real industrial sensor data.")
