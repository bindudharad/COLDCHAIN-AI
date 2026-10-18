import os, sys, json
from pathlib import Path
from datetime import timedelta
import numpy as np
import torch

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
for p in [str(BACKEND_DIR), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()


from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from apps.monitoring.models import Sensor, SensorReading
from ml.mad_tcn import MADTCN
from ml.inference import forecast
from core import risk, predict_future, energy
from optimization.nsga2_optimizer import run_nsga2
from analysis_service import decision_for_sensor
from core_preprocessing import prepare, sequences, FEATURES


class ApiWorkflowTests(TestCase):
    def setUp(self):
        self.sensor = Sensor.objects.create(sensor_id='TEST-01', product_type='Food')
        now = timezone.now()
        SensorReading.objects.bulk_create([
            SensorReading(
                sensor=self.sensor,
                timestamp=now + timedelta(minutes=i),
                temperature=3.5 + 0.05 * np.sin(i),
                humidity=70.0,
                ambient_temperature=20.0,
                power_kw=0.4,
                compressor_state=True,
                door_open=False
            ) for i in range(70)
        ])

    # 1. Django configuration
    def test_01_django_configuration(self):
        self.assertTrue(settings.SECRET_KEY)
        self.assertIn('apps.monitoring', settings.INSTALLED_APPS)
        self.assertEqual(settings.WINDOW_SIZE, 60)
        self.assertEqual(settings.FORECAST_HORIZON, 15)

    # 2. Dashboard API
    def test_02_dashboard_api(self):
        res = self.client.get('/api/dashboard/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('current_temperature', data)
        self.assertIn('forecast', data)
        self.assertEqual(len(data['forecast']), 15)
        self.assertIn('risk', data)
        self.assertIn('recommended_solution', data)
        self.assertIn('pareto_solutions', data)

    # 3. Sensors API
    def test_03_sensors_api(self):
        res = self.client.get('/api/sensors/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('results', data)
        self.assertTrue(len(data['results']) >= 1)
        sensor_ids = [s['sensor_id'] for s in data['results']]
        self.assertIn('TEST-01', sensor_ids)

    # 4. Pipeline API
    def test_04_pipeline_api(self):
        res = self.client.get('/api/pipeline/')
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertTrue(payload['success'])
        d = payload['data']
        self.assertIn('reading', d)
        self.assertIn('temperature', d['reading'])
        self.assertEqual(len(d['forecast']), 15)
        self.assertIn('risk', d)
        self.assertIn('recommended_solution', d)

    # 5. Model API
    def test_05_model_api(self):
        res = self.client.get('/api/model/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        model_info = d['data']
        self.assertEqual(model_info['model'], 'MAD-TCN')
        self.assertEqual(model_info['input'], '60 x 12')
        self.assertEqual(model_info['output_steps'], 15)
        self.assertIn('mae', model_info['metrics'])
        self.assertIn('rmse', model_info['metrics'])

    # 6. Predictions API
    def test_06_predictions_api(self):
        res = self.client.get('/api/predictions/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertIsInstance(d['data'], list)
        self.assertEqual(len(d['data']), 15)
        for val in d['data']:
            self.assertIsInstance(val, (int, float))

    # 7. Risk API
    def test_07_risk_api(self):
        res = self.client.get('/api/risk/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        r = d['data']
        self.assertIn('risk_score', r)
        self.assertIn('risk_level', r)
        self.assertIn(r['risk_level'], ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])

    # 8. Optimization API
    def test_08_optimization_api(self):
        res = self.client.get('/api/optimization/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        rec = d['data']
        self.assertIn('cooling_intensity', rec)
        self.assertIn('compressor_duty_cycle', rec)
        self.assertIn('estimated_energy_kwh', rec)
        self.assertIn('safety_risk', rec)
        self.assertTrue(rec['estimated_energy_kwh'] > 0)

    # 9. Alerts API
    def test_09_alerts_api(self):
        res = self.client.get('/api/alerts/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertIsInstance(d['data'], list)

    # 10. Alert resolve
    def test_10_alert_resolve(self):
        res = self.client.post('/api/alerts/future-breach/resolve/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertEqual(d['data']['id'], 'future-breach')
        self.assertTrue(d['data']['resolved'])

    # 11. Simulation start
    def test_11_simulation_start(self):
        res = self.client.post('/api/simulation/start/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertEqual(d['data']['simulation_state'], 'running')

    # 12. Simulation pause
    def test_12_simulation_pause(self):
        res = self.client.post('/api/simulation/pause/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertEqual(d['data']['simulation_state'], 'paused')

    # 13. Simulation reset
    def test_13_simulation_reset(self):
        res = self.client.post('/api/simulation/reset/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertEqual(d['data']['simulation_cursor'], 0)

    # 14. Upload validation (reject invalid columns)
    def test_14_upload_validation(self):
        bad_file = SimpleUploadedFile('bad.csv', b'timestamp,sensor_id\n2026-01-01T00:00:00+00:00,X\n', content_type='text/csv')
        res = self.client.post('/api/upload/', {'file': bad_file})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()['success'])
        self.assertIn('Required columns', res.json()['errors'][0])

    # 15. Upload persistence (persist valid rows)
    def test_15_upload_persistence(self):
        valid_file = SimpleUploadedFile(
            'valid.csv',
            b'timestamp,sensor_id,temperature,humidity,ambient_temperature,power_kw\n2026-02-02T00:00:00+00:00,NEW-01,4.1,65.0,20.0,0.4\n',
            content_type='text/csv'
        )
        res = self.client.post('/api/upload/', {'file': valid_file})
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertEqual(d['rows_persisted'], 1)
        self.assertTrue(SensorReading.objects.filter(sensor__sensor_id='NEW-01').exists())

    # 16. Report generation (JSON, Markdown, and CSV)
    def test_16_report_generation(self):
        res = self.client.post('/api/reports/generate/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertIn('coldchain_report.json', d['files'])
        self.assertIn('coldchain_report.md', d['files'])
        self.assertIn('coldchain_report.csv', d['files'])

        # Download JSON
        r_json = self.client.get('/reports/coldchain_report.json/')
        self.assertEqual(r_json.status_code, 200)
        content_json = b''.join(r_json.streaming_content)
        self.assertIn(b'DEMONSTRATION / SIMULATION DATA', content_json)

        # Download Markdown
        r_md = self.client.get('/reports/coldchain_report.md/')
        self.assertEqual(r_md.status_code, 200)

        # Download CSV
        r_csv = self.client.get('/reports/coldchain_report.csv/')
        self.assertEqual(r_csv.status_code, 200)
        content_csv = b''.join(r_csv.streaming_content)
        self.assertIn(b'forecast_temperature_c', content_csv)

    # 17. MAD-TCN inference (tensor shape 1x60x12 -> 15, no NaN, no Inf)
    def test_17_mad_tcn_inference(self):
        ckpt_path = Path('models/mad_tcn_best.pt') if Path('models/mad_tcn_best.pt').exists() else (REPO_ROOT / 'models/mad_tcn_best.pt')
        self.assertTrue(ckpt_path.exists(), "Model checkpoint must exist")


        seq = np.random.randn(60, 12).astype(np.float32)
        out = forecast(seq)
        self.assertEqual(len(out), 15)
        arr = np.array(out)
        self.assertFalse(np.isnan(arr).any(), "Forecast must not contain NaN")
        self.assertFalse(np.isinf(arr).any(), "Forecast must not contain Inf")

    # 18. Future-risk calculation
    def test_18_future_risk_calculation(self):
        # Normal safe temperatures
        safe_forecast = [3.5] * 15
        safe_risk = risk(safe_forecast, 'Food')
        self.assertIn('risk_score', safe_risk)
        self.assertEqual(safe_risk['risk_level'], 'LOW')
        self.assertIsNone(safe_risk['predicted_breach_time'])

        # Critical breach temperatures (>5.0 C for Food)
        breach_forecast = [3.5, 4.0, 5.5, 6.2, 7.0] + [7.5] * 10
        breach_risk = risk(breach_forecast, 'Food')
        self.assertGreater(breach_risk['risk_score'], 0)
        self.assertEqual(breach_risk['predicted_breach_time'], 3)

    # 19. NSGA-II execution (objectives finite, decision variables within bounds)
    def test_19_nsga2_execution(self):
        pareto, rec = run_nsga2(current=4.0, ambient=22.0, future_risk=15.0, population=24, generations=10)
        self.assertTrue(len(pareto) >= 1)
        for sol in pareto:
            self.assertGreaterEqual(sol['cooling_intensity'], 0.1)
            self.assertLessEqual(sol['cooling_intensity'], 1.0)
            self.assertGreaterEqual(sol['compressor_duty_cycle'], 0.2)
            self.assertLessEqual(sol['compressor_duty_cycle'], 1.0)
            self.assertGreaterEqual(sol['estimated_energy_kwh'], 0)
            self.assertGreaterEqual(sol['safety_risk'], 0)
            self.assertFalse(np.isnan(sol['estimated_energy_kwh']))
            self.assertFalse(np.isnan(sol['safety_risk']))

    # 20. Recommendation generation
    def test_20_recommendation_generation(self):
        pareto, rec = run_nsga2(current=3.8, ambient=20.0, future_risk=5.0, population=24, generations=10)
        self.assertIn('cooling_intensity', rec)
        self.assertIn('compressor_duty_cycle', rec)
        self.assertIn('estimated_energy_kwh', rec)
        self.assertIn('safety_risk', rec)
        self.assertTrue(0.1 <= rec['cooling_intensity'] <= 1.0)
        self.assertTrue(0.2 <= rec['compressor_duty_cycle'] <= 1.0)
        self.assertTrue(rec['estimated_energy_kwh'] > 0)

    # 21. End-to-end pipeline
    def test_21_end_to_end_pipeline(self):
        res = decision_for_sensor(self.sensor)
        self.assertEqual(res['sensor'], 'TEST-01')
        self.assertIn('current_temperature', res)
        self.assertEqual(len(res['forecast']), 15)
        self.assertIn('risk', res)
        self.assertIn('pareto_solutions', res)
        self.assertIn('recommended_solution', res)
        self.assertIn('explanation', res['recommended_solution'])

    # 22. Sensor history endpoint
    def test_22_sensor_history_endpoint(self):
        res = self.client.get(f'/api/sensors/{self.sensor.sensor_id}/history/?limit=20')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertEqual(d['sensor'], 'TEST-01')
        self.assertEqual(len(d['data']), 20)
        self.assertIn('temperature', d['data'][0])
        self.assertIn('timestamp', d['data'][0])

    # 23. Query parameter sensor selection across endpoints
    def test_23_query_param_sensor_selection(self):
        sensor2 = Sensor.objects.create(sensor_id='TEST-02', product_type='Vaccine')
        now = timezone.now()
        SensorReading.objects.bulk_create([
            SensorReading(
                sensor=sensor2,
                timestamp=now + timedelta(minutes=i),
                temperature=4.0,
                humidity=60.0,
                ambient_temperature=21.0,
                power_kw=0.5,
                compressor_state=True,
                door_open=False
            ) for i in range(65)
        ])
        res = self.client.get('/api/pipeline/?sensor=TEST-02')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d['data']['sensor'], 'TEST-02')

    # 24. Enhanced sensors API returns aggregates and latest reading
    def test_24_sensors_api_aggregates(self):
        res = self.client.get('/api/sensors/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        test_sensor = next(s for s in d['results'] if s['sensor_id'] == 'TEST-01')
        self.assertIn('reading_count', test_sensor)
        self.assertIn('latest_temperature', test_sensor)
        self.assertIn('temp_min', test_sensor)
        self.assertIn('temp_max', test_sensor)
        self.assertIn('temp_avg', test_sensor)
        self.assertEqual(test_sensor['reading_count'], 70)

    # 25. API report endpoint (GET & POST)
    def test_25_api_report(self):
        res = self.client.get('/api/report/?sensor=TEST-01')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertEqual(d['data']['sensor'], 'TEST-01')

    # 26. API file_content endpoint
    def test_26_api_file_content(self):
        # Generate report first
        self.client.post('/api/reports/generate/')
        res = self.client.get('/api/file_content/?name=coldchain_report.json')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertIn('content', d)
        self.assertTrue(d['size_bytes'] > 0)

    # 27. API save_case endpoint
    def test_27_api_save_case(self):
        res = self.client.get('/api/save_case/?sensor=TEST-01')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertIn('case_id', d)
        self.assertEqual(d['sensor'], 'TEST-01')

    # 28. API profile endpoint
    def test_28_api_profile(self):
        res = self.client.get('/api/profile/?profile=Vaccine')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d['success'])
        self.assertEqual(d['active_profile'], 'Vaccine')
        self.assertEqual(d['limits']['min_c'], 2.0)
        self.assertEqual(d['limits']['max_c'], 8.0)

    # Page route verification (all 11 pages return HTTP 200)
    def test_all_page_routes_return_200(self):
        routes = [
            '/',
            '/dashboard/',
            '/live-monitoring/',
            '/predictions/',
            '/optimization/',
            '/alerts/',
            '/model/',
            '/sensors/',
            '/reports/',
            '/upload/',
            '/methodology/',
            '/datasets/',
        ]
        for url in routes:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Route {url} failed with status {response.status_code}")

    # 29. IoT Telemetry Ingestion API (Single Reading)
    def test_29_iot_telemetry_single(self):
        # Use a device registered in REGISTERED_IOT_HARDWARE_DEVICES so
        # per-device auth grants REAL_SENSOR provenance.
        payload = {
            'sensor_id': 'HW-NODE-01',
            'timestamp': timezone.now().isoformat(),
            'temperature': 3.72,
            'humidity': 65.0,
            'ambient_temperature': 21.5,
            'data_source': 'REAL_SENSOR'
        }
        from django.conf import settings
        hw_key = getattr(settings, 'IOT_HARDWARE_API_KEY', 'coldchain-verified-hardware-secret-key-2026')
        res = self.client.post('/api/iot/telemetry/', data=json.dumps(payload),
                               content_type='application/json',
                               HTTP_X_HARDWARE_KEY=hw_key)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['records_persisted'], 1)
        self.assertEqual(data['provenance'], 'REAL_SENSOR')

    # 30. IoT Telemetry Ingestion (Duplicate & Fahrenheit Unit Conversion)
    def test_30_iot_telemetry_unit_and_duplicate(self):
        ts = timezone.now().isoformat()
        payload = {
            'sensor_id': 'IOT-TEST-02',
            'timestamp': ts,
            'temperature': 39.2,  # 39.2 °F = 4.0 °C
            'temperature_unit': 'F',
            'data_source': 'REAL_SENSOR'
        }
        res1 = self.client.post('/api/iot/telemetry/', data=json.dumps(payload),
                                content_type='application/json')
        self.assertEqual(res1.status_code, 201)
        reading = SensorReading.objects.filter(sensor__sensor_id='IOT-TEST-02').first()
        self.assertAlmostEqual(reading.temperature, 4.0, places=1)

        # Duplicate should be ignored
        res2 = self.client.post('/api/iot/telemetry/', data=json.dumps(payload),
                                content_type='application/json')
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()['duplicates_ignored'], 1)

    # 31. IoT Telemetry Rejection of Corrupted Spikes
    def test_31_iot_telemetry_range_rejection(self):
        payload = {
            'sensor_id': 'IOT-TEST-03',
            'timestamp': timezone.now().isoformat(),
            'temperature': -95.0,  # Below -60 °C physical boundary
        }
        res = self.client.post('/api/iot/telemetry/', data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()['success'])

    # 32. Constrained NSGA-II Feasibility Check
    def test_32_nsga2_constrained_feasibility(self):
        pareto, rec = run_nsga2(current=3.8, ambient=22.0, future_risk=20.0, profile='Food')
        self.assertTrue(len(pareto) >= 1)
        self.assertTrue(rec['feasible'])
        self.assertIn('expected_temperature', rec)
        self.assertTrue(0.0 <= rec['expected_temperature'] <= 5.0)
        self.assertTrue(rec['cooling_intensity'] >= 0.1)
        self.assertTrue(rec['compressor_duty_cycle'] >= 0.2)

    # 33. Pipeline Handles Sensor With Zero Readings Gracefully
    def test_33_pipeline_missing_sensor_history(self):
        empty_sensor = Sensor.objects.create(
            sensor_id='EMPTY-SENSOR-99',
            location='Chamber with no telemetry',
            product_type='Food'
        )
        res = self.client.get(f'/api/pipeline/?sensor={empty_sensor.sensor_id}')
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['sensor'], 'EMPTY-SENSOR-99')
        self.assertIn('At least 60 readings are required', data['error'])
        self.assertEqual(data['reading_count'], 0)

    # 34. Profile API and Fallback on Unknown Product Profile
    def test_34_unknown_product_profile_fallback(self):
        res = self.client.get('/api/profile/?profile=NonExistentCargo')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        # Defaults to Generic (0.0 to 5.0 °C)
        self.assertEqual(data['active_profile'], 'NonExistentCargo')
        self.assertEqual(data['limits'], {'min_c': 0.0, 'max_c': 5.0})

    # 35. Constrained NSGA-II Under Extreme Ambient Heat Shock
    def test_35_nsga2_extreme_heat_shock_feasibility(self):
        # Extreme ambient 45.0 °C, current chamber 4.9 °C, critical risk 85.0
        pareto, rec = run_nsga2(current=4.9, ambient=45.0, future_risk=85.0, profile='Food')
        self.assertTrue(len(pareto) >= 1)
        # Should aggressively activate high cooling (at least 0.70 duty and intensity)
        self.assertGreaterEqual(rec['cooling_intensity'], 0.70)
        self.assertGreaterEqual(rec['compressor_duty_cycle'], 0.70)

    # 36. IoT Ingestion Rejects Malformed Timestamps & Missing Keys
    def test_36_iot_telemetry_malformed_payload(self):
        # Missing sensor_id
        res1 = self.client.post('/api/iot/telemetry/', data=json.dumps({'temperature': 3.5}),
                                content_type='application/json')
        self.assertEqual(res1.status_code, 400)

        # Invalid timestamp string
        res2 = self.client.post('/api/iot/telemetry/',
                                data=json.dumps({'sensor_id': 'BAD-TS-01', 'temperature': 3.5, 'timestamp': 'not-a-timestamp'}),
                                content_type='application/json')
        self.assertEqual(res2.status_code, 400)

