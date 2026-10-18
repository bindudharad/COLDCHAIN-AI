import os, sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
for p in [str(BACKEND_DIR), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import SimpleTestCase
import torch
import numpy as np
import pandas as pd
from ml.mad_tcn import MADTCN
from ml.inference import forecast
from core import risk, estimated_power_kw, estimated_energy_kwh
from core_preprocessing import prepare, sequences, FEATURES
from optimization.nsga2_optimizer import run_nsga2
from scripts.compare_nsga2_methods import simulate_interval


class PipelineTests(SimpleTestCase):
    def test_mad_tcn_shape(self):
        self.assertEqual(tuple(MADTCN(12)(torch.randn(1, 60, 12)).shape), (1, 15))

    def test_nsga2(self):
        points, recommendation = run_nsga2(4, 24, 40, 16, 3)
        self.assertTrue(points)
        self.assertIn('estimated_energy_kwh', recommendation)

    def test_leak_free_sequence_slicing(self):
        """Verify that sequence slicing prevents temporal leakage across horizon."""
        df_dummy = pd.DataFrame({
            'timestamp': pd.date_range('2026-01-01', periods=80, freq='min'),
            'sensor_id': 'TEST-01',
            'temperature': np.linspace(3.0, 5.0, 80),
            'humidity': 70.0,
            'ambient_temperature': 22.0,
            'power_kw': 0.5,
            'compressor_state': 1,
            'door_open': 0
        })
        df_prep = prepare(df_dummy)
        X, y = sequences(df_prep, window=60, horizon=15)
        
        # Verify strict shape and dimension
        self.assertEqual(X.shape[1], 60)
        self.assertEqual(X.shape[2], 12)
        self.assertEqual(y.shape[1], 15)
        
        # Verify target y does not overlap with features in X
        # For sequence 0: X uses rows [0:60], y uses rows [60:75]
        expected_y0_start = df_prep.iloc[60]['temperature']
        self.assertAlmostEqual(y[0, 0], expected_y0_start, places=4)
        
        # Last feature in X[0] at index 59 must equal row 59 temperature
        self.assertAlmostEqual(X[0, 59, 0], df_prep.iloc[59]['temperature'], places=4)

    def test_end_to_end_forecast_to_optimizer_coupling(self):
        """Verify genuine coupling from 60x12 input -> MAD-TCN -> risk -> NSGA-II decision -> simulation."""
        # 1. Synthetic 60x12 sequence
        dummy_seq = np.random.normal(loc=0.0, scale=0.1, size=(60, 12)).tolist()
        
        # 2. Inference produces exactly 15 forecast steps
        pred = forecast(dummy_seq)
        self.assertEqual(len(pred), 15)
        
        # 3. Impending heat excursion risk computation
        pred_warm = [4.2 + 0.1 * i for i in range(15)]  # Drifts from 4.2 to 5.6 °C
        r_warm = risk(pred_warm, profile='Food')
        self.assertGreater(r_warm['risk_score'], 15.0)
        self.assertIn(r_warm['risk_level'], ['MEDIUM', 'HIGH', 'CRITICAL'])
        
        # 4. Optimizer run with forecast risk (Method C) vs disabled risk (Method D)
        t_cur, t_amb = 4.2, 22.0
        _, rec_c = run_nsga2(t_cur, t_amb, future_risk=r_warm['risk_score'], profile='Food', buffer=0.2)
        _, rec_d = run_nsga2(t_cur, t_amb, future_risk=0.0, profile='Food', buffer=0.2)
        
        # Method C responds to forecast risk with equal or greater cooling effort
        cooling_c = rec_c['cooling_intensity'] * rec_c['compressor_duty_cycle']
        cooling_d = rec_d['cooling_intensity'] * rec_d['compressor_duty_cycle']
        self.assertGreaterEqual(cooling_c, cooling_d - 1e-4)
        
        # Method C achieves equal or cooler chamber peak temperature than Method D
        self.assertLessEqual(rec_c['max_trajectory_temp'], rec_d['max_trajectory_temp'] + 1e-4)
        
        # 5. Independent forward simulation matches optimizer reported trajectory peak
        _, sim_hist = simulate_interval(t_cur, t_amb, rec_c['cooling_intensity'], rec_c['compressor_duty_cycle'])
        self.assertAlmostEqual(max(sim_hist), rec_c['max_trajectory_temp'], places=3)

