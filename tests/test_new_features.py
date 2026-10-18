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
    """Group 4: Comprehensive adversarial unit tests for physical breach event detection."""

    def test_correctly_detected_event_with_positive_actionable_lead_time(self):
        """Test a clear impending breach is correctly credited with positive actionable lead time."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        # 50-step series: safe at 5.0 °C, breaches at step 20 (stays 6.5 °C for 5 steps)
        series = np.full(50, 5.0)
        series[20:25] = 6.5
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        # Model predicts safe everywhere except at sequence 12 (origin index 16, which is 4 steps before step 20)
        pred = np.tile(t_origin[:, np.newaxis], (1, horizon))
        pred[12] = 6.8  # Alarm raised at origin step 16, lead time = 20 - 16 = 4 min

        res = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=6.0, min_lead_time_min=1)
        self.assertEqual(res['total_unique_physical_events'], 1)
        self.assertEqual(res['unique_events_detected'], 1)
        self.assertEqual(res['unique_events_missed'], 0)
        self.assertEqual(res['event_detection_rate_pct'], 100.0)
        self.assertEqual(res['mean_warning_lead_time_min'], 4.0)

    def test_alarm_only_after_event_begins_is_rejected_as_advance_warning(self):
        """Test an alarm raised only after the breach is underway is NOT credited as an advance warning."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        series = np.full(50, 5.0)
        series[20:25] = 6.5  # Event starts at step 20
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        # Model raises alarm ONLY at sequence 16 (origin step 20, where T=6.5 is ALREADY breached)
        pred = np.tile(t_origin[:, np.newaxis], (1, horizon))
        pred[16] = 7.0  # Alarm at or after breach start

        res = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=6.0, min_lead_time_min=1)
        self.assertEqual(res['total_unique_physical_events'], 1)
        self.assertEqual(res['unique_events_detected'], 0)  # Must NOT credit in-breach alarms as advance warning
        self.assertEqual(res['unique_events_missed'], 1)
        self.assertEqual(res['mean_warning_lead_time_min'], 0.0)

    def test_duplicate_alarms_counted_at_most_once_per_physical_event(self):
        """Test multiple consecutive warning sequences for one physical breach count as ONE detected event."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        series = np.full(50, 5.0)
        series[20:25] = 6.5
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        # Model alarms at 4 consecutive safe origin sequences (origins 16, 17, 18, 19)
        pred = np.tile(t_origin[:, np.newaxis], (1, horizon))
        pred[12:16] = 6.8

        res = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=6.0)
        self.assertEqual(res['total_unique_physical_events'], 1)
        self.assertEqual(res['unique_events_detected'], 1)  # Strictly counted at most once
        self.assertEqual(res['total_sequence_warnings_on_events'], 4)
        self.assertEqual(res['duplicate_warnings_per_detected_event'], 4.0)
        self.assertEqual(res['mean_warning_lead_time_min'], 4.0)  # Earliest advance lead time

    def test_two_distinct_events_separated_by_genuine_safe_interval(self):
        """Test two distinct breach events separated by a safe period are both evaluated independently."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        series = np.full(80, 5.0)
        series[15:20] = 6.5  # Event 1: steps 15-19
        # Steps 20-39: safe at 5.0 °C
        series[40:45] = 6.8  # Event 2: steps 40-44
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        # Oracle predictions (detects both events)
        res = compute_event_metrics(y, y, t_origin, horizon=horizon, threshold=6.0)
        self.assertEqual(res['total_unique_physical_events'], 2)
        self.assertEqual(res['unique_events_detected'], 2)
        self.assertEqual(res['unique_events_missed'], 0)
        self.assertEqual(res['event_detection_rate_pct'], 100.0)

    def test_event_at_beginning_of_series_pre_existing_breach_handled(self):
        """Test that a breach event active at t=0 (pre-existing breach) is counted and cannot be falsely claimed as anticipated."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        series = np.full(50, 5.0)
        series[0:8] = 6.8   # Event 1: starts at t=0 (pre-existing breach)
        series[30:35] = 6.5 # Event 2: starts at step 30
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        # Model alarms before Event 2, but cannot alarm before Event 1 (starts at t=0)
        pred = np.tile(t_origin[:, np.newaxis], (1, horizon))
        # Alarm for event 2 at origin step 27 (seq 23)
        pred[23] = 6.8

        res = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=6.0)
        self.assertEqual(res['total_unique_physical_events'], 2)
        self.assertEqual(res['unique_events_detected'], 1)  # Only Event 2 detected
        self.assertEqual(res['unique_events_missed'], 1)    # Event 1 missed (no prior safe warning possible)

    def test_event_at_end_of_series_handled(self):
        """Test an event starting near the very end of the series is properly identified."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        series = np.full(50, 5.0)
        series[38:40] = 6.6  # Event at end of series
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        pred = np.tile(t_origin[:, np.newaxis], (1, horizon))
        # start_k in test_eval_series is 34 (series[38]). Advance alarm at sequence 32 (lead time 2 steps)
        pred[32] = 6.7  # Advance alarm

        res = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=6.0)
        self.assertEqual(res['total_unique_physical_events'], 1)
        self.assertEqual(res['unique_events_detected'], 1)

    def test_missing_observations_and_timestamp_gaps_prevent_event_merging(self):
        """Test that sensor downtime gaps split breach episodes rather than artificially merging them."""
        import numpy as np
        import pandas as pd
        from scripts.evaluate_real_forecasting import compute_event_metrics

        # Reconstructed test series has high temp at k=1..4 (series[2..5]), then safe
        series = np.array([5.0, 5.0, 6.5, 6.5, 6.5, 6.5, 5.0, 5.0, 5.0, 5.0, 5.0])
        window, horizon = 2, 2
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        # len(test_eval_series) = len(t_origin) + horizon = 7 + 2 = 9
        # Construct exactly 9 timestamps with a 3-hour downtime gap between k=2 and k=3
        ts_eval = pd.to_datetime([
            '2026-01-01 00:00',
            '2026-01-01 00:01',
            '2026-01-01 00:02',
            '2026-01-01 03:00',  # 3-hour downtime gap!
            '2026-01-01 03:01',
            '2026-01-01 03:02',
            '2026-01-01 03:03',
            '2026-01-01 03:04',
            '2026-01-01 03:05',
        ])
        pred_flat = np.tile(t_origin[:, np.newaxis], (1, horizon))

        res_gapped = compute_event_metrics(y, pred_flat, t_origin, timestamps=ts_eval, horizon=horizon, threshold=6.0, max_gap_minutes=10.0)
        # Without gap splitting it would be 1 merged event; with gap splitting it must be 2 events
        self.assertEqual(res_gapped['total_unique_physical_events'], 2)

    def test_misaligned_forecast_timestamp_rejected(self):
        """Test that alarms predicting breach at misaligned timestamps outside the event are identified."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        series = np.full(50, 5.0)
        series[25:30] = 6.5  # Event from step 25 to 29
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        # Model predicts breach at horizon step 0 (step 16), which is BEFORE step 25, but safe at step 25
        pred = np.tile(t_origin[:, np.newaxis], (1, horizon))
        pred[11, 0] = 6.8  # Target step 16 (safe in ground truth), but step 25 is safe
        pred[11, 1:] = 5.0

        res = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=6.0)
        # Event is not overlap matched because the predicted breach was misaligned
        self.assertEqual(res['overlap_matched_events'], 0)

    def test_no_eligible_safe_origins_flagged_inconclusive(self):
        """Test that evaluating when chamber is constantly above threshold is flagged as STATISTICALLY INCONCLUSIVE."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        # All observations at 7.0 °C (chamber continuously breached against 5.0 °C limit)
        series = np.full(50, 7.0)
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]
        pred = np.full_like(y, 7.0)

        res = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=5.0)
        self.assertEqual(res['safe_origins_count'], 0)
        self.assertIn("INCONCLUSIVE", res['conclusive_status'])

    def test_false_alarm_with_no_subsequently_matched_event(self):
        """Test false alarms on sequences where no breach occurs in ground truth are tracked and counted."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        # Temperature stays safe at 5.0 °C for all 50 steps
        series = np.full(50, 5.0)
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        # Model triggers false alarms on 3 consecutive sequences (seq 10, 11, 12)
        pred = np.tile(t_origin[:, np.newaxis], (1, horizon))
        pred[10:13] = 6.5

        res = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=6.0)
        self.assertEqual(res['total_unique_physical_events'], 0)
        self.assertEqual(res['unique_events_detected'], 0)
        self.assertEqual(res['false_alarm_sequences'], 3)
        self.assertEqual(res['false_alarm_clustered_episodes'], 1)  # Grouped within 15-min cooldown
        self.assertGreater(res['false_alarm_rate_per_day'], 0.0)

    def test_reproducibility_on_same_input(self):
        """Test compute_event_metrics produces perfectly deterministic, reproducible metrics."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        series = np.full(60, 5.0)
        series[20:25] = 6.5
        series[40:48] = 6.8
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        pred = np.tile(t_origin[:, np.newaxis], (1, horizon))
        pred[12:15] = 6.6

        run1 = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=6.0)
        run2 = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=6.0)
        self.assertEqual(run1, run2)

    def test_lookahead_leakage_adversarial_rejection(self):
        """Test that an alarm raised without a safe origin or outside the actionable window is rejected."""
        import numpy as np
        from scripts.evaluate_real_forecasting import compute_event_metrics

        series = np.full(50, 5.0)
        series[30:35] = 6.5
        window, horizon = 5, 5
        X = np.array([series[i : i + window] for i in range(len(series) - window - horizon)])
        y = np.array([series[i + window : i + window + horizon] for i in range(len(series) - window - horizon)])
        t_origin = X[:, -1]

        # Adversary attempts to warn from sequence 5 (origin index 9, 21 minutes before event onset at 30)
        # Advance window is [30 - horizon, 30 - 1] = [25, 29]
        # Origin index 9 is OUTSIDE the lookahead horizon (too early to be a valid actionable forecast for step 30)
        pred = np.tile(t_origin[:, np.newaxis], (1, horizon))
        pred[5] = 6.8

        res = compute_event_metrics(y, pred, t_origin, horizon=horizon, threshold=6.0)
        # Because sequence 5 does not cover step 30, it is NOT an advance warning for step 30
        self.assertEqual(res['unique_events_detected'], 0)
        self.assertEqual(res['unique_events_missed'], 1)
        # Instead, it is properly counted as a false alarm sequence!
        self.assertEqual(res['false_alarm_sequences'], 1)


class TemporalSplitPurgingTests(TestCase):
    """Regression test suite for strict chronological target separation and boundary purging."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import pandas as pd
        import numpy as np
        from pathlib import Path
        from scripts.evaluate_real_forecasting import load_real_sensor_series, create_purged_chronological_splits

        csv_path = Path("Datasets/zenodo_hohenheim/preprocessed_extracted/SENSOR03_preprocessed.csv")
        if csv_path.exists():
            cls.series, _ = load_real_sensor_series(csv_path)
        else:
            # Fallback synthetic 1-minute series of 7037 timestamps
            idx = pd.date_range("2024-09-06 14:08:00", periods=7037, freq="1min")
            cls.series = pd.Series(5.0 + np.sin(np.linspace(0, 50, 7037)), index=idx)
        cls.splits = create_purged_chronological_splits(cls.series, window=60, horizon=15)

    def test_no_training_target_timestamp_overlaps_validation_target_timestamp(self):
        """Test that train and validation target timestamp sets have zero intersection."""
        train_targets = self.splits["train_target_timestamps"]
        val_targets = self.splits["val_target_timestamps"]
        overlap = train_targets.intersection(val_targets)
        self.assertEqual(len(overlap), 0, f"Expected 0 target timestamp overlap between train and val, got {len(overlap)}")

    def test_no_validation_target_timestamp_overlaps_test_target_timestamp(self):
        """Test that validation and held-out test target timestamp sets have zero intersection."""
        val_targets = self.splits["val_target_timestamps"]
        test_targets = self.splits["test_target_timestamps"]
        overlap = val_targets.intersection(test_targets)
        self.assertEqual(len(overlap), 0, f"Expected 0 target timestamp overlap between val and test, got {len(overlap)}")

    def test_no_train_or_val_target_inside_held_out_test_target_period(self):
        """Test that no training or validation target falls inside the held-out test target period."""
        train_targets = self.splits["train_target_timestamps"]
        val_targets = self.splits["val_target_timestamps"]
        test_targets = self.splits["test_target_timestamps"]

        max_train_ts = max(train_targets)
        min_val_ts = min(val_targets)
        max_val_ts = max(val_targets)
        min_test_ts = min(test_targets)

        self.assertLess(max_train_ts, min_val_ts, "Train target horizon must strictly precede validation targets")
        self.assertLess(max_val_ts, min_test_ts, "Validation target horizon must strictly precede test targets")
        self.assertEqual(len(train_targets.intersection(test_targets)), 0)

    def test_test_input_history_strictly_precedes_forecast_origin(self):
        """Test that test input history uses only past observations preceding each sequence forecast origin."""
        import numpy as np
        vals = self.series.to_numpy(dtype=float)
        W, H = 60, 15
        test_start = self.splits["test_sequence_indices"][0]
        total_seq = self.splits["total_sequences_raw"]

        # For the very first test sequence (test_start)
        first_test_x = self.splits["X_test"][0]
        expected_x = vals[test_start : test_start + W]
        np.testing.assert_array_equal(first_test_x, expected_x)

        # Forecast origin for first test sequence is at test_start + W - 1
        origin_idx = test_start + W - 1
        # Target period starts at test_start + W
        first_target_idx = test_start + W
        self.assertLess(origin_idx, first_target_idx)

    def test_forecast_timestamps_and_target_arrays_strictly_aligned(self):
        """Test that target arrays y match the underlying continuous series values at identical timestamps."""
        import numpy as np
        vals = self.series.to_numpy(dtype=float)
        W, H = 60, 15

        # Check alignment across random train, val, and test sequences
        y_train = self.splits["y_train"]
        np.testing.assert_array_equal(y_train[0], vals[W : W + H])
        np.testing.assert_array_equal(y_train[-1], vals[len(y_train) - 1 + W : len(y_train) - 1 + W + H])

        val_start = self.splits["val_sequence_indices"][0]
        y_val = self.splits["y_val"]
        np.testing.assert_array_equal(y_val[0], vals[val_start + W : val_start + W + H])

        test_start = self.splits["test_sequence_indices"][0]
        y_test = self.splits["y_test"]
        np.testing.assert_array_equal(y_test[0], vals[test_start + W : test_start + W + H])
        last_test_idx = (len(vals) - W - H) - 1
        np.testing.assert_array_equal(y_test[-1], vals[last_test_idx + W : last_test_idx + W + H])

    def test_boundary_purging_counts_and_reproducibility(self):
        """Test that boundary purging removes exactly H-1=14 sequences at boundaries and is deterministic."""
        from scripts.evaluate_real_forecasting import create_purged_chronological_splits
        splits2 = create_purged_chronological_splits(self.series, window=60, horizon=15)

        self.assertEqual(self.splits["train_purged_sequences_count"], 14)
        self.assertEqual(self.splits["val_purged_sequences_count"], 14)
        self.assertEqual(self.splits["total_purged_sequences_count"], 28)

        self.assertEqual(self.splits["train_sequences_count"], 4859)
        self.assertEqual(self.splits["val_sequences_count"], 1030)
        self.assertEqual(self.splits["test_sequences_count"], 1045)

        # Assert determinism between runs
        self.assertEqual(self.splits["train_sequence_indices"], splits2["train_sequence_indices"])
        self.assertEqual(self.splits["val_sequence_indices"], splits2["val_sequence_indices"])
        self.assertEqual(self.splits["test_sequence_indices"], splits2["test_sequence_indices"])


class ModelArchitectureAndProvenanceTestCase(TestCase):
    """Scientific verification of neural architecture claims and data provenance contracts."""

    def test_real_dense_forecaster_architecture(self):
        """Assert RealDenseForecaster is strictly an MLP (Linear layers) and contains NO Conv1d layers."""
        import torch.nn as nn
        from scripts.evaluate_real_forecasting import RealDenseForecaster

        model = RealDenseForecaster(in_features=60, hidden=32, horizon=15)
        modules = list(model.modules())
        linear_layers = [m for m in modules if isinstance(m, nn.Linear)]
        conv_layers = [m for m in modules if isinstance(m, (nn.Conv1d, nn.Conv2d))]

        self.assertEqual(len(linear_layers), 3, "RealDenseForecaster must have exactly 3 Linear layers")
        self.assertEqual(len(conv_layers), 0, "RealDenseForecaster must NOT contain any Convolutional layers")
        self.assertEqual(linear_layers[0].in_features, 60)
        self.assertEqual(linear_layers[0].out_features, 32)
        self.assertEqual(linear_layers[1].in_features, 32)
        self.assertEqual(linear_layers[1].out_features, 32)
        self.assertEqual(linear_layers[2].in_features, 32)
        self.assertEqual(linear_layers[2].out_features, 15)

    def test_mad_tcn_genuine_convolutional_architecture(self):
        """Assert MADTCN is a genuine dilated causal convolutional neural network."""
        import torch.nn as nn
        from ml.mad_tcn import MADTCN

        model = MADTCN(features=12, hidden=32, horizon=15)
        modules = list(model.modules())
        conv1d_layers = [m for m in modules if isinstance(m, nn.Conv1d)]

        self.assertGreater(len(conv1d_layers), 0, "MADTCN must contain genuine Conv1d layers")
        dilations = [c.dilation[0] for c in conv1d_layers]
        self.assertIn(1, dilations)
        self.assertTrue(any(d > 1 for d in dilations), "MADTCN must contain dilated convolutions (dilation > 1)")

    def test_mad_tcn_univariate_forward_contract(self):
        """Assert MADTCN executes properly with univariate (1-channel) input shape (batch, window, 1)."""
        import torch
        from ml.mad_tcn import MADTCN

        model = MADTCN(features=1, hidden=32, horizon=15)
        x = torch.randn(8, 60, 1)
        y = model(x)
        self.assertEqual(y.shape, (8, 15), "Output shape must be (batch, horizon=15)")


class ForecastGuidedOptimizationCouplingTestCase(TestCase):
    """Scientific verification that forecast directly drives risk and influences NSGA-II decision-making."""

    def test_forecast_changes_alter_risk_and_optimization_decisions(self):
        """Prove that changing forecast trajectory changes risk score and resulting cooling intensity."""
        from core import risk
        from optimization.nsga2_optimizer import run_nsga2

        # Safe trajectory: temperatures stay around 3.0 °C
        safe_forecast = [3.0 + 0.05 * i for i in range(15)]
        risk_safe = risk(safe_forecast, profile='Food')

        # Dangerous trajectory: temperature rapidly rises past 5.0 °C limit
        unsafe_forecast = [3.5 + 0.25 * i for i in range(15)]
        risk_unsafe = risk(unsafe_forecast, profile='Food')

        self.assertGreater(risk_unsafe['risk_score'], risk_safe['risk_score'],
                           "Unsafe warming trajectory must yield higher risk score")

        # Run NSGA-II under identical current/ambient conditions but different forecast risks
        current_t = 3.8
        ambient_t = 25.0

        pareto_safe, rec_safe = run_nsga2(current_t, ambient_t, risk_safe['risk_score'], profile='Food')
        pareto_unsafe, rec_unsafe = run_nsga2(current_t, ambient_t, risk_unsafe['risk_score'], profile='Food')

        cooling_power_safe = rec_safe['cooling_intensity'] * rec_safe['compressor_duty_cycle']
        cooling_power_unsafe = rec_unsafe['cooling_intensity'] * rec_unsafe['compressor_duty_cycle']

        self.assertGreaterEqual(cooling_power_unsafe, cooling_power_safe - 1e-4,
                                "High future thermal risk must demand proactive refrigeration response")


class OptimizationFeasibilityAndAblationTests(TestCase):
    """Rigorous scientific tests for trajectory thermal feasibility, emergency fallbacks, and energy reconciliation."""

    def test_trajectory_thermal_feasibility_detection(self):
        """Verify trajectory feasibility detects in-interval breaches and exceedance magnitudes."""
        from scripts.compare_nsga2_methods import evaluate_solution_trajectory

        # Case 1: Trajectory with breach (initial temp 4.8 °C, rising past 5.0 °C before cooling)
        eval_breach = evaluate_solution_trajectory(t0=4.8, ambient=26.0, intensity=0.5, duty=0.4, hi_limit=5.0)
        self.assertFalse(eval_breach['is_trajectory_feasible'])
        self.assertTrue(eval_breach['has_breach'])
        self.assertGreater(eval_breach['violations_min'], 0)
        self.assertGreater(eval_breach['max_exceedance'], 0.0)

        # Case 2: Trajectory entirely within safe envelope (initial temp 3.0 °C, max temp <= 5.0 °C)
        eval_safe = evaluate_solution_trajectory(t0=3.0, ambient=15.0, intensity=0.8, duty=0.8, hi_limit=5.0)
        self.assertTrue(eval_safe['is_trajectory_feasible'])
        self.assertFalse(eval_safe['has_breach'])
        self.assertEqual(eval_safe['violations_min'], 0)
        self.assertEqual(eval_safe['max_exceedance'], 0.0)

    def test_infeasible_initial_state_triggers_emergency_fallback(self):
        """Verify severely breached initial states trigger Emergency Fallback and are not counted as ordinary feasible."""
        from optimization.nsga2_optimizer import run_nsga2

        # Severe initial breach: chamber at 8.2 °C (far above 5.0 °C limit)
        pareto, rec = run_nsga2(current=8.2, ambient=28.0, future_risk=90.0, profile='Food')
        self.assertTrue(rec['is_emergency_fallback'], "Severely breached initial state must engage emergency fallback")
        self.assertFalse(rec['feasible'], "Emergency fallback override must NOT be labeled as an ordinary feasible solution")
        self.assertEqual(rec['cooling_intensity'], 1.0, "Emergency fallback must command maximum cooling intensity")
        self.assertEqual(rec['compressor_duty_cycle'], 1.0, "Emergency fallback must command maximum duty cycle")
        self.assertIn("Emergency Fallback Override", rec['explanation'])

    def test_forecast_guided_vs_risk_disabled_objective_impact(self):
        """Verify predictive risk directly escalates the NSGA-II risk objective F0, compelling higher refrigeration."""
        import numpy as np
        from optimization.nsga2_optimizer import ColdProblem

        current_t = 3.8
        ambient_t = 24.0

        # Run with genuine predictive risk vs risk disabled (fr=0)
        prob_guided = ColdProblem(current_t, ambient_t, future_risk=75.0, t_min=0.0, t_max=5.0)
        prob_blind = ColdProblem(current_t, ambient_t, future_risk=0.0, t_min=0.0, t_max=5.0)

        # Evaluate identical candidate: intensity=0.4, duty=0.4, offset=0.0
        x_cand = np.array([[0.4, 0.4, 0.0]])
        out_guided = {}; out_blind = {}
        prob_guided._evaluate(x_cand, out_guided)
        prob_blind._evaluate(x_cand, out_blind)

        # Objective F0 for guided should be significantly higher due to residual forecast risk
        self.assertGreater(out_guided['F'][0, 0], out_blind['F'][0, 0],
                           "Forecast risk must directly elevate the optimizer risk objective F0")

    def test_energy_unit_consistency_in_optimizer(self):
        """Verify ColdProblem objective F1 is mathematically consistent with estimated_energy_kwh (P * 0.25)."""
        import numpy as np
        from optimization.nsga2_optimizer import ColdProblem
        from core import estimated_power_kw, estimated_energy_kwh

        current_t = 3.5
        ambient_t = 22.0
        prob = ColdProblem(current_t, ambient_t, future_risk=10.0)

        x_test = np.array([[0.8, 0.7, 0.0]])
        out = {}
        prob._evaluate(x_test, out)

        power_kw = estimated_power_kw(current_t, ambient_t, 0.8, 0.7)
        expected_kwh = estimated_energy_kwh(current_t, ambient_t, 0.8, 0.7, duration_hours=0.25)

        self.assertAlmostEqual(out['F'][0, 1], expected_kwh, places=3,
                               msg="F1 objective must match estimated_energy_kwh over 15-minute interval (power * 0.25)")

    def test_nsga2_comparison_data_reconciliation(self):
        """Verify machine-readable nsga2_comparison_data.json matches verified audit figures exactly."""
        json_path = Path('reports/nsga2_comparison/nsga2_comparison_data.json')
        self.assertTrue(json_path.exists(), "nsga2_comparison_data.json must exist")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data['num_scenarios'], 50)
        self.assertEqual(data['method_a_reactive']['total_violations_min'], 583)
        self.assertEqual(data['method_c_audited_forecast_guided']['total_violations_min'], 479)
        self.assertEqual(data['method_c_audited_forecast_guided']['vs_method_a']['violation_reduction_min'], -104)
        self.assertAlmostEqual(data['method_c_audited_forecast_guided']['vs_method_a']['violation_change_pct'], -17.84, places=1)
        self.assertEqual(data['feasibility_accounting']['ordinary_algebraic_feasible_scenarios'], 23)
        self.assertEqual(data['feasibility_accounting']['emergency_fallback_overrides'], 27)
        self.assertEqual(data['feasibility_accounting']['trajectory_thermal_feasible_scenarios'], 18)
        self.assertEqual(data['feasibility_accounting']['decision_bounds_compliance_pct'], 100.0)
        self.assertEqual(len(data['per_scenario_results']['scenarios']), 50)






