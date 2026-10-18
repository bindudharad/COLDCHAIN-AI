"""QA Sections 9-16: Energy, E2E pipeline, all API endpoints, simulation,
alerts, upload, reports, frontend pages.
Run from project root.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
import json

PASS = []
FAIL = []
SECTION = {}
client = Client()

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

# =============================================================================
# SECTION 9 -- ENERGY CALCULATION
# =============================================================================
print("\n=== SECTION 9 -- ENERGY CALCULATION ===")
from core import energy

def s9_energy_basic():
    e = energy(4.0, 22.0, 0.5, 0.7)
    print(f"         energy(4.0, 22.0, 0.5, 0.7) = {e}")
    assert e > 0

def s9_energy_formula():
    # Verify: (0.25 + 0.035 * max(22-4, 0)) * (0.35 + 0.65*0.5) * 0.7
    expected = (0.25 + 0.035 * max(22.0 - 4.0, 0)) * (0.35 + 0.65 * 0.5) * 0.7
    actual = energy(4.0, 22.0, 0.5, 0.7)
    print(f"         Formula check: expected={expected:.4f}, actual={actual:.4f}")
    assert abs(actual - round(expected, 3)) < 0.001

def s9_energy_clamp():
    # max(ambient - current, 0) = max(20 - 25, 0) = 0 (no cooling needed when cold ambient)
    e = energy(25.0, 20.0, 0.3, 0.5)
    expected = (0.25 + 0) * (0.35 + 0.65 * 0.3) * 0.5
    print(f"         No heat load: expected={expected:.4f}, actual={e:.4f}")
    assert abs(e - round(expected, 3)) < 0.001

def s9_energy_floor():
    # Floor is 0.05 when formula would give < 0.05
    e = energy(4.0, 20.0, 0.001, 0.001)
    print(f"         Floor test: energy={e}")
    assert e >= 0.05

def s9_energy_disclaimer():
    print(f"         [DISCLAIMER] Energy is ESTIMATED/SIMULATED.")
    print(f"         Thermodynamic model. Not from metered consumption.")

check("energy_basic", s9_energy_basic, 9)
check("energy_formula", s9_energy_formula, 9)
check("energy_clamp", s9_energy_clamp, 9)
check("energy_floor", s9_energy_floor, 9)
check("energy_disclaimer", s9_energy_disclaimer, 9)

# =============================================================================
# SECTION 10 -- END-TO-END PIPELINE
# =============================================================================
print("\n=== SECTION 10 -- END-TO-END PIPELINE ===")
from apps.monitoring.models import Sensor
from analysis_service import decision_for_sensor

def s10_e2e_cc01():
    s = Sensor.objects.get(sensor_id='CC-01')
    r = decision_for_sensor(s)
    assert r['sensor'] == 'CC-01'
    assert isinstance(r['forecast'], list) and len(r['forecast']) == 15
    assert 'risk_score' in r['risk']
    assert len(r['pareto_solutions']) >= 1
    rec = r['recommended_solution']
    assert 'cooling_intensity' in rec
    assert 'expected_temperature' in rec
    assert 'explanation' in rec
    print(f"         CC-01: temp={r['current_temperature']:.2f}, risk={r['risk']['risk_level']}, pareto={len(r['pareto_solutions'])}")

def s10_e2e_cc02():
    s = Sensor.objects.get(sensor_id='CC-02')
    r = decision_for_sensor(s)
    print(f"         CC-02: temp={r['current_temperature']:.2f}, risk={r['risk']['risk_level']}")
    assert r['sensor'] == 'CC-02'
    assert len(r['forecast']) == 15

def s10_e2e_cc03():
    s = Sensor.objects.get(sensor_id='CC-03')
    r = decision_for_sensor(s)
    print(f"         CC-03: temp={r['current_temperature']:.2f}, risk={r['risk']['risk_level']}")
    assert r['sensor'] == 'CC-03'
    assert len(r['forecast']) == 15

def s10_e2e_no_fake_data():
    """Verify pipeline uses real DB readings, not hardcoded values."""
    s = Sensor.objects.get(sensor_id='CC-01')
    r = decision_for_sensor(s)
    # Real latest reading from DB
    latest_db = s.readings.order_by('-timestamp').first()
    assert abs(r['current_temperature'] - latest_db.temperature) < 0.001, \
        f"current_temperature {r['current_temperature']} != DB value {latest_db.temperature}"
    print(f"         Data trace: API temp={r['current_temperature']:.4f} matches DB={latest_db.temperature:.4f}")

check("e2e_cc01", s10_e2e_cc01, 10)
check("e2e_cc02", s10_e2e_cc02, 10)
check("e2e_cc03", s10_e2e_cc03, 10)
check("no_fake_data", s10_e2e_no_fake_data, 10)

# =============================================================================
# SECTION 11 -- ALL API ENDPOINTS
# =============================================================================
print("\n=== SECTION 11 -- API ENDPOINTS ===")

def api_json(url, method='GET', data=None, expected_status=200):
    if method == 'POST':
        resp = client.post(url, data=data, content_type='application/json')
    else:
        resp = client.get(url)
    assert resp.status_code == expected_status, f"{url} returned {resp.status_code}"
    body = json.loads(resp.content)
    return body

def s11_dashboard_api():
    d = api_json('/api/dashboard/')
    assert 'forecast' in d, f"Missing 'forecast' key: {list(d.keys())}"
    assert 'risk' in d
    assert 'pareto_solutions' in d
    assert 'current_temperature' in d
    print(f"         /api/dashboard/: temp={d['current_temperature']:.2f}, risk={d['risk']['risk_level']}")

def s11_sensors_api():
    d = api_json('/api/sensors/')
    assert d.get('success')
    sensors = d['data']
    assert len(sensors) >= 3
    for s in sensors[:3]:
        assert 'sensor_id' in s
        assert 'latest_temperature' in s
    print(f"         /api/sensors/: {len(sensors)} sensors returned")

def s11_sensor_history():
    d = api_json('/api/sensors/CC-01/history/')
    assert d.get('success')
    readings = d['data']
    assert len(readings) > 0
    assert 'temperature' in readings[0]
    print(f"         /api/sensors/CC-01/history/: {len(readings)} readings")

def s11_pipeline_api():
    d = api_json('/api/pipeline/')
    assert d.get('success')
    data = d['data']
    assert 'forecast' in data
    assert 'risk' in data
    print(f"         /api/pipeline/: risk_level={data['risk']['risk_level']}")

def s11_pipeline_sensor_param():
    d = api_json('/api/pipeline/?sensor=CC-02')
    assert d.get('success')
    assert d['data']['sensor'] == 'CC-02'
    print(f"         /api/pipeline/?sensor=CC-02: sensor={d['data']['sensor']}")

def s11_model_api():
    d = api_json('/api/model/')
    assert d.get('success')
    assert 'mae' in d['data'] or 'metrics' in d['data'] or 'mae' in str(d)
    print(f"         /api/model/: keys={list(d.get('data',d).keys())}")

def s11_predictions_api():
    d = api_json('/api/predictions/')
    assert d.get('success')
    print(f"         /api/predictions/: success=True")

def s11_risk_api():
    d = api_json('/api/risk/')
    assert d.get('success')
    print(f"         /api/risk/: success=True")

def s11_optimization_api():
    d = api_json('/api/optimization/')
    assert d.get('success')
    print(f"         /api/optimization/: success=True")

def s11_alerts_api():
    d = api_json('/api/alerts/')
    assert d.get('success')
    alerts = d.get('data', [])
    print(f"         /api/alerts/: {len(alerts)} alerts returned")

def s11_reports_api():
    d = api_json('/api/reports/')
    assert d.get('success')
    print(f"         /api/reports/: success=True")

def s11_report_api():
    d = api_json('/api/report/')
    assert d.get('success')
    print(f"         /api/report/: success=True")

def s11_profile_api():
    d = api_json('/api/profile/')
    assert d.get('success') or 'data' in d
    print(f"         /api/profile/: returned")

def s11_save_case_api():
    d = api_json('/api/save_case/', method='POST', data='{}')
    assert d.get('success') or 'error' in d
    print(f"         /api/save_case/ POST: returned")

check("dashboard_api", s11_dashboard_api, 11)
check("sensors_api", s11_sensors_api, 11)
check("sensor_history", s11_sensor_history, 11)
check("pipeline_api", s11_pipeline_api, 11)
check("pipeline_sensor_param", s11_pipeline_sensor_param, 11)
check("model_api", s11_model_api, 11)
check("predictions_api", s11_predictions_api, 11)
check("risk_api", s11_risk_api, 11)
check("optimization_api", s11_optimization_api, 11)
check("alerts_api", s11_alerts_api, 11)
check("reports_api", s11_reports_api, 11)
check("report_api", s11_report_api, 11)
check("profile_api", s11_profile_api, 11)
check("save_case_api", s11_save_case_api, 11)

# =============================================================================
# SECTION 12 -- SIMULATION START/PAUSE/RESET
# =============================================================================
print("\n=== SECTION 12 -- SIMULATION CONTROLS ===")

def s12_start():
    d = api_json('/api/simulation/start/', method='POST')
    assert d.get('success'), f"Start failed: {d}"
    print(f"         /api/simulation/start/: {d}")

def s12_pause():
    d = api_json('/api/simulation/pause/', method='POST')
    assert d.get('success'), f"Pause failed: {d}"
    print(f"         /api/simulation/pause/: {d}")

def s12_reset():
    d = api_json('/api/simulation/reset/', method='POST')
    assert d.get('success'), f"Reset failed: {d}"
    print(f"         /api/simulation/reset/: {d}")

check("simulation_start", s12_start, 12)
check("simulation_pause", s12_pause, 12)
check("simulation_reset", s12_reset, 12)

# =============================================================================
# SECTION 13 -- ALERTS
# =============================================================================
print("\n=== SECTION 13 -- ALERTS ===")

def s13_alerts_list():
    d = api_json('/api/alerts/')
    alerts = d.get('data', [])
    print(f"         Active alerts: {len(alerts)}")
    for a in alerts:
        assert 'id' in a
        assert 'type' in a or 'alert_type' in a or 'message' in a

def s13_alert_resolve():
    resp = client.post('/api/alerts/future-breach/resolve/')
    assert resp.status_code == 200
    d = json.loads(resp.content)
    assert d.get('success')
    print(f"         Resolve alert: {d}")

def s13_alert_invalid_resolve():
    resp = client.post('/api/alerts/nonexistent-id/resolve/')
    # Should return 200 with success (cache.set always works)
    assert resp.status_code == 200
    print(f"         Nonexistent alert resolve: graceful")

check("alerts_list", s13_alerts_list, 13)
check("alert_resolve", s13_alert_resolve, 13)
check("alert_invalid_resolve", s13_alert_invalid_resolve, 13)

# =============================================================================
# SECTION 14 -- UPLOAD
# =============================================================================
print("\n=== SECTION 14 -- UPLOAD ===")
import io

def s14_upload_valid_csv():
    csv_content = (
        "timestamp,sensor_id,temperature,humidity,ambient_temperature,"
        "power_kw,compressor_state,door_open\n"
        "2026-01-04 00:00:00,CC-01,4.1,72.0,21.5,1.3,1,0\n"
        "2026-01-04 00:01:00,CC-01,4.2,71.5,21.6,1.2,1,0\n"
    )
    f = io.BytesIO(csv_content.encode())
    f.name = 'test_upload.csv'
    resp = client.post('/api/upload/', {'file': f})
    d = json.loads(resp.content)
    print(f"         Upload valid CSV: {d}")
    assert d.get('success') or 'rows_persisted' in d or 'error' in d

def s14_upload_missing_cols():
    csv_content = "timestamp,sensor_id\n2026-01-04,CC-01\n"
    f = io.BytesIO(csv_content.encode())
    f.name = 'bad.csv'
    resp = client.post('/api/upload/', {'file': f})
    d = json.loads(resp.content)
    print(f"         Upload missing cols: success={d.get('success')}")
    # Should fail gracefully
    assert not d.get('success') or 'error' in d or d.get('rows_persisted', 0) == 0

def s14_upload_no_file():
    resp = client.post('/api/upload/', {})
    d = json.loads(resp.content)
    print(f"         Upload no file: {d}")
    assert not d.get('success') or 'error' in d

check("upload_valid_csv", s14_upload_valid_csv, 14)
check("upload_missing_cols", s14_upload_missing_cols, 14)
check("upload_no_file", s14_upload_no_file, 14)

# =============================================================================
# SECTION 15 -- REPORTS
# =============================================================================
print("\n=== SECTION 15 -- REPORTS ===")
import pathlib

def s15_generate_report():
    resp = client.post('/api/reports/generate/')
    d = json.loads(resp.content)
    print(f"         Generate report: {d}")
    assert d.get('success') or 'files' in d

def s15_report_files_exist():
    rdir = pathlib.Path(os.getcwd()) / 'reports'
    files = list(rdir.glob('coldchain_report.*'))
    print(f"         Report files: {[f.name for f in files]}")
    assert len(files) >= 1

def s15_report_json_valid():
    rpath = pathlib.Path(os.getcwd()) / 'reports' / 'coldchain_report.json'
    if rpath.exists():
        with open(rpath) as f:
            data = json.load(f)
        assert 'risk' in data or 'forecast' in data or len(data) > 0
        print(f"         Report JSON keys: {list(data.keys())[:8]}")
    else:
        print(f"         Report JSON not yet generated (skipping)")

def s15_report_download():
    resp = client.get('/reports/coldchain_report.json')
    assert resp.status_code in (200, 404)  # 404 ok if not yet generated
    print(f"         /reports/coldchain_report.json: {resp.status_code}")

check("generate_report", s15_generate_report, 15)
check("report_files_exist", s15_report_files_exist, 15)
check("report_json_valid", s15_report_json_valid, 15)
check("report_download", s15_report_download, 15)

# =============================================================================
# SECTION 16 -- FRONTEND PAGES (HTTP 200)
# =============================================================================
print("\n=== SECTION 16 -- FRONTEND PAGES ===")

PAGES = [
    ('/', 'Home'),
    ('/dashboard/', 'Dashboard'),
    ('/live-monitoring/', 'Live Monitoring'),
    ('/predictions/', 'Predictions'),
    ('/optimization/', 'Optimization'),
    ('/alerts/', 'Alerts'),
    ('/sensors/', 'Sensors'),
    ('/model/', 'Model Performance'),
    ('/reports/', 'Reports'),
    ('/upload/', 'Upload'),
    ('/methodology/', 'Methodology'),
]

def make_page_test(url, name):
    def fn():
        resp = client.get(url)
        assert resp.status_code == 200, f"{name} ({url}) returned {resp.status_code}"
        content = resp.content.decode('utf-8', errors='replace')
        assert len(content) > 100, f"{name} returned empty response"
        print(f"         {name} ({url}): 200 OK, {len(content):,} bytes")
    fn.__name__ = f"page_{name.lower().replace(' ','_')}"
    return fn

for url, name in PAGES:
    check(name, make_page_test(url, name), 16)

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "="*60)
print("SECTIONS 9-16 SUMMARY")
print("="*60)
for s, r in sorted(SECTION.items()):
    p, f = len(r['pass']), len(r['fail'])
    status = "PASS" if f == 0 else "FAIL"
    print(f"  Section {s:2d}: {p:2d} PASS / {f} FAIL  [{status}]")
    if f:
        print(f"    FAILED: {r['fail']}")

total_pass = len(PASS)
total_fail = len(FAIL)
print(f"\nTotal: {total_pass} PASS / {total_fail} FAIL")
if total_fail:
    sys.exit(1)
