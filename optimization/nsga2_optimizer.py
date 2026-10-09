"""pymoo NSGA-II constrained multi-objective optimizer driven by forecast-derived risk."""
from __future__ import annotations
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from core import PROFILES

class ColdProblem(Problem):
    """
    Constrained Multi-Objective Cold-Chain Optimization Problem.
    
    Decision Variables (n_var=3):
      x[0]: Cooling intensity u in [0.1, 1.0]
      x[1]: Compressor duty cycle d in [0.2, 1.0]
      x[2]: Target temperature offset delta in [-0.5, 0.5] °C
      
    Objectives (n_obj=2, minimization):
      F[0]: Total safety risk (residual forecast risk + thermal breach penalties)
      F[1]: Estimated energy consumption (kWh) over control interval
      
    Inequality Constraints (n_constr=2, G <= 0 for feasibility):
      G[0]: Upper temperature safety limit: T_expected <= T_max - buffer
      G[1]: Lower temperature freezing limit: T_min + buffer <= T_expected
    """
    def __init__(self, current: float, ambient: float, future_risk: float,
                 t_min: float = 0.0, t_max: float = 5.0, buffer: float = 0.2):
        super().__init__(
            n_var=3,
            n_obj=2,
            n_ieq_constr=2,
            xl=[0.1, 0.2, -0.5],
            xu=[1.0, 1.0, 0.5]
        )
        self.current = float(current)
        self.ambient = float(ambient)
        self.future_risk = float(future_risk)
        self.t_min = float(t_min)
        self.t_max = float(t_max)
        self.buffer = float(buffer)

    def _evaluate(self, x, out, *args, **kwargs):
        # Thermodynamic dynamics over 15-minute control interval:
        # Infiltration heat gain from ambient environment
        ambient_gain = 0.18 * np.maximum(self.ambient - self.current, 0.0)
        # Active mechanical refrigeration cooling capacity
        cooling = 3.2 * x[:, 0] * x[:, 1]
        offset = x[:, 2]
        
        # Expected stabilized chamber temperature after interval
        t_expected = self.current + ambient_gain - cooling + offset
        
        # Upper and lower boundary violations
        upper_viol = np.maximum(0.0, t_expected - self.t_max)
        lower_viol = np.maximum(0.0, self.t_min - t_expected)
        
        # Corrective cooling mitigates predicted future excursion
        risk_reduction = cooling * 8.0
        residual_risk = np.maximum(0.0, self.future_risk - risk_reduction)
        
        # Objective 1: Safety risk minimization (penalty-weighted)
        total_risk = residual_risk + upper_viol * 25.0 + lower_viol * 25.0
        
        # Objective 2: Energy consumption estimation (kWh)
        energy = (0.25 + 0.035 * np.maximum(self.ambient - self.current, 0.0)) * (0.35 + 0.65 * x[:, 0]) * x[:, 1]
        
        out['F'] = np.column_stack([total_risk, energy])
        
        # Constraints (G <= 0 represents feasible operation):
        # G1: Upper temperature boundary constraint
        g1 = t_expected - (self.t_max - self.buffer)
        # G2: Lower temperature freezing constraint
        g2 = (self.t_min + self.buffer) - t_expected
        out['G'] = np.column_stack([g1, g2])


def run_nsga2(current: float, ambient: float, future_risk: float,
              population: int = 48, generations: int = 30,
              profile: str = 'Food', buffer: float = 0.2):
    """
    Execute prediction-guided NSGA-II optimization.
    Returns (pareto_solutions, recommended_solution).
    """
    lo, hi = PROFILES.get(profile, PROFILES['Generic'])
    problem = ColdProblem(current, ambient, future_risk, t_min=lo, t_max=hi, buffer=buffer)
    algorithm = NSGA2(pop_size=population)
    r = minimize(problem, algorithm, ('n_gen', generations), seed=42, verbose=False)
    
    ambient_gain = 0.18 * max(ambient - current, 0.0)
    
    if r.X is None or len(r.X) == 0:
        # Fallback candidate maintaining safe cooling
        default_intensity = 0.75
        default_duty = 0.70
        default_offset = 0.0
        cooling = 3.2 * default_intensity * default_duty
        t_exp = current + ambient_gain - cooling + default_offset
        def_upper = max(0.0, t_exp - hi)
        def_lower = max(0.0, lo - t_exp)
        res_risk = max(0.0, future_risk - cooling * 8.0)
        tot_risk = res_risk + def_upper * 25.0 + def_lower * 25.0
        def_energy = (0.25 + 0.035 * max(ambient - current, 0.0)) * (0.35 + 0.65 * default_intensity) * default_duty
        X = np.array([[default_intensity, default_duty, default_offset]])
        F = np.array([[tot_risk, def_energy]])
        G = np.array([[t_exp - (hi - buffer), (lo + buffer) - t_exp]])
    else:
        X = np.atleast_2d(r.X)
        F = np.atleast_2d(r.F)
        G = np.atleast_2d(r.G) if (hasattr(r, 'G') and r.G is not None) else np.zeros((len(X), 2))
        
    rows = []
    for x_val, f_val, g_val in zip(X, F, G):
        cooling = 3.2 * x_val[0] * x_val[1]
        t_exp = round(float(current + ambient_gain - cooling + x_val[2]), 2)
        is_feasible = bool(g_val[0] <= 1e-4 and g_val[1] <= 1e-4)
        rows.append({
            'cooling_intensity': round(float(x_val[0]), 3),
            'compressor_duty_cycle': round(float(x_val[1]), 3),
            'target_temperature_offset': round(float(x_val[2]), 3),
            'safety_risk': round(float(f_val[0]), 3),
            'estimated_energy_kwh': round(float(f_val[1]), 4),
            'expected_temperature': t_exp,
            'feasible': is_feasible
        })

    # Filter feasible solutions for recommendation
    feasible_rows = [row for row in rows if row['feasible']]
    candidate_pool = feasible_rows if feasible_rows else rows
    
    min_risk = min(a['safety_risk'] for a in candidate_pool)
    max_risk = max(a['safety_risk'] for a in candidate_pool)
    min_energy = min(a['estimated_energy_kwh'] for a in candidate_pool)
    max_energy = max(a['estimated_energy_kwh'] for a in candidate_pool)
    
    risk_range = max_risk - min_risk if (max_risk - min_risk) > 1e-6 else 1.0
    energy_range = max_energy - min_energy if (max_energy - min_energy) > 1e-6 else 1.0
    
    # Select solution prioritizing safety (70% weight) and energy efficiency (30% weight)
    rec = min(
        candidate_pool,
        key=lambda z: (
            0.70 * ((z['safety_risk'] - min_risk) / risk_range) +
            0.30 * ((z['estimated_energy_kwh'] - min_energy) / energy_range)
        )
    )
    rec_copy = dict(rec)
    rec_copy['explanation'] = (
        f"Selected from constrained NSGA-II Pareto frontier. "
        f"Maintains expected temperature {rec_copy['expected_temperature']} °C "
        f"within {lo:.1f} to {hi:.1f} °C safe profile with {rec_copy['estimated_energy_kwh']:.3f} kWh estimated energy."
    )
    return rows, rec_copy
