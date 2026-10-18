"""QA Section 5 — Preprocessing test."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        import traceback; traceback.print_exc()

from core_preprocessing import prepare, sequences, FEATURES

CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'data', 'raw', 'simulated_cold_chain.csv')

_df = None
_X = None
_y = None

def test_features_list():
    print(f"         FEATURES ({len(FEATURES)}): {FEATURES}")
    assert len(FEATURES) == 12, f"Expected 12 features, got {len(FEATURES)}"

def test_prepare():
    global _df
    _df = prepare(CSV, 'CC-01')
    print(f"         prepare() shape: {_df.shape}")
    assert _df is not None
    assert len(_df) > 0
    for f in FEATURES:
        assert f in _df.columns, f"Feature '{f}' missing from prepared frame"

def test_sequences():
    global _X, _y
    _X, _y = sequences(_df, window=60, horizon=15)
    print(f"         X shape: {_X.shape}, y shape: {_y.shape}")
    assert _X.ndim == 3
    assert _X.shape[1] == 60
    assert _X.shape[2] == 12
    assert _y.ndim == 2
    assert _y.shape[1] == 15

def test_no_nan_inf():
    assert not np.isnan(_X).any(), "NaN in X"
    assert not np.isnan(_y).any(), "NaN in y"
    assert not np.isinf(_X).any(), "Inf in X"
    assert not np.isinf(_y).any(), "Inf in y"

def test_sequence_count():
    # 4000 readings - 60 window - 15 horizon + 1 = ~3926 sequences
    expected = 4000 - 60 - 15 + 1
    diff = abs(_X.shape[0] - expected)
    print(f"         Sequences: {_X.shape[0]} (expected ~{expected})")
    assert diff <= 5, f"Sequence count {_X.shape[0]} far from expected {expected}"

def test_cc02():
    from core_preprocessing import prepare as _prepare, sequences as _sequences
    df2 = _prepare(CSV, 'CC-02')
    X2, y2 = _sequences(df2, window=60, horizon=15)
    assert X2.shape[1:] == (60, 12)
    assert y2.shape[1] == 15
    print(f"         CC-02 sequences: {X2.shape[0]}")

print("\n=== SECTION 5 — PREPROCESSING TEST ===")
check("features_list", test_features_list)
check("prepare", test_prepare)
check("sequences", test_sequences)
check("no_nan_inf", test_no_nan_inf)
check("sequence_count", test_sequence_count)
check("cc02", test_cc02)

print(f"\nSection 5 Result: {len(PASS)} PASS / {len(FAIL)} FAIL")
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)
