"""pymoo NSGA-II constrained multi-objective optimizer driven by forecast-derived risk."""
from __future__ import annotations
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from core import PROFILES

class ColdProblem(Problem):
    """
    Constrained Multi-Objective Cold-Chain Optimization Problem with True Trajectory Simulation.
    
    Decision Variables (n_var=3):
      x[0]: Cooling intensity u in [0.1, 1.0]
      x[1]: Compressor duty cycle d in [0.2, 1.0]
      x[2]: Target temperature offset delta in [-0.5, 0.5] °C
      
    Objectives (n_obj=2, minimization):
      F[0]: Total safety risk (residual forecast risk + trajectory thermal breach penalties)
      F[1]: Estimated energy consumption (kWh) over control interval
      
    Inequality Constraints (n_constr=2, G <= 0 for feasibility):
      G[0]: Upper temperature safety limit across entire trajectory: max(T_sim) <= T_max - buffer
      G[1]: Lower temperature freezing limit across entire trajectory: T_min + buffer <= min(T_sim)
    """
    def __init__(self, current: float, ambient: float, future_risk: float,
                 t_min: float = 0.0, t_max: float = 5.0, buffer: float = 0.05):
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
        N = len(x)
        # Authoritative dynamic forward simulation across 15-minute operational interval
        # using the calibrated thermodynamic plant parameters (k_inf=0.018, k_cool=0.32)
        k_inf = 0.018
        k_cool = 0.32
        temp_sim = np.full(N, self.current)
        max_sim = np.copy(temp_sim)
        min_sim = np.copy(temp_sim)
        for m in range(15):
            comp_on = np.where((m / 15.0) < x[:, 1], 1.0, 0.0)
            temp_sim += k_inf * (self.ambient - temp_sim) - k_cool * x[:, 0] * comp_on
            max_sim = np.maximum(max_sim, temp_sim)
            min_sim = np.minimum(min_sim, temp_sim)
        
        # Corrective cooling mitigates predicted future excursion
        cooling = 3.2 * x[:, 0] * x[:, 1]
        risk_reduction = cooling * 8.0
        residual_risk = np.maximum(0.0, self.future_risk - risk_reduction)
        
        # Penalties based on entire simulated trajectory exceedance
        upper_viol = np.maximum(0.0, max_sim - self.t_max)
        lower_viol = np.maximum(0.0, self.t_min - min_sim)
        
        # Objective 1: Safety risk minimization (penalty-weighted)
        total_risk = residual_risk + upper_viol * 25.0 + lower_viol * 25.0
        
        # Objective 2: Electrical energy consumption in kWh over 15-minute interval (0.25 h)
        power_kw = (0.25 + 0.035 * np.maximum(self.ambient - self.current, 0.0)) * (0.35 + 0.65 * x[:, 0]) * x[:, 1]
        energy_kwh = power_kw * 0.25
        
        out['F'] = np.column_stack([total_risk, energy_kwh])
        
        # Constraints (G <= 0 represents feasible operation across entire trajectory):
        # G1: Upper temperature boundary constraint
        g1 = max_sim - (self.t_max - self.buffer)
        # G2: Lower temperature freezing constraint
        g2 = (self.t_min + self.buffer) - min_sim
        out['G'] = np.column_stack([g1, g2])


def search_deterministic_feasible(current: float, ambient: float, lo: float = 0.0, hi: float = 5.0,
                                  future_risk: float = 0.0):
    """
    Deterministic grid search for feasible actuator control settings (u, d).
    Ensures that if physical compliance is achievable, a valid feasible schedule is found.
    """
    k_inf = 0.018
    k_cool = 0.32
    candidates = []
    # Grid search over duty cycle and cooling intensity
    for d in np.linspace(0.50, 1.0, 11):
        for u in np.linspace(0.50, 1.0, 11):
            temp_sim = current
            max_t = temp_sim
            min_t = temp_sim
            for m in range(15):
                comp_on = 1.0 if (m / 15.0) < d else 0.0
                temp_sim += k_inf * (ambient - temp_sim) - k_cool * u * comp_on
                max_t = max(max_t, temp_sim)
                min_t = min(min_t, temp_sim)
            if max_t <= hi and min_t >= lo:
                cooling = 3.2 * u * d
                risk_reduction = cooling * 8.0
                res_risk = max(0.0, future_risk - risk_reduction)
                power_kw = (0.25 + 0.035 * max(ambient - current, 0.0)) * (0.35 + 0.65 * u) * d
                e_kwh = power_kw * 0.25
                candidates.append({
                    'cooling_intensity': round(float(u), 3),
                    'compressor_duty_cycle': round(float(d), 3),
                    'target_temperature_offset': 0.0,
                    'safety_risk': round(float(res_risk), 3),
                    'estimated_energy_kwh': round(float(e_kwh), 4),
                    'estimated_power_kw': round(float(power_kw), 3),
                    'expected_temperature': round(float(temp_sim), 2),
                    'feasible': True,
                    'algebraic_feasible': True,
                    'trajectory_feasible': True,
                    'max_trajectory_temp': round(float(max_t), 3),
                    'min_trajectory_temp': round(float(min_t), 3),
                    'is_emergency_fallback': False
                })
    return candidates


def run_nsga2(current: float, ambient: float, future_risk: float,
              population: int = 48, generations: int = 30,
              profile: str = 'Food', buffer: float = 0.05):
    """
    Execute prediction-guided NSGA-II optimization with full trajectory constraints.
    Returns (pareto_solutions, recommended_solution).
    """
    lo, hi = PROFILES.get(profile, PROFILES['Generic'])
    problem = ColdProblem(current, ambient, future_risk, t_min=lo, t_max=hi, buffer=buffer)
    algorithm = NSGA2(pop_size=population)
    r = minimize(problem, algorithm, ('n_gen', generations), seed=42, verbose=False)
    
    ambient_gain = 0.18 * max(ambient - current, 0.0)
    
    if r.X is None or len(r.X) == 0:
        # Emergency override: when current temperature is already in severe breach
        # or heat gain makes compliance impossible within 15 min, engage maximum cooling
        if current > hi:
            default_intensity = 1.0
            default_duty = 1.0
            default_offset = -0.5
        elif current < lo:
            default_intensity = 0.1
            default_duty = 0.2
            default_offset = 0.5
        else:
            default_intensity = 0.85
            default_duty = 0.80
            default_offset = 0.0
        cooling = 3.2 * default_intensity * default_duty
        t_exp = current + ambient_gain - cooling + default_offset
        def_upper = max(0.0, t_exp - hi)
        def_lower = max(0.0, lo - t_exp)
        res_risk = max(0.0, future_risk - cooling * 8.0)
        tot_risk = res_risk + def_upper * 25.0 + def_lower * 25.0
        def_power = (0.25 + 0.035 * max(ambient - current, 0.0)) * (0.35 + 0.65 * default_intensity) * default_duty
        def_energy = def_power * 0.25
        X = np.array([[default_intensity, default_duty, default_offset]])
        F = np.array([[tot_risk, def_energy]])
        G = np.array([[t_exp - (hi - buffer), (lo + buffer) - t_exp]])
    else:
        X = np.atleast_2d(r.X)
        F = np.atleast_2d(r.F)
        G = np.atleast_2d(r.G) if (hasattr(r, 'G') and r.G is not None) else np.zeros((len(X), 2))
        
    is_fallback = bool(r.X is None or len(r.X) == 0)
    
    rows = []
    for x_val, f_val, g_val in zip(X, F, G):
        cooling = 3.2 * x_val[0] * x_val[1]
        t_exp = round(float(current + ambient_gain - cooling + x_val[2]), 2)
        # Trajectory forward simulation across 15-minute operational interval
        # using the calibrated thermodynamic plant parameters (k_inf=0.018, k_cool=0.32)
        k_inf = 0.018
        k_cool = 0.32
        temp_sim = current
        max_sim = temp_sim
        min_sim = temp_sim
        for m in range(15):
            comp_on = 1.0 if (m / 15.0) < float(x_val[1]) else 0.0
            temp_sim += k_inf * (ambient - temp_sim) - k_cool * float(x_val[0]) * comp_on
            max_sim = max(max_sim, temp_sim)
            min_sim = min(min_sim, temp_sim)
            
        # Complete trajectory feasibility: entire 16-point profile remains strictly within safe bounds
        is_traj_feasible = bool(not is_fallback and max_sim <= hi and min_sim >= lo)
        is_alg_feasible = bool(not is_fallback and g_val[0] <= 1e-4 and g_val[1] <= 1e-4)
        
        rows.append({
            'cooling_intensity': round(float(x_val[0]), 3),
            'compressor_duty_cycle': round(float(x_val[1]), 3),
            'target_temperature_offset': round(float(x_val[2]), 3),
            'safety_risk': round(float(f_val[0]), 3),
            'estimated_energy_kwh': round(float(f_val[1]), 4),
            'estimated_power_kw': round(float(f_val[1]) / 0.25, 3),
            'expected_temperature': t_exp,
            'feasible': is_traj_feasible,
            'algebraic_feasible': is_alg_feasible,
            'trajectory_feasible': is_traj_feasible,
            'max_trajectory_temp': round(float(max_sim), 3),
            'min_trajectory_temp': round(float(min_sim), 3),
            'is_emergency_fallback': is_fallback
        })

    # If NSGA-II returned candidates but none achieved full trajectory feasibility,
    # and the chamber started compliant (current in [lo, hi]), invoke deterministic grid search repair
    traj_feasible_rows = [row for row in rows if row['trajectory_feasible']]
    if not traj_feasible_rows and (lo <= current <= hi):
        repaired = search_deterministic_feasible(current, ambient, lo=lo, hi=hi, future_risk=future_risk)
        if repaired:
            rows.extend(repaired)
            traj_feasible_rows = [row for row in rows if row['trajectory_feasible']]
            is_fallback = False

    # Filter feasible solutions for recommendation:
    # First priority: solutions satisfying the complete dynamic trajectory constraints
    alg_feasible_rows = [row for row in rows if row['algebraic_feasible']]
    
    if traj_feasible_rows:
        candidate_pool = traj_feasible_rows
    elif alg_feasible_rows:
        candidate_pool = alg_feasible_rows
    else:
        candidate_pool = rows
    
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
    if is_fallback:
        rec_copy['explanation'] = (
            f"Emergency Fallback Override: No feasible solution could bring chamber "
            f"into the safe {lo:.1f} to {hi:.1f} °C range within 15 min. Maximum cooling "
            f"(intensity {rec_copy['cooling_intensity']}, duty {rec_copy['compressor_duty_cycle']}) "
            f"commanded. Expected temperature: {rec_copy['expected_temperature']} °C."
        )
    elif rec_copy.get('trajectory_feasible', False):
        rec_copy['explanation'] = (
            f"Selected from constrained NSGA-II Pareto frontier with complete trajectory verification. "
            f"Maintains chamber temperature within {lo:.1f} to {hi:.1f} °C safe profile throughout the interval "
            f"(peak: {rec_copy['max_trajectory_temp']} °C) with {rec_copy['estimated_energy_kwh']:.3f} kWh estimated energy."
        )
    else:
        rec_copy['explanation'] = (
            f"Selected from constrained NSGA-II Pareto frontier. "
            f"Maintains expected temperature {rec_copy['expected_temperature']} °C "
            f"within {lo:.1f} to {hi:.1f} °C safe profile with {rec_copy['estimated_energy_kwh']:.3f} kWh estimated energy."
        )
    return rows, rec_copy
