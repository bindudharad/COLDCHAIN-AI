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
from ml.mad_tcn import MADTCN
from optimization.nsga2_optimizer import run_nsga2
class PipelineTests(SimpleTestCase):
 def test_mad_tcn_shape(self): self.assertEqual(tuple(MADTCN(12)(torch.randn(1,60,12)).shape),(1,15))
 def test_nsga2(self):
  points,recommendation=run_nsga2(4,24,40,16,3); self.assertTrue(points); self.assertIn('estimated_energy_kwh',recommendation)
