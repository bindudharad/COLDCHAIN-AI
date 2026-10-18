"""Regression tests for Scenario 14 full-trajectory safety and NSGA-II constraint enforcement.

Ensures that:
1. Scenario 14 (T0=3.8131, Tamb=19.6426, risk=1.75) selects trajectory-feasible controls.
2. ColdProblem dynamically simulates the entire 15-minute interval during optimization.
3. search_deterministic_feasible() guarantees feasible actuator settings for initially compliant chambers.
4. No duty-cycle shutoff warming breach occurs in controllable scenarios.
"""
import os
import sys
from pathlib import Path
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
for p in [str(BACKEND_DIR), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()


from django.test import TestCase
from optimization.nsga2_optimizer import run_nsga2, ColdProblem, search_deterministic_feasible
from scripts.compare_nsga2_methods import simulate_interval, evaluate_solution_trajectory


class Scenario14SafetyRegressionTests(TestCase):
    """Priority 1: Verification of Scenario 14 trajectory safety and NSGA-II constraint unification."""

    def test_scenario14_selects_trajectory_feasible_control(self):
        """Scenario 14 (T0=3.8131 °C, Tamb=19.6426 °C, risk=1.75) must achieve full buffered trajectory compliance."""
        t0 = 3.8131
        tamb = 19.6426
        risk_score = 1.75

        pareto, rec = run_nsga2(t0, tamb, risk_score, profile='Food', buffer=0.2)

        # 1. Verification of recommendation metadata
        self.assertTrue(rec['trajectory_feasible'], "Recommendation must achieve trajectory_feasible=True")
        self.assertTrue(rec['nominal_trajectory_feasible'], "Must achieve nominal_trajectory_feasible=True")
        self.assertTrue(rec['buffered_trajectory_feasible'], "Must achieve buffered_trajectory_feasible=True (<= 4.8 °C)")
        self.assertFalse(rec['is_emergency_fallback'], "Scenario 14 is controllable; cannot be emergency fallback")
        self.assertLessEqual(rec['max_trajectory_temp'], 4.8, "Max trajectory temperature must be <= 4.8 °C under buffer=0.2")
        self.assertGreaterEqual(rec['min_trajectory_temp'], 0.2, "Min trajectory temperature must be >= 0.2 °C under buffer=0.2")

        # 2. Independent forward simulation verification
        final_temp, hist = simulate_interval(t0, tamb, rec['cooling_intensity'], rec['compressor_duty_cycle'])
        eval_metrics = evaluate_solution_trajectory(t0, tamb, rec['cooling_intensity'], rec['compressor_duty_cycle'], buffer=0.2)

        self.assertTrue(eval_metrics['is_trajectory_feasible'], "Independent evaluation must confirm trajectory feasibility")
        self.assertTrue(eval_metrics['is_buffered_trajectory_feasible'], "Independent evaluation must confirm buffered feasibility")
        self.assertEqual(eval_metrics['violating_samples_count'], 0, "Must have zero discrete violating samples")
        self.assertEqual(eval_metrics['excursion_duration_min'], 0.0, "Continuous excursion duration must be exactly 0.0 min")
        self.assertLessEqual(max(hist), 4.8, f"Simulated peak temp {max(hist):.3f} °C must not exceed buffered limit 4.8 °C")
        self.assertGreaterEqual(min(hist), 0.2, f"Simulated min temp {min(hist):.3f} °C must not drop below 0.2 °C")

        # 3. Exact agreement between reported trajectory max and fresh forward simulation
        self.assertAlmostEqual(rec['max_trajectory_temp'], round(float(max(hist)), 3), places=3,
                               msg="Reported max_trajectory_temp must identically match fresh forward simulation")

    def test_hard_buffer_distinguishes_nominal_from_buffered_feasibility(self):
        """Assert peak of 4.945 °C fails hard 4.8 °C constraint while 4.79 °C satisfies it, and flags are separate."""
        problem = ColdProblem(current=3.8131, ambient=19.6426, future_risk=1.75, t_min=0.0, t_max=5.0, buffer=0.2)

        # 1. Candidate producing peak of ~4.945 °C (u=0.883, d=0.667)
        cand_4945 = np.array([[0.883, 0.667, 0.0]])
        out_4945 = {}
        problem._evaluate(cand_4945, out_4945)
        g_4945 = out_4945['G'][0]
        # Peak of ~4.945 °C is <= 5.0 °C (nominally safe), but strictly FAILS hard 4.8 °C constraint (G1 > 0)
        self.assertGreater(g_4945[0], 0.0, "Peak of ~4.945 °C must FAIL the hard 4.8 °C maximum constraint (G1 > 0)")

        eval_4945 = evaluate_solution_trajectory(3.8131, 19.6426, 0.883, 0.667, hi_limit=5.0, lo_limit=0.0, buffer=0.2)
        self.assertTrue(eval_4945['is_nominal_trajectory_feasible'], "4.945 °C must be nominally trajectory feasible (<= 5.0 °C)")
        self.assertFalse(eval_4945['is_buffered_trajectory_feasible'], "4.945 °C must NOT be buffered trajectory feasible (> 4.8 °C)")

        # 2. Candidate producing peak of ~4.774 °C / 4.79 °C (u=0.94, d=0.68)
        cand_479 = np.array([[0.94, 0.68, 0.0]])
        out_479 = {}
        problem._evaluate(cand_479, out_479)
        g_479 = out_479['G'][0]
        # Peak of <= 4.8 °C satisfies upper constraint (G1 <= 0) and lower constraint (G2 <= 0)
        self.assertLessEqual(g_479[0], 0.0, "Peak of ~4.77-4.79 °C must SATISFY the hard 4.8 °C upper constraint (G1 <= 0)")
        self.assertLessEqual(g_479[1], 0.0, "Candidate must satisfy lower freezing constraint G2 (<= 0)")

        eval_479 = evaluate_solution_trajectory(3.8131, 19.6426, 0.94, 0.68, hi_limit=5.0, lo_limit=0.0, buffer=0.2)
        self.assertTrue(eval_479['is_nominal_trajectory_feasible'], "Must be nominally trajectory feasible")
        self.assertTrue(eval_479['is_buffered_trajectory_feasible'], "Must be buffered trajectory feasible")

        # 3. Assert separate representation: nominal status != buffered status for borderline scenarios
        self.assertNotEqual(eval_4945['is_buffered_trajectory_feasible'], eval_4945['is_nominal_trajectory_feasible'],
                            msg="Nominal safety and buffered feasibility must be represented as separate boolean metrics")

    def test_coldproblem_evaluates_complete_15_step_trajectory(self):
        """ColdProblem constraint evaluation must reflect peak trajectory temperature, not just endpoint."""
        problem = ColdProblem(current=3.8131, ambient=19.6426, future_risk=1.75, t_min=0.0, t_max=5.0, buffer=0.2)

        # Candidate with low duty cycle (u=0.78, d=0.55): shuts off at 8.25 min, warms to ~5.7 °C
        unsafe_candidate = np.array([[0.781, 0.558, 0.0]])
        out_unsafe = {}
        problem._evaluate(unsafe_candidate, out_unsafe)
        g_unsafe = out_unsafe['G'][0]
        # G1 > 0 indicates constraint violation
        self.assertGreater(g_unsafe[0], 0.0, "Unsafe low-duty candidate must violate upper constraint G1")

        # Candidate with adequate cooling and duty cycle (u=0.94, d=0.68): stays below 4.8 °C
        safe_candidate = np.array([[0.94, 0.68, 0.0]])
        out_safe = {}
        problem._evaluate(safe_candidate, out_safe)
        g_safe = out_safe['G'][0]
        self.assertLessEqual(g_safe[0], 0.0, "Safe candidate must satisfy upper constraint G1 (<= 0)")
        self.assertLessEqual(g_safe[1], 0.0, "Safe candidate must satisfy lower constraint G2 (<= 0)")

    def test_deterministic_feasible_search_guarantees_compliant_candidates(self):
        """search_deterministic_feasible() must produce candidates that satisfy trajectory bounds."""
        candidates = search_deterministic_feasible(current=3.8131, ambient=19.6426, lo=0.0, hi=5.0, buffer=0.2, future_risk=1.75)
        self.assertGreater(len(candidates), 0, "Deterministic search must find feasible candidates for controllable state")

        buffered_found = False
        for cand in candidates:
            self.assertTrue(cand['trajectory_feasible'])
            self.assertLessEqual(cand['max_trajectory_temp'], 5.0)
            self.assertGreaterEqual(cand['min_trajectory_temp'], 0.0)
            if cand['buffered_trajectory_feasible']:
                buffered_found = True
                self.assertLessEqual(cand['max_trajectory_temp'], 4.8)
                self.assertGreaterEqual(cand['min_trajectory_temp'], 0.2)

            # Confirm with ground-truth simulator
            _, hist = simulate_interval(3.8131, 19.6426, cand['cooling_intensity'], cand['compressor_duty_cycle'])
            self.assertLessEqual(max(hist), 5.0)
            self.assertGreaterEqual(min(hist), 0.0)

        self.assertTrue(buffered_found, "Scenario 14 must have buffered-feasible candidates found by deterministic search")

    def test_initially_compliant_controllable_scenarios_achieve_full_compliance(self):
        """Chambers starting within [0.2, 4.8] °C under moderate ambient (Tamb <= 22.78 °C) must stay compliant."""
        test_cases = [
            {'t0': 4.0, 'tamb': 18.5, 'name': 'Cool ambient'},
            {'t0': 4.25, 'tamb': 20.0, 'name': 'Moderate ambient'},
            {'t0': 3.78, 'tamb': 20.15, 'name': 'Typical storage'},
            {'t0': 4.13, 'tamb': 22.35, 'name': 'Near-critical ambient'},
        ]
        for tc in test_cases:
            _, rec = run_nsga2(tc['t0'], tc['tamb'], future_risk=1.5, profile='Food', buffer=0.2)
            self.assertTrue(rec['trajectory_feasible'], f"{tc['name']} must achieve trajectory feasibility")
            self.assertLessEqual(rec['max_trajectory_temp'], 5.0)
            self.assertGreaterEqual(rec['min_trajectory_temp'], 0.0)
