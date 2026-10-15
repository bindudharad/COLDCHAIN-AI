"""Automated tests for newly implemented features in ColdChain-AI.

Covers:
1. Delimiter Detection in datasets utility (scripts.audit_datasets.detect_delimiter)
2. Energy Unit Contracts and thermodynamic estimators (core.estimated_power_kw, estimated_energy_kwh, energy)
3. Per-Device IoT Hardware Authentication & Provenance assignment (/api/iot/telemetry/)
"""
import json
import os
from pathlib import Path
import sys
import tempfile

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from core import energy, estimated_energy_kwh, estimated_power_kw
from scripts.audit_datasets import detect_delimiter


class DelimiterDetectionTests(TestCase):
    """Group 1: Tests for CSV delimiter detection utility."""

    def _create_temp_csv(self, content: str) -> Path:
        """Helper to create a temporary CSV file with guaranteed cleanup."""
        tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8")
        tmp.write(content)
        tmp.close()
        temp_path = Path(tmp.name)
        self.addCleanup(lambda: temp_path.unlink(missing_ok=True))
        return temp_path

    def test_semicolon_delimited_csv(self):
        """Test semicolon-delimited CSV content is correctly detected as ';'."""
        content = (
            "timestamp;sensor_id;temperature;humidity\n"
            "2026-03-01T00:00:00Z;S-01;3.5;65.0\n"
            "2026-03-01T00:01:00Z;S-01;3.6;64.8\n"
        )
        csv_path = self._create_temp_csv(content)
        detected = detect_delimiter(csv_path)
        self.assertEqual(detected, ";")

    def test_comma_delimited_csv(self):
        """Test comma-delimited CSV content is correctly detected as ','."""
        content = (
            "timestamp,sensor_id,temperature,humidity\n"
            "2026-03-01T00:00:00Z,S-01,3.5,65.0\n"
            "2026-03-01T00:01:00Z,S-01,3.6,64.8\n"
        )
        csv_path = self._create_temp_csv(content)
        detected = detect_delimiter(csv_path)
        self.assertEqual(detected, ",")

    def test_tab_delimited_csv(self):
        """Test tab-delimited CSV content is correctly detected as '\\t'."""
        content = (
            "timestamp\tsensor_id\ttemperature\thumidity\n"
            "2026-03-01T00:00:00Z\tS-01\t3.5\t65.0\n"
            "2026-03-01T00:01:00Z\tS-01\t3.6\t64.8\n"
        )
        csv_path = self._create_temp_csv(content)
        detected = detect_delimiter(csv_path)
        self.assertEqual(detected, "\t")

    def test_fallback_empty_or_ambiguous_content(self):
        """Test fallback to ',' for empty, single-column, or ambiguous files."""
        # Case A: Empty file
        empty_csv = self._create_temp_csv("")
        self.assertEqual(detect_delimiter(empty_csv), ",")

        # Case B: Ambiguous single column (no delimiters)
        ambiguous_csv = self._create_temp_csv("raw_unformatted_stream_values\n123456\n789012\n")
        self.assertEqual(detect_delimiter(ambiguous_csv), ",")

        # Case C: Non-existent file path gracefully defaults to comma
        missing_csv = Path(tempfile.gettempdir()) / "non_existent_coldchain_test_file.csv"
        self.assertEqual(detect_delimiter(missing_csv), ",")


class EnergyUnitContractTests(TestCase):
    """Group 2: Tests for energy unit contracts and thermodynamic estimators."""

    def test_estimated_power_kw_reasonable_inputs(self):
        """Test estimated_power_kw returns positive float for realistic operating conditions."""
        power = estimated_power_kw(current=3.0, ambient=25.0, intensity=0.8, duty=0.9)
        self.assertIsInstance(power, float)
        self.assertGreater(power, 0.0)
        # Theoretical calculation:
        # P_rated = 0.25 + 0.035 * max(25 - 3, 0) = 0.25 + 0.77 = 1.02
        # (0.35 + 0.65 * 0.8) * 0.9 = 0.87 * 0.9 = 0.783
        # 1.02 * 0.783 = 0.79866 -> rounded to 3 decimals: 0.799
        self.assertEqual(power, 0.799)

    def test_energy_alias_contract(self):
        """Test energy() returns the exact same value as estimated_power_kw() for compatibility."""
        p1 = estimated_power_kw(current=3.0, ambient=25.0, intensity=0.8, duty=0.9)
        e1 = energy(current=3.0, ambient=25.0, intensity=0.8, duty=0.9)
        self.assertEqual(e1, p1)

        p2 = estimated_power_kw(current=4.5, ambient=32.0, intensity=1.0, duty=1.0)
        e2 = energy(current=4.5, ambient=32.0, intensity=1.0, duty=1.0)
        self.assertEqual(e2, p2)

    def test_estimated_energy_kwh_quarter_hour_interval(self):
        """Test estimated_energy_kwh for 15-minute operational interval (duration_hours=0.25)."""
        power = estimated_power_kw(current=3.0, ambient=25.0, intensity=0.8, duty=0.9)
        energy_15min = estimated_energy_kwh(current=3.0, ambient=25.0, intensity=0.8, duty=0.9, duration_hours=0.25)
        expected_kwh = round(power * 0.25, 4)
        self.assertAlmostEqual(energy_15min, expected_kwh, places=4)
        self.assertEqual(energy_15min, 0.1998)

    def test_estimated_energy_kwh_one_hour_interval(self):
        """Test estimated_energy_kwh for 1-hour interval (duration_hours=1.0)."""
        power = estimated_power_kw(current=3.0, ambient=25.0, intensity=0.8, duty=0.9)
        energy_1h = estimated_energy_kwh(current=3.0, ambient=25.0, intensity=0.8, duty=0.9, duration_hours=1.0)
        expected_kwh = round(power * 1.0, 4)
        self.assertAlmostEqual(energy_1h, expected_kwh, places=4)
        self.assertEqual(energy_1h, power)

    def test_estimated_power_zero_duty_floor(self):
        """Test when compressor duty is 0.0, power output is 0.0 and <= floor threshold (0.05 kW)."""
        power_zero = estimated_power_kw(current=3.0, ambient=25.0, intensity=0.8, duty=0.0)
        self.assertEqual(power_zero, 0.0)
        self.assertLessEqual(power_zero, 0.05)
        self.assertAlmostEqual(power_zero, 0.0, delta=0.05)

    def test_power_monotonically_increasing_with_ambient_temperature(self):
        """Test power demand increases monotonically as ambient temperature climbs (thermal lift penalty)."""
        ambients = [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0]
        powers = [
            estimated_power_kw(current=3.0, ambient=t_amb, intensity=0.8, duty=0.9)
            for t_amb in ambients
        ]
        # Verify strictly monotonic or non-decreasing progression across ambient temperatures
        for i in range(len(powers) - 1):
            self.assertLess(powers[i], powers[i + 1], f"Power at {ambients[i]}°C ({powers[i]}) should be < power at {ambients[i+1]}°C ({powers[i+1]})")
        self.assertGreater(powers[-1], powers[0])


class PerDeviceIoTAuthTests(TestCase):
    """Group 3: Tests for server-side per-device IoT authorization and provenance defense."""

    def test_registered_device_with_master_key(self):
        """Test registered device with valid master key receives REAL_SENSOR provenance."""
        payload = {
            'sensor_id': 'HW-NODE-01',
            'timestamp': timezone.now().isoformat(),
            'temperature': 3.5,
            'data_source': 'REAL_SENSOR'
        }
        res = self.client.post(
            '/api/iot/telemetry/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_HARDWARE_KEY=settings.IOT_HARDWARE_API_KEY
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['records_persisted'], 1)
        self.assertEqual(data['provenance'], 'REAL_SENSOR')

    def test_registered_device_with_valid_per_device_token(self):
        """Test registered device with its correct per-device secret token receives REAL_SENSOR provenance."""
        device_token = settings.REGISTERED_IOT_HARDWARE_DEVICES['HW-NODE-01']
        payload = {
            'sensor_id': 'HW-NODE-01',
            'timestamp': timezone.now().isoformat(),
            'temperature': 3.6,
            'data_source': 'REAL_SENSOR'
        }
        res = self.client.post(
            '/api/iot/telemetry/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_DEVICE_TOKEN=device_token
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['records_persisted'], 1)
        self.assertEqual(data['provenance'], 'REAL_SENSOR')

    def test_registered_device_with_wrong_token_spoofing_defense(self):
        """Test registered device presenting invalid token is degraded to SIMULATION provenance."""
        payload = {
            'sensor_id': 'HW-NODE-01',
            'timestamp': timezone.now().isoformat(),
            'temperature': 3.7,
            'data_source': 'REAL_SENSOR'
        }
        res = self.client.post(
            '/api/iot/telemetry/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_DEVICE_TOKEN='invalid-tampered-device-token'
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['records_persisted'], 1)
        self.assertEqual(data['provenance'], 'SIMULATION')

    def test_unregistered_device_with_master_key_defense(self):
        """Test unregistered device presenting master key is degraded to SIMULATION (not in registry)."""
        payload = {
            'sensor_id': 'RANDOM-DEVICE-99',
            'timestamp': timezone.now().isoformat(),
            'temperature': 3.8,
            'data_source': 'REAL_SENSOR'
        }
        res = self.client.post(
            '/api/iot/telemetry/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_HARDWARE_KEY=settings.IOT_HARDWARE_API_KEY
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['records_persisted'], 1)
        self.assertEqual(data['provenance'], 'SIMULATION')

    def test_request_with_no_hardware_key(self):
        """Test request with no hardware credentials at all is degraded to SIMULATION provenance."""
        payload = {
            'sensor_id': 'HW-NODE-01',
            'timestamp': timezone.now().isoformat(),
            'temperature': 3.9,
            'data_source': 'REAL_SENSOR'
        }
        res = self.client.post(
            '/api/iot/telemetry/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['records_persisted'], 1)
        self.assertEqual(data['provenance'], 'SIMULATION')


class PhysicalEventMetricsTests(TestCase):
    """Group 4: Tests for physical breach event detection metrics."""

    def test_compute_event_metrics_synthetic(self):
        """Test compute_event_metrics on synthetic sequences."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        # Create 100 timesteps of synthetic temperature
        # Event 1: at step 20-25 (crosses > 6.0)
        # Event 2: at step 60-70 (crosses > 6.0)
        series = np.full(100, 5.0)
        series[20:26] = 6.5
        series[60:71] = 6.8

        window = 10
        horizon = 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        # Persistence prediction (flatline at origin)
        pred_pers = np.tile(t_origin[:, np.newaxis], (1, horizon))
        res_pers = compute_event_metrics(y, pred_pers, t_origin, horizon=horizon, threshold=6.0)

        self.assertEqual(res_pers['total_unique_physical_events'], 2)
        self.assertEqual(res_pers['unique_events_detected'], 0)
        self.assertEqual(res_pers['event_detection_rate_pct'], 0.0)
        self.assertEqual(res_pers['event_missed_rate_pct'], 100.0)

        # Oracle/Perfect prediction
        res_oracle = compute_event_metrics(y, y, t_origin, horizon=horizon, threshold=6.0)
        self.assertEqual(res_oracle['total_unique_physical_events'], 2)
        self.assertEqual(res_oracle['unique_events_detected'], 2)
        self.assertEqual(res_oracle['event_detection_rate_pct'], 100.0)
        self.assertEqual(res_oracle['unique_events_missed'], 0)
        self.assertGreater(res_oracle['mean_warning_lead_time_min'], 0.0)

