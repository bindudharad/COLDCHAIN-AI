"""QA Sections 5-8 — Preprocessing, MAD-TCN, Risk, NSGA-II.
Corrected to match actual API signatures and output field names.
Run from project root: .venv\Scripts\python.exe scripts\qa_sections5to8.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import torch

PASS = []
FAIL = []
SECTION = {}

def check(name, fn, section):
    try:
        fn()
        PASS.append(name)
        SECTION.setdefault(section, {'pass': [], 'fail': []})['pass'].append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append(name)
        SECTION.setdefault(section, {'pass': [], 'fail': []})['fail'].append(name)
        print(f"  FAIL  {name}: {e}")
        import traceback; traceback.print_exc()

CSV = os.path.join(os.getcwd(), 'data', 'raw', 'simulated_cold_chain.csv')

# Load raw data once
_raw = pd.read_csv(CSV)

# =============================================================================
# SECTION 5 -- PREPROCESSING
# =============================================================================
print("\n=== SECTION 5 -- PREPROCESSING TEST ===")
from core_preprocessing import prepare, sequences, FEATURES

_df_cc01 = None
_X = None
_y = None

def s5_features():
    print(f"         FEATURES ({len(FEATURES)}): {FEATURES}")
    assert len(FEATURES) == 12

def s5_prepare():
    global _df_cc01
    cc01_raw = _raw[_raw['sensor_id'] == 'CC-01'].copy()
    _df_cc01 = prepare(cc01_raw)
    print(f"         prepare(CC-01 slice): {_df_cc01.shape}")
    assert _df_cc01 is not None and len(_df_cc01) > 0
    for f in FEATURES:
        assert f in _df_cc01.columns, f"Feature '{f}' missing"

def s5_sequences():
    global _X, _y
    _X, _y = sequences(_df_cc01, window=60, horizon=15)
    print(f"         X shape: {_X.shape}, y shape: {_y.shape}")
    assert _X.ndim == 3
    assert _X.shape[1] == 60
    assert _X.shape[2] == 12
    assert _y.ndim == 2
    assert _y.shape[1] == 15

def s5_no_nan():
    arr = _X.astype(float)
    assert not np.isnan(arr).any(), "NaN in X"
    assert not np.isinf(arr).any(), "Inf in X"

def s5_sequence_count():
    n = len(_df_cc01)
    expected = n - 60 - 15
    diff = abs(_X.shape[0] - expected)
    print(f"         Sequences: {_X.shape[0]} (expected ~{expected})")
    assert diff <= 5

def s5_cc02():
    cc02_raw = _raw[_raw['sensor_id'] == 'CC-02'].copy()
    df2 = prepare(cc02_raw)
    X2, y2 = sequences(df2, window=60, horizon=15)
    assert X2.shape[1:] == (60, 12)
    assert y2.shape[1] == 15
    print(f"         CC-02 sequences: {X2.shape[0]}")

def s5_full_dataset_prepare():
    # prepare() with full multi-sensor dataset also works
    df_all = prepare(_raw.copy())
    assert len(df_all) == 12000
    print(f"         Full dataset prepare(): {df_all.shape}")

check("features_list", s5_features, 5)
check("prepare_cc01", s5_prepare, 5)
check("sequences_shape", s5_sequences, 5)
check("no_nan_in_X", s5_no_nan, 5)
check("sequence_count", s5_sequence_count, 5)
check("cc02_sequences", s5_cc02, 5)
check("full_dataset_prepare", s5_full_dataset_prepare, 5)

# =============================================================================
# SECTION 6 -- MAD-TCN
# =============================================================================
print("\n=== SECTION 6 -- MAD-TCN TEST ===")
from ml.mad_tcn import MADTCN
from ml.inference import forecast

CKPT = os.path.join(os.getcwd(), 'models', 'mad_tcn_best.pt')
_model = None

def s6_checkpoint():
    assert os.path.exists(CKPT)
    size_kb = os.path.getsize(CKPT) / 1024
    print(f"         Checkpoint: {CKPT} ({size_kb:.1f} KB)")

def s6_metrics_json():
    import json
    path = os.path.join(os.getcwd(), 'models', 'metrics.json')
    with open(path) as f:
        m = json.load(f)
    print(f"         metrics.json: MAE={m['mae']:.4f}, RMSE={m['rmse']:.4f}, dataset={m['dataset']}")
    assert m['mae'] > 0 and m['rmse'] > 0

def s6_model_load():
    global _model
    # MADTCN(features, hidden=32, horizon=15) -- positional arg
    _model = MADTCN(len(FEATURES))
    state = torch.load(CKPT, map_location='cpu', weights_only=True)
    _model.load_state_dict(state)
    _model.eval()
    params = sum(p.numel() for p in _model.parameters())
    print(f"         MADTCN loaded: {params:,} parameters, features={len(FEATURES)}, horizon=15")

def s6_inference_shape():
    x = torch.randn(1, 60, 12)
    with torch.no_grad():
        out = _model(x)
    print(f"         Input {tuple(x.shape)} -> Output {tuple(out.shape)}")
    assert out.shape == (1, 15)

def s6_no_nan():
    x = torch.randn(4, 60, 12)
    with torch.no_grad():
        out = _model(x)
    assert not torch.isnan(out).any()
    assert not torch.isinf(out).any()

def s6_forecast_api():
    """Test forecast() -- the actual production function.
    forecast(sequence) takes (60, 12) numpy array, returns list of 15 floats.
    """
    seq = _X[-1]  # shape (60, 12)
    preds = forecast(seq)
    print(f"         forecast() -> {len(preds)} steps")
    print(f"         First 5 predictions: {[round(p, 3) for p in preds[:5]]}")
    assert len(preds) == 15
    assert all(np.isfinite(p) for p in preds)

def s6_mae_rmse():
    """Evaluate on 20% held-out test split."""
    split = int(len(_X) * 0.8)
    X_test = torch.tensor(_X[split:].astype(float), dtype=torch.float32)
    y_test = _y[split:].astype(float)
    with torch.no_grad():
        preds = _model(X_test).numpy()
    mae = float(np.mean(np.abs(preds - y_test)))
    rmse = float(np.sqrt(np.mean((preds - y_test)**2)))
    print(f"         Test-split (20%) MAE:  {mae:.4f}")
    print(f"         Test-split (20%) RMSE: {rmse:.4f}")
    print(f"         metrics.json (training eval): MAE=1.2501, RMSE=1.4672")
    assert mae < 5.0, f"MAE too high: {mae:.4f}"
    assert rmse < 7.0, f"RMSE too high: {rmse:.4f}"

check("checkpoint_exists", s6_checkpoint, 6)
check("metrics_json", s6_metrics_json, 6)
check("model_load", s6_model_load, 6)
check("inference_shape", s6_inference_shape, 6)
check("no_nan_output", s6_no_nan, 6)
check("forecast_api", s6_forecast_api, 6)
check("mae_rmse_test_split", s6_mae_rmse, 6)

# =============================================================================
# SECTION 7 -- RISK ENGINE
# Actual output keys: risk_score, risk_level, risk_reason, predicted_breach_time
# =============================================================================
print("\n=== SECTION 7 -- RISK ENGINE TEST ===")
from core import risk

def s7_output_fields():
    """Verify actual risk() output keys match what frontend uses."""
    r = risk([4.0] * 15, 'Food')
    required = {'risk_score', 'risk_level', 'risk_reason', 'predicted_breach_time'}
    missing = required - set(r.keys())
    assert not missing, f"Missing keys: {missing}"
    print(f"         Risk output keys: {list(r.keys())}")

def s7_safe_forecast():
    preds = [3.5] * 15  # well within Food range (0-5)
    r = risk(preds, 'Food')
    print(f"         SAFE (Food, all 3.5): score={r['risk_score']:.3f}, level={r['risk_level']}")
    assert r['risk_level'] == 'LOW'
    assert r['risk_score'] < 0.4
    assert r['predicted_breach_time'] is None

def s7_warning_breach():
    preds = [4.5, 4.7, 4.9, 5.1, 5.2, 5.3, 5.2, 5.0, 4.9, 4.8, 4.7, 4.6, 4.5, 4.4, 4.3]
    r = risk(preds, 'Food')
    print(f"         BREACH (Food, slight): score={r['risk_score']:.3f}, breach_step={r['predicted_breach_time']}")
    assert r['risk_score'] > 0.0
    assert r['predicted_breach_time'] is not None  # step 4 (index 3)

def s7_critical_forecast():
    preds = [6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 10.0, 9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5]
    r = risk(preds, 'Food')
    print(f"         CRITICAL (Food, major): score={r['risk_score']:.3f}, level={r['risk_level']}")
    assert r['risk_level'] in ('HIGH', 'CRITICAL')
    assert r['risk_score'] > 0.5

def s7_lower_limit():
    preds = [-2.0] * 15  # below 0 C for Food
    r = risk(preds, 'Food')
    print(f"         LOWER BREACH (Food, -2 C): score={r['risk_score']:.3f}, level={r['risk_level']}")
    assert r['risk_score'] > 0.0
    assert r['predicted_breach_time'] == 1  # first step is a breach

def s7_empty_input():
    r = risk([], 'Food')
    print(f"         EMPTY input: score={r['risk_score']}, level={r['risk_level']}")
    assert r['risk_score'] == 0.0
    assert r['risk_level'] == 'LOW'

def s7_vaccine_profile():
    preds = [8.5] * 15  # above 8 C, outside Vaccine range (2-8)
    r = risk(preds, 'Vaccine')
    print(f"         VACCINE breach (8.5 C): score={r['risk_score']:.3f}, level={r['risk_level']}")
    assert r['risk_score'] > 0.0
    assert r['predicted_breach_time'] is not None

def s7_reason_string():
    r = risk([4.0] * 15, 'Food')
    assert isinstance(r['risk_reason'], str) and len(r['risk_reason']) > 10
    print(f"         risk_reason: {r['risk_reason'][:60]}...")

check("output_fields", s7_output_fields, 7)
check("safe_food", s7_safe_forecast, 7)
check("warning_breach", s7_warning_breach, 7)
check("critical_breach", s7_critical_forecast, 7)
check("lower_limit_breach", s7_lower_limit, 7)
check("empty_input", s7_empty_input, 7)
check("vaccine_profile", s7_vaccine_profile, 7)
check("reason_string", s7_reason_string, 7)

# =============================================================================
# SECTION 8 -- NSGA-II OPTIMIZER
# Actual signature: run_nsga2(current, ambient, future_risk, population, generations)
# Actual output row keys: cooling_intensity, compressor_duty_cycle,
#                         target_temperature_offset, safety_risk, estimated_energy_kwh
# =============================================================================
print("\n=== SECTION 8 -- NSGA-II TEST ===")
from optimization.nsga2_optimizer import run_nsga2

def s8_low_risk():
    pareto, rec = run_nsga2(3.5, 22.0, 0.1)
    print(f"         Low risk -- Pareto solutions: {len(pareto)}")
    print(f"         Recommendation: cooling={rec['cooling_intensity']:.3f}, duty={rec['compressor_duty_cycle']:.3f}, energy={rec['estimated_energy_kwh']:.4f}")
    assert len(pareto) >= 1
    assert 'cooling_intensity' in rec
    assert 'compressor_duty_cycle' in rec
    assert 'estimated_energy_kwh' in rec
    assert 'safety_risk' in rec

def s8_high_risk():
    pareto, rec = run_nsga2(8.5, 28.0, 0.9)
    print(f"         High risk -- Pareto solutions: {len(pareto)}")
    print(f"         Recommendation: cooling={rec['cooling_intensity']:.3f}, duty={rec['compressor_duty_cycle']:.3f}")
    assert len(pareto) >= 1

def s8_pareto_structure():
    pareto, rec = run_nsga2(5.0, 25.0, 0.5)
    for sol in pareto:
        assert 'cooling_intensity' in sol
        assert 'compressor_duty_cycle' in sol
        assert 'estimated_energy_kwh' in sol
        assert 'safety_risk' in sol
        assert 'target_temperature_offset' in sol
        assert 0 <= sol['cooling_intensity'] <= 1
        assert 0 <= sol['compressor_duty_cycle'] <= 1
        assert sol['estimated_energy_kwh'] >= 0
    print(f"         Pareto structure validated: {len(pareto)} solutions")

def s8_energy_range():
    pareto, rec = run_nsga2(4.0, 20.0, 0.3)
    for sol in pareto:
        e = sol['estimated_energy_kwh']
        assert 0 <= e <= 10, f"Energy {e} out of range"
    print(f"         Energy values in [0,10] kWh for all {len(pareto)} solutions")

def s8_analysis_service_integration():
    """Test the full pipeline via analysis_service (the actual production path)."""
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    from apps.monitoring.models import Sensor
    from analysis_service import decision_for_sensor
    sensor = Sensor.objects.get(sensor_id='CC-01')
    result = decision_for_sensor(sensor)
    print(f"         Pipeline result sensor: {result['sensor']}")
    print(f"         current_temperature: {result['current_temperature']:.2f}")
    print(f"         forecast steps: {len(result['forecast'])}")
    print(f"         risk_level: {result['risk']['risk_level']}")
    print(f"         pareto_solutions: {len(result['pareto_solutions'])}")
    rec = result['recommended_solution']
    print(f"         recommendation: cooling={rec['cooling_intensity']:.3f}, expected_temp={rec.get('expected_temperature','N/A')}")
    assert len(result['forecast']) == 15
    assert 'risk_score' in result['risk']
    assert len(result['pareto_solutions']) >= 1
    assert 'explanation' in rec  # added by analysis_service
    assert 'expected_temperature' in rec  # added by analysis_service

check("low_risk_run", s8_low_risk, 8)
check("high_risk_run", s8_high_risk, 8)
check("pareto_structure", s8_pareto_structure, 8)
check("energy_range", s8_energy_range, 8)
check("analysis_service_integration", s8_analysis_service_integration, 8)

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "="*60)
print("SECTIONS 5-8 SUMMARY")
print("="*60)
for s, r in sorted(SECTION.items()):
    p, f = len(r['pass']), len(r['fail'])
    status = "PASS" if f == 0 else "FAIL"
    print(f"  Section {s}: {p} PASS / {f} FAIL  [{status}]")
    if f:
        print(f"    FAILED: {r['fail']}")

total_pass = len(PASS)
total_fail = len(FAIL)
print(f"\nTotal: {total_pass} PASS / {total_fail} FAIL")

if total_fail:
    sys.exit(1)
